from __future__ import annotations

import argparse
from pathlib import Path

from kvfabric.config import SimulationConfig
from kvfabric.cost import estimate_run_cost
from kvfabric.metrics import SimulationMetrics
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


def format_value(value: float | int) -> str:
    if isinstance(value, float):
        return f"{value:,.4f}" if abs(value) < 10 else f"{value:,.2f}"
    return f"{value:,}"


def print_metrics(title: str, metrics: dict[str, float | int]) -> None:
    print(title)
    for key, value in metrics.items():
        print(f"{key:28} {format_value(value)}")


def print_config(config_data: dict[str, object]) -> None:
    workload = config_data["workload"]
    tiers = config_data["tiers"]
    compression = config_data["compression"]
    policy = config_data["policy"]
    pipeline = config_data["pipeline"]
    cost_model = config_data["cost_model"]

    print("KVFabric configuration")
    print(f"workload_path               {config_data['workload_path']}")
    print(f"workload_name               {workload['name']}")
    print(f"workload_description        {workload['description']}")
    print(f"model_layers                {workload['model_layers']}")
    print(f"num_heads                   {workload['num_heads']}")
    print(f"head_dim                    {workload['head_dim']}")
    print(f"batch_size                  {workload['batch_size']}")
    print(f"context_length              {workload['context_length']}")
    print(f"decode_steps                {workload['decode_steps']}")
    print(f"dtype_bytes                 {workload['dtype_bytes']}")
    print(f"kv_block_tokens             {workload['kv_block_tokens']}")
    print(f"assumed_kv_block_size_bytes {config_data['assumed_kv_block_size_bytes']}")
    print("")
    print("Memory tiers")
    for tier_name, tier_data in tiers.items():
        print(
            f"{tier_name:28} capacity={format_value(tier_data['capacity_bytes'])} bytes "
            f"bandwidth={format_value(tier_data['bandwidth_gbps'])} GB/s "
            f"latency={format_value(tier_data['latency_ns'])} ns"
        )
    print("")
    print("Compression model")
    for state, ratio in compression["ratios"].items():
        penalty = compression["decompression_penalties_ns"][state]
        print(f"{state:28} ratio={ratio} penalty_ns={penalty}")
    print("")
    print("Policy / pipeline")
    for key, value in policy.items():
        print(f"{key:28} {value}")
    for key, value in pipeline.items():
        print(f"{key:28} {value}")
    print("")
    print("Cost model")
    for key, value in cost_model.items():
        print(f"{key:28} {value}")
    print("")


def print_compare_table(baseline: dict[str, float | int], kvfabric: dict[str, float | int]) -> None:
    keys = [
        "total_bytes_moved",
        "hbm_bytes_read",
        "cxl_bytes_read",
        "host_bytes_read",
        "compression_savings_bytes",
        "simulated_latency_ns",
        "compute_latency_ns",
        "transfer_latency_ns",
        "decompression_latency_ns",
        "hidden_transfer_ns",
        "exposed_transfer_ns",
        "overlap_ratio",
        "sram_hit_rate",
        "blocks_evicted",
        "blocks_compressed",
        "prefetched_blocks",
        "staged_blocks",
    ]

    metric_width = 27
    value_width = 14
    print(f"{'metric':{metric_width}} | {'baseline':{value_width}} | {'kvfabric':{value_width}} | {'delta':{value_width}}")
    print("-" * (metric_width + value_width * 3 + 9))
    for key in keys:
        base_value = baseline[key]
        kv_value = kvfabric[key]
        delta = kv_value - base_value  # type: ignore[operator]
        print(
            f"{key:{metric_width}} | {format_value(base_value):{value_width}} | "
            f"{format_value(kv_value):{value_width}} | {format_value(delta):{value_width}}"
        )


def make_config(workload_path: str | None) -> SimulationConfig:
    config = SimulationConfig.default()
    if workload_path is not None:
        config.with_workload_path(Path(workload_path))
    return config


def apply_policy_profile_tuning(config: SimulationConfig, profile_name: str) -> None:
    """Give each policy experiment a distinct tuning shape."""

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


