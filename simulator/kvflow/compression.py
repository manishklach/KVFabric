from __future__ import annotations

from .kv_block import COMPRESSION_RATIOS, DECOMPRESSION_PENALTIES_NS, KVBlock


def compression_ratio(state: str) -> float:
    return COMPRESSION_RATIOS[state]


def decompression_penalty_ns(state: str) -> float:
    return DECOMPRESSION_PENALTIES_NS[state]


def apply_compression(block: KVBlock, state: str) -> int:
    """Apply a simulated compression state and return bytes saved."""
    previous_size = block.effective_size_bytes()
    block.compression_state = state
    return max(0, previous_size - block.effective_size_bytes())
