from __future__ import annotations

import argparse
from pathlib import Path

from kvflow.config import WorkloadConfig
from kvflow.trace import generate_synthetic_trace, write_trace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a synthetic KVFabric trace for locality experiments.")
    parser.add_argument("--output", required=True, help="Output JSONL trace path.")
    parser.add_argument("--context-length", type=int, default=8192, help="Synthetic context length.")
    parser.add_argument("--decode-steps", type=int, default=128, help="Synthetic decode steps.")
    parser.add_argument("--request-id", default="chat_0", help="Synthetic request identifier.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workload = WorkloadConfig(
        name="synthetic_trace_workload",
        description="Synthetic trace generator workload for KVFabric locality experiments",
        model_layers=32,
        num_heads=32,
        head_dim=128,
        batch_size=4,
        context_length=args.context_length,
        decode_steps=args.decode_steps,
        dtype_bytes=2,
        kv_block_tokens=16,
    )
    events = generate_synthetic_trace(workload, request_id=args.request_id)
    write_trace(events, Path(args.output))
    print("Synthetic KVFabric trace written")
    print("This is a synthetic trace generator for testing locality assumptions.")
    print("It is not a real vLLM trace.")
    print(f"events: {len(events)}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
