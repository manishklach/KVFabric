from __future__ import annotations

from dataclasses import dataclass

from .compression import apply_compression
from .config import PolicyConfig
from .kv_block import KVBlock
from .memory_tier import MemoryTier
from .metrics import SimulationMetrics


@dataclass(slots=True)
class SchedulerState:
    step: int
    current_block_index: int


class KVScheduler:
    """Placement and temperature logic for baseline and KVFlow modes."""

    def __init__(self, tiers: dict[str, MemoryTier], policy: PolicyConfig, mode: str) -> None:
        self.tiers = tiers
        self.policy = policy
        self.mode = mode

    def classify_block(self, block: KVBlock, state: SchedulerState) -> str:
        if self.mode == "baseline":
            return "warm"

        age_tokens = max(0, state.current_block_index * block.token_count - block.token_start)
        if age_tokens <= self.policy.recent_window:
            return "hot"
        if block.access_count >= self.policy.warm_reuse_threshold:
            return "warm"
        return "cold"

    def compression_choice(self, block: KVBlock, state: SchedulerState) -> str:
        if self.mode == "baseline":
            return "none"
        distance = max(0, state.current_block_index * block.token_count - block.token_start)
        if block.temperature != "cold":
            return "none"
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
            if len(unique_candidates) >= self.policy.prefetch_window:
                break
        return unique_candidates

    def ensure_placement(self, block: KVBlock, metrics: SimulationMetrics, allow_eviction: bool = True) -> None:
        target_tiers = self.preferred_tiers(block)
        size_bytes = block.effective_size_bytes()

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

        for resident_id in list(tier.resident_blocks):
            if resident_id == preferred_block_id:
                continue
            tier.free(resident_id, needed_bytes)
            metrics.blocks_evicted += 1
            if tier.can_fit(needed_bytes):
                return True
        return tier.can_fit(needed_bytes)

    def update_block_state(self, block: KVBlock, state: SchedulerState, metrics: SimulationMetrics) -> None:
        previous_size = block.effective_size_bytes()
        block.temperature = self.classify_block(block, state)
        desired_compression = self.compression_choice(block, state)
        if desired_compression != block.compression_state:
            saved = apply_compression(block, desired_compression)
            if saved > 0:
                metrics.compression_savings_bytes += saved
                metrics.blocks_compressed += 1
            current_tier = self.tiers[block.current_tier]
            current_tier.used_bytes = max(0, current_tier.used_bytes - previous_size + block.effective_size_bytes())
        self.ensure_placement(block, metrics)
