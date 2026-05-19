from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class HardwareProfile:
    """
    Approximate single-node accelerator profile for simulator defaults.

    HBM capacity and bandwidth values are based on vendor product/spec pages.
    SRAM staging capacity and per-tier latency values remain simulator-side
    abstractions because vendors do not expose an equivalent KV-orchestration
    SRAM in this form.
    """

    name: str
    hbm_bandwidth_gbps: float
    hbm_capacity_gb: float
    sram_capacity_mb: float
    cxl_bandwidth_gbps: float
    dram_bandwidth_gbps: float
    estimated_latency_ns: float
    cxl_capacity_gb: float = 24.0
    dram_capacity_gb: float = 64.0
    source: str = ""

    def as_dict(self) -> dict[str, float | str]:
        return asdict(self)


# Sources:
# - NVIDIA H100 product specs: https://www.nvidia.com/en-gb/data-center/h100/
# - NVIDIA H200 product specs: https://www.nvidia.com/en-us/data-center/h200/
# - NVIDIA HGX AI Factory reference architecture for B200:
#   https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html
# - AMD MI300X product page / platform datasheet:
#   https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html
#   https://www.amd.com/content/dam/amd/en/documents/instinct-tech-docs/data-sheets/amd-instinct-mi300x-platform-data-sheet.pdf
# - CXL 3.1 release note:
#   https://computeexpresslink.org/wp-content/uploads/2024/01/CXL_3.1-Specification-Release_FINAL.pdf

HARDWARE_PROFILES: dict[str, HardwareProfile] = {
    "H100_SXM5": HardwareProfile(
        name="H100_SXM5",
        hbm_bandwidth_gbps=3350.0,
        hbm_capacity_gb=80.0,
        sram_capacity_mb=64.0,
        cxl_bandwidth_gbps=128.0,
        dram_bandwidth_gbps=200.0,
        estimated_latency_ns=300.0,
        source="NVIDIA H100 product specifications",
    ),
    "H200_SXM": HardwareProfile(
        name="H200_SXM",
        hbm_bandwidth_gbps=4800.0,
        hbm_capacity_gb=141.0,
        sram_capacity_mb=80.0,
        cxl_bandwidth_gbps=128.0,
        dram_bandwidth_gbps=220.0,
        estimated_latency_ns=280.0,
        source="NVIDIA H200 product specifications",
    ),
    "B200_SXM": HardwareProfile(
        name="B200_SXM",
        hbm_bandwidth_gbps=8000.0,
        hbm_capacity_gb=180.0,
        sram_capacity_mb=96.0,
        cxl_bandwidth_gbps=128.0,
        dram_bandwidth_gbps=240.0,
        estimated_latency_ns=250.0,
        source="NVIDIA HGX AI Factory B200 reference specs",
    ),
    "MI300X": HardwareProfile(
        name="MI300X",
        hbm_bandwidth_gbps=5325.0,
        hbm_capacity_gb=192.0,
        sram_capacity_mb=64.0,
        cxl_bandwidth_gbps=128.0,
        dram_bandwidth_gbps=220.0,
        estimated_latency_ns=290.0,
        source="AMD Instinct MI300X product specifications",
    ),
    "GENERIC_CXL_3_1": HardwareProfile(
        name="GENERIC_CXL_3_1",
        hbm_bandwidth_gbps=3000.0,
        hbm_capacity_gb=80.0,
        sram_capacity_mb=64.0,
        cxl_bandwidth_gbps=128.0,
        dram_bandwidth_gbps=200.0,
        estimated_latency_ns=350.0,
        source="Conservative generic profile aligned to PCIe Gen5/CXL 3.1-era assumptions",
    ),
}


def get_hardware_profile(name: str) -> HardwareProfile:
    try:
        return HARDWARE_PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown hardware profile: {name}") from exc
