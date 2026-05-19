from pathlib import Path
import subprocess
import sys

from kvflow.config import SimulationConfig
from kvflow.simulator import Simulator


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
    assert "kvflow" in result.stdout
    assert "simulated_latency_ns" in result.stdout


def test_kvflow_generates_compression_and_sram_hits() -> None:
    config = SimulationConfig.default()
    metrics = Simulator(config, mode="kvflow").run()
    assert metrics.blocks_compressed > 0
    assert metrics.sram_hit_rate > 0.0


def test_baseline_and_kvflow_produce_metrics() -> None:
    config = SimulationConfig.default()
    baseline = Simulator(config, mode="baseline").run()
    kvflow = Simulator(config, mode="kvflow").run()
    assert baseline.total_accesses > 0
    assert kvflow.total_accesses > 0
