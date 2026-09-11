"""
tests/test_agentic_examples.py
==============================
Test suite validating that all runnable examples and benchmarks in examples/
and benchmarks/ execute deterministically with exit code 0.
Pure Python 3.12 Standard Library // Zero PIP Dependencies
"""

import sys
import unittest
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


class TestAgenticExamples(unittest.TestCase):

    def setUp(self):
        self.root = _REPO_ROOT

    def _run_script(self, rel_path: str):
        script_path = self.root / rel_path
        self.assertTrue(script_path.exists(), f"Script does not exist: {script_path}")
        proc = subprocess.run(
            [sys.executable, str(script_path)],
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

    def test_benchmark_runtime_latency(self):
        self._run_script("benchmarks/benchmark_runtime_latency.py")


if __name__ == "__main__":
    unittest.main()
