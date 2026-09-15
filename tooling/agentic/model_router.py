"""
model_router.py // J.A.R.V.I.S. Cost-Aware Privacy-First Model Router
Pure Python 3.12 Standard Library (Zero PIP Dependencies)

Implements Phase 27 of the Autonomous Evolution Protocol:
- Privacy-first model selection (local sovereign vs cloud)
- Hard context window capacity & budget headroom constraints
- Cost-aware escalation sequence (Local Sovereign -> Fast Cloud -> Frontier Cloud)
- Generates formal DecisionReceipt for explainable model routing
"""

from __future__ import annotations
import uuid
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import TaskNode, RiskLevel
from .decision_receipt import DecisionReceipt, DecisionType


@dataclass
class ModelCandidate:
    model_id: str
    provider: str
    context_window_tokens: int
    cost_per_1k_tokens_usd: float
    capability_rating: float  # 0.0 to 1.0
    is_local: bool = False
    supports_structured_outputs: bool = True
    tier: int = 0  # 0=Local Sovereign, 1=Fast Economy, 2=Frontier
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

    def __post_init__(self):
        if not math.isfinite(self.cost_per_1k_tokens_usd) or self.cost_per_1k_tokens_usd < 0:
            raise ValueError("Invalid model cost")
        if not math.isfinite(self.capability_rating) or not 0 <= self.capability_rating <= 1:
            raise ValueError("Invalid model capability")
        if not isinstance(self.context_window_tokens, int) or self.context_window_tokens < 1:
            raise ValueError("Invalid context capacity")


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
            if values is not None and (not isinstance(values, tuple) or any(not isinstance(v, str) or not v for v in values)):
                raise ValueError("INVALID_ALLOWLIST")


@dataclass(frozen=True)
class InferenceRequirements:
    min_capability: float = 0.8
    context_tokens: int = 4000
    requires_tools: bool = False

    def __post_init__(self):
        if type(self.context_tokens) is not int or self.context_tokens <= 0:
            raise ValueError("INVALID_CONTEXT_REQUIREMENT")
        if isinstance(self.min_capability, bool) or not isinstance(self.min_capability, (int, float)) or not math.isfinite(self.min_capability) or not 0 <= self.min_capability <= 1:
            raise ValueError("INVALID_CAPABILITY_REQUIREMENT")
        if type(self.requires_tools) is not bool:
            raise ValueError("INVALID_TOOL_REQUIREMENT")


@dataclass(frozen=True)
class ModelRoutingWeights:
    capability_weight: float = 100.0
    cost_penalty: float = 200.0
    locality_bonus: float = 5.0

    def __post_init__(self):
        if any(not math.isfinite(v) or v < 0 for v in (self.capability_weight, self.cost_penalty, self.locality_bonus)):
            raise ValueError("INVALID_ROUTING_WEIGHTS")


DEFAULT_MODELS = [ModelCandidate(**entry) for entry in json.loads(
    (Path(__file__).resolve().parents[2] / "config" / "model-catalog.json").read_text(encoding="utf-8")
)]


