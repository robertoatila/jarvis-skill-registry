"""
test_agentic_m2_cognitive_execution.py
Milestone 2 (M2) — Bounded Local Cognitive Execution (Phases 12–16)
Validates:
1. LocalAction adapter contract & schema validation (bounds, traversal protection, protected paths)
2. LocalActionAdapter execution (atomic write, read, concurrency protection via expected_before_sha256)
3. ConcurrencyConflictError handling
4. Runtime task.action execution vs independent verification_requirements
5. Independent multi-dimensional state separation (ExecutionState.FINISHED != VerificationState.VERIFIED)
6. Progressive Disclosure audit receipts (DisclosureReceipt) across L0, L1, L2
7. Deterministic Agent Resolution decision receipts (ProfileDecisionReceipt)
8. Strict scope confinement in CompositeSkill DAG expansion
"""

from __future__ import annotations
import os
import sys
import json
import uuid
import shutil
import tempfile
import unittest
import hashlib
from pathlib import Path

from tooling.agentic.adapters.local import (
    LocalAction,
    LocalActionAdapter,
    LocalActionResult,
    LocalAdapterType,
    ConcurrencyConflictError,
    LocalActionError,
    MAX_PAYLOAD_BYTES,
    PROTECTED_PATHS
)
from tooling.agentic.models import (
    Mission,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
    VerificationStatus,
    ExecutionAttempt,
    ExecutionState,
    VerificationState,
    RecoveryState,
    MissionOutcome,
    FailureClass,
    FailureAttribution,
    SideEffectRecord,
    SideEffectType,
    RiskLevel
)
from tooling.agentic.progressive_disclosure import (
    ProgressiveDisclosureEngine,
    DisclosureReceipt,
    SkillCatalogEntry,
    SkillManifestEntry,
    SkillExecutionPackage
)
from tooling.agentic.profiles import (
    AgentProfileRegistry,
    AgentProfile,
    ProfileDecisionReceipt
)
from tooling.agentic.composite import (
    CompositeSkill,
    SubSkillReference
)
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.runtime import JarvisAgenticRuntime
from tooling.agentic.config import JarvisRuntimeConfig


