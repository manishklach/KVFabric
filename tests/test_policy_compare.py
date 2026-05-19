from pathlib import Path
import subprocess
import sys


def test_policy_compare_outputs_expected_fields() -> None:
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, str(root / "simulator" / "run_experiment.py"), "--mode", "policy-compare"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "LRUHotWindowPolicy" in result.stdout
    assert "LFUCompressionPolicy" in result.stdout
    assert "HotWarmColdPolicy" in result.stdout
    assert "hbm_bytes_read" in result.stdout
    assert "exposed_latency_ns" in result.stdout
