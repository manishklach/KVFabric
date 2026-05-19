from pathlib import Path
import subprocess
import sys

from kvfabric.config import SimulationConfig
from kvfabric.simulator import Simulator


def test_compare_mode_reports_both_paths() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, str(root / "simulator" / "run_experiment.py"), "--mode", "compare"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "baseline" in result.stdout
    assert "kvfabric" in result.stdout
    assert "simulated_latency_ns" in result.stdout


def test_compare_mode_can_show_config() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "simulator" / "run_experiment.py"),
            "--mode",
            "compare",
            "--show-config",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "KVFabric configuration" in result.stdout
    assert "kv_block_tokens" in result.stdout


def test_compare_mode_can_show_cost_model() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "simulator" / "run_experiment.py"),
            "--mode",
            "compare",
            "--cost-model",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Cost Model Proxy" in result.stdout
    assert "Cost / 1M tokens proxy" in result.stdout


def test_sweep_mode_runs_context_length_experiment() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            str(root / "simulator" / "run_experiment.py"),
            "--mode",
            "sweep",
            "--sweep",
            "context_length",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "short_2k" in result.stdout
    assert "long_128k_cold" in result.stdout
    assert "context_length" in result.stdout


def test_kvfabric_generates_compression_and_sram_hits() -> None:
    config = SimulationConfig.default()
    metrics = Simulator(config, mode="kvfabric").run()
    assert metrics.blocks_compressed > 0
    assert metrics.sram_hit_rate > 0.0
    assert metrics.prefetched_blocks > 0
    assert metrics.staged_blocks > 0
    assert metrics.dma_overlap_ratio >= 0.0


def test_baseline_and_kvfabric_produce_metrics() -> None:
    config = SimulationConfig.default()
    baseline = Simulator(config, mode="baseline").run()
    kvfabric = Simulator(config, mode="kvfabric").run()
    assert baseline.total_accesses > 0
    assert kvfabric.total_accesses > 0
    assert "transfer_latency_ns" in kvfabric.as_dict()
    assert "prefetched_blocks" in kvfabric.as_dict()
