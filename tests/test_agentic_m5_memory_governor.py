"""
test_agentic_m5_memory_governor.py // Milestone 5 Comprehensive Test Suite
Pure Python 3.12 Standard Library (Zero PIP Dependencies)

Tests:
1. MemoryFabric 4-tier storage & working memory bounded FIFO eviction
2. Memory admission provenance validation (rejecting ungrounded memories)
3. Memory semantic conflict detection (forbidding silent contradiction overwrite)
4. Ordered memory retrieval with temporal decay & auditable MemoryReceipts
5. FailureAttribution root cause disentanglement & skill penalty isolation
6. CognitiveGovernor infinite loop & repetitive thrashing detection
7. CognitiveGovernor autonomy ceiling enforcement (A0 to A5)
8. MemoryFabric atomic snapshot persistence & restore
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.memory import (
    MemoryFabric,
    MemoryItem,
    MemoryTier,
    MemoryStatus,
    MemoryReceipt,
    MemoryAdmissionResult
)
from tooling.agentic.failure_attribution import (
    FailureAttributionEngine,
    AttributionDiagnosis
)
from tooling.agentic.cognitive_governor import (
    CognitiveGovernor,
    AutonomyLevel,
    CognitiveReceipt
)
from tooling.agentic.models import (
    TaskNode,
    TaskStatus,
    RiskLevel,
    ExecutionAttempt,
    FailureAttribution
)


class TestAgenticM5MemoryGovernor(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name).resolve()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_memory_fabric_4_tiers_and_capacity(self):
        """Test 1: MemoryFabric supports 4 tiers and bounds working memory via FIFO eviction."""
        fabric = MemoryFabric(working_capacity=3, storage_dir=self.tmp_path)

        # Populate working memory beyond capacity of 3
        for i in range(5):
            res = fabric.admit(MemoryItem(
                memory_id=f"work-{i}",
                tier=MemoryTier.WORKING,
                key=f"scratch_{i}",
                content=f"Draft computation {i}",
                provenance="mission:msn-01"
            ))
            self.assertTrue(res.admitted)

        counts = fabric.get_tier_counts()
        self.assertEqual(counts["working"], 3)
        # Oldest items (scratch_0, scratch_1) must be evicted
        self.assertNotIn("scratch_0", fabric._working)
        self.assertNotIn("scratch_1", fabric._working)
        self.assertIn("scratch_4", fabric._working)

        # Populate other tiers
        fabric.admit(MemoryItem(
            memory_id="ep-1",
            tier=MemoryTier.EPISODIC,
            key="task_01_result",
            content="Task verified with zero errors",
            provenance="mission:msn-01"
        ))
        fabric.admit(MemoryItem(
            memory_id="sem-1",
            tier=MemoryTier.SEMANTIC,
            key="sys_architecture",
            content="System operates in pure Python 3.12 standard library",
            provenance="manifest:core"
        ))
        fabric.admit(MemoryItem(
            memory_id="proc-1",
            tier=MemoryTier.PROCEDURAL,
            key="patch_repair_recipe",
            content="Check py_compile before executing functional test",
            provenance="playbook:swe"
        ))

        counts = fabric.get_tier_counts()
        self.assertEqual(counts["episodic"], 1)
        self.assertEqual(counts["semantic"], 1)
        self.assertEqual(counts["procedural"], 1)
        self.assertEqual(counts["total"], 6)

    def test_memory_admission_provenance_validation(self):
        """Test 2: Memory admission gate rejects items lacking explicit provenance."""
        fabric = MemoryFabric(storage_dir=self.tmp_path)

        # Empty provenance must be rejected
        unprovenanced = MemoryItem(
            memory_id="mem-bad",
            tier=MemoryTier.SEMANTIC,
            key="untrusted_fact",
            content="Hallucinated information",
            provenance=""
        )
        res = fabric.admit(unprovenanced)
        self.assertFalse(res.admitted)
        self.assertIn("REJECTED", res.reason)

        # Valid provenance must be admitted
        provenanced = MemoryItem(
            memory_id="mem-good",
            tier=MemoryTier.SEMANTIC,
            key="trusted_fact",
            content="Verified baseline information",
            provenance="operator:admin"
        )
        res_good = fabric.admit(provenanced)
        self.assertTrue(res_good.admitted)

    def test_memory_conflict_detection(self):
        """Test 3: MemoryFabric flags direct semantic contradictions instead of silently overwriting."""
        fabric = MemoryFabric(storage_dir=self.tmp_path)

        # Item 1: Auth is mandatory
        item1 = MemoryItem(
            memory_id="mem-auth-01",
            tier=MemoryTier.SEMANTIC,
            key="policy_strict_mode",
            content="always allow strict policy enforcement: true",
            provenance="policy:v1"
        )
        res1 = fabric.admit(item1)
        self.assertTrue(res1.admitted)
        self.assertEqual(res1.status, MemoryStatus.ACTIVE)

        # Item 2: Contradictory policy rule
        item2 = MemoryItem(
            memory_id="mem-auth-02",
            tier=MemoryTier.SEMANTIC,
            key="policy_strict_mode",
            content="never allow strict policy enforcement: false",
            provenance="policy:v2"
        )
        res2 = fabric.admit(item2)
        self.assertTrue(res2.admitted)
        self.assertEqual(res2.status, MemoryStatus.CONFLICT_DETECTED)
        self.assertIn(item1.memory_id, res2.conflicts_detected)

        # Verify search automatically excludes contradictory items
        results, receipt = fabric.query("policy enforcement", tiers=[MemoryTier.SEMANTIC])
        self.assertEqual(len(results), 0)
        self.assertEqual(len(receipt.excluded_conflicts), 1)
        self.assertEqual(receipt.excluded_conflicts[0]["memory_id"], "mem-auth-02")

    def test_memory_ordered_retrieval_and_receipt(self):
        """Test 4: Ordered memory retrieval ranks by composite score and emits a complete MemoryReceipt."""
        fabric = MemoryFabric(storage_dir=self.tmp_path)

        fabric.admit(MemoryItem(
            memory_id="m1",
            tier=MemoryTier.SEMANTIC,
            key="quantum_encryption_spec",
            content="Quantum cryptographic algorithms require lattice-based mathematics",
            provenance="manual:rfc",
            tags=["crypto", "quantum"],
            confidence=0.95
        ))
        fabric.admit(MemoryItem(
            memory_id="m2",
            tier=MemoryTier.SEMANTIC,
            key="standard_rsa_spec",
            content="RSA uses prime factorization algorithms",
            provenance="manual:rfc",
            tags=["crypto", "rsa"],
            confidence=0.80
        ))

        results, receipt = fabric.query("quantum cryptographic algorithms", min_confidence=0.70)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].memory_id, "m1")
        self.assertIsNotNone(receipt.receipt_id)
        self.assertIn("m1", receipt.decay_scores)
        self.assertGreater(receipt.total_tokens_estimated, 0)

    def test_failure_attribution_penalizable_isolation(self):
        """Test 5: FailureAttributionEngine disentangles causes and isolates skill penalties."""
        engine = FailureAttributionEngine()
        task = TaskNode(task_id="tsk-01", title="Execute task")

        # Case A: Policy denial -> POLICY (NOT penalizable for skill)
        task.execution_result = {"denied": True, "reason": "Scope violation"}
        diag_policy = engine.diagnose_failure(task=task)
        self.assertEqual(diag_policy.attributed_cause, FailureAttribution.POLICY)
        self.assertFalse(diag_policy.is_skill_penalizable)
        self.assertFalse(engine.is_penalizable(diag_policy.attributed_cause))

        # Case B: Concurrency error -> ENVIRONMENT (NOT penalizable for skill)
        task.execution_result = {"denied": False}
        diag_env = engine.diagnose_failure(task=task, error_log="ConcurrencyConflictError: expected sha256 mismatch")
        self.assertEqual(diag_env.attributed_cause, FailureAttribution.ENVIRONMENT)
        self.assertFalse(diag_env.is_skill_penalizable)

        # Case C: Agent parameter error -> AGENT (NOT penalizable for skill)
        diag_agent = engine.diagnose_failure(task=task, error_log="TypeError: missing required positional argument 'path'")
        # Note: missing required positional argument is attributed to AGENT
        self.assertEqual(diag_agent.attributed_cause, FailureAttribution.AGENT)
        self.assertFalse(diag_agent.is_skill_penalizable)

        # Case D: Internal code bug in skill -> SKILL (PENALIZABLE)
        diag_skill = engine.diagnose_failure(task=task, error_log="ZeroDivisionError: division by zero in skill computation")
        self.assertEqual(diag_skill.attributed_cause, FailureAttribution.SKILL)
        self.assertTrue(diag_skill.is_skill_penalizable)
        self.assertTrue(engine.is_penalizable(diag_skill.attributed_cause))

    def test_cognitive_governor_infinite_loop_detection(self):
        """Test 6: CognitiveGovernor detects repeated actions and triggers HALT."""
        governor = CognitiveGovernor(max_consecutive_repeats=3)

        # Step 1 & 2: Identical repeated action
        r1 = governor.evaluate_step(action_signature="read_file:config/settings.json")
        self.assertFalse(r1.loop_detected)
        self.assertFalse(r1.halt_triggered)
        self.assertEqual(r1.governor_decision, "PERMIT")

        r2 = governor.evaluate_step(action_signature="read_file:config/settings.json")
        self.assertFalse(r2.loop_detected)
        self.assertFalse(r2.halt_triggered)

        # Step 3: Repeated 3rd time -> Trigger HALT
        r3 = governor.evaluate_step(action_signature="read_file:config/settings.json")
        self.assertTrue(r3.loop_detected)
        self.assertTrue(r3.halt_triggered)
        self.assertEqual(r3.governor_decision, "HALT")
        self.assertIn("INFINITE_LOOP_DETECTED", r3.reason)

    def test_cognitive_governor_autonomy_ceiling_enforcement(self):
        """Test 7: CognitiveGovernor enforces autonomy ceiling and blocks escalating actions."""
        # Governor capped at A2 (Read-Only)
        governor = CognitiveGovernor(autonomy_ceiling=AutonomyLevel.A2_READ_ONLY)

        # Permitted: R0 read-only
        r_read = governor.evaluate_step(action_signature="read_file:data.txt", requested_risk=RiskLevel.R0_READ_ONLY)
        self.assertFalse(r_read.halt_triggered)
        self.assertEqual(r_read.governor_decision, "PERMIT")

        # Blocked: R1 local write requires A3 (exceeds A2 ceiling)
        r_write = governor.evaluate_step(action_signature="write_file:data.txt", requested_risk=RiskLevel.R1_LOCAL_WRITE)
        self.assertTrue(r_write.halt_triggered)
        self.assertEqual(r_write.governor_decision, "HALT")
        self.assertIn("AUTONOMY_CEILING_BREACHED", r_write.reason)

    def test_memory_fabric_snapshot_atomic_persistence(self):
        """Test 8: MemoryFabric saves and loads complete snapshot atomically."""
        fabric = MemoryFabric(storage_dir=self.tmp_path)

        fabric.admit(MemoryItem(
            memory_id="work-snap",
            tier=MemoryTier.WORKING,
            key="current_thought",
            content="Evaluating invariant",
            provenance="task:1"
        ))
        fabric.admit(MemoryItem(
            memory_id="sem-snap",
            tier=MemoryTier.SEMANTIC,
            key="core_rule",
            content="Always verify before declaring success",
            provenance="policy:master"
        ))

        snapshot_path = fabric.save_snapshot("test_snapshot.json")
        self.assertTrue(snapshot_path.exists())

        # Create fresh instance and restore
        fresh_fabric = MemoryFabric(storage_dir=self.tmp_path)
        loaded = fresh_fabric.load_snapshot("test_snapshot.json")
        self.assertTrue(loaded)

        counts = fresh_fabric.get_tier_counts()
        self.assertEqual(counts["working"], 1)
        self.assertEqual(counts["semantic"], 1)
        self.assertEqual(fresh_fabric._semantic["core_rule"].content, "Always verify before declaring success")


if __name__ == "__main__":
    unittest.main()
