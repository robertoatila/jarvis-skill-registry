"""
test_agentic_runtime_hardening.py // Unit & Integration Tests for Tier 2 Runtime Hardening
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Validates:
- PolicyEngine wiring into task dispatch (R0-R5, scope confinement, anti-self-approval)
- BudgetTracker circuit breaker tripping & fail-closed termination
- AuthoritativeStateStore atomic mission lifecycle persistence
- Canonical Artifact generation with cryptographic SHA-256 provenance
- Idempotent mission recovery & restart resilience
"""

import unittest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime, timezone

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.models import (
    Mission,
    MissionStatus,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
    VerificationStatus,
    RiskLevel,
    ApprovalStatus,
    Artifact,
    ArtifactType,
    SCHEMA_VERSION
)
from tooling.agentic.policy import PolicyDecision
from tooling.agentic.budgets import BudgetLimits, CircuitBreakerTrippedError
from tooling.agentic.dag import ExecutionDAG


class TestAgenticRuntimeHardening(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create workspace directory structure
        (self.root / "src").mkdir(parents=True, exist_ok=True)
        (self.root / "state" / "missions").mkdir(parents=True, exist_ok=True)
        (self.root / "state" / "corrupted").mkdir(parents=True, exist_ok=True)
        (self.root / "skills").mkdir(parents=True, exist_ok=True)
        (self.root / "artifacts").mkdir(parents=True, exist_ok=True)

        self.config = JarvisRuntimeConfig(registry_root=self.root)
        self.runtime = JarvisAgenticRuntime(config=self.config)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_policy_rejection_blocks_r5_destructive_task(self):
        """Invariant: R5 Destructive actions are strictly denied from autonomous execution."""
        mission_id = "msn-r5-block"
        mission = Mission(mission_id=mission_id, goal="Destructive cleanup")
        dag = ExecutionDAG()
        t1 = TaskNode(
            task_id="tsk-destruct-01",
            title="Dangerous Purge",
            agent_profile="Quantum-ExecutorAgent",
            risk_level=RiskLevel.R5_DESTRUCTIVE,
            required_skills=["systematic-code-debugging"],
            read_scopes=["src"]
        )
        t1.verification_requirements.append(VerificationRequirement(
            check_type=VerificationType.COMMAND_EXIT_ZERO,
            target="python -c \"import sys; sys.exit(0)\""
        ))
        dag.add_node(t1)
        mission.dag = dag
        self.runtime.state_store.save_mission(mission)

        # Run scheduler waves on this DAG directly through runtime loop logic
        waves = self.runtime.scheduler.schedule(dag)
        self.assertEqual(len(waves), 1)

        # Execute goal with planner override or direct wave execution
        res = self.runtime.execute_goal(
            goal_prompt="Run Destructive Cleanup",
            required_capabilities=["systematic-code-debugging"]
        )
        # Modify planned mission node to R5 before execution to test policy gate
        mission_planned = self.runtime.planner.plan_mission(
            goal_title="Purge",
            required_capabilities=["systematic-code-debugging"]
        )
        for node in mission_planned.dag.nodes.values():
            node.risk_level = RiskLevel.R5_DESTRUCTIVE

        self.runtime.state_store.save_mission(mission_planned)

        # Execute mission with R5 tasks
        waves = self.runtime.scheduler.schedule(mission_planned.dag)
        for wave in waves:
            for task in wave.tasks:
                policy_res = self.runtime.policy.evaluate_policy(
                    agent_profile=self.runtime.agents.get(task.agent_profile),
                    action="command",
                    tool_or_skill=task.required_skills[0] if task.required_skills else "general",
                    resource=task.read_scopes[0] if task.read_scopes else "",
                    risk_level=task.risk_level,
                    task_id=task.task_id
                )
                self.assertEqual(policy_res.decision, PolicyDecision.DENY)
                self.assertIn("R5", policy_res.reason)

    def test_02_approval_gate_blocks_r4_without_operator_approval(self):
        """Invariant: R4 Infrastructure Mutation requires explicit operator approval."""
        agent = self.runtime.agents.get("Quantum-ExecutorAgent")
        policy_res = self.runtime.policy.evaluate_policy(
            agent_profile=agent,
            action="command",
            tool_or_skill="systematic-code-debugging",
            resource="src",
            risk_level=RiskLevel.R4_INFRA_MUTATION,
            task_id="tsk-r4-01"
        )
        self.assertEqual(policy_res.decision, PolicyDecision.REQUIRE_APPROVAL)
        self.assertIsNotNone(policy_res.approval_id)

        # Verify anti-self-approval rule
        app_id = policy_res.approval_id
        denied = self.runtime.policy.grant_approval(app_id, operator_id="runtime:Quantum-ExecutorAgent")
        self.assertFalse(denied, "Autonomous agent must not be allowed to self-approve R4 request")

        # Verify human operator can grant approval
        approved = self.runtime.policy.grant_approval(app_id, operator_id="operator:alice")
        self.assertTrue(approved, "Valid operator must be able to grant R4 approval")

        req = self.runtime.policy.get_approval_request(app_id)
        self.assertEqual(req.status, ApprovalStatus.APPROVED)
        self.assertEqual(req.approved_by, "operator:alice")

    def test_03_workspace_path_traversal_denied(self):
        """Invariant: File scopes outside workspace root must be denied."""
        agent = self.runtime.agents.get("Quantum-ExecutorAgent")
        escape_path = "../../etc/shadow"
        policy_res = self.runtime.policy.evaluate_policy(
            agent_profile=agent,
            action="write",
            tool_or_skill="general",
            resource=escape_path,
            risk_level=RiskLevel.R1_LOCAL_WRITE
        )
        self.assertEqual(policy_res.decision, PolicyDecision.DENY)
        self.assertIn("traversal", policy_res.reason)

    def test_04_budget_circuit_breaker_trips_on_tool_calls(self):
        """Invariant: Resource exhaustion trips circuit breaker fail-closed."""
        # Set budget limit to 1 tool call max
        limits = BudgetLimits(max_tool_calls=1, token_budget=100_000, runtime_budget_seconds=60.0)

        result = self.runtime.execute_goal(
            goal_prompt="Multi-task health check",
            required_capabilities=["systematic-code-debugging", "comprehensive-code-review"],
            budget_limits=limits
        )

        self.assertEqual(result["status"], "FAILED")
        self.assertTrue(result["circuit_breaker_tripped"])
        self.assertIn("TOOL_CALL_BUDGET_EXCEEDED", result["circuit_breaker_reason"])

    def test_05_authoritative_state_persisted_atomically(self):
        """Invariant: Mission state is atomically saved to state/missions/{id}.json."""
        result = self.runtime.execute_goal(
            goal_prompt="Audit and Verify Service",
            required_capabilities=["systematic-code-debugging"]
        )
        self.assertEqual(result["status"], "SUCCESS")

        mission_id = result["mission_id"]
        mission_file = self.root / "state" / "missions" / f"{mission_id}.json"
        self.assertTrue(mission_file.exists(), f"State file {mission_file} must exist")

        # Load back via AuthoritativeStateStore
        loaded_mission = self.runtime.load_mission(mission_id)
        self.assertIsNotNone(loaded_mission)
        self.assertEqual(loaded_mission.mission_id, mission_id)
        self.assertEqual(loaded_mission.status, MissionStatus.SUCCEEDED)
        self.assertIn("budget_consumption", loaded_mission.metadata)

    def test_06_canonical_artifact_generation_and_provenance(self):
        """Invariant: Output files are wrapped into canonical Artifacts with SHA-256."""
        # Create a sample file in artifacts
        out_file = self.root / "artifacts" / "test_report.json"
        out_file.write_text('{"tests": "passed"}', encoding="utf-8")

        art = Artifact(
            artifact_id="art-test-01",
            mission_id="msn-art-test",
            task_id="tsk-art-01",
            producer="runtime:Quantum-ExecutorAgent",
            artifact_type=ArtifactType.TEST_REPORT,
            path="artifacts/test_report.json"
        )
        h = art.compute_hash(base_dir=self.root)
        self.assertTrue(len(h) == 64)
        self.assertGreater(art.size_bytes, 0)

        # Verify serialization
        data = art.to_dict()
        self.assertEqual(data["artifact_id"], "art-test-01")
        self.assertEqual(data["artifact_type"], "test_report")
        self.assertEqual(data["sha256"], h)

        # Verify deserialization
        restored = Artifact.from_dict(data)
        self.assertEqual(restored.artifact_id, art.artifact_id)
        self.assertEqual(restored.sha256, art.sha256)

    def test_07_idempotent_mission_resume_skips_verified_tasks(self):
        """Invariant: Resumed missions never re-execute VERIFIED tasks."""
        mission_id = "msn-resume-test"
        mission = Mission(mission_id=mission_id, goal="Resume Goal")
        dag = ExecutionDAG()

        # Task 1 is already verified
        t1 = TaskNode(
            task_id="tsk-step-01",
            title="Step 1",
            status=TaskStatus.VERIFIED,
            agent_profile="Quantum-ExecutorAgent"
        )
        # Task 2 was running when crash happened
        t2 = TaskNode(
            task_id="tsk-step-02",
            title="Step 2",
            status=TaskStatus.RUNNING,
            agent_profile="Quantum-ExecutorAgent",
            retry_count=0,
            max_retries=3
        )
        t2.verification_requirements.append(VerificationRequirement(
            check_type=VerificationType.COMMAND_EXIT_ZERO,
            target="python -c \"import sys; sys.exit(0)\""
        ))
        dag.add_node(t1)
        dag.add_node(t2)
        dag.add_dependency("tsk-step-01", "tsk-step-02")
        mission.dag = dag

        self.runtime.state_store.save_mission(mission)

        # Resume mission
        res = self.runtime.resume_mission(mission_id)
        self.assertEqual(res["status"], "SUCCESS")

        # Load back from store
        reloaded = self.runtime.load_mission(mission_id)
        self.assertEqual(reloaded.status, MissionStatus.SUCCEEDED)
        # Task 1 must stay VERIFIED without retry count increment
        self.assertEqual(reloaded.dag.nodes["tsk-step-01"].status, TaskStatus.VERIFIED)
        self.assertEqual(reloaded.dag.nodes["tsk-step-01"].retry_count, 0)
        # Task 2 was recovered and completed
        self.assertEqual(reloaded.dag.nodes["tsk-step-02"].status, TaskStatus.VERIFIED)
        self.assertEqual(reloaded.dag.nodes["tsk-step-02"].retry_count, 1)


if __name__ == "__main__":
    unittest.main()