def run_mode(
    mode: str,
    workload_path: str | None = None,
    policy_profile: tuple[type, type, type] | None = None,
    policy_profile_name: str | None = None,
) -> tuple[dict[str, float | int], dict[str, object]]:
    config = make_config(workload_path)
    if policy_profile_name is not None:
        apply_policy_profile_tuning(config, policy_profile_name)
    if policy_profile is None:
        simulator = Simulator(config, mode=mode)
    else:
        promotion_cls, compression_cls, eviction_cls = policy_profile
        simulator = Simulator(
            config,
            mode=mode,
            promotion_policy=promotion_cls(config.policy),
            compression_policy=compression_cls(config.policy),
            eviction_policy=eviction_cls(config.policy),
        )
    return simulator.run().as_dict(), simulator.describe_config()


def print_cost_model_compare(
    baseline_metrics: dict[str, float | int],
    kvfabric_metrics: dict[str, float | int],
    config_data: dict[str, object],
) -> None:
    workload = config_data["workload"]
    tiers = config_data["tiers"]
    cost_data = config_data["cost_model"]
    config = SimulationConfig.default()
    config.cost.hbm_cost_per_gb = float(cost_data["hbm_cost_per_gb"])
    config.cost.cxl_cost_per_gb = float(cost_data["cxl_cost_per_gb"])
    config.cost.dram_cost_per_gb = float(cost_data["dram_cost_per_gb"])
    config.cost.gpu_hour_cost = float(cost_data["gpu_hour_cost"])
    config.cost.latency_penalty_per_ms = float(cost_data["latency_penalty_per_ms"])
    config.cost.tokens_per_second = float(cost_data["tokens_per_second"])
    config.cost.request_volume = int(cost_data["request_volume"])
    from kvfabric.config import WorkloadConfig

    workload_obj = WorkloadConfig(**workload)

    baseline_estimate = estimate_run_cost(
        metrics=SimulationMetrics.from_dict(baseline_metrics),
        workload=workload_obj,
        cost=config.cost,
        hbm_capacity_bytes=int(tiers["hbm"]["capacity_bytes"]),
        cxl_capacity_bytes=0,
        baseline_memory_cost=(int(tiers["hbm"]["capacity_bytes"]) / float(1024**3)) * config.cost.hbm_cost_per_gb,
    )
    kvfabric_estimate = estimate_run_cost(
        metrics=SimulationMetrics.from_dict(kvfabric_metrics),
        workload=workload_obj,
        cost=config.cost,
        hbm_capacity_bytes=int(tiers["hbm"]["capacity_bytes"]),
        cxl_capacity_bytes=int(tiers["cxl"]["capacity_bytes"]),
        baseline_memory_cost=(int(tiers["hbm"]["capacity_bytes"]) / float(1024**3)) * config.cost.hbm_cost_per_gb,
    )

    print("")
    print("Cost Model Proxy")
    labels = [
        ("HBM capacity proxy", "estimated_hbm_capacity_cost"),
        ("CXL capacity proxy", "estimated_cxl_capacity_cost"),
        ("Latency penalty proxy", "estimated_latency_penalty"),
        ("Cost / 1M tokens proxy", "rough_cost_per_1m_tokens_proxy"),
    ]
    for label, key in labels:
        baseline_value = baseline_estimate.as_dict()[key]
        kvfabric_value = kvfabric_estimate.as_dict()[key]
        delta = kvfabric_value - baseline_value
        print(
            f"{label:24} baseline={format_value(baseline_value)} "
            f"kvfabric={format_value(kvfabric_value)} delta={format_value(delta)}"
        )
    print(
        f"{'Memory cost delta':24} baseline={format_value(baseline_estimate.estimated_memory_cost_delta)} "
        f"kvfabric={format_value(kvfabric_estimate.estimated_memory_cost_delta)} "
        f"delta={format_value(kvfabric_estimate.estimated_memory_cost_delta - baseline_estimate.estimated_memory_cost_delta)}"
    )


def print_policy_compare_table(rows: list[dict[str, float | int | str]]) -> None:
    fields = [
        "policy",
        "hbm_bytes_read",
        "cxl_bytes_read",
        "sram_hit_rate",
        "exposed_latency_ns",
        "compression_savings_bytes",
    ]
    widths = {
        "policy": 20,
        "hbm_bytes_read": 15,
        "cxl_bytes_read": 14,
        "sram_hit_rate": 13,
        "exposed_latency_ns": 18,
        "compression_savings_bytes": 25,
    }
    print(
        " | ".join(
            f"{field:{widths[field]}}" for field in fields
        )
    )
    print("-" * (sum(widths.values()) + (3 * (len(fields) - 1))))
    for row in rows:
        print(" | ".join(f"{format_value(row[field]) if field != 'policy' else row[field]:{widths[field]}}" for field in fields))


