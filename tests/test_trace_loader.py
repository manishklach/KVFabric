from pathlib import Path

from kvfabric.config import WorkloadConfig
from kvfabric.trace_loader import TraceReplayWorkload, load_trace


def test_trace_loader_parses_jsonl_requests() -> None:
    trace_path = Path("examples/traces/sharegpt_small.jsonl")
    requests = load_trace(trace_path)
    assert len(requests) >= 3
    assert requests[0].prompt_length > 0
    assert requests[0].decode_length > 0


def test_trace_replay_builds_access_sequence() -> None:
    trace_path = Path("examples/traces/synthetic_chat.jsonl")
    requests = load_trace(trace_path)
    workload = TraceReplayWorkload(
        requests,
        WorkloadConfig(
            name="trace_base",
            description="trace test",
            model_layers=4,
            num_heads=4,
            head_dim=64,
            batch_size=1,
            context_length=2048,
            decode_steps=64,
            dtype_bytes=2,
            kv_block_tokens=16,
        ),
        trace_path,
    )
    assert workload.access_sequence()
    assert workload.build_block_catalog()
    assert workload.summary()["requests"] == len(requests)
