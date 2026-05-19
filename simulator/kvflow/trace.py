from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .config import WorkloadConfig
from .workload import Workload


@dataclass(slots=True)
class TraceEvent:
    """Synthetic KV access event used for locality testing."""

    step: int
    request_id: str
    layer_id: int
    head_id: int
    token_start: int
    token_count: int
    access_type: str = "read"

    def to_json(self) -> str:
        return json.dumps(asdict(self))


def parse_block_id(block_id: str) -> tuple[int, int, int]:
    layer_str, head_str, block_str = block_id.split("_")
    return int(layer_str[1:]), int(head_str[1:]), int(block_str[1:])


def generate_synthetic_trace(workload_config: WorkloadConfig, request_id: str = "chat_0") -> list[TraceEvent]:
    """
    Generate a synthetic JSONL-friendly trace from the workload access pattern.

    This trace is intended only for locality and scheduling experiments. It is
    not a real serving trace from vLLM or another production system.
    """
    workload = Workload(workload_config)
    events: list[TraceEvent] = []
    for step, accesses in enumerate(workload.access_sequence()):
        seen: set[str] = set()
        for block_id in accesses:
            if block_id in seen:
                continue
            seen.add(block_id)
            layer_id, head_id, block_index = parse_block_id(block_id)
            events.append(
                TraceEvent(
                    step=step,
                    request_id=request_id,
                    layer_id=layer_id,
                    head_id=head_id,
                    token_start=block_index * workload.token_block_size,
                    token_count=workload.token_block_size,
                )
            )
    return events


def write_trace(events: list[TraceEvent], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(event.to_json() for event in events) + "\n", encoding="utf-8")
