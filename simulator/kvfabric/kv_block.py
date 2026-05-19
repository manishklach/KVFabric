from __future__ import annotations

from dataclasses import dataclass

from .config import DEFAULT_COMPRESSION_RATIOS, DEFAULT_DECOMPRESSION_PENALTIES_NS


COMPRESSION_RATIOS: dict[str, float] = dict(DEFAULT_COMPRESSION_RATIOS)
DECOMPRESSION_PENALTIES_NS: dict[str, float] = dict(DEFAULT_DECOMPRESSION_PENALTIES_NS)


@dataclass(slots=True)
class KVBlock:
    """Logical unit of KV-cache tracked by the simulator."""

    block_id: str
    layer_id: int
    head_id: int
    token_start: int
    token_count: int
    size_bytes: int
    last_access_step: int = -1
    access_count: int = 0
    temperature: str = "cold"
    compression_state: str = "none"
    current_tier: str = "hbm"
    staged_in_sram: bool = False
    last_prefetch_step: int = -1

    def effective_size_bytes(self, compression_ratios: dict[str, float] | None = None) -> int:
        ratios = compression_ratios or COMPRESSION_RATIOS
        ratio = ratios[self.compression_state]
        return max(1, int(self.size_bytes * ratio))

    def compression_savings_bytes(self, compression_ratios: dict[str, float] | None = None) -> int:
        return self.size_bytes - self.effective_size_bytes(compression_ratios)

    def decompression_penalty_ns(self, penalties_ns: dict[str, float] | None = None) -> float:
        penalties = penalties_ns or DECOMPRESSION_PENALTIES_NS
        return penalties[self.compression_state]