class TestM2CognitiveExecution(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_m2_test_")
        self.workspace = Path(self.temp_dir).resolve()
        # Setup basic workspace structure
        (self.workspace / "skills").mkdir(parents=True, exist_ok=True)
        (self.workspace / "state" / "authoritative").mkdir(parents=True, exist_ok=True)
        (self.workspace / "reports").mkdir(parents=True, exist_ok=True)
        (self.workspace / "config").mkdir(parents=True, exist_ok=True)

        self.adapter = LocalActionAdapter(workspace_root=self.workspace)

    def tearDown(self) -> None:
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # Test 1: LocalAction Schema & Contract Validation
    # -------------------------------------------------------------------------
    def test_local_action_schema_validation(self) -> None:
        # Valid read action
        action_read = LocalAction(adapter="local.read_file", path="reports/summary.md")
        self.assertEqual(action_read.adapter, LocalAdapterType.READ_FILE)
        self.assertEqual(action_read.path, "reports/summary.md")

        # Valid write action
        action_write = LocalAction(adapter="local.write_text", path="reports/out.txt", content="Hello World")
        self.assertEqual(action_write.adapter, LocalAdapterType.WRITE_TEXT)
        self.assertEqual(action_write.content, "Hello World")

        # Invalid schema version
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.read_file", path="test.txt", schema_version="2.0.0")

        # Unsupported adapter
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="remote.fetch_url", path="test.txt")

        # Absolute paths forbidden
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.read_file", path="C:/Windows/System32/cmd.exe")
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.read_file", path="/etc/passwd")

        # Directory traversal forbidden
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.read_file", path="../secrets.json")
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.read_file", path="reports/../../root.txt")

        # Payload size limit strictly enforced (> 1 MiB)
        large_content = "x" * (MAX_PAYLOAD_BYTES + 1)
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.write_text", path="large.txt", content=large_content)

        # Content forbidden for read_file
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.read_file", path="test.txt", content="not allowed")

        # expected_before_sha256 forbidden for read_file
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.read_file", path="test.txt", expected_before_sha256="a" * 64)

        # Content required for write_text
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.write_text", path="test.txt", content=None)

        # Invalid expected_before_sha256 format
        with self.assertRaises(LocalActionError):
            LocalAction(adapter="local.write_text", path="test.txt", content="data", expected_before_sha256="not-a-hash")

        # Roundtrip to_dict and from_dict
        d = action_write.to_dict()
        action_reconstructed = LocalAction.from_dict(d)
        self.assertEqual(action_write, action_reconstructed)

    # -------------------------------------------------------------------------
    # Test 2: LocalActionAdapter File Operations & Protection
    # -------------------------------------------------------------------------
    def test_local_action_adapter_file_operations(self) -> None:
        # Write file
        content = "Sovereign Cognitive Execution Payload\nLine 2"
        action = LocalAction(adapter="local.write_text", path="sub/dir/test.txt", content=content)
        res = self.adapter.execute(action)
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.bytes_transferred, len(content.encode("utf-8")))
        self.assertEqual(res.sha256, hashlib.sha256(content.encode("utf-8")).hexdigest())

        # Verify on disk
        target_path = self.workspace / "sub" / "dir" / "test.txt"
        self.assertTrue(target_path.exists())
        self.assertEqual(target_path.read_text(encoding="utf-8"), content)

        # Read file
        read_action = LocalAction(adapter="local.read_file", path="sub/dir/test.txt")
        read_res = self.adapter.execute(read_action)
        self.assertTrue(read_res.success)
        self.assertEqual(read_res.exit_code, 0)
        self.assertEqual(read_res.content, content)
        self.assertEqual(read_res.sha256, res.sha256)

        # Non-existent file read
        read_missing = LocalAction(adapter="local.read_file", path="missing.txt")
        missing_res = self.adapter.execute(read_missing)
        self.assertFalse(missing_res.success)
        self.assertEqual(missing_res.exit_code, 1)
        self.assertIn("File not found", missing_res.error_message)

        # Protected paths access strictly prohibited
        for prot in (".git", ".gitignore", "config/api_keys.json", "state/authoritative"):
            with self.assertRaises(LocalActionError):
                self.adapter.resolve_confined_path(prot)
            with self.assertRaises(LocalActionError):
                self.adapter.resolve_confined_path(f"{prot}/inner.txt")

    # -------------------------------------------------------------------------
    # Test 3: Concurrency Protection via expected_before_sha256
    # -------------------------------------------------------------------------
    def test_concurrency_conflict_protection(self) -> None:
        initial_content = "Baseline content v1"
        initial_hash = hashlib.sha256(initial_content.encode("utf-8")).hexdigest()

        # Create initial file
        self.adapter.execute(LocalAction(adapter="local.write_text", path="shared/config.json", content=initial_content))

        # Successful optimistic update with correct expected hash
        update_action = LocalAction(
            adapter="local.write_text",
            path="shared/config.json",
            content="Updated content v2",
            expected_before_sha256=initial_hash
        )
        res = self.adapter.execute(update_action)
        self.assertTrue(res.success)

        # Conflicting update with stale hash raises ConcurrencyConflictError
        stale_action = LocalAction(
            adapter="local.write_text",
            path="shared/config.json",
            content="Conflicting content v3",
            expected_before_sha256=initial_hash  # Stale! Hash has changed to v2
        )
        with self.assertRaises(ConcurrencyConflictError):
            self.adapter.execute(stale_action)

        # Missing file when expected_before_sha256 specified
        missing_action = LocalAction(
            adapter="local.write_text",
            path="shared/does_not_exist.json",
            content="Some data",
            expected_before_sha256=initial_hash
        )
        with self.assertRaises(ConcurrencyConflictError):
            self.adapter.execute(missing_action)

    # -------------------------------------------------------------------------
    # Test 4: Runtime Execution with Task.Action
    # -------------------------------------------------------------------------
    def test_runtime_local_action_execution(self) -> None:
        cfg = JarvisRuntimeConfig(registry_root=self.workspace)
        runtime = JarvisAgenticRuntime(config=cfg)

        task_id = "task-write-artifact"
        action_dict = {
            "schema_version": "1.0.0",
            "adapter": "local.write_text",
            "path": "reports/phase-16-evidence.txt",
            "content": "Authoritative evidence content generated during Phase 16 execution."
        }

        # Create task with action
        node = TaskNode(
            task_id=task_id,
            title="Generate Phase 16 Evidence",
            description="Writes evidence report via LocalAction adapter",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["comprehensive-code-review"],
            write_scopes=["reports/phase-16-evidence.txt"],
            action=action_dict,
            risk_level=RiskLevel.R1_LOCAL_WRITE,
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target="reports/phase-16-evidence.txt"
                ),
                VerificationRequirement(
                    check_type=VerificationType.ARTIFACT_HASH_MATCHES,
                    target="reports/phase-16-evidence.txt",
                    expected=hashlib.sha256(action_dict["content"].encode("utf-8")).hexdigest()
                )
            ]
        )

        dag = ExecutionDAG()
        dag.add_node(node)
        mission = Mission(
            mission_id=f"msn-{uuid.uuid4().hex[:8]}",
            goal="Test bounded cognitive local execution",
            dag=dag
        )
        runtime.state_store.save_mission(mission)

        res = runtime.resume_mission(mission.mission_id)
        self.assertEqual(res["status"], "SUCCESS")

        # Load persisted mission
        saved = runtime.state_store.load_mission(mission.mission_id)
        saved_task = saved.dag.nodes[task_id]
        self.assertEqual(saved_task.status, TaskStatus.VERIFIED)
        self.assertIsNotNone(saved_task.execution_result)
        self.assertEqual(saved_task.execution_result.get("producer"), "adapter:local.write_text")
        self.assertEqual(saved_task.execution_result.get("exit_code"), 0)

        # Verify attempt recorded
        self.assertGreaterEqual(len(saved_task.attempts), 1)
        last_att = saved_task.attempts[-1]
        self.assertEqual(last_att.execution_state, ExecutionState.FINISHED)
        self.assertEqual(last_att.verification_state, VerificationState.VERIFIED)
        self.assertEqual(last_att.outcome, MissionOutcome.SUCCEEDED)
        self.assertIn("local.write_text", last_att.input_reference)

        # Verify physical file exists and contains content
        target_file = self.workspace / "reports" / "phase-16-evidence.txt"
        self.assertTrue(target_file.exists())
        self.assertIn("Authoritative evidence content", target_file.read_text(encoding="utf-8"))

    # -------------------------------------------------------------------------
    # Test 5: Separation of Execution from Independent Verification
    # -------------------------------------------------------------------------
    def test_independent_state_axes_action_vs_verification(self) -> None:
        """
        Critical Multi-Dimensional Invariant:
        LocalAction executes successfully (ExecutionState.FINISHED),
        but an independent verification check rejects it (VerificationState.REJECTED).
        Result must be:
        ExecutionState.FINISHED != VerificationState.VERIFIED
        MissionOutcome == FAILED
        FailureClass == VALIDATION
        FailureAttribution == AGENT
        """
        cfg = JarvisRuntimeConfig(registry_root=self.workspace)
        runtime = JarvisAgenticRuntime(config=cfg)

        task_id = "task-failing-verification"
        action_dict = {
            "schema_version": "1.0.0",
            "adapter": "local.write_text",
            "path": "reports/partial.txt",
            "content": "This content is written correctly by the adapter."
        }

        # Requirement expects something that does NOT exist in the file
        node = TaskNode(
            task_id=task_id,
            title="Task with Failing Verification",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=["comprehensive-code-review"],
            write_scopes=["reports/partial.txt"],
            action=action_dict,
            risk_level=RiskLevel.R1_LOCAL_WRITE,
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.ARTIFACT_HASH_MATCHES,
                    target="reports/partial.txt",
                    expected="0" * 64
                )
            ]
        )

        dag = ExecutionDAG()
        dag.add_node(node)
        mission = Mission(
            mission_id=f"msn-{uuid.uuid4().hex[:8]}",
            goal="Verify multi-dimensional state separation",
            dag=dag
        )
        runtime.state_store.save_mission(mission)

        res = runtime.resume_mission(mission.mission_id)
        self.assertEqual(res["status"], "FAILED")

        saved = runtime.state_store.load_mission(mission.mission_id)
        saved_task = saved.dag.nodes[task_id]

        # File was actually written (action executed successfully)
        self.assertEqual(saved_task.execution_result.get("exit_code"), 0)

        # But verification was rejected
        self.assertGreaterEqual(len(saved_task.attempts), 1)
        att = saved_task.attempts[-1]
        self.assertEqual(att.execution_state, ExecutionState.FINISHED)
        self.assertEqual(att.verification_state, VerificationState.REJECTED)
        self.assertEqual(att.outcome, MissionOutcome.FAILED)
        self.assertEqual(att.failure_class, FailureClass.VALIDATION)
        self.assertEqual(att.failure_attribution, FailureAttribution.AGENT)

    # -------------------------------------------------------------------------
    # Test 6: Progressive Disclosure Receipts (DisclosureReceipt)
    # -------------------------------------------------------------------------
    def test_progressive_disclosure_receipt(self) -> None:
        # Create a mock skill directory with SKILL.md
        skill_dir = self.workspace / "skills" / "sample-audit"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: sample-audit\ndescription: Sample audit skill for tests\ntags: [audit, test]\n---\n# Full Instructions\nStep 1: Inspect code.\nStep 2: Generate report.\n",
            encoding="utf-8"
        )
        (skill_dir / "dependencies.json").write_text(
            json.dumps({"dependencies": ["systematic-debugging"]}),
            encoding="utf-8"
        )

        pde = ProgressiveDisclosureEngine(skills_dir=self.workspace / "skills")

        # Level 0: Catalog
        l0_entry, rcp_0 = pde.load_with_receipt("sample-audit", level=0, mission_id="msn-001", task_id="tsk-001")
        self.assertIsInstance(l0_entry, SkillCatalogEntry)
        self.assertEqual(rcp_0.disclosure_level, 0)
        self.assertEqual(rcp_0.skill_id, "sample-audit")
        self.assertTrue(len(rcp_0.content_hash) == 64)
        self.assertGreater(rcp_0.estimated_tokens, 0)
        self.assertEqual(rcp_0.mission_id, "msn-001")

        # Level 1: Manifest
        l1_entry, rcp_1 = pde.load_with_receipt("sample-audit", level=1, mission_id="msn-001", task_id="tsk-001")
        self.assertIsInstance(l1_entry, SkillManifestEntry)
        self.assertEqual(rcp_1.disclosure_level, 1)
        self.assertIn("systematic-debugging", l1_entry.dependencies)

        # Level 2: Execution
        l2_entry, rcp_2 = pde.load_with_receipt("sample-audit", level=2, mission_id="msn-001", task_id="tsk-001")
        self.assertIsInstance(l2_entry, SkillExecutionPackage)
        self.assertEqual(rcp_2.disclosure_level, 2)
        self.assertIn("Step 1: Inspect code", l2_entry.instructions)

        # Progressive Token Economy Invariant:
        # L0 tokens < L1 tokens < L2 tokens
        self.assertLess(rcp_0.estimated_tokens, rcp_1.estimated_tokens)
        self.assertLess(rcp_1.estimated_tokens, rcp_2.estimated_tokens)

        # Receipts list contains all 3
        self.assertEqual(len(pde.receipts), 3)

        # Roundtrip receipt serialization
        d = rcp_2.to_dict()
        rcp_recon = DisclosureReceipt.from_dict(d)
        self.assertEqual(rcp_2, rcp_recon)

    # -------------------------------------------------------------------------
    # Test 7: Profile Decision Receipts (ProfileDecisionReceipt)
    # -------------------------------------------------------------------------
    def test_profile_decision_receipt(self) -> None:
        reg = AgentProfileRegistry()
        prof, receipt = reg.resolve_agent_with_receipt(
            required_capabilities=["security-audit", "code-review"],
            task_id="tsk-sec-01"
        )
        self.assertIsNotNone(prof)
        self.assertEqual(prof.agent_id, "Quantum-AuditAgent")
        self.assertEqual(receipt.task_id, "tsk-sec-01")
        self.assertEqual(receipt.selected_agent_id, "Quantum-AuditAgent")
        self.assertGreater(receipt.score, 0.0)
        self.assertIn("Selected best matching profile", receipt.selection_reason)
        self.assertGreater(len(receipt.candidates_evaluated), 0)

        # Serialization
        rd = receipt.to_dict()
        r_recon = ProfileDecisionReceipt.from_dict(rd)
        self.assertEqual(receipt, r_recon)

        # Unmatched requirements receipt
        no_prof, no_rcp = reg.resolve_agent_with_receipt(
            required_capabilities=["impossible-quantum-super-skill-xyz"],
            task_id="tsk-impossible"
        )
        self.assertIsNone(no_prof)
        self.assertIsNone(no_rcp.selected_agent_id)
        self.assertEqual(no_rcp.score, 0.0)
        self.assertIn("No agent profile matched", no_rcp.selection_reason)

    # -------------------------------------------------------------------------
    # Test 8: Composite Skill Strict Scope Confinement
    # -------------------------------------------------------------------------
    def test_composite_skill_scope_confinement(self) -> None:
        # Valid relative scopes
        sub_valid = SubSkillReference(
            skill_id="security-research-audit",
            alias="audit_task",
            read_scopes=["src/models.py"],
            write_scopes=["reports/audit.json"]
        )
        self.assertEqual(sub_valid.read_scopes, ["src/models.py"])

        # Path traversal prohibited in read_scopes
        with self.assertRaises(ValueError):
            SubSkillReference(
                skill_id="security-research-audit",
                read_scopes=["../etc/passwd"]
            )

        # Absolute paths prohibited in write_scopes
        with self.assertRaises(ValueError):
            SubSkillReference(
                skill_id="security-research-audit",
                write_scopes=["C:/Windows/temp.txt"]
            )

        # Traversal in write_scopes
        with self.assertRaises(ValueError):
            SubSkillReference(
                skill_id="security-research-audit",
                write_scopes=["reports/../../secrets.json"]
            )

        # Composite skill expansion with valid sub-skills
        comp = CompositeSkill(
            composite_id="sec-audit-pipeline",
            name="SecurityAuditPipeline",
            sub_skills=[
                SubSkillReference("security-research-audit", alias="audit", write_scopes=["reports/audit.json"]),
                SubSkillReference("comprehensive-code-review", alias="review", read_scopes=["reports/audit.json"])
            ],
            dependency_graph=[("audit", "review")]
        )
        dag = comp.expand_to_dag(task_prefix="p16")
        self.assertIn("p16_audit", dag.nodes)
        self.assertIn("p16_review", dag.nodes)
        self.assertEqual(dag.nodes["p16_audit"].write_scopes, ["reports/audit.json"])
        self.assertEqual(dag.nodes["p16_review"].read_scopes, ["reports/audit.json"])


if __name__ == "__main__":
    unittest.main()
