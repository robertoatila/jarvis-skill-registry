"""
model_router.py // J.A.R.V.I.S. Cost-Aware Privacy-First Model Router
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

from __future__ import annotations
import json
import math
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import TaskNode
from .decision_receipt import CandidateEvidence, DecisionReceipt, DecisionType


@dataclass
class ModelCandidate:
    model_id: str
    provider: str
    context_window_tokens: int
    cost_per_1k_tokens_usd: float
    capability_rating: float
    is_local: bool = False
    supports_structured_outputs: bool = True
    tier: int = 0
    supports_tools: bool = False
    requires_network: Optional[bool] = None
    available: bool = True
    version: str = "1"

    def __post_init__(self):
        if any(not isinstance(v, str) or not v for v in (self.model_id, self.provider, self.version)):
            raise ValueError("INVALID_MANIFEST_ID")
        if type(self.tier) is not int or self.tier < 0:
            raise ValueError("INVALID_MANIFEST_TIER")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (self.capability_rating, self.cost_per_1k_tokens_usd)):
            raise ValueError("INVALID_MANIFEST_NUMBER")
        if type(self.context_window_tokens) is not int or self.context_window_tokens <= 0:
            raise ValueError("INVALID_CONTEXT_CAPACITY")
        if not math.isfinite(self.capability_rating) or not 0 <= self.capability_rating <= 1:
            raise ValueError("INVALID_CAPABILITY")
        if not math.isfinite(self.cost_per_1k_tokens_usd) or self.cost_per_1k_tokens_usd < 0:
            raise ValueError("INVALID_COST")
        for value in (self.is_local, self.supports_tools, self.available, self.supports_structured_outputs):
            if type(value) is not bool:
                raise ValueError("INVALID_MANIFEST_BOOLEAN")
        if self.requires_network is None:
            self.requires_network = not self.is_local
        elif type(self.requires_network) is not bool:
            raise ValueError("INVALID_NETWORK_CAPABILITY")


@dataclass(frozen=True)
class InferencePolicy:
    local_only: bool = True
    network_allowed: bool = False
    allowed_models: Optional[tuple[str, ...]] = None
    allowed_tools: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.local_only) is not bool or type(self.network_allowed) is not bool:
            raise ValueError("INVALID_POLICY")
        for values in (self.allowed_models, self.allowed_tools):
            if values is not None and (
                not isinstance(values, tuple)
                or any(not isinstance(v, str) or not v for v in values)
            ):
                raise ValueError("INVALID_ALLOWLIST")


@dataclass(frozen=True)
class InferenceRequirements:
    min_capability: float = 0.8
    context_tokens: int = 4000
    requires_tools: bool = False

    def __post_init__(self):
        if type(self.context_tokens) is not int or self.context_tokens <= 0:
            raise ValueError("INVALID_CONTEXT_REQUIREMENT")
        if (
            isinstance(self.min_capability, bool)
            or not isinstance(self.min_capability, (int, float))
            or not math.isfinite(self.min_capability)
            or not 0 <= self.min_capability <= 1
        ):
            raise ValueError("INVALID_CAPABILITY_REQUIREMENT")
        if type(self.requires_tools) is not bool:
            raise ValueError("INVALID_TOOL_REQUIREMENT")


@dataclass(frozen=True)
class ModelRoutingWeights:
    capability_weight: float = 100.0
    cost_penalty: float = 200.0
    locality_bonus: float = 5.0

    def __post_init__(self):
        if any(
            not math.isfinite(v) or v < 0
            for v in (
                self.capability_weight,
                self.cost_penalty,
                self.locality_bonus,
            )
        ):
            raise ValueError("INVALID_ROUTING_WEIGHTS")


DEFAULT_MODELS = [
    ModelCandidate(**entry)
    for entry in json.loads(
        (Path(__file__).resolve().parents[2] / "config" / "model-catalog.json").read_text(
            encoding="utf-8"
        )
    )
]


class ModelRouter:
    """Hard-filter first, then deterministic prior/qualified-empirical ranking."""

    def __init__(
        self,
        catalog: Optional[List[ModelCandidate]] = None,
        weights: Optional[ModelRoutingWeights] = None,
        catalog_version: str = "builtin-v1",
    ):
        self._catalog: Dict[str, ModelCandidate] = {}
        self.weights = weights or ModelRoutingWeights()
        self.catalog_version = catalog_version
        for model in (DEFAULT_MODELS if catalog is None else catalog):
            self.register_model(model)

    def register_model(self, model: ModelCandidate) -> None:
        self._catalog[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[ModelCandidate]:
        return self._catalog.get(model_id)

    def list_models(self) -> List[ModelCandidate]:
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

    def route_model(
        self,
        task: TaskNode,
        privacy_enforced: bool = False,
        required_context_tokens: int = 4000,
        budget_headroom_usd: Optional[float] = None,
        min_capability_rating: float = 0.80,
        policy: Optional[InferencePolicy] = None,
        requirements: Optional[InferenceRequirements] = None,
        candidate_evidence: Optional[Dict[str, CandidateEvidence]] = None,
        environment_fingerprint: Optional[str] = None,
        evidence_now_utc: Optional[str] = None,
        max_evidence_age_seconds: Optional[float] = None,
    ) -> Tuple[Optional[ModelCandidate], DecisionReceipt]:
        if requirements is not None:
            required_context_tokens = requirements.context_tokens
            min_capability_rating = requirements.min_capability
        self._validate_evidence_input(
            candidate_evidence,
            environment_fingerprint,
            evidence_now_utc,
            max_evidence_age_seconds,
        )

        decision_id = f"dec-mod-{uuid.uuid4().hex[:8]}"
        candidates = sorted(self._catalog.keys())
        rejected: Dict[str, str] = {}
        scores: Dict[str, float] = {}

        is_sensitive = privacy_enforced or any(
            "key" in scope or "secret" in scope or "auth" in scope
            for scope in task.read_scopes + task.write_scopes
        )

        survivors: List[ModelCandidate] = []
        for model_id, model in self._catalog.items():
            if not model.available:
                rejected[model_id] = "UNAVAILABLE"
                continue
            if policy is not None:
                if policy.local_only and not model.is_local:
                    rejected[model_id] = "LOCAL_ONLY"
                    continue
                if not policy.network_allowed and model.requires_network:
                    rejected[model_id] = "NETWORK_DENIED"
                    continue
                if policy.allowed_models is not None and model_id not in policy.allowed_models:
                    rejected[model_id] = "MODEL_NOT_AUTHORIZED"
                    continue
            if requirements is not None and requirements.requires_tools and not model.supports_tools:
                rejected[model_id] = "TOOLS_UNSUPPORTED"
                continue
            if is_sensitive and not model.is_local:
                rejected[model_id] = (
                    "Cloud model rejected: task contains sensitive scopes or requires sovereign privacy"
                )
                continue
            if model.context_window_tokens < required_context_tokens:
                rejected[model_id] = (
                    f"Context window {model.context_window_tokens} insufficient for required "
                    f"{required_context_tokens} tokens"
                )
                continue
            if model.capability_rating < min_capability_rating:
                rejected[model_id] = (
                    f"Capability rating {model.capability_rating:.2f} below required "
                    f"{min_capability_rating:.2f}"
                )
                continue
            estimated_cost = (
                required_context_tokens / 1000.0
            ) * model.cost_per_1k_tokens_usd
            if budget_headroom_usd is not None and estimated_cost > budget_headroom_usd:
                rejected[model_id] = (
                    f"Estimated cost ${estimated_cost:.5f} exceeds headroom "
                    f"${budget_headroom_usd:.5f}"
                )
                continue
            survivors.append(model)

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
                decision_type=DecisionType.MODEL_ROUTING,
                task_id=task.task_id,
                candidates=candidates,
                rejected_candidates=rejected,
                scores={},
                selected_candidate="",
                selection_reason=(
                    "BLOCKED: No admissible model meets privacy, context window, "
                    "or budget headroom constraints"
                ),
                confidence=0.0,
                metadata={
                    "evidence_status": evidence_status,
                    "ranking_mode": "hard_constraints_only",
                    "catalog_version": self.catalog_version,
                },
            )

        for model in survivors:
            est_cost = (
                required_context_tokens / 1000.0
            ) * model.cost_per_1k_tokens_usd
            score = (
                model.capability_rating * self.weights.capability_weight
                - est_cost * self.weights.cost_penalty
            )
            if model.is_local:
                score += self.weights.locality_bonus
            scores[model.model_id] = round(score, 2)

        qualified_ids = {
            model.model_id
            for model in survivors
            if evidence_status[model.model_id] == "QUALIFIED"
        }

        def rank_key(model: ModelCandidate):
            evidence = (candidate_evidence or {}).get(model.model_id)
            if model.model_id in qualified_ids and evidence is not None:
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
                    -scores[model.model_id],
                    model.tier,
                    model.model_id,
                )
            return (
                1,
                0.0,
                math.inf,
                math.inf,
                0,
                -scores[model.model_id],
                model.tier,
                model.model_id,
            )

        ranked = sorted(survivors, key=rank_key)
        winner = ranked[0]
        ranking_mode = (
            "qualified_empirical_then_prior"
            if qualified_ids
            else "configured_prior"
        )
        winner_evidence = (candidate_evidence or {}).get(winner.model_id)
        est_cost = round(
            (required_context_tokens / 1000.0) * winner.cost_per_1k_tokens_usd,
            6,
        )
        if winner.model_id in qualified_ids and winner_evidence is not None:
            selection_reason = (
                "QUALIFIED_EMPIRICAL_MODEL: verified success evidence ranked "
                "the hard-constraint survivor first"
            )
        else:
            selection_reason = (
                f"SELECTED_OPTIMAL_MODEL: Score {scores[winner.model_id]} "
                f"(Tier {winner.tier}, Local: {winner.is_local})"
            )

        return winner, DecisionReceipt(
            decision_id=decision_id,
            decision_type=DecisionType.MODEL_ROUTING,
            task_id=task.task_id,
            candidates=candidates,
            rejected_candidates=rejected,
            scores=scores,
            selected_candidate=winner.model_id,
            selection_reason=selection_reason,
            confidence=0.0,
            estimated_cost_usd=est_cost,
            estimated_tokens=required_context_tokens,
            metadata={
                "provider": winner.provider,
                "eligible_order": [model.model_id for model in ranked],
                "is_local": winner.is_local,
                "confidence_status": (
                    "QUALIFIED_EVIDENCE"
                    if winner.model_id in qualified_ids
                    else "UNKNOWN"
                ),
                "ranking_mode": ranking_mode,
                "evidence_status": evidence_status,
                "evidence_basis": (
                    winner_evidence.to_dict()
                    if winner.model_id in qualified_ids and winner_evidence is not None
                    else None
                ),
                "catalog_version": self.catalog_version,
                "weights": {
                    "capability_weight": self.weights.capability_weight,
                    "cost_penalty": self.weights.cost_penalty,
                    "locality_bonus": self.weights.locality_bonus,
                },
            },
        )
