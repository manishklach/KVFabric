from __future__ import annotations

from dataclasses import dataclass, field

from .runtime_api import (
    AccessNotification,
    BlockDescriptor,
    BlockRef,
    CompressionRequest,
    KVFabricRuntime,
    PrefetchRequest,
    TelemetrySnapshot,
)


@dataclass(slots=True)
class MockBlockState:
    descriptor: BlockDescriptor
    tier: str = "hbm"
    compression_mode: str = "none"
    access_count: int = 0
    last_access_step: int = -1


class MockKVFabricRuntime(KVFabricRuntime):
    """In-memory runtime shim that makes the API contract concrete for tests and docs."""

    def __init__(self) -> None:
        self.blocks: dict[str, MockBlockState] = {}
        self.telemetry = TelemetrySnapshot(blocks_by_tier={"hbm": 0, "cxl": 0, "dram": 0, "sram": 0})

    def allocate_block(self, desc: BlockDescriptor) -> BlockRef:
        self.blocks[desc.block_id] = MockBlockState(descriptor=desc)
        self.telemetry.allocations += 1
        self.telemetry.blocks_by_tier["hbm"] += 1
        return BlockRef(desc.block_id)

    def notify_access(self, access: AccessNotification) -> None:
        block = self.blocks[access.ref.block_id]
        block.access_count += 1
        block.last_access_step = access.step
        self.telemetry.accesses += 1

    def request_prefetch(self, request: PrefetchRequest) -> None:
        self.telemetry.prefetch_requests += 1
        for ref in request.refs:
            block = self.blocks[ref.block_id]
            self.telemetry.blocks_by_tier[block.tier] = max(0, self.telemetry.blocks_by_tier[block.tier] - 1)
            block.tier = request.target_tier
            self.telemetry.blocks_by_tier.setdefault(block.tier, 0)
            self.telemetry.blocks_by_tier[block.tier] += 1

    def compress_blocks(self, request: CompressionRequest) -> None:
        self.telemetry.compression_requests += 1
        for ref in request.refs:
            self.blocks[ref.block_id].compression_mode = request.mode

    def release_block(self, ref: BlockRef) -> None:
        block = self.blocks.pop(ref.block_id)
        self.telemetry.releases += 1
        self.telemetry.blocks_by_tier[block.tier] = max(0, self.telemetry.blocks_by_tier[block.tier] - 1)

    def snapshot_telemetry(self) -> TelemetrySnapshot:
        return TelemetrySnapshot(
            allocations=self.telemetry.allocations,
            accesses=self.telemetry.accesses,
            prefetch_requests=self.telemetry.prefetch_requests,
            compression_requests=self.telemetry.compression_requests,
            releases=self.telemetry.releases,
            blocks_by_tier=dict(self.telemetry.blocks_by_tier),
        )
