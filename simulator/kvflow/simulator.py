from __future__ import annotations

from dataclasses import replace

from .config import SimulationConfig, WorkloadConfig
from .kv_block import KVBlock
from .memory_tier import MemoryTier
from .metrics import SimulationMetrics
from .scheduler import KVScheduler, SchedulerState
from .workload import Workload


class Simulator:
    """Runs either the baseline path or the KVFlow path over the same workload."""

    def __init__(self, config: SimulationConfig, mode: str) -> None:
        if mode not in {"baseline", "kvflow"}:
            raise ValueError(f"Unsupported mode: {mode}")

        self.config = config
        self.mode = mode
        self.workload_config = WorkloadConfig.from_json(config.workload_path)
        self.workload = Workload(self.workload_config)
        self.tiers = {name: MemoryTier.from_config(tier_config) for name, tier_config in config.tiers.items()}
        self.metrics = SimulationMetrics()
        self.scheduler = KVScheduler(self.tiers, config.policy, mode)
        self.blocks = self._build_blocks()
        self._seed_initial_residency()

    def _build_blocks(self) -> dict[str, KVBlock]:
        blocks: dict[str, KVBlock] = {}
        for spec in self.workload.build_block_catalog():
            blocks[spec.block_id] = KVBlock(
                block_id=spec.block_id,
                layer_id=spec.layer_id,
                head_id=spec.head_id,
                token_start=spec.token_start,
                token_count=spec.token_count,
                size_bytes=spec.size_bytes,
            )
        return blocks

    def _seed_initial_residency(self) -> None:
        # Baseline starts by filling HBM and spilling remaining blocks.
        for block in self.blocks.values():
            if self.mode == "kvflow":
                if block.token_start <= self.config.policy.recent_window:
                    block.temperature = "hot"
                    target = "hbm"
                elif block.token_start <= self.config.policy.cold_int4_distance:
                    block.temperature = "warm"
                    target = "cxl"
                else:
                    block.temperature = "cold"
                    block.compression_state = "int8"
                    target = "dram"
            else:
                block.temperature = "warm"
                target = "hbm"

            size_bytes = block.effective_size_bytes()
            if not self.tiers[target].allocate(block.block_id, size_bytes):
                for fallback in ("cxl", "dram"):
                    if self.tiers[fallback].allocate(block.block_id, size_bytes):
                        target = fallback
                        break
            block.current_tier = target

    def run(self) -> SimulationMetrics:
        accesses_by_step = self.workload.access_sequence()
        for step, accesses in enumerate(accesses_by_step):
            current_block_index = min(self.workload.num_token_blocks - 1, step // 2)
            state = SchedulerState(step=step, current_block_index=current_block_index)

            self._update_temperatures(accesses, state)
            self._prefetch(accesses, state)
            self._service_accesses(accesses, state)

        return replace(self.metrics)

    def _update_temperatures(self, accesses: list[str], state: SchedulerState) -> None:
        seen: set[str] = set()
        for block_id in accesses:
            if block_id in seen:
                continue
            seen.add(block_id)
            self.scheduler.update_block_state(self.blocks[block_id], state, self.metrics)

    def _prefetch(self, accesses: list[str], state: SchedulerState) -> None:
        for block in self.scheduler.prefetch_candidates(self.blocks, accesses, state):
            self.scheduler.ensure_placement(block, self.metrics)

    def _service_accesses(self, accesses: list[str], state: SchedulerState) -> None:
        for block_id in accesses:
            block = self.blocks[block_id]
            self.metrics.total_accesses += 1

            # Try to keep imminent hot blocks in SRAM during KVFlow servicing.
            if self.mode == "kvflow" and block.temperature == "hot":
                self.scheduler.ensure_placement(block, self.metrics)

            tier = self.tiers[block.current_tier]
            size_bytes = block.effective_size_bytes()
            read_cost = tier.latency_ns + tier.transfer_time_ns(size_bytes) + block.decompression_penalty_ns()
            self.metrics.simulated_latency_ns += read_cost

            if block.current_tier == "sram":
                self.metrics.sram_hits += 1
            elif block.current_tier == "hbm":
                self.metrics.hbm_bytes_read += size_bytes
            elif block.current_tier == "cxl":
                self.metrics.cxl_bytes_read += size_bytes
            elif block.current_tier == "dram":
                self.metrics.host_bytes_read += size_bytes

            block.last_access_step = state.step
            block.access_count += 1
