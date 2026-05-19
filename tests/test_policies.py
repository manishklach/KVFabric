from kvfabric.config import PolicyConfig
from kvfabric.kv_block import KVBlock
from kvfabric.policies import HotWarmColdPolicy, LFUCompressionPolicy, LRUHotWindowPolicy, PolicyState


def make_block(block_id: str, token_start: int, access_count: int, last_access_step: int, temperature: str = "cold") -> KVBlock:
    return KVBlock(
        block_id=block_id,
        layer_id=0,
        head_id=0,
        token_start=token_start,
        token_count=16,
        size_bytes=4096,
        access_count=access_count,
        last_access_step=last_access_step,
        temperature=temperature,
    )


def test_lru_selects_oldest_blocks_for_eviction() -> None:
    policy = LRUHotWindowPolicy(PolicyConfig())
    blocks = [
        make_block("b0", token_start=0, access_count=3, last_access_step=8),
        make_block("b1", token_start=16, access_count=2, last_access_step=2),
        make_block("b2", token_start=32, access_count=4, last_access_step=5),
    ]
    selected = policy.select_blocks_for_eviction(blocks, limit=2)
    assert [block.block_id for block in selected] == ["b1", "b2"]


def test_lfu_selects_least_accessed_blocks_for_compression() -> None:
    policy = LFUCompressionPolicy(PolicyConfig())
    blocks = [
        make_block("b0", token_start=0, access_count=10, last_access_step=8),
        make_block("b1", token_start=16, access_count=1, last_access_step=2),
        make_block("b2", token_start=32, access_count=3, last_access_step=5),
    ]
    selected = policy.select_blocks_for_compression(blocks, limit=2)
    assert [block.block_id for block in selected] == ["b1", "b2"]


def test_hot_warm_cold_preserves_recent_hot_blocks() -> None:
    policy = HotWarmColdPolicy(PolicyConfig(recent_window=64, warm_reuse_threshold=2))
    state = PolicyState(step=20, current_block_index=4)
    blocks = [
        make_block("hot", token_start=64, access_count=1, last_access_step=18),
        make_block("warm", token_start=0, access_count=4, last_access_step=10),
        make_block("cold", token_start=0, access_count=0, last_access_step=1),
    ]
    selected = policy.select_blocks_for_promotion(blocks, state=state, limit=1)
    assert [block.block_id for block in selected] == ["hot"]
