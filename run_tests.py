#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_tests.py // J.A.R.V.I.S. Master System Test Runner
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Executes all 25 sovereign test suites across 134+ automated tests.
Provides instant feedback and verification of the entire agentic runtime.
"""

import os
import sys
import time
from pathlib import Path

# Add root to python path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.agentic.system_test_runner import SystemTestRunner


def main():
    # Cybernetic banner
    banner = r"""
======================================================================
     J.A.R.V.I.S. // AUTONOMOUS AGENTIC RUNTIME TEST BATTERY
  Sovereign Evolution Protocol v2.0 // Pure Python 3.12 Stdlib
======================================================================
"""
    print(banner)

    runner = SystemTestRunner(ROOT / "tests")
    t0 = time.perf_counter()
    res = runner.run_all_system_tests()
    elapsed = round(time.perf_counter() - t0, 3)

    status = res.get("status", "FAIL")
    passed = res.get("tests_passed", 0)
    failed = res.get("tests_failed", 0)
    errored = res.get("tests_errored", 0)
    total = res.get("tests_run", 0)
    suites = res.get("total_test_suites", 0)

    print(f"  Target Workspace   : {ROOT}")
    print(f"  Test Batteries     : {suites} Suites")
    print(f"  Total Tests Run    : {total}")
    print(f"  Tests Passed       : {passed}")
    print(f"  Tests Failed       : {failed}")
    print(f"  Tests Errored      : {errored}")
    print(f"  Execution Duration : {elapsed}s")
    print("----------------------------------------------------------------------")

    if status in ("PASS", "PASS_WITH_WARNINGS"):
        print(f"  >>> VERDICT: {status} (ALL SYSTEMS GREEN)")
        print("======================================================================\n")
        sys.exit(0)
    else:
        print(f"  >>> VERDICT: {status}")
        if res.get("failures"):
            print("\n  FAILURES:")
            for f in res["failures"]:
                print(f"    - {f.get('test')}: {f.get('trace')}")
        if res.get("load_errors"):
            print("\n  LOAD ERRORS:")
            for e in res["load_errors"]:
                print(f"    - {e.get('test_module')}: {e.get('error')}")
        print("======================================================================\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
