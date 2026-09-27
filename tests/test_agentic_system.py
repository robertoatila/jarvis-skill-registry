"""
test_agentic_system.py // Unit tests for System Test Runner (Phase 26)
"""

import unittest
import tempfile
from pathlib import Path
from tooling.agentic.system_test_runner import SystemTestRunner


class TestSystemTestRunner(unittest.TestCase):

    def test_01_run_all_system_tests(self):
        runner = SystemTestRunner()
        res = runner.run_all_system_tests()

        self.assertEqual(res["status"], "PASS")
        self.assertGreaterEqual(res["total_test_suites"], 20)
        self.assertGreaterEqual(res["tests_run"], 70)
        self.assertEqual(res["tests_failed"], 0)
        self.assertEqual(res["tests_errored"], 0)


class TestRunnerAccounting(unittest.TestCase):
    def run_fixture(self, source=None):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            if source is not None:
                (path / "test_agentic_fixture.py").write_text(source, encoding="utf-8")
            return SystemTestRunner(path).run_all_system_tests()

    def test_empty_suite_is_not_success(self):
        self.assertEqual(self.run_fixture()["status"], "FAIL")

    def test_import_failure_is_counted_and_fails(self):
        result = self.run_fixture('raise ImportError("controlled fixture")\n')
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["tests_errored"], 1)
        self.assertEqual(result["tests_passed"], 0)

    def test_skips_are_not_counted_as_passed(self):
        source = 'import unittest\nclass T(unittest.TestCase):\n @unittest.skip("fixture")\n def test_skip(self): pass\n'
        result = self.run_fixture(source)
        self.assertEqual(result["tests_skipped"], 1)
        self.assertEqual(result["tests_passed"], 0)
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")

    def test_different_test_roots_do_not_reuse_cached_module(self):
        good = 'import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n'
        bad = 'import unittest\nclass T(unittest.TestCase):\n def test_bad(self): self.fail("fixture")\n'
        self.assertEqual(self.run_fixture(good)["status"], "PASS")
        self.assertEqual(self.run_fixture(bad)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
