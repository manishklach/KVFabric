from __future__ import annotations

from dataclasses import dataclass


COMPRESSION_RATIOS: dict[str, float] = {"none": 1.0, "int8": 0.5, "int4": 0.25}
DECOMPRESSION_PENALTIES_NS: dict[str, float] = {"none": 0.0, "int8": 120.0, "int4": 260.0}


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

    def effective_size_bytes(self) -> int:
        ratio = COMPRESSION_RATIOS[self.compression_state]
        return max(1, int(self.size_bytes * ratio))

    def compression_savings_bytes(self) -> int:
        return self.size_bytes - self.effective_size_bytes()

    def decompression_penalty_ns(self) -> float:
        return DECOMPRESSION_PENALTIES_NS[self.compression_state]
