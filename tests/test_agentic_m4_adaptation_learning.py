"""
test_agentic_m4_adaptation_learning.py // Milestone 4 Comprehensive Test Suite
Pure Python 3.12 Standard Library (Zero PIP Dependencies)

Tests:
1. DecisionReceipt immutability & outcome attachment without estimate mutation
2. ToolRouter hard capability filtering & fail-closed BLOCKED receipts
3. ToolRouter deterministic risk and cost trade-off ranking
4. ModelRouter privacy-first enforcement on sensitive scopes
5. ModelRouter context window capacity & budget headroom escalation
6. AutonomousMissionPlanner replan_affected_region preserving verified upstream
7. Skill and Agent profile resolution with explainable DecisionReceipts
8. SoftwareEngineeringOrchestrator atomic patch & separate AST vs functional verification
"""

import unittest
import tempfile
from pathlib import Path

from tooling.agentic.decision_receipt import DecisionReceipt, DecisionType
from tooling.agentic.tool_router import ToolRouter, ToolCandidate
from tooling.agentic.model_router import ModelRouter, ModelCandidate
from tooling.agentic.planner_resolver import AutonomousMissionPlanner, AutonomousSkillResolver
from tooling.agentic.profiles import AgentProfileRegistry, AgentProfile
from tooling.agentic.swe_orchestrator import SoftwareEngineeringOrchestrator
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


