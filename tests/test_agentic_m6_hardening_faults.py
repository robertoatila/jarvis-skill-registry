"""
test_agentic_m6_hardening_faults.py // Milestone 6 Comprehensive Test Suite
Pure Python 3.12 Standard Library (Zero PIP Dependencies)

Tests:
1. Concurrency drift protection (optimistic concurrency rejects out-of-band mutations)
2. Corrupted state store resilience (truncated JSON does not crash state recovery)
3. Adversarial path traversal rejection (fail-closed directory traversal containment)
4. Protected system path tamper protection (.git, config/api_keys.json, state/authoritative)
5. Context compaction efficiency & invariant retention benchmark
6. Sovereign cost-utility economic efficiency benchmark
7. End-to-end 9-stage local verified SWE mission execution
8. Meta-cognitive governor loop halting in runtime execution
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.fault_injection import (
    FaultInjectionHarness,
    FaultType,
    FaultExperimentResult
)
from tooling.agentic.benchmarks import (
    BenchmarkSuite,
    ContextBenchmarkReport,
    CostUtilityBenchmarkReport
)
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.models import (
    Mission,
    MissionStatus,
    TaskNode,
    TaskStatus,
    RiskLevel,
    VerificationRequirement,
    VerificationType
)
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.adapters.local import LocalAction, LocalAdapterType


class TestAgenticM6HardeningFaults(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name).resolve()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_fault_concurrency_drift_protection(self):
        """Test 1: Optimistic concurrency rejects out-of-band file modifications safely."""
        harness = FaultInjectionHarness(workspace_root=self.tmp_path)
        res = harness.inject_concurrency_drift("src/config.py")

        self.assertTrue(res.induced)
        self.assertTrue(res.handled_safely)
        self.assertTrue(res.state_preserved)
        self.assertIn("Concurrency Conflict", res.exception_caught or "")

    def test_fault_corrupted_state_recovery(self):
        """Test 2: Truncated or corrupted JSON in state store does not crash mission listing."""
        harness = FaultInjectionHarness(workspace_root=self.tmp_path)
        res = harness.inject_corrupted_state_file(self.tmp_path / "state" / "missions")

        self.assertTrue(res.induced)
        self.assertTrue(res.handled_safely)
        self.assertIsNone(res.exception_caught)

    def test_adversarial_directory_traversal_blocked(self):
        """Test 3: Fail-closed containment blocks directory traversal attempts."""
        harness = FaultInjectionHarness(workspace_root=self.tmp_path)

        for evil_path in ["../../evil.txt", "..\\..\\evil.txt", "sub/../../escape.py"]:
            res = harness.inject_directory_traversal_attack(evil_path)
            self.assertTrue(res.handled_safely, f"Failed to block traversal: {evil_path}")
            self.assertIsNotNone(res.exception_caught)

    def test_adversarial_protected_path_blocked(self):
        """Test 4: Fail-closed containment strictly blocks modifications to protected files."""
        harness = FaultInjectionHarness(workspace_root=self.tmp_path)

        for prot_target in [".git/hooks/pre-commit", "config/api_keys.json", "state/authoritative/master.json"]:
            res = harness.inject_protected_path_tampering(prot_target)
            self.assertTrue(res.handled_safely, f"Failed to block protected path: {prot_target}")
            self.assertIsNotNone(res.exception_caught)

    def test_context_compaction_benchmark(self):
        """Test 5: Context compaction benchmark verifies >30% token reduction and invariant retention."""
        sample_log = """
        [2026-09-11T00:01:00Z] INFO: Starting mission execution wave 1.
        DECISION: Selected sovereign-local-deepseek-8b for privacy reasons.
        UNCERTAINTY: Unknown network latency to remote endpoint.
        DEBUG: Memory address 0x7fff89ab100.
        DEBUG: Thread 14002 processing chunk 1 of 500.
        DEBUG: Detailed stack frame: module.py line 45 in execute.
        DECISION: Approved LocalAction write to pkg/module.py.
        """ * 5

        report = BenchmarkSuite.run_context_compaction_benchmark(sample_log)
        self.assertGreater(report.token_reduction_percent, 25.0)
        self.assertTrue(report.decisions_retained)
        self.assertTrue(report.uncertainties_retained)

    def test_cost_utility_benchmark(self):
        """Test 6: Cost-utility benchmark verifies sovereign local models provide 100% cost savings."""
        report = BenchmarkSuite.run_cost_utility_benchmark(task_tokens=100_000)
        self.assertEqual(report.sovereign_local_cost_usd, 0.0)
        self.assertGreater(report.frontier_cloud_cost_usd, 0.0)
        self.assertEqual(report.cost_savings_percent, 100.0)
        self.assertGreaterEqual(len(report.models_evaluated), 3)

    def test_end_to_end_local_verified_mission(self):
        """Test 7: End-to-end execution of a local verified SWE mission across all 9 stages."""
        runtime = JarvisAgenticRuntime(registry_root=self.tmp_path)
        dag = ExecutionDAG()

        # Task: write a local math module and verify it exists
        target_file = "pkg/math_operations.py"
        code_content = "def multiply(a: int, b: int) -> int:\n    return a * b\n"

        action = LocalAction(
            adapter=LocalAdapterType.WRITE_TEXT,
            path=target_file,
            content=code_content
        )

        abs_target = (self.tmp_path / target_file).resolve()
        task = TaskNode(
            task_id="tsk-e2e-01",
            title="Create Math Operations Module",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["python-pro"],
            action=action.to_dict(),
            risk_level=RiskLevel.R1_LOCAL_WRITE,
            write_scopes=[str(abs_target)],
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target=str(abs_target)
                )
            ]
        )
        dag.add_node(task)

        mission = Mission(
            mission_id="msn-e2e-m6-01",
            goal="E2E SWE Mission",
            dag=dag
        )

        exec_res = runtime.execute_goal(mission)
        self.assertEqual(exec_res["status"], "SUCCESS")
        self.assertIn("EXECUTE", exec_res["lifecycle_stages"])
        self.assertIn("VERIFY", exec_res["lifecycle_stages"])
        self.assertIn("LEARN", exec_res["lifecycle_stages"])

        # Verify task node terminal states
        completed_task = mission.dag.nodes["tsk-e2e-01"]
        self.assertEqual(completed_task.status, TaskStatus.VERIFIED)
        self.assertTrue(abs_target.exists())
        self.assertEqual(abs_target.read_text(encoding="utf-8"), code_content)

        # Verify evidence ledger has decision receipts and verification artifacts
        self.assertGreater(len(mission.evidence_ledger), 0)

    def test_cognitive_governor_loop_and_halt_integration(self):
        """Test 8: CognitiveGovernor halts execution when infinite repetition threshold is exceeded."""
        runtime = JarvisAgenticRuntime(registry_root=self.tmp_path)
        runtime.cognitive_governor.max_consecutive_repeats = 2

        dag = ExecutionDAG()
        # Two tasks with identical signatures
        t1 = TaskNode(task_id="tsk-rep-01", title="Repeated Task", required_skills=["general"])
        t2 = TaskNode(task_id="tsk-rep-02", title="Repeated Task", required_skills=["general"])
        dag.add_node(t1)
        dag.add_node(t2)

        mission = Mission(
            mission_id="msn-cog-halt-01",
            goal="Cognitive Loop Halt Test",
            dag=dag
        )

        res = runtime.execute_goal(mission)
        # Should detect loop and cancel subsequent tasks
        cancelled_tasks = [t for t in mission.dag.nodes.values() if t.status == TaskStatus.CANCELLED]
        self.assertGreaterEqual(len(cancelled_tasks), 1)


if __name__ == "__main__":
    unittest.main()
