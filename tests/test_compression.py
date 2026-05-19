from kvflow.compression import apply_compression, compression_ratio, decompression_penalty_ns
from kvflow.kv_block import KVBlock


def test_compression_ratios_and_penalties() -> None:
    assert compression_ratio("none") == 1.0
    assert compression_ratio("int8") == 0.5
    assert compression_ratio("int4") == 0.25
    assert decompression_penalty_ns("int8") > decompression_penalty_ns("none")
    assert decompression_penalty_ns("int4") > decompression_penalty_ns("int8")


def test_apply_compression_changes_effective_size() -> None:
    block = KVBlock(
        block_id="b0",
        layer_id=0,
        head_id=0,
        token_start=0,
        token_count=128,
        size_bytes=4096,
    )
    saved = apply_compression(block, "int4")
    assert block.effective_size_bytes() == 1024
    assert saved == 3072
