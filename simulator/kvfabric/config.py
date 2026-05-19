from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


DEFAULT_COMPRESSION_RATIOS: dict[str, float] = {"none": 1.0, "int8": 0.5, "int4": 0.25}
DEFAULT_DECOMPRESSION_PENALTIES_NS: dict[str, float] = {"none": 0.0, "int8": 120.0, "int4": 260.0}


@dataclass(slots=True)
class TierConfig:
    """Static configuration for one memory tier."""

    name: str
    capacity_bytes: int
    bandwidth_gbps: float
    latency_ns: float

    def as_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


@dataclass(slots=True)
class WorkloadConfig:
    """Workload parameters used to synthesize KV accesses."""

    model_layers: int
    num_heads: int
    head_dim: int
    batch_size: int
    context_length: int
    decode_steps: int
    dtype_bytes: int
    kv_block_tokens: int = 16
    name: str = "default_8k_decode"
    description: str = "Synthetic 8k-context decode workload for early KVFabric experiments"

    @classmethod
    def from_json(cls, path: Path) -> "WorkloadConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass(slots=True)
class CompressionConfig:
    """Configurable compression assumptions for the simulator."""

    ratios: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_COMPRESSION_RATIOS))
    decompression_penalties_ns: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_DECOMPRESSION_PENALTIES_NS)
    )

    def as_dict(self) -> dict[str, dict[str, float]]:
        return {
            "ratios": dict(self.ratios),
            "decompression_penalties_ns": dict(self.decompression_penalties_ns),
        }


@dataclass(slots=True)
class PolicyConfig:
    """Tunable knobs for the KVFabric scheduler."""

    recent_window: int = 128
    warm_reuse_threshold: int = 2
    prefetch_window: int = 96
    cold_int4_distance: int = 768

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(slots=True)
class PipelineConfig:
    """Approximate decode-pipeline timing knobs."""

    compute_ns_per_access: float = 180.0
    sram_stage_latency_ns: float = 40.0
    max_prefetch_per_step: int = 48

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(slots=True)
class CostModelConfig:
    """Rough economic assumptions for comparing memory-tier tradeoffs."""

    hbm_cost_per_gb: float = 18.0
    cxl_cost_per_gb: float = 4.5
    dram_cost_per_gb: float = 1.5
    gpu_hour_cost: float = 3.25
    latency_penalty_per_ms: float = 0.015
    tokens_per_second: float = 800.0
    request_volume: int = 10_000

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(slots=True)
class SimulationConfig:
    """Top-level simulator configuration with conservative defaults."""

    tiers: dict[str, TierConfig] = field(default_factory=dict)
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    cost: CostModelConfig = field(default_factory=CostModelConfig)
    workload_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
        / "examples"
        / "workloads"
        / "default_8k.json"
    )

    @classmethod
    def default(cls) -> "SimulationConfig":
        # Capacities are deliberately modest so the default workload exercises tiering.
        tiers = {
            "sram": TierConfig("sram", capacity_bytes=512 * 1024 * 1024, bandwidth_gbps=20000.0, latency_ns=25.0),
            "hbm": TierConfig("hbm", capacity_bytes=8 * 1024 * 1024 * 1024, bandwidth_gbps=3000.0, latency_ns=300.0),
            "cxl": TierConfig("cxl", capacity_bytes=24 * 1024 * 1024 * 1024, bandwidth_gbps=300.0, latency_ns=900.0),
            "dram": TierConfig("dram", capacity_bytes=64 * 1024 * 1024 * 1024, bandwidth_gbps=120.0, latency_ns=1800.0),
        }
        return cls(tiers=tiers)

    def with_workload_path(self, workload_path: Path | None) -> "SimulationConfig":
        if workload_path is not None:
            self.workload_path = workload_path
        return self

    def create_workload_config(self) -> WorkloadConfig:
        return WorkloadConfig.from_json(self.workload_path)

    def display_dict(self) -> dict[str, object]:
        workload = self.create_workload_config()
        return {
            "workload_path": str(self.workload_path),
            "workload": workload.as_dict(),
            "tiers": {name: tier.as_dict() for name, tier in self.tiers.items()},
            "compression": self.compression.as_dict(),
            "policy": self.policy.as_dict(),
            "pipeline": self.pipeline.as_dict(),
            "cost_model": self.cost.as_dict(),
        }
