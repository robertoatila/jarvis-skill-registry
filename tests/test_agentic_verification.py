"""
test_agentic_verification.py // Unit tests for Verification & Evidence Engine
"""

import os
import unittest
import tempfile
import hashlib
import json
from pathlib import Path

from tooling.agentic.models import (
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
    VerificationStatus,
    Mission,
    MissionStatus
)
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.verification import (
    VerificationEngine,
    VerificationEvidence
)


class TestVerificationEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)
        self.engine = VerificationEngine(registry_root=self.work_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_file_exists_and_hash_matches(self):
        test_file = self.work_dir / "artifact.txt"
        test_content = b"Sovereign Verification Test Content"
        test_file.write_bytes(test_content)
        expected_hash = hashlib.sha256(test_content).hexdigest()

        # 1. file_exists
        req_exists = VerificationRequirement(
            check_type=VerificationType.FILE_EXISTS,
            target=str(test_file)
        )
        ev1 = self.engine.verify_requirement(req_exists)
        self.assertEqual(ev1.status, VerificationStatus.VERIFIED)
        self.assertTrue(ev1.provenance_hash)

        # 2. artifact_hash_matches
        req_hash = VerificationRequirement(
            check_type=VerificationType.ARTIFACT_HASH_MATCHES,
            target=str(test_file),
            expected=expected_hash
        )
        ev2 = self.engine.verify_requirement(req_hash)
        self.assertEqual(ev2.status, VerificationStatus.VERIFIED)
        self.assertEqual(ev2.actual, expected_hash)

    def test_02_command_exit_zero_and_lint_typecheck(self):
        # Python test file
        py_file = self.work_dir / "valid_code.py"
        py_file.write_text("def hello() -> str:\n    return 'JARVIS'\n", encoding="utf-8")

        # 1. lint_clean
        req_lint = VerificationRequirement(
            check_type=VerificationType.LINT_CLEAN,
            target=str(py_file)
        )
        ev_lint = self.engine.verify_requirement(req_lint)
        self.assertEqual(ev_lint.status, VerificationStatus.UNVERIFIED)
        self.assertEqual(ev_lint.evidence_payload["execution"], "NOT_EXECUTED")

        # 2. A compiler cannot substitute for a type checker.
        req_typecheck = VerificationRequirement(
            check_type=VerificationType.TYPECHECK_CLEAN,
            target=str(py_file)
        )
        ev_tc = self.engine.verify_requirement(req_typecheck)
        self.assertEqual(ev_tc.status, VerificationStatus.UNVERIFIED)

        # 3. command_exit_zero
        req_cmd = VerificationRequirement(
            check_type=VerificationType.COMMAND_EXIT_ZERO,
            target="python -c \"print('OK')\""
        )
        ev_cmd = self.engine.verify_requirement(req_cmd)
        self.assertEqual(ev_cmd.status, VerificationStatus.VERIFIED)

    def test_03_task_execution_completed_not_equal_task_verified(self):
        # Create a task marked EXECUTED but with a failing verification requirement
        non_existent = self.work_dir / "missing_file.txt"
        task = TaskNode(
            task_id="task-critical-01",
            title="Produce Missing File",
            status=TaskStatus.EXECUTED,
            execution_result={"producer": "test_fixture", "exit_code": 0},
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target=str(non_existent)
                )
            ]
        )

        # Before verification: status is EXECUTED, NOT VERIFIED
        self.assertEqual(task.status, TaskStatus.EXECUTED)
        self.assertNotEqual(task.status, TaskStatus.VERIFIED)

        # Execute verification gate: must fail and NOT mark as VERIFIED
        verified = self.engine.verify_task(task, base_dir=self.work_dir)
        self.assertFalse(verified)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertNotEqual(task.status, TaskStatus.VERIFIED)

    def test_04_all_tasks_executed_not_equal_mission_success(self):
        # Create a mission where all tasks are executed, but verification fails
        dag = ExecutionDAG()
        non_existent = self.work_dir / "unverified.txt"
        t1 = TaskNode(
            task_id="t1",
            title="Step 1",
            status=TaskStatus.EXECUTED,
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target=str(non_existent)
                )
            ]
        )
        dag.add_node(t1)

        mission = Mission(mission_id="msn-fail-test", goal="Fail-Closed Verification Mission")

        success = self.engine.verify_mission(mission, dag, base_dir=self.work_dir)
        self.assertFalse(success)
        self.assertEqual(mission.status, MissionStatus.FAILED)
        self.assertNotEqual(mission.status, MissionStatus.SUCCEEDED)

    def test_unexecuted_and_evidence_free_tasks_cannot_be_verified(self):
        for status, result in ((TaskStatus.PENDING, None), (TaskStatus.EXECUTED, {"executed": True}),
                               (TaskStatus.EXECUTED, {"producer": "fixture", "exit_code": 0})):
            task = TaskNode("t", "Task", status=status, execution_result=result)
            self.assertFalse(self.engine.verify_task(task))
            self.assertNotEqual(task.status, TaskStatus.VERIFIED)

    def test_real_execution_result_and_file_evidence_can_verify(self):
        target = self.work_dir / "produced.json"
        target.write_text('{"ok": true}', encoding="utf-8")
        task = TaskNode("t", "Produce file", status=TaskStatus.EXECUTED,
                        execution_result={"producer": "fixture_file_writer", "exit_code": 0},
                        verification_requirements=[VerificationRequirement(VerificationType.FILE_EXISTS, str(target))])
        self.assertTrue(self.engine.verify_task(task))
        self.assertEqual(task.status, TaskStatus.VERIFIED)

    def test_regression_check_requires_measured_finite_data(self):
        target = self.work_dir / "metric.json"
        req = VerificationRequirement(VerificationType.NO_REGRESSION, "metric.json", expected=10)
        self.assertEqual(self.engine.verify_requirement(req).status, VerificationStatus.FAILED)
        for metric, expected in ((9, VerificationStatus.FAILED), (11, VerificationStatus.VERIFIED),
                                 ("11", VerificationStatus.FAILED), (float("nan"), VerificationStatus.FAILED)):
            target.write_text(json.dumps({"metric_value": metric}), encoding="utf-8")
            self.assertEqual(self.engine.verify_requirement(req).status, expected)

    def test_invalid_json_schema_instance_is_never_certified(self):
        target = self.work_dir / "instance.json"
        target.write_text('{"count":"bad"}', encoding="utf-8")
        schema = {"type":"object", "properties":{"count":{"type":"integer"}}}
        req = VerificationRequirement(VerificationType.SCHEMA_VALID, "instance.json", expected=schema)
        self.assertNotEqual(self.engine.verify_requirement(req).status, VerificationStatus.VERIFIED)


if __name__ == "__main__":
    unittest.main()
