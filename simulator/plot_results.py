from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from kvfabric.config import SimulationConfig
from kvfabric.policies import HotWarmColdPolicy, LFUCompressionPolicy, LRUHotWindowPolicy
from kvfabric.simulator import Simulator


POLICY_PROFILES: dict[str, tuple[type, type, type]] = {
    "LRUHotWindowPolicy": (LRUHotWindowPolicy, LFUCompressionPolicy, LRUHotWindowPolicy),
    "LFUCompressionPolicy": (LRUHotWindowPolicy, LFUCompressionPolicy, HotWarmColdPolicy),
    "HotWarmColdPolicy": (HotWarmColdPolicy, LFUCompressionPolicy, HotWarmColdPolicy),
}

SWEEP_WORKLOADS: dict[str, str] = {
    "short_2k": "examples/workloads/short_2k.json",
    "medium_32k": "examples/workloads/medium_32k.json",
    "long_128k_cold": "examples/workloads/long_128k_cold.json",
}


def apply_policy_profile_tuning(config: SimulationConfig, profile_name: str) -> None:
    if profile_name == "LRUHotWindowPolicy":
        config.policy.recent_window = 192
        config.policy.prefetch_window = 128
    elif profile_name == "LFUCompressionPolicy":
        config.policy.recent_window = 64
        config.policy.prefetch_window = 48
        config.policy.cold_int4_distance = 256
    elif profile_name == "HotWarmColdPolicy":
        config.policy.recent_window = 128
        config.policy.warm_reuse_threshold = 1
        config.policy.prefetch_window = 96


def run_simulator(
    mode: str,
    workload_path: str | None = None,
    trace_path: str | None = None,
    policy_name: str | None = None,
) -> Simulator:
    config = SimulationConfig.default()
    if workload_path is not None:
        config.with_workload_path(Path(workload_path))
    if trace_path is not None:
        config.with_trace_path(Path(trace_path))
    kwargs = {}
    if policy_name is not None:
        apply_policy_profile_tuning(config, policy_name)
        promotion_cls, compression_cls, eviction_cls = POLICY_PROFILES[policy_name]
        kwargs = {
            "promotion_policy": promotion_cls(config.policy),
            "compression_policy": compression_cls(config.policy),
            "eviction_policy": eviction_cls(config.policy),
        }
    simulator = Simulator(config, mode=mode, **kwargs)
    simulator.run()
    return simulator


def ensure_output_dir() -> Path:
    output_dir = Path("results/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_hbm_vs_context(output_dir: Path) -> None:
    workloads = []
    context_lengths = []
    baseline_hbm = []
    kvfabric_hbm = []
    for workload_name, workload_path in SWEEP_WORKLOADS.items():
        baseline = run_simulator("baseline", workload_path=workload_path)
        kvfabric = run_simulator("kvfabric", workload_path=workload_path)
        workloads.append(workload_name)
        context_lengths.append(kvfabric.workload_config.context_length)
        baseline_hbm.append(baseline.metrics.hbm_bytes_read / 1_000_000)
        kvfabric_hbm.append(kvfabric.metrics.hbm_bytes_read / 1_000_000)

    plt.figure(figsize=(7, 4.5))
    plt.plot(context_lengths, baseline_hbm, marker="o", label="Baseline")
    plt.plot(context_lengths, kvfabric_hbm, marker="o", label="KVFabric")
    plt.xlabel("Context length")
    plt.ylabel("HBM reads (MB)")
    plt.title("HBM Bytes vs Context Length")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "hbm_vs_context_length.png", dpi=160)
    plt.close()


def save_sram_hit_rate(output_dir: Path) -> None:
    kvfabric = run_simulator("kvfabric")
    steps = [record.step for record in kvfabric.step_records]
    rates = [record.sram_hit_rate for record in kvfabric.step_records]

    plt.figure(figsize=(7, 4.5))
    plt.plot(steps, rates, color="#2a6f97")
    plt.xlabel("Decode step")
    plt.ylabel("Per-step SRAM hit rate")
    plt.title("SRAM Hit Rate vs Decode Step")
    plt.tight_layout()
    plt.savefig(output_dir / "sram_hit_rate_vs_decode_step.png", dpi=160)
    plt.close()


def save_latency_exposure(output_dir: Path) -> None:
    baseline = run_simulator("baseline")
    kvfabric = run_simulator("kvfabric")
    labels = ["Baseline", "KVFabric"]
    hidden = [baseline.metrics.hidden_latency_ns / 1_000_000, kvfabric.metrics.hidden_latency_ns / 1_000_000]
    exposed = [baseline.metrics.exposed_latency_ns / 1_000_000, kvfabric.metrics.exposed_latency_ns / 1_000_000]

    plt.figure(figsize=(7, 4.5))
    plt.bar(labels, hidden, label="Hidden latency")
    plt.bar(labels, exposed, bottom=hidden, label="Exposed latency")
    plt.ylabel("Latency (ms)")
    plt.title("Exposed vs Hidden Latency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "exposed_vs_hidden_latency.png", dpi=160)
    plt.close()


def save_policy_comparison(output_dir: Path) -> None:
    policy_names = list(POLICY_PROFILES.keys())
    exposed_ms = []
    hbm_mb = []
    for policy_name in policy_names:
        simulator = run_simulator("kvfabric", policy_name=policy_name)
        exposed_ms.append(simulator.metrics.exposed_latency_ns / 1_000_000)
        hbm_mb.append(simulator.metrics.hbm_bytes_read / 1_000_000)

    fig, ax1 = plt.subplots(figsize=(8, 4.8))
    ax1.bar(policy_names, exposed_ms, color="#cdb4db", label="Exposed latency (ms)")
    ax1.set_ylabel("Exposed latency (ms)")
    ax1.tick_params(axis="x", rotation=15)

    ax2 = ax1.twinx()
    ax2.plot(policy_names, hbm_mb, color="#264653", marker="o", label="HBM reads (MB)")
    ax2.set_ylabel("HBM reads (MB)")

    fig.suptitle("Policy Comparison")
    fig.tight_layout()
    fig.savefig(output_dir / "policy_comparison.png", dpi=160)
    plt.close(fig)


def main() -> None:
    output_dir = ensure_output_dir()
    save_hbm_vs_context(output_dir)
    save_sram_hit_rate(output_dir)
    save_latency_exposure(output_dir)
    save_policy_comparison(output_dir)
    print(f"Figures written to {output_dir}")


if __name__ == "__main__":
    main()
