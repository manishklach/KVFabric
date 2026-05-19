from kvfabric.mock_runtime import MockKVFabricRuntime
from kvfabric.runtime_api import AccessNotification, BlockDescriptor, PrefetchRequest


def test_mock_runtime_tracks_basic_telemetry() -> None:
    runtime = MockKVFabricRuntime()
    ref = runtime.allocate_block(
        BlockDescriptor(
            block_id="L0_H0_B0",
            layer_id=0,
            head_id=0,
            token_start=0,
            token_count=16,
            size_bytes=8192,
        )
    )
    runtime.notify_access(AccessNotification(ref=ref, step=0, timestamp_ns=0))
    runtime.request_prefetch(PrefetchRequest(refs=[ref], target_tier="sram", deadline_ns=10_000))
    snapshot = runtime.snapshot_telemetry()
    assert snapshot.allocations == 1
    assert snapshot.accesses == 1
    assert snapshot.prefetch_requests == 1
    assert snapshot.blocks_by_tier["sram"] == 1
