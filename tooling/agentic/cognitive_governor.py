"""J.A.R.V.I.S. high-level cognitive strategy governor."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import RecoveryState, RiskLevel


class AutonomyLevel(str, Enum):
    A0_OBSERVE = "A0"
    A1_RECOMMEND = "A1"
    A2_READ_ONLY = "A2"
    A3_REVERSIBLE_LOCAL = "A3"
    A4_BOUNDED_EXTERNAL = "A4"
    A5_HIGH_RISK_APPROVAL = "A5"


class GovernorAction(str, Enum):
    CONTINUE = "CONTINUE"
    EXPAND_CONTEXT = "EXPAND_CONTEXT"
    ESCALATE_CAPABILITY = "ESCALATE_CAPABILITY"
    REPLAN = "REPLAN"
    STOP = "STOP"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"


@dataclass(frozen=True)
class GovernorObservation:
    authority_valid: bool
    risk_level: RiskLevel
    confidence: Optional[float]
    evidence_sufficient: bool
    context_exhausted: bool
    eligible_alternatives: int
    attempts: int
    repeats: int
    remaining_tokens: Optional[int]
    remaining_cost_usd: Optional[float]
    recovery_state: RecoveryState

    def __post_init__(self) -> None:
        for name in ("authority_valid", "evidence_sufficient", "context_exhausted"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"INVALID_{name.upper()}")
        if not isinstance(self.risk_level, RiskLevel):
            raise ValueError("INVALID_GOVERNOR_RISK_LEVEL")
        if not isinstance(self.recovery_state, RecoveryState):
            raise ValueError("INVALID_GOVERNOR_RECOVERY_STATE")
        if self.confidence is not None:
            if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
                raise ValueError("INVALID_GOVERNOR_CONFIDENCE")
            if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
                raise ValueError("INVALID_GOVERNOR_CONFIDENCE")
        for name in ("eligible_alternatives", "attempts", "repeats"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"INVALID_{name.upper()}")
        if self.remaining_tokens is not None:
            if type(self.remaining_tokens) is not int or self.remaining_tokens < 0:
                raise ValueError("INVALID_REMAINING_TOKENS")
        if self.remaining_cost_usd is not None:
            if isinstance(self.remaining_cost_usd, bool) or not isinstance(self.remaining_cost_usd, (int, float)):
                raise ValueError("INVALID_REMAINING_COST_USD")
            if not math.isfinite(self.remaining_cost_usd) or self.remaining_cost_usd < 0:
                raise ValueError("INVALID_REMAINING_COST_USD")


@dataclass
class CognitiveReceipt:
    receipt_id: str
    autonomy_level: AutonomyLevel
    iteration_count: int
    loop_detected: bool
    halt_triggered: bool
    governor_decision: str
    reason: str
    evidence: Dict[str, Any]
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "autonomy_level": self.autonomy_level.value if isinstance(self.autonomy_level, AutonomyLevel) else str(self.autonomy_level),
            "iteration_count": self.iteration_count,
            "loop_detected": self.loop_detected,
            "halt_triggered": self.halt_triggered,
            "governor_decision": self.governor_decision,
            "reason": self.reason,
            "evidence": self.evidence,
            "timestamp_utc": self.timestamp_utc,
        }


class CognitiveGovernor:
    @staticmethod
    def confidence_action(confidence: Optional[float], evidence_valid: bool, threshold: float) -> str:
        if not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("INVALID_CONFIDENCE_THRESHOLD")
        if confidence is None:
            return "GATHER_EVIDENCE"
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("INVALID_CONFIDENCE")
        if not evidence_valid:
            return "VERIFY_EVIDENCE"
        return "ACCEPT" if confidence >= threshold else "TRY_ELIGIBLE_ALTERNATIVE"

    def __init__(
        self,
        max_consecutive_repeats: int = 3,
        autonomy_ceiling: AutonomyLevel = AutonomyLevel.A3_REVERSIBLE_LOCAL,
        confidence_threshold: float = 0.8,
    ):
        if type(max_consecutive_repeats) is not int or max_consecutive_repeats <= 0:
            raise ValueError("INVALID_MAX_CONSECUTIVE_REPEATS")
        if isinstance(confidence_threshold, bool) or not isinstance(confidence_threshold, (int, float)):
            raise ValueError("INVALID_CONFIDENCE_THRESHOLD")
        if not math.isfinite(confidence_threshold) or not 0 <= confidence_threshold <= 1:
            raise ValueError("INVALID_CONFIDENCE_THRESHOLD")
        self.max_consecutive_repeats = max_consecutive_repeats
        self.autonomy_ceiling = autonomy_ceiling
        self.confidence_threshold = float(confidence_threshold)
        self._action_history: List[str] = []
        self._iteration_count = 0

    def decide(self, mission_id: str, observation: GovernorObservation) -> GovernorAction:
        """Choose a deterministic strategy action without performing effects."""
        if not isinstance(mission_id, str) or not mission_id.strip():
            raise ValueError("INVALID_GOVERNOR_MISSION_ID")
        if not isinstance(observation, GovernorObservation):
            raise TypeError("GOVERNOR_OBSERVATION_REQUIRED")

        if observation.recovery_state == RecoveryState.UNRECOVERABLE:
            return GovernorAction.STOP

        if (
            not observation.authority_valid
            or observation.risk_level.value == "R5"
            or observation.recovery_state in {
                RecoveryState.RECONCILIATION_PENDING,
                RecoveryState.COMPENSATION_PENDING,
                RecoveryState.RECOVERY_PENDING,
            }
        ):
            return GovernorAction.REQUIRE_HUMAN

        if observation.remaining_tokens == 0 or observation.remaining_cost_usd == 0:
            return GovernorAction.STOP

        evidence_insufficient = (
            not observation.evidence_sufficient
            or observation.confidence is None
            or observation.confidence < self.confidence_threshold
        )

        if evidence_insufficient and not observation.context_exhausted:
            return GovernorAction.EXPAND_CONTEXT
        if evidence_insufficient and observation.context_exhausted and observation.eligible_alternatives > 0:
            return GovernorAction.ESCALATE_CAPABILITY
        if observation.repeats >= self.max_consecutive_repeats:
            return GovernorAction.REPLAN
        if evidence_insufficient and observation.context_exhausted:
            return GovernorAction.REQUIRE_HUMAN
        return GovernorAction.CONTINUE

    def evaluate_step(
        self,
        action_signature: str,
        requested_risk: RiskLevel = RiskLevel.R0_READ_ONLY,
        is_external: bool = False,
        requires_approval: bool = False,
    ) -> CognitiveReceipt:
        receipt_id = f"rcp-cog-{uuid.uuid4().hex[:8]}"
        self._iteration_count += 1
        self._action_history.append(action_signature)

        loop_detected = False
        if len(self._action_history) >= self.max_consecutive_repeats:
            recent = self._action_history[-self.max_consecutive_repeats:]
            if len(set(recent)) == 1:
                loop_detected = True

        if loop_detected:
            return CognitiveReceipt(
                receipt_id=receipt_id,
                autonomy_level=self.autonomy_ceiling,
                iteration_count=self._iteration_count,
                loop_detected=True,
                halt_triggered=True,
                governor_decision="HALT",
                reason=f"INFINITE_LOOP_DETECTED: Action '{action_signature}' repeated {self.max_consecutive_repeats} consecutive times without progression",
                evidence={"recent_actions": recent},
            )

        autonomy_hierarchy = {
            AutonomyLevel.A0_OBSERVE: 0,
            AutonomyLevel.A1_RECOMMEND: 1,
            AutonomyLevel.A2_READ_ONLY: 2,
            AutonomyLevel.A3_REVERSIBLE_LOCAL: 3,
            AutonomyLevel.A4_BOUNDED_EXTERNAL: 4,
            AutonomyLevel.A5_HIGH_RISK_APPROVAL: 5,
        }
        ceiling_rank = autonomy_hierarchy.get(self.autonomy_ceiling, 3)

        if requires_approval or requested_risk.value in {"R4", "R5"}:
            required_level = AutonomyLevel.A5_HIGH_RISK_APPROVAL
        elif is_external or requested_risk == RiskLevel.R3_EXTERNAL_SIDE_EFFECT:
            required_level = AutonomyLevel.A4_BOUNDED_EXTERNAL
        elif requested_risk in (RiskLevel.R1_LOCAL_WRITE, RiskLevel.R2_REPO_MUTATION):
            required_level = AutonomyLevel.A3_REVERSIBLE_LOCAL
        else:
            required_level = AutonomyLevel.A2_READ_ONLY

        required_rank = autonomy_hierarchy.get(required_level, 2)
        if required_rank > ceiling_rank:
            return CognitiveReceipt(
                receipt_id=receipt_id,
                autonomy_level=self.autonomy_ceiling,
                iteration_count=self._iteration_count,
                loop_detected=False,
                halt_triggered=True,
                governor_decision="HALT",
                reason=f"AUTONOMY_CEILING_BREACHED: Required {required_level.value} exceeds granted ceiling {self.autonomy_ceiling.value}",
                evidence={"required_autonomy": required_level.value, "ceiling": self.autonomy_ceiling.value},
            )

        return CognitiveReceipt(
            receipt_id=receipt_id,
            autonomy_level=self.autonomy_ceiling,
            iteration_count=self._iteration_count,
            loop_detected=False,
            halt_triggered=False,
            governor_decision="PERMIT",
            reason="Step within authorized autonomy envelope and loop thresholds",
            evidence={"action": action_signature, "required_autonomy": required_level.value},
        )

    def reset(self) -> None:
        self._action_history.clear()
        self._iteration_count = 0
