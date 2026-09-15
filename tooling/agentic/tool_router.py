"""
tool_router.py // J.A.R.V.I.S. Constrained Autonomous Tool Router
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

from __future__ import annotations
import math
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .models import RiskLevel, TaskNode
from .decision_receipt import CandidateEvidence, DecisionReceipt, DecisionType
from .model_router import InferencePolicy


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
    requires_network: bool = False

    def __post_init__(self):
        if (
            not self.tool_id
            or not isinstance(self.capabilities, list)
            or any(not isinstance(capability, str) or not capability for capability in self.capabilities)
        ):
            raise ValueError("INVALID_TOOL_MANIFEST")
        if type(self.requires_network) is not bool or type(self.is_mutation) is not bool:
            raise ValueError("INVALID_TOOL_BOOLEAN")
        if not math.isfinite(self.cost_per_invocation_usd) or self.cost_per_invocation_usd < 0:
            raise ValueError("INVALID_TOOL_COST")

    def matches_capabilities(self, required_caps: List[str]) -> bool:
        if not required_caps:
            return True
        tool_caps = {capability.lower() for capability in self.capabilities}
        if "*" in tool_caps or "general-tooling" in tool_caps:
            return True
        return all(requirement.lower() in tool_caps for requirement in required_caps)


@dataclass(frozen=True)
class ToolRoutingWeights:
    base_utility: float = 100.0
    risk_penalty: float = 10.0
    cost_penalty: float = 50.0


DEFAULT_TOOLS: List[ToolCandidate] = [
    ToolCandidate(
        tool_id="local.read_file",
        name="Local File Reader",
        capabilities=["local.read_file", "read_file", "view_file", "source_inspection", "file_read"],
        risk_level=RiskLevel.R0_READ_ONLY,
        is_mutation=False,
        cost_per_invocation_usd=0.0,
    ),
    ToolCandidate(
        tool_id="local.write_text",
        name="Local File Writer",
        capabilities=["local.write_text", "write_file", "create_file", "patch_file", "file_write", "codegen"],
        risk_level=RiskLevel.R1_LOCAL_WRITE,
        is_mutation=True,
        cost_per_invocation_usd=0.0,
    ),
    ToolCandidate(
        tool_id="local.ast_inspector",
        name="Static AST Integrity Inspector",
        capabilities=["systematic-code-debugging", "ast_analysis", "syntax_check"],
        risk_level=RiskLevel.R0_READ_ONLY,
        is_mutation=False,
        cost_per_invocation_usd=0.0,
    ),
    ToolCandidate(
        tool_id="local.test_runner",
        name="Subprocess Test Runner",
        capabilities=["test_runner", "pytest", "unittest", "verification"],
        risk_level=RiskLevel.R1_LOCAL_WRITE,
        is_mutation=False,
        cost_per_invocation_usd=0.0,
    ),
    ToolCandidate(
        tool_id="local.repo_intel_scanner",
        name="Incremental Repository Intelligence Scanner",
        capabilities=["repo_intel", "symbol_extraction", "dependency_graph"],
        risk_level=RiskLevel.R0_READ_ONLY,
        is_mutation=False,
        cost_per_invocation_usd=0.0,
    ),
]


class ToolRouter:
    """Hard-filter first, then deterministic prior/qualified-empirical ranking."""

    def __init__(
        self,
        catalog: Optional[List[ToolCandidate]] = None,
        weights: Optional[ToolRoutingWeights] = None,
        catalog_version: str = "builtin-v1",
    ):
        self._catalog: Dict[str, ToolCandidate] = {}
        self.weights = weights or ToolRoutingWeights()
        self.catalog_version = catalog_version
        for tool in (DEFAULT_TOOLS if catalog is None else catalog):
            self.register_tool(tool)

    def register_tool(self, tool: ToolCandidate) -> None:
        self._catalog[tool.tool_id] = tool

    def get_tool(self, tool_id: str) -> Optional[ToolCandidate]:
        return self._catalog.get(tool_id)

    def list_tools(self) -> List[ToolCandidate]:
        return list(self._catalog.values())

    @staticmethod
    def _validate_evidence_input(
        candidate_evidence: Optional[Dict[str, CandidateEvidence]],
        environment_fingerprint: Optional[str],
        evidence_now_utc: Optional[str],
        max_evidence_age_seconds: Optional[float],
    ) -> None:
        if candidate_evidence is not None:
            if not isinstance(candidate_evidence, dict) or any(
                not isinstance(candidate_id, str)
                or not candidate_id
                or not isinstance(evidence, CandidateEvidence)
                for candidate_id, evidence in candidate_evidence.items()
            ):
                raise ValueError("INVALID_CANDIDATE_EVIDENCE")
        if environment_fingerprint is not None and (
            not isinstance(environment_fingerprint, str) or not environment_fingerprint.strip()
        ):
            raise ValueError("INVALID_EXPECTED_ENVIRONMENT_FINGERPRINT")
        if max_evidence_age_seconds is not None:
            if (
                isinstance(max_evidence_age_seconds, bool)
                or not isinstance(max_evidence_age_seconds, (int, float))
                or not math.isfinite(max_evidence_age_seconds)
                or max_evidence_age_seconds < 0
            ):
                raise ValueError("INVALID_MAX_EVIDENCE_AGE")
            if evidence_now_utc is None:
                raise ValueError("EVIDENCE_NOW_REQUIRED")

    def route_tool(
        self,
        task: TaskNode,
        risk_ceiling: RiskLevel = RiskLevel.R3_EXTERNAL_SIDE_EFFECT,
        budget_usd_headroom: Optional[float] = None,
        required_capabilities: Optional[List[str]] = None,
        policy: Optional[InferencePolicy] = None,
        candidate_evidence: Optional[Dict[str, CandidateEvidence]] = None,
        environment_fingerprint: Optional[str] = None,
        evidence_now_utc: Optional[str] = None,
        max_evidence_age_seconds: Optional[float] = None,
    ) -> Tuple[Optional[ToolCandidate], DecisionReceipt]:
        self._validate_evidence_input(
            candidate_evidence,
            environment_fingerprint,
            evidence_now_utc,
            max_evidence_age_seconds,
        )

        decision_id = f"dec-tool-{uuid.uuid4().hex[:8]}"
        candidates = sorted(self._catalog.keys())
        rejected: Dict[str, str] = {}
        scores: Dict[str, float] = {}

        required_caps = (
            task.required_skills
            if required_capabilities is None
            else required_capabilities
        )
        risk_hierarchy = {
            RiskLevel.R0_READ_ONLY: 0,
            RiskLevel.R1_LOCAL_WRITE: 1,
            RiskLevel.R2_REPO_MUTATION: 2,
            RiskLevel.R3_EXTERNAL_SIDE_EFFECT: 3,
            RiskLevel.R4_INFRA_MUTATION: 4,
            RiskLevel.R5_DESTRUCTIVE: 5,
        }

        survivors: List[ToolCandidate] = []
        for tool_id, tool in self._catalog.items():
            if policy is not None:
                if tool_id not in policy.allowed_tools:
                    rejected[tool_id] = "TOOL_NOT_AUTHORIZED"
                    continue
                if tool.requires_network and (policy.local_only or not policy.network_allowed):
                    rejected[tool_id] = "NETWORK_DENIED"
                    continue
            if not tool.matches_capabilities(required_caps):
                rejected[tool_id] = (
                    f"Tool lacks required capabilities: {', '.join(required_caps)}"
                )
                continue

            tool_risk_score = risk_hierarchy.get(tool.risk_level, 0)
            ceiling_score = risk_hierarchy.get(risk_ceiling, 3)
            if tool_risk_score > ceiling_score:
                rejected[tool_id] = (
                    f"Tool risk {tool.risk_level.value} exceeds ceiling {risk_ceiling.value}"
                )
                continue
            if (
                budget_usd_headroom is not None
                and tool.cost_per_invocation_usd > budget_usd_headroom
            ):
                rejected[tool_id] = (
                    f"Tool cost ${tool.cost_per_invocation_usd:.4f} exceeds headroom "
                    f"${budget_usd_headroom:.4f}"
                )
                continue
            survivors.append(tool)

        evidence_status: Dict[str, str] = {}
        for candidate_id in candidates:
            if candidate_id in rejected:
                evidence_status[candidate_id] = "HARD_REJECTED"
                continue
            evidence = (candidate_evidence or {}).get(candidate_id)
            evidence_status[candidate_id] = (
                "NO_EVIDENCE"
                if evidence is None
                else evidence.qualification_status(
                    environment_fingerprint=environment_fingerprint,
                    evidence_now_utc=evidence_now_utc,
                    max_evidence_age_seconds=max_evidence_age_seconds,
                )
            )

        if not survivors:
            return None, DecisionReceipt(
                decision_id=decision_id,
                decision_type=DecisionType.TOOL_ROUTING,
                task_id=task.task_id,
                candidates=candidates,
                rejected_candidates=rejected,
                scores={},
                selected_candidate="",
                selection_reason=(
                    "BLOCKED: No admissible tool satisfies required capabilities "
                    "and hard constraints (zero tool hallucination)"
                ),
                confidence=0.0,
                metadata={
                    "evidence_status": evidence_status,
                    "ranking_mode": "hard_constraints_only",
                    "catalog_version": self.catalog_version,
                },
            )

        for tool in survivors:
            score = self.weights.base_utility
            score -= risk_hierarchy.get(tool.risk_level, 0) * self.weights.risk_penalty
            score -= tool.cost_per_invocation_usd * self.weights.cost_penalty
            scores[tool.tool_id] = round(score, 2)

        qualified_ids = {
            tool.tool_id
            for tool in survivors
            if evidence_status[tool.tool_id] == "QUALIFIED"
        }

        def rank_key(tool: ToolCandidate):
            evidence = (candidate_evidence or {}).get(tool.tool_id)
            if tool.tool_id in qualified_ids and evidence is not None:
                return (
                    0,
                    -float(evidence.verified_success_rate),
                    (
                        float(evidence.measured_cost_usd)
                        if evidence.measured_cost_usd is not None
                        else math.inf
                    ),
                    (
                        float(evidence.median_latency_ms)
                        if evidence.median_latency_ms is not None
                        else math.inf
                    ),
                    -evidence.sample_count,
                    -scores[tool.tool_id],
                    tool.tool_id,
                )
            return (
                1,
                0.0,
                math.inf,
                math.inf,
                0,
                -scores[tool.tool_id],
                tool.tool_id,
            )

        ranked = sorted(survivors, key=rank_key)
        winner = ranked[0]
        winner_evidence = (candidate_evidence or {}).get(winner.tool_id)
        ranking_mode = (
            "qualified_empirical_then_prior"
            if qualified_ids
            else "configured_prior"
        )
        if winner.tool_id in qualified_ids and winner_evidence is not None:
            selection_reason = (
                "QUALIFIED_EMPIRICAL_TOOL: verified success evidence ranked "
                "the hard-constraint survivor first"
            )
        else:
            selection_reason = (
                f"OPTIMAL_TOOL_UTILITY: Score {scores[winner.tool_id]} "
                f"within risk ceiling {risk_ceiling.value}"
            )

        return winner, DecisionReceipt(
            decision_id=decision_id,
            decision_type=DecisionType.TOOL_ROUTING,
            task_id=task.task_id,
            candidates=candidates,
            rejected_candidates=rejected,
            scores=scores,
            selected_candidate=winner.tool_id,
            selection_reason=selection_reason,
            confidence=0.0,
            estimated_cost_usd=winner.cost_per_invocation_usd,
            estimated_risk=winner.risk_level.value,
            metadata={
                "confidence_status": (
                    "QUALIFIED_EVIDENCE"
                    if winner.tool_id in qualified_ids
                    else "UNKNOWN"
                ),
                "score_source": "configured_heuristic",
                "ranking_mode": ranking_mode,
                "eligible_order": [tool.tool_id for tool in ranked],
                "evidence_status": evidence_status,
                "evidence_basis": (
                    winner_evidence.to_dict()
                    if winner.tool_id in qualified_ids and winner_evidence is not None
                    else None
                ),
                "catalog_version": self.catalog_version,
                "weights": {
                    "base_utility": self.weights.base_utility,
                    "risk_penalty": self.weights.risk_penalty,
                    "cost_penalty": self.weights.cost_penalty,
                },
            },
        )
