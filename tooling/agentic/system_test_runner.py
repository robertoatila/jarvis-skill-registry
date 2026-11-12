"""
system_test_runner.py // J.A.R.V.I.S. Master System Test Runner
Pure Python Standard Library (Zero PIP Dependencies)
Implements Phase 26 System Test:
- Discovers and executes every tests/test_*.py suite without a hard-coded count
  (test_agentic_system.py is excluded because it runs this runner itself)
- Produces verified consolidated evidence of zero regressions
"""

from __future__ import annotations
import sys
import time
import unittest
from pathlib import Path
from typing import Dict, Any, Optional
import importlib.util
import hashlib


from .config import CONFIG

REGISTRY_ROOT = CONFIG.registry_root
TESTS_DIR = REGISTRY_ROOT / "tests"
DISCOVERY_PATTERN = "test_*.py"
# Runs the runner itself; discovering it would recurse.
EXCLUDED_TEST_FILES = frozenset({"test_agentic_system.py"})


class SystemTestRunner:
    """
    Consolidated test runner executing the complete battery of agentic test suites.
    """

    def __init__(self, tests_dir: Optional[Path] = None):
        self.tests_dir = (tests_dir or TESTS_DIR).resolve()

    def run_all_system_tests(self) -> Dict[str, Any]:
        if str(REGISTRY_ROOT) not in sys.path:
            sys.path.insert(0, str(REGISTRY_ROOT))
        if str(self.tests_dir) not in sys.path:
            sys.path.insert(0, str(self.tests_dir))

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        # Every unittest module is part of the battery.  Discovery used to be
        # limited to test_agentic_*.py, which silently left a dozen modules
        # (UI security, remote companion, memory privacy, ...) out of --full-test.
        test_files = sorted(
            f.name for f in self.tests_dir.glob(DISCOVERY_PATTERN)
            if f.is_file() and f.name not in EXCLUDED_TEST_FILES
        )

        load_errors = []
        for f_name in test_files:
            mod_name = f_name[:-3]
            try:
                source = self.tests_dir / f_name
                unique_name = mod_name + "_" + hashlib.sha256(str(source).encode()).hexdigest()[:12]
                spec = importlib.util.spec_from_file_location(unique_name, source)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[unique_name] = mod
                spec.loader.exec_module(mod)
                suite.addTests(loader.loadTestsFromModule(mod))
            except Exception as e:
                load_errors.append({"test_module": mod_name, "error": str(e)})

        # Custom runner to capture results silently
        result = unittest.TestResult()
        start_test_time = time.perf_counter()
        suite.run(result)
        duration_s = round(time.perf_counter() - start_test_time, 3)

        passed_count = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped) - len(result.expectedFailures) - len(result.unexpectedSuccesses)
        failed_count = len(result.failures)
        error_count = len(result.errors) + len(load_errors)

        failure_details = []
        for test, trace in result.failures:
            failure_details.append({"test": str(test), "trace": trace[-300:]})
        for test, trace in result.errors:
            failure_details.append({"test": str(test), "trace": trace[-300:], "error": True})

        status = "PASS" if (result.testsRun > 0 and failed_count == 0 and error_count == 0 and not result.unexpectedSuccesses) else "FAIL"
        if status == "PASS" and (result.skipped or result.expectedFailures):
            status = "PASS_WITH_WARNINGS"

        return {
            "status": status,
            "total_test_suites": len(test_files),
            "test_suite_files": test_files,
            "tests_run": result.testsRun,
            "tests_passed": passed_count,
            "tests_failed": failed_count,
            "tests_errored": error_count,
            "duration_seconds": duration_s,
            "failures": failure_details,
            "load_errors": load_errors,
            "tests_skipped": len(result.skipped),
            "expected_failures": len(result.expectedFailures),
            "unexpected_successes": len(result.unexpectedSuccesses)
        }


if __name__ == "__main__":
    runner = SystemTestRunner()
    res = runner.run_all_system_tests()
    print(f"Status: {res['status']}")
    print(f"Suites: {res['total_test_suites']} | Tests: {res['tests_run']} | Passed: {res['tests_passed']} | Failed: {res['tests_failed']} | Duration: {res['duration_seconds']}s")
    sys.exit(0 if res["status"] in ("PASS", "PASS_WITH_WARNINGS") else 1)
