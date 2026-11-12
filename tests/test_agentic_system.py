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

    def test_every_unittest_module_is_discovered_not_only_the_agentic_prefix(self):
        good = 'import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n'
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            (path / "test_agentic_fixture.py").write_text(good, encoding="utf-8")
            (path / "test_ui_fixture.py").write_text(good, encoding="utf-8")
            (path / "helper_not_a_test.py").write_text('raise RuntimeError("must not be imported")\n', encoding="utf-8")
            # The self-referential runner test is never discovered.
            (path / "test_agentic_system.py").write_text('raise RuntimeError("must not be imported")\n', encoding="utf-8")
            result = SystemTestRunner(path).run_all_system_tests()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["test_suite_files"], ["test_agentic_fixture.py", "test_ui_fixture.py"])
        self.assertEqual(result["tests_run"], 2)

    def test_repository_battery_includes_the_non_prefixed_modules(self):
        tests_dir = Path(__file__).resolve().parent
        on_disk = {p.name for p in tests_dir.glob("test_*.py")} - {"test_agentic_system.py"}
        self.assertIn("test_ui_security.py", on_disk)
        from tooling.agentic import system_test_runner
        discovered = {
            p.name for p in tests_dir.glob(system_test_runner.DISCOVERY_PATTERN)
        } - set(system_test_runner.EXCLUDED_TEST_FILES)
        self.assertEqual(discovered, on_disk)

    def test_different_test_roots_do_not_reuse_cached_module(self):
        good = 'import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n'
        bad = 'import unittest\nclass T(unittest.TestCase):\n def test_bad(self): self.fail("fixture")\n'
        self.assertEqual(self.run_fixture(good)["status"], "PASS")
        self.assertEqual(self.run_fixture(bad)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
