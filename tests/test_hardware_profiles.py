from kvfabric.config import SimulationConfig
from kvfabric.hardware_profiles import HARDWARE_PROFILES, get_hardware_profile


def test_hardware_profiles_expose_expected_devices() -> None:
    assert "H100_SXM5" in HARDWARE_PROFILES
    assert "H200_SXM" in HARDWARE_PROFILES
    assert get_hardware_profile("H200_SXM").hbm_capacity_gb > get_hardware_profile("H100_SXM5").hbm_capacity_gb


def test_config_can_apply_hardware_profile() -> None:
    config = SimulationConfig.default().with_hardware_profile("MI300X")
    assert config.tiers["hbm"].capacity_bytes > 100 * 1024 * 1024 * 1024
    assert config.hardware_profile_name == "MI300X"
