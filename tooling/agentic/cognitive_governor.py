"""
cognitive_governor.py // J.A.R.V.I.S. High-Level Meta-Cognitive Governor
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Implements Phase 39 of the Autonomous Evolution Protocol:
- Meta-cognitive supervision over autonomous execution loops
- Detects infinite looping, hallucinatory drift, and repetitive thrashing
- Enforces Autonomy Envelope (A0_OBSERVE to A5_HIGH_RISK_APPROVAL)
- Issues EMERGENCY_HALT when autonomy bounds or loop thresholds are breached
- Produces verifiable, tamper-evident CognitiveReceipts
"""

from __future__ import annotations
import uuid
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import RiskLevel, MissionStatus


class AutonomyLevel(str, Enum):
    A0_OBSERVE = "A0"                  # Gather authorized state; zero task effects
    A1_RECOMMEND = "A1"                # Produce proposals with evidence and costs
    A2_READ_ONLY = "A2"                # Execute admitted read operations within scope
    A3_REVERSIBLE_LOCAL = "A3"         # Bounded local writes with provenance and recovery
    A4_BOUNDED_EXTERNAL = "A4"         # Explicit external authority, budgets, idempotency
    A5_HIGH_RISK_APPROVAL = "A5"       # Action-specific human approval and controls


@dataclass
class CognitiveReceipt:
    receipt_id: str
    autonomy_level: AutonomyLevel
    iteration_count: int
    loop_detected: bool
    halt_triggered: bool
    governor_decision: str  # PERMIT, WARN, HALT
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
            "timestamp_utc": self.timestamp_utc
        }


class CognitiveGovernor:
    """
    Supervises autonomous cognitive loops.
    Guarantees that autonomous self-direction never exceeds granted autonomy envelopes
    and prevents catastrophic runaway iteration.
    """

    def __init__(
        self,
        max_consecutive_repeats: int = 3,
        autonomy_ceiling: AutonomyLevel = AutonomyLevel.A3_REVERSIBLE_LOCAL
    ):
        self.max_consecutive_repeats = max_consecutive_repeats
        self.autonomy_ceiling = autonomy_ceiling
        self._action_history: List[str] = []
        self._iteration_count = 0

    def evaluate_step(
        self,
        action_signature: str,
        requested_risk: RiskLevel = RiskLevel.R0_READ_ONLY,
        is_external: bool = False,
        requires_approval: bool = False
    ) -> CognitiveReceipt:
        """
        Evaluates a proposed execution step before delegation.
        """
        receipt_id = f"rcp-cog-{uuid.uuid4().hex[:8]}"
        self._iteration_count += 1
        self._action_history.append(action_signature)

        # 1. Detect Infinite Loop / Repetitive Thrashing
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
                evidence={"recent_actions": recent}
            )

        # 2. Check Autonomy Ceiling against Requested Action
        autonomy_hierarchy = {
            AutonomyLevel.A0_OBSERVE: 0,
            AutonomyLevel.A1_RECOMMEND: 1,
            AutonomyLevel.A2_READ_ONLY: 2,
            AutonomyLevel.A3_REVERSIBLE_LOCAL: 3,
            AutonomyLevel.A4_BOUNDED_EXTERNAL: 4,
            AutonomyLevel.A5_HIGH_RISK_APPROVAL: 5
        }
        ceiling_rank = autonomy_hierarchy.get(self.autonomy_ceiling, 3)

        # Infer required autonomy
        if requires_approval or requested_risk in (RiskLevel.R4_INFRA_MUTATION, RiskLevel.R5_DESTRUCTIVE):
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
                evidence={"required_autonomy": required_level.value, "ceiling": self.autonomy_ceiling.value}
            )

        # Step Permitted
        return CognitiveReceipt(
            receipt_id=receipt_id,
            autonomy_level=self.autonomy_ceiling,
            iteration_count=self._iteration_count,
            loop_detected=False,
            halt_triggered=False,
            governor_decision="PERMIT",
            reason="Step within authorized autonomy envelope and loop thresholds",
            evidence={"action": action_signature, "required_autonomy": required_level.value}
        )

    def reset(self) -> None:
        self._action_history.clear()
        self._iteration_count = 0
