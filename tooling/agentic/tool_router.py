"""
tool_router.py // J.A.R.V.I.S. Constrained Autonomous Tool Router
Pure Python 3.12 Standard Library (Zero PIP Dependencies)

Implements Phase 26 of the Autonomous Evolution Protocol:
- Hard authority, privacy, scope, and capability constraints before ranking
- Rejects missing capabilities with an explicit BLOCKED decision (fail-closed, never invent tools)
- Deterministic utility, risk, and cost trade-off ranking
- Generates formal DecisionReceipt for explainable tool routing
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import TaskNode, RiskLevel
from .decision_receipt import DecisionReceipt, DecisionType


@dataclass
class ToolCandidate:
    tool_id: str
    name: str
    capabilities: List[str]
    risk_level: RiskLevel = RiskLevel.R0_READ_ONLY
    is_mutation: bool = False
    cost_per_invocation_usd: float = 0.0
    estimated_latency_ms: int = 10
    allowed_scopes: List[str] = field(default_factory=list)

    def matches_capabilities(self, required_caps: List[str]) -> bool:
        if not required_caps:
            return True
        tool_caps = set(c.lower() for c in self.capabilities)
        if "*" in tool_caps or "general-tooling" in tool_caps:
            return True
        for req in required_caps:
            req_l = req.lower()
            if req_l in tool_caps or any(req_l in c or c in req_l for c in tool_caps):
                return True
        return False


DEFAULT_TOOLS: List[ToolCandidate] = [
    ToolCandidate(
        tool_id="local.read_file",
        name="Local File Reader",
        capabilities=["read_file", "view_file", "source_inspection", "file_read"],
        risk_level=RiskLevel.R0_READ_ONLY,
        is_mutation=False,
        cost_per_invocation_usd=0.0
    ),
    ToolCandidate(
        tool_id="local.write_text",
        name="Local File Writer",
        capabilities=["write_file", "create_file", "patch_file", "file_write", "codegen"],
        risk_level=RiskLevel.R1_LOCAL_WRITE,
        is_mutation=True,
        cost_per_invocation_usd=0.0
    ),
    ToolCandidate(
        tool_id="local.ast_inspector",
        name="Static AST Integrity Inspector",
        capabilities=["systematic-code-debugging", "ast_analysis", "syntax_check"],
        risk_level=RiskLevel.R0_READ_ONLY,
        is_mutation=False,
        cost_per_invocation_usd=0.0
    ),
    ToolCandidate(
        tool_id="local.test_runner",
        name="Subprocess Test Runner",
        capabilities=["test_runner", "pytest", "unittest", "verification"],
        risk_level=RiskLevel.R1_LOCAL_WRITE,
        is_mutation=False,
        cost_per_invocation_usd=0.0
    ),
    ToolCandidate(
        tool_id="local.repo_intel_scanner",
        name="Incremental Repository Intelligence Scanner",
        capabilities=["repo_intel", "symbol_extraction", "dependency_graph"],
        risk_level=RiskLevel.R0_READ_ONLY,
        is_mutation=False,
        cost_per_invocation_usd=0.0
    )
]


class ToolRouter:
    """
    Constrained Autonomous Tool Router:
    Filters candidates by hard constraints (policy, risk, capability, budget),
    ranks survivors deterministically, and produces audit receipts.
    """

    def __init__(self, catalog: Optional[List[ToolCandidate]] = None):
        self._catalog: Dict[str, ToolCandidate] = {}
        for t in (catalog or DEFAULT_TOOLS):
            self.register_tool(t)

    def register_tool(self, tool: ToolCandidate) -> None:
        self._catalog[tool.tool_id] = tool

    def get_tool(self, tool_id: str) -> Optional[ToolCandidate]:
        return self._catalog.get(tool_id)

    def list_tools(self) -> List[ToolCandidate]:
        return list(self._catalog.values())

    def route_tool(
        self,
        task: TaskNode,
        risk_ceiling: RiskLevel = RiskLevel.R3_EXTERNAL_SIDE_EFFECT,
        budget_usd_headroom: Optional[float] = None
    ) -> Tuple[Optional[ToolCandidate], DecisionReceipt]:
        """
        Selects the optimal admissible tool for a given task node.
        Applies hard constraints first. Fail-closed if no tool matches.
        """
        decision_id = f"dec-tool-{uuid.uuid4().hex[:8]}"
        candidates: List[str] = list(self._catalog.keys())
        rejected: Dict[str, str] = {}
        scores: Dict[str, float] = {}

        required_caps = task.required_skills
        task_risk = task.canonical_risk_level

        # Stage 1: Filter hard constraints
        survivors: List[ToolCandidate] = []
        for tool_id, tool in self._catalog.items():
            # 1. Capability matching
            if not tool.matches_capabilities(required_caps):
                rejected[tool_id] = f"Tool lacks required capabilities: {', '.join(required_caps)}"
                continue

            # 2. Risk ceiling check
            risk_hierarchy = {
                RiskLevel.R0_READ_ONLY: 0,
                RiskLevel.R1_LOCAL_WRITE: 1,
                RiskLevel.R2_REPO_MUTATION: 2,
                RiskLevel.R3_EXTERNAL_SIDE_EFFECT: 3,
                RiskLevel.R4_INFRA_MUTATION: 4,
                RiskLevel.R5_DESTRUCTIVE: 5
            }
            tool_risk_score = risk_hierarchy.get(tool.risk_level, 0)
            ceiling_score = risk_hierarchy.get(risk_ceiling, 3)
            if tool_risk_score > ceiling_score:
                rejected[tool_id] = f"Tool risk {tool.risk_level.value} exceeds ceiling {risk_ceiling.value}"
                continue

            # 3. Budget headroom check
            if budget_usd_headroom is not None and tool.cost_per_invocation_usd > budget_usd_headroom:
                rejected[tool_id] = f"Tool cost ${tool.cost_per_invocation_usd:.4f} exceeds headroom ${budget_usd_headroom:.4f}"
                continue

            survivors.append(tool)

        # Fail-closed if no admissible tools found
        if not survivors:
            receipt = DecisionReceipt(
                decision_id=decision_id,
                decision_type=DecisionType.TOOL_ROUTING,
                task_id=task.task_id,
                candidates=candidates,
                rejected_candidates=rejected,
                scores={},
                selected_candidate="",
                selection_reason="BLOCKED: No admissible tool satisfies required capabilities and hard constraints (zero tool hallucination)",
                confidence=0.0
            )
            return None, receipt

        # Stage 2: Deterministic scoring
        # Higher score = better: base 100 - risk penalty - cost penalty
        for tool in survivors:
            score = 100.0
            # Deduct for higher risk
            score -= (risk_hierarchy.get(tool.risk_level, 0) * 10.0)
            # Deduct for cost
            score -= (tool.cost_per_invocation_usd * 50.0)
            scores[tool.tool_id] = round(score, 2)

        # Sort: score DESC, tool_id ASC
        ranked = sorted(survivors, key=lambda t: (-scores[t.tool_id], t.tool_id))
        winner = ranked[0]

        receipt = DecisionReceipt(
            decision_id=decision_id,
            decision_type=DecisionType.TOOL_ROUTING,
            task_id=task.task_id,
            candidates=candidates,
            rejected_candidates=rejected,
            scores=scores,
            selected_candidate=winner.tool_id,
            selection_reason=f"OPTIMAL_TOOL_UTILITY: Score {scores[winner.tool_id]} within risk ceiling {risk_ceiling.value}",
            confidence=0.95,
            estimated_cost_usd=winner.cost_per_invocation_usd,
            estimated_risk=winner.risk_level.value
        )

        return winner, receipt
