from __future__ import annotations

from .config import CompressionConfig, DEFAULT_COMPRESSION_RATIOS, DEFAULT_DECOMPRESSION_PENALTIES_NS
from .kv_block import KVBlock


def compression_ratio(state: str, config: CompressionConfig | None = None) -> float:
    ratios = config.ratios if config is not None else None
    return (ratios or DEFAULT_COMPRESSION_RATIOS)[state]


def decompression_penalty_ns(state: str, config: CompressionConfig | None = None) -> float:
    penalties = config.decompression_penalties_ns if config is not None else None
    return (penalties or DEFAULT_DECOMPRESSION_PENALTIES_NS)[state]


def apply_compression(block: KVBlock, state: str, config: CompressionConfig | None = None) -> int:
    """Apply a simulated compression state and return bytes saved."""
    ratios = config.ratios if config is not None else None
    previous_size = block.effective_size_bytes(ratios)
    block.compression_state = state
    return max(0, previous_size - block.effective_size_bytes(ratios))
