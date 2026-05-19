from kvfabric.config import SimulationConfig
from kvfabric.simulator import Simulator


def test_sram_capacity_is_not_exceeded() -> None:
    config = SimulationConfig.default()
    config.tiers["sram"].capacity_bytes = 64 * 1024
    simulator = Simulator(config, mode="kvfabric")
    simulator.run()
    assert simulator.tiers["sram"].used_bytes <= simulator.tiers["sram"].capacity_bytes


def test_residency_classification_keeps_hot_blocks_out_of_cold_state() -> None:
    config = SimulationConfig.default()
    simulator = Simulator(config, mode="kvfabric")
    simulator.run()
    hot_blocks = [block for block in simulator.blocks.values() if block.last_access_step >= 0 and block.staged_in_sram]
    assert hot_blocks
    assert all(block.temperature in {"hot", "warm"} for block in hot_blocks)
