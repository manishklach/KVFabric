from kvfabric.config import PipelineConfig
from kvfabric.pipeline import PipelineEngine


def test_dma_budget_enforces_serial_issue() -> None:
    engine = PipelineEngine(PipelineConfig())
    first = engine.schedule_demand_fetch("b0", issue_time_ns=0.0, transfer_time_ns=100.0, decompression_time_ns=20.0)
    second = engine.schedule_demand_fetch("b1", issue_time_ns=0.0, transfer_time_ns=100.0, decompression_time_ns=20.0)
    assert second.transfer_done_ns >= first.transfer_done_ns


def test_overlap_accounting_hides_fully_covered_transfer() -> None:
    engine = PipelineEngine(PipelineConfig())
    event = engine.schedule_demand_fetch("b0", issue_time_ns=0.0, transfer_time_ns=80.0, decompression_time_ns=20.0)
    step = engine.model_step(
        step_start_ns=0.0,
        compute_time_ns=300.0,
        service_events=[event],
        required_transfer_ns=80.0,
        required_decompression_ns=20.0,
    )
    assert step.exposed_latency_ns == 0.0
    assert step.hidden_latency_ns > 0.0
