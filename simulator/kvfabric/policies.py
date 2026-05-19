from __future__ import annotations

from dataclasses import dataclass

from .config import PolicyConfig
from .kv_block import KVBlock


@dataclass(slots=True)
class PolicyState:
    step: int
    current_block_index: int


class BasePolicy:
    """Common interface for scheduler policy extensions."""

    def __init__(self, config: PolicyConfig) -> None:
        self.config = config

    def select_blocks_for_promotion(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        return blocks[:limit] if limit is not None else list(blocks)

    def select_blocks_for_compression(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        return blocks[:limit] if limit is not None else list(blocks)

    def select_blocks_for_eviction(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        return blocks[:limit] if limit is not None else list(blocks)


class LRUHotWindowPolicy(BasePolicy):
    """Prefers recent blocks for promotion and oldest blocks for eviction."""

    def select_blocks_for_promotion(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        if state is None:
            ranked = sorted(blocks, key=lambda block: block.last_access_step, reverse=True)
        else:
            ranked = sorted(
                blocks,
                key=lambda block: abs(state.current_block_index * block.token_count - block.token_start),
            )
        return ranked[:limit] if limit is not None else ranked

    def select_blocks_for_eviction(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        ranked = sorted(blocks, key=lambda block: block.last_access_step)
        return ranked[:limit] if limit is not None else ranked


class LFUCompressionPolicy(BasePolicy):
    """Selects least-frequently used blocks for more aggressive compression."""

    def select_blocks_for_compression(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        ranked = sorted(
            blocks,
            key=lambda block: (block.access_count, block.last_access_step, block.token_start),
        )
        return ranked[:limit] if limit is not None else ranked


class HotWarmColdPolicy(BasePolicy):
    """Preserves recent hot blocks and pushes colder data out first."""

    def temperature_for_block(self, block: KVBlock, state: PolicyState) -> str:
        age_tokens = max(0, state.current_block_index * block.token_count - block.token_start)
        if age_tokens <= self.config.recent_window:
            return "hot"
        if block.access_count >= self.config.warm_reuse_threshold:
            return "warm"
        return "cold"

    def select_blocks_for_promotion(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        if state is None:
            ranked = sorted(blocks, key=lambda block: (block.temperature != "hot", -block.last_access_step))
        else:
            ranked = sorted(
                blocks,
                key=lambda block: (
                    self.temperature_for_block(block, state) != "hot",
                    abs(state.current_block_index * block.token_count - block.token_start),
                ),
            )
        return ranked[:limit] if limit is not None else ranked

    def select_blocks_for_eviction(
        self,
        blocks: list[KVBlock],
        state: PolicyState | None = None,
        limit: int | None = None,
    ) -> list[KVBlock]:
        def rank(block: KVBlock) -> tuple[int, int, int]:
            temperature_order = {"cold": 0, "warm": 1, "hot": 2}
            return (temperature_order.get(block.temperature, 0), block.last_access_step, block.access_count)

        ranked = sorted(blocks, key=rank)
        return ranked[:limit] if limit is not None else ranked
