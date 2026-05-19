from __future__ import annotations

from dataclasses import dataclass

from .config import PipelineConfig


@dataclass(slots=True)
class PrefetchEvent:
    """One asynchronous movement event into the SRAM staging buffer."""

    block_id: str
    issued_at_ns: float
    transfer_done_ns: float
    decompression_done_ns: float
    ready_time_ns: float
    transfer_time_ns: float
    decompression_time_ns: float
    source: str


@dataclass(slots=True)
class StepLatency:
    """Step-level timing with overlap-aware critical-path accounting."""

    compute_time_ns: float
    required_transfer_ns: float
    required_decompression_ns: float
    effective_step_latency_ns: float
    overlapped_transfer_ns: float
    exposed_transfer_ns: float
    overlapped_decompression_ns: float
    exposed_decompression_ns: float
    hidden_latency_ns: float
    exposed_latency_ns: float
    overlap_ratio: float


class PipelineEngine:
    """Approximate token-level pipeline with DMA, decompression, and staging overlap."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.current_time_ns = 0.0
        self.dma_available_ns = 0.0
        self.decompression_available_ns = 0.0
        self.sram_stage_available_ns = 0.0
        self.prefetch_events: dict[str, PrefetchEvent] = {}

    def _reserve_pipeline(
        self,
        block_id: str,
        issue_time_ns: float,
        transfer_time_ns: float,
        decompression_time_ns: float,
        source: str,
    ) -> PrefetchEvent:
        dma_start_ns = max(self.dma_available_ns, issue_time_ns)
        transfer_done_ns = dma_start_ns + transfer_time_ns
        decompression_done_ns = max(self.decompression_available_ns, transfer_done_ns) + decompression_time_ns
        ready_time_ns = max(self.sram_stage_available_ns, decompression_done_ns) + self.config.sram_stage_latency_ns

        self.dma_available_ns = transfer_done_ns
        self.decompression_available_ns = decompression_done_ns
        self.sram_stage_available_ns = ready_time_ns
        return PrefetchEvent(
            block_id=block_id,
            issued_at_ns=issue_time_ns,
            transfer_done_ns=transfer_done_ns,
            decompression_done_ns=decompression_done_ns,
            ready_time_ns=ready_time_ns,
            transfer_time_ns=transfer_time_ns,
            decompression_time_ns=decompression_time_ns,
            source=source,
        )

    def schedule_prefetch(
        self,
        block_id: str,
        now_ns: float,
        transfer_time_ns: float,
        decompression_time_ns: float,
    ) -> bool:
        if block_id in self.prefetch_events:
            return False
        if len(self.prefetch_events) >= self.config.max_staging_queue_depth:
            return False
        self.prefetch_events[block_id] = self._reserve_pipeline(
            block_id,
            issue_time_ns=now_ns,
            transfer_time_ns=transfer_time_ns,
            decompression_time_ns=decompression_time_ns,
            source="prefetch",
        )
        return True

    def get_event(self, block_id: str) -> PrefetchEvent | None:
        return self.prefetch_events.get(block_id)

    def schedule_demand_fetch(
        self,
        block_id: str,
        issue_time_ns: float,
        transfer_time_ns: float,
        decompression_time_ns: float,
    ) -> PrefetchEvent:
        existing = self.prefetch_events.get(block_id)
        if existing is not None:
            return existing
        return self._reserve_pipeline(
            block_id,
            issue_time_ns=issue_time_ns,
            transfer_time_ns=transfer_time_ns,
            decompression_time_ns=decompression_time_ns,
            source="demand",
        )

    def consume_ready_prefetches(self, now_ns: float) -> list[PrefetchEvent]:
        ready_ids = [block_id for block_id, event in self.prefetch_events.items() if event.ready_time_ns <= now_ns]
        return [self.prefetch_events.pop(block_id) for block_id in ready_ids]

    def model_step(
        self,
        step_start_ns: float,
        compute_time_ns: float,
        service_events: list[PrefetchEvent],
        required_transfer_ns: float,
        required_decompression_ns: float,
    ) -> StepLatency:
        if not service_events:
            self.current_time_ns = step_start_ns + compute_time_ns
            return StepLatency(
                compute_time_ns=compute_time_ns,
                required_transfer_ns=required_transfer_ns,
                required_decompression_ns=required_decompression_ns,
                effective_step_latency_ns=compute_time_ns,
                overlapped_transfer_ns=0.0,
                exposed_transfer_ns=0.0,
                overlapped_decompression_ns=0.0,
                exposed_decompression_ns=0.0,
                hidden_latency_ns=0.0,
                exposed_latency_ns=0.0,
                overlap_ratio=1.0,
            )

        latest_transfer_done_ns = max(event.transfer_done_ns for event in service_events)
        latest_ready_ns = max(event.ready_time_ns for event in service_events)

        transfer_window_ns = max(0.0, latest_transfer_done_ns - step_start_ns)
        decompression_window_ns = max(0.0, latest_ready_ns - latest_transfer_done_ns)
        overlapped_transfer_ns = min(compute_time_ns, transfer_window_ns)
        exposed_transfer_ns = max(0.0, transfer_window_ns - compute_time_ns)
        remaining_compute_ns = max(0.0, compute_time_ns - overlapped_transfer_ns)
        overlapped_decompression_ns = min(remaining_compute_ns, decompression_window_ns)
        exposed_decompression_ns = max(0.0, decompression_window_ns - remaining_compute_ns)

        hidden_latency_ns = overlapped_transfer_ns + overlapped_decompression_ns
        exposed_latency_ns = exposed_transfer_ns + exposed_decompression_ns
        effective_step_latency_ns = compute_time_ns + exposed_latency_ns
        total_overlap_window = transfer_window_ns + decompression_window_ns
        overlap_ratio = hidden_latency_ns / total_overlap_window if total_overlap_window > 0 else 1.0

        self.current_time_ns = step_start_ns + effective_step_latency_ns
        return StepLatency(
            compute_time_ns=compute_time_ns,
            required_transfer_ns=required_transfer_ns,
            required_decompression_ns=required_decompression_ns,
            effective_step_latency_ns=effective_step_latency_ns,
            overlapped_transfer_ns=overlapped_transfer_ns,
            exposed_transfer_ns=exposed_transfer_ns,
            overlapped_decompression_ns=overlapped_decompression_ns,
            exposed_decompression_ns=exposed_decompression_ns,
            hidden_latency_ns=hidden_latency_ns,
            exposed_latency_ns=exposed_latency_ns,
            overlap_ratio=overlap_ratio,
        )
