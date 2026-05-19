from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol


@dataclass(slots=True)
class BlockDescriptor:
    block_id: str
    layer_id: int
    head_id: int
    token_start: int
    token_count: int
    size_bytes: int


@dataclass(slots=True)
class BlockRef:
    block_id: str


@dataclass(slots=True)
class PrefetchRequest:
    refs: list[BlockRef]
    target_tier: str
    deadline_ns: int


@dataclass(slots=True)
class CompressionRequest:
    refs: list[BlockRef]
    mode: str


@dataclass(slots=True)
class AccessNotification:
    ref: BlockRef
    step: int
    timestamp_ns: int


@dataclass(slots=True)
class TelemetrySnapshot:
    allocations: int = 0
    accesses: int = 0
    prefetch_requests: int = 0
    compression_requests: int = 0
    releases: int = 0
    blocks_by_tier: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, int | dict[str, int]]:
        return asdict(self)


class KVFabricRuntime(Protocol):
    def allocate_block(self, desc: BlockDescriptor) -> BlockRef:
        ...

    def notify_access(self, access: AccessNotification) -> None:
        ...

    def request_prefetch(self, request: PrefetchRequest) -> None:
        ...

    def compress_blocks(self, request: CompressionRequest) -> None:
        ...

    def release_block(self, ref: BlockRef) -> None:
        ...

    def snapshot_telemetry(self) -> TelemetrySnapshot:
        ...
