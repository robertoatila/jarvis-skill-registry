"""
tests/test_agentic_examples.py
==============================
Test suite validating that all runnable examples and benchmarks in examples/
and benchmarks/ execute deterministically with exit code 0.
Pure Python Standard Library // Zero PIP Dependencies
"""

import json
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


class TestAgenticExamples(unittest.TestCase):

    def setUp(self):
        self.root = _REPO_ROOT

    def _run_script(self, rel_path: str, *args: str):
        script_path = self.root / rel_path
        self.assertTrue(script_path.exists(), f"Script does not exist: {script_path}")
        proc = subprocess.run(
            [sys.executable, str(script_path), *args],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            timeout=30
        )
        if proc.returncode != 0:
            self.fail(f"Script {rel_path} failed with code {proc.returncode}:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
        self.assertEqual(proc.returncode, 0)

    def test_example_01_quickstart_mission(self):
        self._run_script("examples/01_quickstart_autonomous_mission.py")

    def test_example_02_security_guardrails(self):
        self._run_script("examples/02_fail_closed_security_guardrails.py")

    def test_example_03_bayesian_fitness(self):
        self._run_script("examples/03_bayesian_fitness_and_evolution.py")

    def test_example_04_lockfile_verification(self):
        self._run_script("examples/04_lockfile_and_merkle_verification.py")

    def test_example_05_osint_niche(self):
        self._run_script("examples/05_osint_recon_and_niche_dispatch.py")

    def test_benchmark_runtime_latency(self):
        # Timings are machine-specific: the test must not rewrite the tracked
        # benchmarks/runtime_latency_report.json and dirty the checkout.
        tracked = self.root / "benchmarks" / "runtime_latency_report.json"
        before = tracked.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "runtime_latency_report.json"
            self._run_script("benchmarks/benchmark_runtime_latency.py", "--output", str(report))
            data = json.loads(report.read_text(encoding="utf-8"))
        self.assertIn("policy_evaluation_latency_ms", data)
        self.assertEqual(tracked.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

