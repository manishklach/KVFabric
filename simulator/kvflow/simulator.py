from __future__ import annotations

from dataclasses import replace

from .config import SimulationConfig
from .kv_block import KVBlock
from .memory_tier import MemoryTier
from .metrics import SimulationMetrics
from .pipeline import PipelineEngine
from .scheduler import KVScheduler, SchedulerState
from .workload import Workload


class Simulator:
    """Runs either the baseline path or the KVFabric path over the same workload."""

    def __init__(self, config: SimulationConfig, mode: str) -> None:
        if mode not in {"baseline", "kvflow"}:
            raise ValueError(f"Unsupported mode: {mode}")

        self.config = config
        self.mode = mode
        self.workload_config = config.create_workload_config()
        self.workload = Workload(self.workload_config)
        self.tiers = {name: MemoryTier.from_config(tier_config) for name, tier_config in config.tiers.items()}
        self.metrics = SimulationMetrics()
        self.scheduler = KVScheduler(self.tiers, config.policy, mode, config.compression)
        self.pipeline = PipelineEngine(config.pipeline)
        self.blocks = self._build_blocks()
        self._seed_initial_residency()

    def describe_config(self) -> dict[str, object]:
        return {
            **self.config.display_dict(),
            "assumed_kv_block_size_bytes": self.workload.assumed_block_size_bytes(),
        }

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

            size_bytes = block.effective_size_bytes(self.config.compression.ratios)
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
            next_accesses = accesses_by_step[min(step + 1, len(accesses_by_step) - 1)]

            self._complete_prefetches()
            self._update_temperatures(accesses, state)
            self._prefetch(next_accesses, state)
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
        limit = self.config.pipeline.max_prefetch_per_step
        for block in self.scheduler.prefetch_candidates(self.blocks, accesses, state)[:limit]:
            if block.staged_in_sram:
                continue
            source_tier = self.tiers[block.current_tier]
            size_bytes = block.effective_size_bytes(self.config.compression.ratios)
            transfer_time_ns = source_tier.latency_ns + source_tier.transfer_time_ns(size_bytes)
            if self.pipeline.schedule_prefetch(
                block.block_id,
                now_ns=self.pipeline.current_time_ns,
                transfer_time_ns=transfer_time_ns,
                decompression_time_ns=block.decompression_penalty_ns(
                    self.config.compression.decompression_penalties_ns
                ),
            ):
                block.last_prefetch_step = state.step
                self.metrics.prefetched_blocks += 1
                self.metrics.total_bytes_moved += size_bytes

    def _complete_prefetches(self) -> None:
        for event in self.pipeline.consume_ready_prefetches(self.pipeline.current_time_ns):
            block = self.blocks[event.block_id]
            if block.staged_in_sram:
                continue
            if self._stage_in_sram(block):
                self.metrics.staged_blocks += 1

    def _service_accesses(self, accesses: list[str], state: SchedulerState) -> None:
        unique_miss_ids: set[str] = set()
        required_transfer_ns = 0.0
        required_decompression_ns = 0.0

        for block_id in accesses:
            block = self.blocks[block_id]
            self.metrics.total_accesses += 1

            if block.staged_in_sram:
                self.metrics.sram_hits += 1
            else:
                tier = self.tiers[block.current_tier]
                size_bytes = block.effective_size_bytes(self.config.compression.ratios)
                if block_id not in unique_miss_ids:
                    unique_miss_ids.add(block_id)
                    required_transfer_ns += tier.latency_ns + tier.transfer_time_ns(size_bytes)
                    required_decompression_ns += block.decompression_penalty_ns(
                        self.config.compression.decompression_penalties_ns
                    )

            if block.current_tier == "hbm":
                self.metrics.hbm_bytes_read += block.effective_size_bytes(self.config.compression.ratios)
            elif block.current_tier == "cxl":
                self.metrics.cxl_bytes_read += block.effective_size_bytes(self.config.compression.ratios)
            elif block.current_tier == "dram":
                self.metrics.host_bytes_read += block.effective_size_bytes(self.config.compression.ratios)

            block.last_access_step = state.step
            block.access_count += 1

        compute_time_ns = self.config.pipeline.compute_ns_per_access * len(accesses)
        step_latency = self.pipeline.model_step(compute_time_ns, required_transfer_ns, required_decompression_ns)
        self.metrics.simulated_latency_ns += step_latency.effective_step_latency_ns
        self.metrics.compute_latency_ns += compute_time_ns
        self.metrics.transfer_latency_ns += required_transfer_ns
        self.metrics.decompression_latency_ns += required_decompression_ns
        self.metrics.overlapped_transfer_ns += step_latency.overlapped_transfer_ns
        self.metrics.exposed_transfer_ns += step_latency.exposed_transfer_ns
        self.metrics.hidden_transfer_ns += step_latency.overlapped_transfer_ns
        self.metrics.overlapped_decompression_ns += step_latency.overlapped_decompression_ns
        self.metrics.exposed_decompression_ns += step_latency.exposed_decompression_ns
        self._refresh_sram_residency()

    def _stage_in_sram(self, block: KVBlock) -> bool:
        sram = self.tiers["sram"]
        size_bytes = block.effective_size_bytes(self.config.compression.ratios)
        if not sram.can_fit(size_bytes):
            self._evict_sram_blocks(size_bytes)
        if not sram.allocate(block.block_id, size_bytes):
            return False
        block.staged_in_sram = True
        return True

    def _evict_sram_blocks(self, needed_bytes: int) -> None:
        sram = self.tiers["sram"]
        if sram.can_fit(needed_bytes):
            return
        staged_blocks = [block for block in self.blocks.values() if block.staged_in_sram]
        eviction_candidates = self.scheduler.eviction_policy.select_blocks_for_eviction(staged_blocks)
        for block in eviction_candidates:
            sram.free(block.block_id, block.effective_size_bytes(self.config.compression.ratios))
            block.staged_in_sram = False
            self.metrics.blocks_evicted += 1
            if sram.can_fit(needed_bytes):
                return

    def _refresh_sram_residency(self) -> None:
        for block in self.blocks.values():
            if block.staged_in_sram and block.temperature == "cold":
                self.tiers["sram"].free(block.block_id, block.effective_size_bytes(self.config.compression.ratios))
                block.staged_in_sram = False
