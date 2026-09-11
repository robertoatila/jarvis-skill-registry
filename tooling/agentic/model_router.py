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


DEFAULT_MODELS: List[ModelCandidate] = [
    ModelCandidate(
        model_id="sovereign-local-deepseek-8b",
        provider="local_ollama",
        context_window_tokens=32_768,
        cost_per_1k_tokens_usd=0.0,
        capability_rating=0.82,
        is_local=True,
        tier=0
    ),
    ModelCandidate(
        model_id="groq-llama-3.3-70b-versatile",
        provider="groq",
        context_window_tokens=128_000,
        cost_per_1k_tokens_usd=0.00059,
        capability_rating=0.91,
        is_local=False,
        tier=1
    ),
    ModelCandidate(
        model_id="gemini-2.0-flash",
        provider="google",
        context_window_tokens=1_000_000,
        cost_per_1k_tokens_usd=0.0001,
        capability_rating=0.92,
        is_local=False,
        tier=1
    ),
    ModelCandidate(
        model_id="claude-3-7-sonnet",
        provider="anthropic",
        context_window_tokens=200_000,
        cost_per_1k_tokens_usd=0.003,
        capability_rating=0.98,
        is_local=False,
        tier=2
    )
]


class ModelRouter:
    """
    Cost-Aware Autonomous Model Router:
    Enforces privacy confinement, context bounds, budget limits, and tiered escalation.
    """

    def __init__(self, catalog: Optional[List[ModelCandidate]] = None):
        self._catalog: Dict[str, ModelCandidate] = {}
        for m in (catalog or DEFAULT_MODELS):
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
        min_capability_rating: float = 0.80
    ) -> Tuple[Optional[ModelCandidate], DecisionReceipt]:
        """
        Routes the optimal model candidate based on privacy, capacity, and cost.
        Applies cost-aware escalation (starts cheap/local, escalates only when needed).
        """
        decision_id = f"dec-mod-{uuid.uuid4().hex[:8]}"
        candidates = list(self._catalog.keys())
        rejected: Dict[str, str] = {}
        scores: Dict[str, float] = {}

        # If task operates on sensitive scopes or risk is high, privacy is mandatory
        is_sensitive = privacy_enforced or any(
            "key" in s or "secret" in s or "auth" in s for s in task.read_scopes + task.write_scopes
        )

        survivors: List[ModelCandidate] = []
        for model_id, model in self._catalog.items():
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
            score = (model.capability_rating * 100.0) - (est_cost * 200.0)
            if model.is_local:
                score += 5.0  # Sovereign locality bonus
            scores[model.model_id] = round(score, 2)

        # Sort: score DESC, tier ASC
        ranked = sorted(survivors, key=lambda m: (-scores[m.model_id], m.tier))
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
            confidence=round(winner.capability_rating, 2),
            estimated_cost_usd=est_cost,
            estimated_tokens=required_context_tokens,
            metadata={"provider": winner.provider, "is_local": winner.is_local}
        )

        return winner, receipt
