from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass(slots=True)
class TierConfig:
    """Static configuration for one memory tier."""

    name: str
    capacity_bytes: int
    bandwidth_gbps: float
    latency_ns: float


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

    @classmethod
    def from_json(cls, path: Path) -> "WorkloadConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)


@dataclass(slots=True)
class PolicyConfig:
    """Tunable knobs for the KVFlow scheduler."""

    recent_window: int = 128
    warm_reuse_threshold: int = 2
    prefetch_window: int = 96
    cold_int4_distance: int = 768


@dataclass(slots=True)
class PipelineConfig:
    """Approximate decode-pipeline timing knobs."""

    compute_ns_per_access: float = 180.0
    sram_stage_latency_ns: float = 40.0
    max_prefetch_per_step: int = 48


@dataclass(slots=True)
class SimulationConfig:
    """Top-level simulator configuration with conservative defaults."""

    tiers: dict[str, TierConfig] = field(default_factory=dict)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    workload_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "examples" / "sample_workload.json"
    )

    @classmethod
    def default(cls) -> "SimulationConfig":
        # Capacities are deliberately modest so the sample workload exercises tiering.
        tiers = {
            "sram": TierConfig("sram", capacity_bytes=512 * 1024 * 1024, bandwidth_gbps=20000.0, latency_ns=25.0),
            "hbm": TierConfig("hbm", capacity_bytes=8 * 1024 * 1024 * 1024, bandwidth_gbps=3000.0, latency_ns=300.0),
            "cxl": TierConfig("cxl", capacity_bytes=24 * 1024 * 1024 * 1024, bandwidth_gbps=300.0, latency_ns=900.0),
            "dram": TierConfig("dram", capacity_bytes=64 * 1024 * 1024 * 1024, bandwidth_gbps=120.0, latency_ns=1800.0),
        }
        return cls(tiers=tiers)
