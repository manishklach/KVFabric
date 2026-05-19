from kvfabric.config import PolicyConfig, SimulationConfig
from kvfabric.kv_block import KVBlock
from kvfabric.memory_tier import MemoryTier
from kvfabric.metrics import SimulationMetrics
from kvfabric.scheduler import KVScheduler, SchedulerState


def build_scheduler(mode: str) -> KVScheduler:
    config = SimulationConfig.default()
    tiers = {name: MemoryTier.from_config(tier_config) for name, tier_config in config.tiers.items()}
    return KVScheduler(tiers, PolicyConfig(), mode=mode, compression=config.compression)


def test_hot_block_prefers_hbm_or_nearby_tier() -> None:
    scheduler = build_scheduler("kvfabric")
    block = KVBlock(
        block_id="hot",
        layer_id=0,
        head_id=0,
        token_start=0,
        token_count=16,
        size_bytes=4096,
        access_count=5,
        current_tier="cxl",
    )
    scheduler.tiers["cxl"].allocate(block.block_id, block.effective_size_bytes())
    scheduler.update_block_state(block, SchedulerState(step=10, current_block_index=0), SimulationMetrics())
    assert block.temperature == "hot"
    assert block.current_tier in {"hbm", "cxl"}


def test_cold_block_gets_compressed_and_demoted() -> None:
    scheduler = build_scheduler("kvfabric")
    block = KVBlock(
        block_id="cold",
        layer_id=0,
        head_id=0,
        token_start=0,
        token_count=16,
        size_bytes=4096,
        access_count=0,
        current_tier="hbm",
    )
    scheduler.tiers["hbm"].allocate(block.block_id, block.effective_size_bytes())
    metrics = SimulationMetrics()
    scheduler.update_block_state(block, SchedulerState(step=10, current_block_index=100), metrics)
    assert block.temperature == "cold"
    assert block.compression_state in {"int8", "int4"}
    assert block.current_tier in {"cxl", "dram", "hbm"}
    assert metrics.blocks_compressed >= 1
