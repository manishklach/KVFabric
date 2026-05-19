from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path

from .config import WorkloadConfig
from .workload import Workload, WorkloadBlockSpec


@dataclass(slots=True)
class TraceRequest:
    """One request record from a JSONL trace."""

    request_id: str
    prompt_length: int
    decode_length: int
    arrival_time_ns: int = 0
    source: str = "synthetic"

    def as_dict(self) -> dict[str, int | str]:
        return asdict(self)


class TraceReplayWorkload:
    """Replay-like workload built from request-level JSONL traces."""

    def __init__(
        self,
        requests: list[TraceRequest],
        base_config: WorkloadConfig,
        trace_path: Path,
        arrival_quantum_ns: int = 100_000,
    ) -> None:
        self.requests = requests
        self.base_config = base_config
        self.trace_path = trace_path
        self.arrival_quantum_ns = arrival_quantum_ns
        self.token_block_size = base_config.kv_block_tokens
        self.block_size_bytes = self.token_block_size * base_config.head_dim * base_config.dtype_bytes * 2
        self._catalog = self._build_catalog()
        self._accesses, self._step_block_index = self._build_accesses()
        self.num_token_blocks = max(1, max(self._step_block_index, default=0) + 1)

    def _request_workload(self, request: TraceRequest) -> Workload:
        request_config = replace(
            self.base_config,
            context_length=max(self.base_config.kv_block_tokens, request.prompt_length),
            decode_steps=max(1, request.decode_length),
            batch_size=1,
        )
        return Workload(request_config, request_prefix=request.request_id)

    def _build_catalog(self) -> list[WorkloadBlockSpec]:
        catalog: list[WorkloadBlockSpec] = []
        for request in self.requests:
            catalog.extend(self._request_workload(request).build_block_catalog())
        return catalog

    def _build_accesses(self) -> tuple[list[list[str]], list[int]]:
        sequences: dict[int, list[str]] = {}
        step_block_index: dict[int, int] = {}
        max_step = 0
        for request in self.requests:
            arrival_step = max(0, request.arrival_time_ns // self.arrival_quantum_ns)
            request_workload = self._request_workload(request)
            for local_step, accesses in enumerate(request_workload.access_sequence()):
                global_step = arrival_step + local_step
                sequences.setdefault(global_step, []).extend(accesses)
                step_block_index[global_step] = max(
                    step_block_index.get(global_step, 0),
                    request_workload.current_block_index_for_step(local_step),
                )
                max_step = max(max_step, global_step)

        replay_accesses = [sequences.get(step, []) for step in range(max_step + 1)]
        replay_block_index = [step_block_index.get(step, 0) for step in range(max_step + 1)]
        return replay_accesses, replay_block_index

    def build_block_catalog(self) -> list[WorkloadBlockSpec]:
        return list(self._catalog)

    def access_sequence(self) -> list[list[str]]:
        return list(self._accesses)

    def current_block_index_for_step(self, step: int) -> int:
        if not self._step_block_index:
            return 0
        return self._step_block_index[min(step, len(self._step_block_index) - 1)]

    def assumed_block_size_bytes(self) -> int:
        return self.block_size_bytes

    def summary(self) -> dict[str, int | str]:
        return {
            "trace_path": str(self.trace_path),
            "requests": len(self.requests),
            "max_prompt_length": max((request.prompt_length for request in self.requests), default=0),
            "max_decode_length": max((request.decode_length for request in self.requests), default=0),
            "arrival_quantum_ns": self.arrival_quantum_ns,
        }


def load_trace(path: Path) -> list[TraceRequest]:
    requests: list[TraceRequest] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        requests.append(TraceRequest(**data))
    return requests