class ModelRouter:
    """
    Cost-Aware Autonomous Model Router:
    Enforces privacy confinement, context bounds, budget limits, and tiered escalation.
    """

    def __init__(
        self,
        catalog: Optional[List[ModelCandidate]] = None,
        weights: Optional[ModelRoutingWeights] = None,
        catalog_version: str = "builtin-v1"
    ):
        self._catalog: Dict[str, ModelCandidate] = {}
        self.weights = weights or ModelRoutingWeights()
        self.catalog_version = catalog_version
        for m in (DEFAULT_MODELS if catalog is None else catalog):
            self.register_model(m)

    def register_model(self, model: ModelCandidate) -> None:
        self._catalog[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[ModelCandidate]:
        return self._catalog.get(model_id)

    def list_models(self) -> List[ModelCandidate]:
        return list(self._catalog.values())

    def route_model(
        self,
        task: TaskNode,
        privacy_enforced: bool = False,
        required_context_tokens: int = 4000,
        budget_headroom_usd: Optional[float] = None,
        min_capability_rating: float = 0.80,
        policy: Optional[InferencePolicy] = None,
        requirements: Optional[InferenceRequirements] = None,
    ) -> Tuple[Optional[ModelCandidate], DecisionReceipt]:
        """
        Routes the optimal model candidate based on privacy, capacity, and cost.
        Applies cost-aware escalation (starts cheap/local, escalates only when needed).
        """
        if requirements is not None:
            required_context_tokens = requirements.context_tokens
            min_capability_rating = requirements.min_capability
        decision_id = f"dec-mod-{uuid.uuid4().hex[:8]}"
        candidates = sorted(self._catalog.keys())
        rejected: Dict[str, str] = {}
        scores: Dict[str, float] = {}

        # If task operates on sensitive scopes or risk is high, privacy is mandatory
        is_sensitive = privacy_enforced or any(
            "key" in s or "secret" in s or "auth" in s for s in task.read_scopes + task.write_scopes
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
            # 1. Privacy enforcement: non-local models rejected if sensitive
            if is_sensitive and not model.is_local:
                rejected[model_id] = "Cloud model rejected: task contains sensitive scopes or requires sovereign privacy"
                continue

            # 2. Context capacity check
            if model.context_window_tokens < required_context_tokens:
                rejected[model_id] = f"Context window {model.context_window_tokens} insufficient for required {required_context_tokens} tokens"
                continue

            # 3. Minimum capability rating
            if model.capability_rating < min_capability_rating:
                rejected[model_id] = f"Capability rating {model.capability_rating:.2f} below required {min_capability_rating:.2f}"
                continue

            # 4. Estimated invocation cost check
            estimated_cost = (required_context_tokens / 1000.0) * model.cost_per_1k_tokens_usd
            if budget_headroom_usd is not None and estimated_cost > budget_headroom_usd:
                rejected[model_id] = f"Estimated cost ${estimated_cost:.5f} exceeds headroom ${budget_headroom_usd:.5f}"
                continue

            survivors.append(model)

        if not survivors:
            receipt = DecisionReceipt(
                decision_id=decision_id,
                decision_type=DecisionType.MODEL_ROUTING,
                task_id=task.task_id,
                candidates=candidates,
                rejected_candidates=rejected,
                scores={},
                selected_candidate="",
                selection_reason="BLOCKED: No admissible model meets privacy, context window, or budget headroom constraints",
                confidence=0.0
            )
            return None, receipt

        # Scoring & Cost-Aware Escalation:
        # Score = (capability * 100) - (cost penalty) - (tier penalty for unnecessary escalation)
        for model in survivors:
            est_cost = (required_context_tokens / 1000.0) * model.cost_per_1k_tokens_usd
            score = (
                model.capability_rating * self.weights.capability_weight
                - est_cost * self.weights.cost_penalty
            )
            if model.is_local:
                score += self.weights.locality_bonus
            scores[model.model_id] = round(score, 2)

        # Sort: score DESC, tier ASC
        ranked = sorted(survivors, key=lambda m: (-scores[m.model_id], m.tier, m.model_id))
        winner = ranked[0]
        est_cost = round((required_context_tokens / 1000.0) * winner.cost_per_1k_tokens_usd, 6)

        receipt = DecisionReceipt(
            decision_id=decision_id,
            decision_type=DecisionType.MODEL_ROUTING,
            task_id=task.task_id,
            candidates=candidates,
            rejected_candidates=rejected,
            scores=scores,
            selected_candidate=winner.model_id,
            selection_reason=f"SELECTED_OPTIMAL_MODEL: Score {scores[winner.model_id]} (Tier {winner.tier}, Local: {winner.is_local})",
            confidence=0.0,
            estimated_cost_usd=est_cost,
            estimated_tokens=required_context_tokens,
            metadata={
                "provider": winner.provider,
                "eligible_order": [model.model_id for model in ranked],
                "is_local": winner.is_local,
                "confidence_status": "UNKNOWN",
                "catalog_version": self.catalog_version,
                "measurement_kind": "catalog_estimate",
                "provider_invoked": False,
                "weights": {
                    "capability_weight": self.weights.capability_weight,
                    "cost_penalty": self.weights.cost_penalty,
                    "locality_bonus": self.weights.locality_bonus
                }
            }
        )

        return winner, receipt
