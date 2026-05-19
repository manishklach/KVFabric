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


def print_compare_table(baseline: dict[str, float | int], kvflow: dict[str, float | int]) -> None:
    keys = [
        "total_bytes_moved",
        "hbm_bytes_read",
        "cxl_bytes_read",
        "host_bytes_read",
        "compression_savings_bytes",
        "simulated_latency_ns",
        "sram_hit_rate",
        "blocks_evicted",
        "blocks_compressed",
    ]

    metric_width = 27
    value_width = 14
    print(f"{'metric':{metric_width}} | {'baseline':{value_width}} | {'kvflow':{value_width}} | {'delta':{value_width}}")
    print("-" * (metric_width + value_width * 3 + 9))
    for key in keys:
        base_value = baseline[key]
        kv_value = kvflow[key]
        delta = kv_value - base_value  # type: ignore[operator]
        print(
            f"{key:{metric_width}} | {format_value(base_value):{value_width}} | "
            f"{format_value(kv_value):{value_width}} | {format_value(delta):{value_width}}"
        )


def run_mode(mode: str) -> dict[str, float | int]:
    config = SimulationConfig.default()
    simulator = Simulator(config, mode=mode)
    return simulator.run().as_dict()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run KVFlow simulator experiments.")
    parser.add_argument(
        "--mode",
        choices=["baseline", "kvflow", "compare"],
        default="compare",
        help="Execution mode: baseline path, KVFlow path, or side-by-side comparison.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "baseline":
        print_metrics("KVFlow baseline run", run_mode("baseline"))
        return
    if args.mode == "kvflow":
        print_metrics("KVFlow semantic orchestration run", run_mode("kvflow"))
        return

    baseline = run_mode("baseline")
    kvflow = run_mode("kvflow")
    print_compare_table(baseline, kvflow)


if __name__ == "__main__":
    main()
