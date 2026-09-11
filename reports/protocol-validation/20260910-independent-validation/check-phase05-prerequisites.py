"""Read-only production inspection plus temporary-fixture acceptance probes.

Exit 1 means the existing execution/evidence prerequisites do not meet the
protocol. Never starts jarvis_server or an autonomous worker.
"""
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tooling.agentic.models import TaskNode, VerificationRequirement, VerificationType, VerificationStatus
from tooling.agentic.verification import VerificationEngine
from tooling.agentic.system_test_runner import SystemTestRunner

checks = []
with tempfile.TemporaryDirectory(prefix='jarvis-prerequisites-') as td:
    root = Path(td)
    verifier = VerificationEngine(root)
    unexecuted = TaskNode('pending', 'Never executed')
    accepted = verifier.verify_task(unexecuted)
    checks.append({'contract': 'Unexecuted task cannot become verified', 'passed': not accepted,
                   'actual': unexecuted.status.value})

    req = VerificationRequirement(VerificationType.NO_REGRESSION, target='missing-metric.json', expected=100)
    result = verifier.verify_requirement(req)
    checks.append({'contract': 'No regression requires an observed metric',
                   'passed': result.status != VerificationStatus.VERIFIED, 'actual': result.to_dict()})

    (root / 'wrong-types.py').write_text('def result() -> int:\n    return "wrong type"\n', encoding='utf-8')
    result = verifier.verify_requirement(VerificationRequirement(VerificationType.TYPECHECK_CLEAN, target='wrong-types.py'))
    checks.append({'contract': 'Compilation alone cannot certify type checking',
                   'passed': result.status != VerificationStatus.VERIFIED, 'actual': result.to_dict()})

    (root / 'invalid-schema-instance.json').write_text('{"count": "not an integer"}', encoding='utf-8')
    schema = {'type': 'object', 'required': ['count'], 'properties': {'count': {'type': 'integer'}}}
    result = verifier.verify_requirement(VerificationRequirement(VerificationType.SCHEMA_VALID, target='invalid-schema-instance.json', expected=schema))
    checks.append({'contract': 'Schema verification validates field types',
                   'passed': result.status != VerificationStatus.VERIFIED, 'actual': result.to_dict()})

    tests = root / 'tests'; tests.mkdir()
    (tests / 'test_agentic_load_failure_probe.py').write_text('raise ImportError("intentional local acceptance fixture")\n', encoding='utf-8')
    result = SystemTestRunner(tests_dir=tests).run_all_system_tests()
    checks.append({'contract': 'Test loader failure must fail the check', 'passed': result['status'] == 'FAIL', 'actual': result})

print(json.dumps({'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
                  'checks_passed': sum(c['passed'] for c in checks), 'checks_total':len(checks), 'checks':checks}, indent=2))
raise SystemExit(0 if all(c['passed'] for c in checks) else 1)
