"""
test_agentic_swe.py // Unit and Integration Tests for Phase 05 (Software Engineering Orchestrator)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tooling.agentic.swe_orchestrator import SoftwareEngineeringOrchestrator


class TestSWEOrchestrator(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.orchestrator = SoftwareEngineeringOrchestrator(self.root)

    def test_valid_pipeline_execution(self):
        valid_code = '''def compute_sum(a: int, b: int) -> int:
    """Computes the sum of two integers."""
    return a + b
'''
        result = self.orchestrator.execute_pipeline("math-sum-tool", valid_code)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.composite_score, 100.0)
        self.assertEqual(result.passed_stages, 4)
        self.assertGreaterEqual(len(result.artifacts), 3)
        self.assertEqual(result.evidence["inspection"]["compilation"]["status"], "PASS")
        self.assertEqual(result.evidence["functional_tests"], "NOT_EXECUTED")
        self.assertEqual(result.evidence["model_or_remote_agent_calls"], 0)
        for art in result.evidence["artifacts"]:
            self.assertEqual(hashlib.sha256(Path(art["path"]).read_bytes()).hexdigest(), art["sha256"])

        # Check that artifacts exist
        for art in result.artifacts:
            self.assertTrue(Path(art).exists(), f"Artifact must exist: {art}")

    def test_syntax_error_failure(self):
        broken_code = '''def invalid_python_code(
    # Missing closing paren and colon
    return 42
'''
        result = self.orchestrator.execute_pipeline("broken-syntax-tool", broken_code)
        self.assertEqual(result.status, "FAIL")
        self.assertLess(result.composite_score, 80.0)
        self.assertFalse(result.evidence["inspection"]["ast_valid"])
        self.assertIn("SyntaxError", result.evidence["inspection"]["ast_error"])

    def test_placeholder_violation_interception(self):
        placeholder_code = '''def dummy_service():
    # TODO: implement this function later
    raise NotImplementedError("Not ready yet")
'''
        result = self.orchestrator.execute_pipeline("placeholder-tool", placeholder_code)
        self.assertEqual(result.status, "FAIL")
        self.assertFalse(result.evidence["inspection"]["valid"])
        self.assertGreaterEqual(len(result.evidence["inspection"]["violations"]), 2)

    def test_repeated_target_preserves_previous_artifacts(self):
        first = self.orchestrator.execute_pipeline("same", "value = 1")
        old = {p: Path(p).read_bytes() for p in first.artifacts}
        second = self.orchestrator.execute_pipeline("same", "value = 2")
        self.assertTrue(set(first.artifacts).isdisjoint(second.artifacts))
        self.assertEqual(old, {p: Path(p).read_bytes() for p in first.artifacts})

    def test_compilation_does_not_execute_source(self):
        marker = self.root / "executed.txt"
        source = f"from pathlib import Path\nPath({str(marker)!r}).write_text('unexpected')\n"
        result = self.orchestrator.execute_pipeline("side-effect", source)
        self.assertEqual(result.status, "PASS")
        self.assertFalse(marker.exists())

    def test_empty_source_and_unsafe_target_are_rejected(self):
        for target, source in (("../outside", "x=1"), ("", "x=1"), ("test", "")):
            with self.assertRaises(ValueError):
                self.orchestrator.execute_pipeline(target, source)

    def test_cli_requires_real_source_and_preserves_failure_exit_code(self):
        cwd = Path(__file__).resolve().parents[1]
        missing = subprocess.run([sys.executable, "-B", "-m", "tooling.agentic.swe_orchestrator", "target"], cwd=cwd, capture_output=True, text=True, timeout=15)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("--source", missing.stderr)
        source = self.root / "bad.py"
        source.write_text("def bad(:", encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", "-m", "tooling.agentic.swe_orchestrator", "target", "--source", str(source), "--registry-root", str(self.root)], cwd=cwd, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
