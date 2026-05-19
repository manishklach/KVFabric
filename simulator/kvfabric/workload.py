from __future__ import annotations

from dataclasses import dataclass

from .config import WorkloadConfig


@dataclass(slots=True)
class WorkloadBlockSpec:
    """Static description of one logical KV block."""

    block_id: str
    layer_id: int
    head_id: int
    token_start: int
    token_count: int
    size_bytes: int


class Workload:
    """Generates a deterministic long-context decode access pattern."""

    def __init__(self, config: WorkloadConfig) -> None:
        self.config = config
        self.token_block_size = config.kv_block_tokens
        self.num_token_blocks = max(1, config.context_length // self.token_block_size)
        self.block_size_bytes = self.token_block_size * config.head_dim * config.dtype_bytes * 2

    def build_block_catalog(self) -> list[WorkloadBlockSpec]:
        blocks: list[WorkloadBlockSpec] = []
        for layer_id in range(self.config.model_layers):
            for head_id in range(self.config.num_heads):
                for block_index in range(self.num_token_blocks):
                    token_start = block_index * self.token_block_size
                    blocks.append(
                        WorkloadBlockSpec(
                            block_id=f"L{layer_id}_H{head_id}_B{block_index}",
                            layer_id=layer_id,
                            head_id=head_id,
                            token_start=token_start,
                            token_count=self.token_block_size,
                            size_bytes=self.block_size_bytes,
                        )
                    )
        return blocks

    def access_sequence(self) -> list[list[str]]:
        """
        Create a deterministic sequence of block accesses per decode step.

        The pattern intentionally mixes:
        - a recent local window that should become hot
        - a medium-range region that should remain warm
        - a periodic long-tail sample that becomes cold but occasionally reused
        """
        accesses: list[list[str]] = []
        layers = self.config.model_layers
        heads = self.config.num_heads
        for step in range(self.config.decode_steps):
            current_block = min(self.num_token_blocks - 1, step // 2)
            recent_start = max(0, current_block - 2)
            warm_block = max(0, current_block - 8)
            cold_stride_block = (step * 11) % self.num_token_blocks

            step_accesses: list[str] = []
            for layer_id in range(layers):
                hot_head = (step + layer_id) % heads
                warm_head = (step * 3 + layer_id) % heads
                cold_head = (step * 7 + layer_id) % heads

                for block_index in range(recent_start, current_block + 1):
                    step_accesses.append(f"L{layer_id}_H{hot_head}_B{block_index}")

                step_accesses.append(f"L{layer_id}_H{warm_head}_B{warm_block}")
                step_accesses.append(f"L{layer_id}_H{cold_head}_B{cold_stride_block}")

            accesses.append(step_accesses)
        return accesses

    def assumed_block_size_bytes(self) -> int:
        return self.block_size_bytes