class TestAgenticM4AdaptationLearning(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name).resolve()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_decision_receipt_immutability_and_outcome(self):
        """Test 1: DecisionReceipt stores immutable estimates and allows attaching actual outcome."""
        receipt = DecisionReceipt(
            decision_id="dec-test-01",
            decision_type=DecisionType.TOOL_ROUTING,
            task_id="task-01",
            candidates=["tool-a", "tool-b"],
            rejected_candidates={"tool-b": "Missing capability"},
            scores={"tool-a": 95.0},
            selected_candidate="tool-a",
            selection_reason="Highest utility and zero risk",
            confidence=0.92,
            estimated_cost_usd=0.015,
            estimated_tokens=350,
            estimated_risk="R0"
        )

        receipt_dict = receipt.to_dict()
        self.assertEqual(receipt_dict["decision_id"], "dec-test-01")
        self.assertEqual(receipt_dict["selected_candidate"], "tool-a")
        self.assertEqual(receipt_dict["estimated_cost_usd"], 0.015)
        self.assertIsNone(receipt_dict["actual_outcome"])

        # Attach actual outcome
        receipt.attach_actual_outcome(
            actual_cost_usd=0.012,
            actual_tokens=320,
            actual_outcome="SUCCESS"
        )

        # Verify estimates were NOT mutated
        self.assertEqual(receipt.estimated_cost_usd, 0.015)
        self.assertEqual(receipt.estimated_tokens, 350)
        self.assertEqual(receipt.confidence, 0.92)

        # Verify actual outcomes are recorded
        self.assertEqual(receipt.actual_cost_usd, 0.012)
        self.assertEqual(receipt.actual_tokens, 320)
        self.assertEqual(receipt.actual_outcome, "SUCCESS")
        self.assertIsNotNone(receipt.actual_attached_utc)

        # Deserialization test
        restored = DecisionReceipt.from_dict(receipt.to_dict())
        self.assertEqual(restored.decision_id, "dec-test-01")
        self.assertEqual(restored.actual_outcome, "SUCCESS")
        self.assertEqual(restored.estimated_cost_usd, 0.015)

    def test_tool_router_capability_filtering(self):
        """Test 2: ToolRouter rejects missing capabilities with an explicit BLOCKED decision."""
        router = ToolRouter()
        task = TaskNode(
            task_id="task-crypto",
            title="Attempt quantum break",
            required_skills=["quantum-cryptography-breaker"]
        )

        selected_tool, receipt = router.route_tool(task)
        self.assertIsNone(selected_tool)
        self.assertFalse(receipt.selected_candidate)
        self.assertIn("BLOCKED", receipt.selection_reason)
        self.assertEqual(receipt.confidence, 0.0)

        # Verify every default tool was rejected due to missing capability
        for tool in router.list_tools():
            self.assertIn(tool.tool_id, receipt.rejected_candidates)
            self.assertIn("quantum-cryptography-breaker", receipt.rejected_candidates[tool.tool_id])

    def test_tool_router_deterministic_ranking(self):
        """Test 3: ToolRouter scores candidates deterministically based on risk and cost trade-offs."""
        tools = [
            ToolCandidate(
                tool_id="tool.read_only",
                name="Read-Only Utility",
                capabilities=["code_edit"],
                risk_level=RiskLevel.R0_READ_ONLY,
                cost_per_invocation_usd=0.0
            ),
            ToolCandidate(
                tool_id="tool.costly_write",
                name="Costly Local Write",
                capabilities=["code_edit"],
                risk_level=RiskLevel.R1_LOCAL_WRITE,
                cost_per_invocation_usd=0.10
            ),
            ToolCandidate(
                tool_id="tool.repo_mutation",
                name="Repo Mutator",
                capabilities=["code_edit"],
                risk_level=RiskLevel.R2_REPO_MUTATION,
                cost_per_invocation_usd=0.0
            )
        ]
        router = ToolRouter(catalog=tools)
        task = TaskNode(
            task_id="task-edit",
            title="Edit code",
            required_skills=["code_edit"]
        )

        selected_tool, receipt = router.route_tool(task, risk_ceiling=RiskLevel.R2_REPO_MUTATION)
        self.assertIsNotNone(selected_tool)
        self.assertEqual(selected_tool.tool_id, "tool.read_only")
        self.assertEqual(receipt.selected_candidate, "tool.read_only")

        # R0 has score 100.0, R1 has 100 - 10 - (0.10 * 50) = 85.0, R2 has 100 - 20 = 80.0
        self.assertEqual(receipt.scores["tool.read_only"], 100.0)
        self.assertEqual(receipt.scores["tool.costly_write"], 85.0)
        self.assertEqual(receipt.scores["tool.repo_mutation"], 80.0)

    def test_model_router_privacy_enforcement(self):
        """Test 4: ModelRouter rejects cloud models when privacy is enforced or sensitive scopes present."""
        router = ModelRouter()

        # Task with sensitive scopes
        task = TaskNode(
            task_id="task-secret-audit",
            title="Audit Vault Keys",
            read_scopes=["config/keys/private_auth.env"]
        )

        selected_model, receipt = router.route_model(task)
        self.assertIsNotNone(selected_model)
        self.assertTrue(selected_model.is_local)
        self.assertEqual(selected_model.model_id, "sovereign-local-deepseek-8b")

        # Cloud models must be rejected for privacy
        for m_id in ["groq-llama-3.3-70b-versatile", "gemini-2.0-flash", "claude-3-7-sonnet"]:
            self.assertIn(m_id, receipt.rejected_candidates)
            self.assertIn("Cloud model rejected", receipt.rejected_candidates[m_id])

    def test_model_router_context_capacity_and_cost(self):
        """Test 5: ModelRouter respects context window bounds and cost headroom."""
        router = ModelRouter()
        task = TaskNode(
            task_id="task-large-repo",
            title="Analyze 500k token repository graph"
        )

        # Require 500,000 tokens (only Gemini 2.0 Flash has 1M window)
        selected_model, receipt = router.route_model(task, required_context_tokens=500_000)
        self.assertIsNotNone(selected_model)
        self.assertEqual(selected_model.model_id, "gemini-2.0-flash")
        self.assertIn("sovereign-local-deepseek-8b", receipt.rejected_candidates)
        self.assertIn("insufficient", receipt.rejected_candidates["sovereign-local-deepseek-8b"])

        # Test budget headroom constraint
        task_small = TaskNode(task_id="task-small", title="Quick reasoning")
        # Headroom $0.000001 (cheaper than Claude and Groq, local DeepSeek is free $0.0)
        selected_cheap, receipt_cheap = router.route_model(task_small, required_context_tokens=4000, budget_headroom_usd=0.000001)
        self.assertIsNotNone(selected_cheap)
        self.assertEqual(selected_cheap.model_id, "sovereign-local-deepseek-8b")
        self.assertIn("claude-3-7-sonnet", receipt_cheap.rejected_candidates)

    def test_planner_replan_affected_region(self):
        """Test 6: AutonomousMissionPlanner replans downstream region while preserving verified tasks."""
        planner = AutonomousMissionPlanner(registry_root=self.tmp_path)
        dag = ExecutionDAG()

        t1 = TaskNode(task_id="t1", title="Setup Environment", status=TaskStatus.VERIFIED)
        t2 = TaskNode(task_id="t2", title="Apply Patch", dependencies=["t1"], status=TaskStatus.FAILED)
        t3 = TaskNode(task_id="t3", title="Run Integration Tests", dependencies=["t2"], status=TaskStatus.PENDING)
        t4 = TaskNode(task_id="t4", title="Deploy Staging", dependencies=["t3"], status=TaskStatus.PENDING)

        dag.add_node(t1)
        dag.add_node(t2)
        dag.add_node(t3)
        dag.add_node(t4)

        mission = Mission(
            mission_id="msn-replan-test",
            goal="Continuous SWE Deployment",
            dag=dag,
            status=MissionStatus.RUNNING
        )

        replan_res = planner.replan_affected_region(
            mission=mission,
            invalidated_task_ids=["t2"],
            invalidation_reason="Syntax error detected in patch"
        )

        self.assertIsNotNone(replan_res)
        replan_receipt = replan_res["receipt"]
        self.assertEqual(replan_receipt["decision_type"], DecisionType.REPLANNING.value)
        self.assertIn("t2", replan_receipt["candidates"])
        self.assertIn("t3", replan_receipt["candidates"])
        self.assertIn("t4", replan_receipt["candidates"])
        self.assertIn("t1", replan_receipt["candidates"])

        # t1 remains VERIFIED
        self.assertEqual(mission.dag.nodes["t1"].status, TaskStatus.VERIFIED)
        # t2, t3, t4 are reset to READY
        self.assertEqual(mission.dag.nodes["t2"].status, TaskStatus.READY)
        self.assertEqual(mission.dag.nodes["t3"].status, TaskStatus.READY)
        self.assertEqual(mission.dag.nodes["t4"].status, TaskStatus.READY)

        # Verification that replan history is saved in mission metadata
        history = mission.metadata.get("replan_history", [])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["metadata"]["invalidation_reason"], "Syntax error detected in patch")

    def test_resolver_and_profile_decision_receipts(self):
        """Test 7: Skill and Agent profile resolvers generate explainable DecisionReceipts."""
        registry = AgentProfileRegistry()
        ag, receipt_ag = registry.resolve_agent_with_decision_receipt(
            required_capabilities=["security-audit"]
        )
        self.assertIsNotNone(ag)
        self.assertEqual(receipt_ag.decision_type, DecisionType.AGENT_SELECTION)
        self.assertEqual(receipt_ag.selected_candidate, ag.agent_id)
        self.assertGreater(receipt_ag.confidence, 0.5)

        resolver = AutonomousSkillResolver()
        rec, receipt_sk = resolver.resolve_with_decision_receipt(
            capability_request="python-pro"
        )
        self.assertIsNotNone(rec)
        self.assertEqual(receipt_sk.decision_type, DecisionType.SKILL_SELECTION)
        self.assertIn("python-pro", receipt_sk.selected_candidate or "")

    def test_swe_orchestrator_apply_and_verify_patch(self):
        """Test 8: SoftwareEngineeringOrchestrator performs atomic write and separates AST syntax from test execution."""
        swe = SoftwareEngineeringOrchestrator(registry_root=self.tmp_path)
        valid_code = "def compute_total(x: int, y: int) -> int:\n    return x + y\n"

        # Case A: Valid Python code
        res_valid = swe.apply_and_verify_patch(
            target_rel_path="pkg/math_utils.py",
            patch_content=valid_code
        )
        self.assertTrue(res_valid["action_executed"])
        self.assertTrue(res_valid["syntax_clean"])
        self.assertTrue(res_valid["overall_verified"])
        self.assertTrue((self.tmp_path / "pkg/math_utils.py").exists())
        self.assertEqual((self.tmp_path / "pkg/math_utils.py").read_text(encoding="utf-8"), valid_code)

        # Case B: Syntax error code
        bad_syntax_code = "def bad_function(x, y:\n    return x + y\n"
        res_bad = swe.apply_and_verify_patch(
            target_rel_path="pkg/bad_syntax.py",
            patch_content=bad_syntax_code
        )
        self.assertTrue(res_bad["action_executed"])
        self.assertFalse(res_bad["syntax_clean"])
        self.assertFalse(res_bad["overall_verified"])


if __name__ == "__main__":
    unittest.main()