def print_sweep_table(rows: list[dict[str, float | int | str]]) -> None:
    fields = [
        "workload",
        "context_length",
        "hbm_bytes_read",
        "cxl_bytes_read",
        "sram_hit_rate",
        "exposed_latency_ns",
        "compression_savings_bytes",
    ]
    widths = {
        "workload": 16,
        "context_length": 14,
        "hbm_bytes_read": 15,
        "cxl_bytes_read": 14,
        "sram_hit_rate": 13,
        "exposed_latency_ns": 18,
        "compression_savings_bytes": 25,
    }
    print(" | ".join(f"{field:{widths[field]}}" for field in fields))
    print("-" * (sum(widths.values()) + (3 * (len(fields) - 1))))
    for row in rows:
        print(" | ".join(f"{format_value(row[field]) if field != 'workload' else row[field]:{widths[field]}}" for field in fields))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run KVFabric simulator experiments.")
    parser.add_argument(
        "--mode",
        choices=["baseline", "kvflow", "kvfabric", "compare", "policy-compare", "sweep"],
        default="compare",
        help="Execution mode: baseline path, KVFabric path, or side-by-side comparison.",
    )
    parser.add_argument(
        "--workload",
        help="Optional workload JSON path. Example: examples/workloads/default_8k.json",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print workload, tier, compression, and pipeline assumptions before metrics.",
    )
    parser.add_argument(
        "--cost-model",
        action="store_true",
        help="Print a rough cost proxy for compare mode.",
    )
    parser.add_argument(
        "--sweep",
        choices=["context_length"],
        help="Run a canned sensitivity sweep over the requested dimension.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "baseline":
        metrics, config_data = run_mode("baseline", args.workload)
        if args.show_config:
            print_config(config_data)
        print_metrics("KVFabric baseline run", metrics)
        return
    if args.mode in {"kvflow", "kvfabric"}:
        metrics, config_data = run_mode("kvfabric", args.workload)
        if args.show_config:
            print_config(config_data)
        print_metrics("KVFabric semantic orchestration run", metrics)
        return
    if args.mode == "policy-compare":
        rows: list[dict[str, float | int | str]] = []
        for policy_name, policy_profile in POLICY_PROFILES.items():
            metrics, _ = run_mode(
                "kvfabric",
                args.workload,
                policy_profile=policy_profile,
                policy_profile_name=policy_name,
            )
            rows.append(
                {
                    "policy": policy_name,
                    "hbm_bytes_read": metrics["hbm_bytes_read"],
                    "cxl_bytes_read": metrics["cxl_bytes_read"],
                    "sram_hit_rate": metrics["sram_hit_rate"],
                    "exposed_latency_ns": metrics["exposed_transfer_ns"],
                    "compression_savings_bytes": metrics["compression_savings_bytes"],
                }
            )
        print_policy_compare_table(rows)
        return
    if args.mode == "sweep":
        if args.sweep != "context_length":
            raise SystemExit("--mode sweep currently requires --sweep context_length")
        rows = []
        for workload_name, workload_path in SWEEP_WORKLOADS.items():
            metrics, config_data = run_mode("kvfabric", workload_path)
            rows.append(
                {
                    "workload": workload_name,
                    "context_length": config_data["workload"]["context_length"],
                    "hbm_bytes_read": metrics["hbm_bytes_read"],
                    "cxl_bytes_read": metrics["cxl_bytes_read"],
                    "sram_hit_rate": metrics["sram_hit_rate"],
                    "exposed_latency_ns": metrics["exposed_transfer_ns"],
                    "compression_savings_bytes": metrics["compression_savings_bytes"],
                }
            )
        print_sweep_table(rows)
        return

    baseline, config_data = run_mode("baseline", args.workload)
    kvfabric, _ = run_mode("kvfabric", args.workload)
    if args.show_config:
        print_config(config_data)
    print_compare_table(baseline, kvfabric)
    if args.cost_model:
        print_cost_model_compare(baseline, kvfabric, config_data)


if __name__ == "__main__":
    main()
