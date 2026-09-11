"""Run only the inspected, isolated regression suites for this change."""
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'tests'))
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for name in ('test_agentic_dag', 'test_agentic_scheduler', 'test_agentic_profiles',
             'test_agentic_composite', 'test_agentic_swe', 'test_agentic_verification',
             'test_agentic_system.TestRunnerAccounting'):
    suite.addTests(loader.loadTestsFromName(name))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() and result.testsRun > 0 else 1)
