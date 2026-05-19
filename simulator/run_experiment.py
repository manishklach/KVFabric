from __future__ import annotations

import argparse
from pathlib import Path

from kvflow.config import SimulationConfig
from kvflow.simulator import Simulator


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


def print_compare_table(baseline: dict[str, float | int], kvflow: dict[str, float | int]) -> None:
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
        kv_value = kvflow[key]
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


def run_mode(mode: str, workload_path: str | None = None) -> tuple[dict[str, float | int], dict[str, object]]:
    config = make_config(workload_path)
    simulator = Simulator(config, mode=mode)
    return simulator.run().as_dict(), simulator.describe_config()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run KVFabric simulator experiments.")
    parser.add_argument(
        "--mode",
        choices=["baseline", "kvflow", "compare"],
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "baseline":
        metrics, config_data = run_mode("baseline", args.workload)
        if args.show_config:
            print_config(config_data)
        print_metrics("KVFabric baseline run", metrics)
        return
    if args.mode == "kvflow":
        metrics, config_data = run_mode("kvflow", args.workload)
        if args.show_config:
            print_config(config_data)
        print_metrics("KVFabric semantic orchestration run", metrics)
        return

    baseline, config_data = run_mode("baseline", args.workload)
    kvflow, _ = run_mode("kvflow", args.workload)
    if args.show_config:
        print_config(config_data)
    print_compare_table(baseline, kvflow)


if __name__ == "__main__":
    main()
