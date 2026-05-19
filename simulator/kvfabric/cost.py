from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import CostModelConfig, WorkloadConfig
from .metrics import SimulationMetrics


BYTES_PER_GB = float(1024**3)


@dataclass(slots=True)
class CostModelEstimate:
    """Approximate economic summary for one simulation run."""

    estimated_hbm_capacity_cost: float
    estimated_cxl_capacity_cost: float
    estimated_memory_cost_delta: float
    estimated_latency_penalty: float
    rough_cost_per_1m_tokens_proxy: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


def estimate_run_cost(
    metrics: SimulationMetrics,
    workload: WorkloadConfig,
    cost: CostModelConfig,
    hbm_capacity_bytes: int,
    cxl_capacity_bytes: int,
    baseline_memory_cost: float,
) -> CostModelEstimate:
    """
    Build a rough cost proxy from simulator metrics.

    This is intentionally not a cloud pricing calculator. It treats configured
    tier capacities and simulated latency as a simple proxy for infrastructure
    tradeoffs that teams often care about while evaluating architecture ideas.
    """

    estimated_hbm_capacity_cost = (hbm_capacity_bytes / BYTES_PER_GB) * cost.hbm_cost_per_gb
    estimated_cxl_capacity_cost = (cxl_capacity_bytes / BYTES_PER_GB) * cost.cxl_cost_per_gb
    total_memory_cost = estimated_hbm_capacity_cost + estimated_cxl_capacity_cost
    estimated_memory_cost_delta = total_memory_cost - baseline_memory_cost

    latency_ms_per_request = metrics.simulated_latency_ns / 1_000_000.0
    estimated_latency_penalty = latency_ms_per_request * cost.latency_penalty_per_ms * cost.request_volume

    gpu_cost_per_1m_tokens = cost.gpu_hour_cost / max(cost.tokens_per_second * 3600.0, 1.0) * 1_000_000.0
    tokens_per_request = max(workload.decode_steps * workload.batch_size, 1)
    requests_per_1m_tokens = 1_000_000.0 / tokens_per_request
    latency_cost_per_1m_tokens = latency_ms_per_request * cost.latency_penalty_per_ms * requests_per_1m_tokens
    memory_cost_per_1m_tokens = total_memory_cost / max(cost.request_volume, 1) * requests_per_1m_tokens

    rough_cost_per_1m_tokens_proxy = gpu_cost_per_1m_tokens + latency_cost_per_1m_tokens + memory_cost_per_1m_tokens
    return CostModelEstimate(
        estimated_hbm_capacity_cost=estimated_hbm_capacity_cost,
        estimated_cxl_capacity_cost=estimated_cxl_capacity_cost,
        estimated_memory_cost_delta=estimated_memory_cost_delta,
        estimated_latency_penalty=estimated_latency_penalty,
        rough_cost_per_1m_tokens_proxy=rough_cost_per_1m_tokens_proxy,
    )
