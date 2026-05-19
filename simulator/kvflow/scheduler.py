from __future__ import annotations

from dataclasses import dataclass

from .compression import apply_compression
from .config import CompressionConfig, PolicyConfig
from .kv_block import KVBlock
from .memory_tier import MemoryTier
from .metrics import SimulationMetrics
from .policies import BasePolicy, HotWarmColdPolicy, LFUCompressionPolicy, LRUHotWindowPolicy, PolicyState


@dataclass(slots=True)
class SchedulerState:
    step: int
    current_block_index: int

    def to_policy_state(self) -> PolicyState:
        return PolicyState(step=self.step, current_block_index=self.current_block_index)


class KVScheduler:
    """Placement and temperature logic for baseline and KVFabric modes."""

    def __init__(
        self,
        tiers: dict[str, MemoryTier],
        policy: PolicyConfig,
        mode: str,
        compression: CompressionConfig,
        promotion_policy: BasePolicy | None = None,
        compression_policy: BasePolicy | None = None,
        eviction_policy: BasePolicy | None = None,
    ) -> None:
        self.tiers = tiers
        self.policy = policy
        self.mode = mode
        self.compression = compression
        self.promotion_policy = promotion_policy or LRUHotWindowPolicy(policy)
        self.compression_policy = compression_policy or LFUCompressionPolicy(policy)
        self.eviction_policy = eviction_policy or HotWarmColdPolicy(policy)
        self.temperature_policy = HotWarmColdPolicy(policy)

    def classify_block(self, block: KVBlock, state: SchedulerState) -> str:
        if self.mode == "baseline":
            return "warm"
        return self.temperature_policy.temperature_for_block(block, state.to_policy_state())

    def compression_choice(self, block: KVBlock, state: SchedulerState) -> str:
        if self.mode == "baseline":
            return "none"

        if block.temperature != "cold":
            return "none"

        selected = self.compression_policy.select_blocks_for_compression([block], state.to_policy_state(), limit=1)
        if not selected:
            return "none"

        distance = max(0, state.current_block_index * block.token_count - block.token_start)
        if distance >= self.policy.cold_int4_distance:
            return "int4"
        return "int8"

    def preferred_tiers(self, block: KVBlock) -> list[str]:
        if self.mode == "baseline":
            return ["hbm", "cxl", "dram"]
        if block.temperature == "hot":
            return ["hbm", "cxl", "dram"]
        if block.temperature == "warm":
            return ["hbm", "cxl", "dram"]
        return ["cxl", "dram", "hbm"]

    def prefetch_candidates(self, blocks: dict[str, KVBlock], accesses: list[str], state: SchedulerState) -> list[KVBlock]:
        if self.mode == "baseline":
            return []

        unique_candidates: list[KVBlock] = []
        seen: set[str] = set()
        for block_id in accesses:
            if block_id in seen:
                continue
            block = blocks[block_id]
            if block.temperature == "hot" and not block.staged_in_sram:
                unique_candidates.append(block)
                seen.add(block_id)

        return self.promotion_policy.select_blocks_for_promotion(
            unique_candidates,
            state.to_policy_state(),
            limit=self.policy.prefetch_window,
        )

    def ensure_placement(self, block: KVBlock, metrics: SimulationMetrics, allow_eviction: bool = True) -> None:
        target_tiers = self.preferred_tiers(block)
        size_bytes = block.effective_size_bytes(self.compression.ratios)

        for tier_name in target_tiers:
            if self._move_if_possible(block, tier_name, size_bytes, metrics):
                return
            if allow_eviction and self._evict_for_fit(tier_name, size_bytes, metrics, preferred_block_id=block.block_id):
                if self._move_if_possible(block, tier_name, size_bytes, metrics):
                    return

    def _move_if_possible(self, block: KVBlock, target_tier_name: str, size_bytes: int, metrics: SimulationMetrics) -> bool:
        target_tier = self.tiers[target_tier_name]
        if block.current_tier == target_tier_name:
            return True
        if not target_tier.allocate(block.block_id, size_bytes):
            return False

        source_tier = self.tiers[block.current_tier]
        source_tier.free(block.block_id, size_bytes)
        block.current_tier = target_tier_name
        metrics.total_bytes_moved += size_bytes
        return True

    def _evict_for_fit(
        self,
        tier_name: str,
        needed_bytes: int,
        metrics: SimulationMetrics,
        preferred_block_id: str,
    ) -> bool:
        tier = self.tiers[tier_name]
        if tier.can_fit(needed_bytes):
            return True

        resident_blocks = [block_id for block_id in tier.resident_blocks if block_id != preferred_block_id]
        ranked_ids = self.eviction_policy.select_blocks_for_eviction(
            [
                KVBlock(
                    block_id=block_id,
                    layer_id=0,
                    head_id=0,
                    token_start=0,
                    token_count=1,
                    size_bytes=needed_bytes,
                    temperature="cold",
                )
                for block_id in resident_blocks
            ]
        )
        for resident in ranked_ids:
            tier.free(resident.block_id, needed_bytes)
            metrics.blocks_evicted += 1
            if tier.can_fit(needed_bytes):
                return True
        return tier.can_fit(needed_bytes)

    def update_block_state(self, block: KVBlock, state: SchedulerState, metrics: SimulationMetrics) -> None:
        previous_size = block.effective_size_bytes(self.compression.ratios)
        block.temperature = self.classify_block(block, state)
        desired_compression = self.compression_choice(block, state)
        if desired_compression != block.compression_state:
            saved = apply_compression(block, desired_compression, self.compression)
            if saved > 0:
                metrics.compression_savings_bytes += saved
                metrics.blocks_compressed += 1
            current_tier = self.tiers[block.current_tier]
            current_tier.used_bytes = max(
                0,
                current_tier.used_bytes - previous_size + block.effective_size_bytes(self.compression.ratios),
            )
        self.ensure_placement(block, metrics)
