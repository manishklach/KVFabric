from __future__ import annotations

from dataclasses import dataclass

from .config import PipelineConfig


@dataclass(slots=True)
class PrefetchEvent:
    """One asynchronous prefetch into the SRAM staging buffer."""

    block_id: str
    ready_time_ns: float
    transfer_time_ns: float
    decompression_time_ns: float


@dataclass(slots=True)
class StepLatency:
    """Step-level timing with approximate overlap accounting."""

    compute_time_ns: float
    required_transfer_ns: float
    required_decompression_ns: float
    effective_step_latency_ns: float
    overlapped_transfer_ns: float
    exposed_transfer_ns: float
    overlapped_decompression_ns: float
    exposed_decompression_ns: float


class PipelineEngine:
    """
    Models a simple decode pipeline with overlapping compute, DMA prefetch,
    decompression staging, and SRAM stage commitment.
    """

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.current_time_ns = 0.0
        self.dma_available_ns = 0.0
        self.decompression_available_ns = 0.0
        self.sram_stage_available_ns = 0.0
        self.prefetch_events: dict[str, PrefetchEvent] = {}

    def schedule_prefetch(
        self,
        block_id: str,
        now_ns: float,
        transfer_time_ns: float,
        decompression_time_ns: float,
    ) -> bool:
        if block_id in self.prefetch_events:
            return False

        dma_start_ns = max(self.dma_available_ns, now_ns)
        dma_done_ns = dma_start_ns + transfer_time_ns
        decomp_start_ns = max(self.decompression_available_ns, dma_done_ns)
        decomp_done_ns = decomp_start_ns + decompression_time_ns
        stage_start_ns = max(self.sram_stage_available_ns, decomp_done_ns)
        ready_time_ns = stage_start_ns + self.config.sram_stage_latency_ns

        self.dma_available_ns = dma_done_ns
        self.decompression_available_ns = decomp_done_ns
        self.sram_stage_available_ns = ready_time_ns
        self.prefetch_events[block_id] = PrefetchEvent(
            block_id=block_id,
            ready_time_ns=ready_time_ns,
            transfer_time_ns=transfer_time_ns,
            decompression_time_ns=decompression_time_ns,
        )
        return True

    def consume_ready_prefetches(self, now_ns: float) -> list[PrefetchEvent]:
        ready_ids = [block_id for block_id, event in self.prefetch_events.items() if event.ready_time_ns <= now_ns]
        return [self.prefetch_events.pop(block_id) for block_id in ready_ids]

    def model_step(
        self,
        compute_time_ns: float,
        required_transfer_ns: float,
        required_decompression_ns: float,
    ) -> StepLatency:
        transfer_window_ns = required_transfer_ns + required_decompression_ns
        effective_step_latency_ns = max(compute_time_ns, transfer_window_ns)

        overlapped_transfer_ns = min(compute_time_ns, required_transfer_ns)
        exposed_transfer_ns = max(0.0, required_transfer_ns - compute_time_ns)
        remaining_compute_ns = max(0.0, compute_time_ns - overlapped_transfer_ns)
        overlapped_decompression_ns = min(remaining_compute_ns, required_decompression_ns)
        exposed_decompression_ns = max(0.0, required_decompression_ns - overlapped_decompression_ns)

        self.current_time_ns += effective_step_latency_ns
        return StepLatency(
            compute_time_ns=compute_time_ns,
            required_transfer_ns=required_transfer_ns,
            required_decompression_ns=required_decompression_ns,
            effective_step_latency_ns=effective_step_latency_ns,
            overlapped_transfer_ns=overlapped_transfer_ns,
            exposed_transfer_ns=exposed_transfer_ns,
            overlapped_decompression_ns=overlapped_decompression_ns,
            exposed_decompression_ns=exposed_decompression_ns,
        )
