"""
failure_attribution.py // J.A.R.V.I.S. Failure Attribution & Root Cause Disentanglement
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Implements Phase 32 of the Autonomous Evolution Protocol:
- Disentangles failure causes across 6 distinct architectural domains:
  SKILL, AGENT, POLICY, TOOL, ENVIRONMENT, EXTERNAL_SERVICE
- Fitness Isolation Invariant:
  Only genuine SKILL defects penalize skill fitness.
  Infrastructure glitches, policy denials, budget timeouts, and agent routing mistakes
  are quarantined and NEVER penalize skill reputation.
"""

from __future__ import annotations
import re
import uuid
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone

from .models import (
    TaskNode,
    TaskStatus,
    ExecutionAttempt,
    FailureClass,
    FailureAttribution
)


@dataclass
class AttributionDiagnosis:
    diagnosis_id: str
    task_id: str
    attempt_id: Optional[str]
    attributed_cause: FailureAttribution
    is_skill_penalizable: bool
    confidence: float
    evidence: Dict[str, Any]
    recommended_recovery: str
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnosis_id": self.diagnosis_id,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "attributed_cause": self.attributed_cause.value if isinstance(self.attributed_cause, FailureAttribution) else str(self.attributed_cause),
            "is_skill_penalizable": self.is_skill_penalizable,
            "confidence": round(self.confidence, 4),
            "evidence": self.evidence,
            "recommended_recovery": self.recommended_recovery,
            "timestamp_utc": self.timestamp_utc
        }


class FailureAttributionEngine:
    """
    Authoritative Failure Attribution Engine.
    Analyzes attempt logs, exit codes, exceptions, and execution metadata
    to assign rigorous root-cause responsibility.
    """

    @staticmethod
    def is_penalizable(attribution: FailureAttribution | str) -> bool:
        """Core Invariant: Only direct SKILL attribution penalizes skill fitness."""
        attr_str = attribution.value if isinstance(attribution, FailureAttribution) else str(attribution)
        return attr_str.upper() == "SKILL"

    def diagnose_failure(
        self,
        task: TaskNode,
        attempt: Optional[ExecutionAttempt] = None,
        error_log: str = ""
    ) -> AttributionDiagnosis:
        """
        Diagnoses root cause of a task failure.
        """
        diagnosis_id = f"diag-{uuid.uuid4().hex[:8]}"
        attempt_id = attempt.attempt_id if attempt else None
        log_snippet = error_log or (attempt.output_reference if attempt else "") or ""
        exec_res = task.execution_result or {}

        # 1. Policy or Admission Denials -> POLICY
        if exec_res.get("denied") or exec_res.get("policy_decision") == "DENY" or exec_res.get("admission_decision"):
            return AttributionDiagnosis(
                diagnosis_id=diagnosis_id,
                task_id=task.task_id,
                attempt_id=attempt_id,
                attributed_cause=FailureAttribution.POLICY,
                is_skill_penalizable=False,
                confidence=0.99,
                evidence={"reason": exec_res.get("reason", "Policy Gate Blocked")},
                recommended_recovery="REQUEST_HUMAN_APPROVAL_OR_EXPAND_SCOPE"
            )

        # 2. Command Exit 0 but Verification Failed -> AGENT
        # Independent Multi-Dimensional Invariant: Command Exit 0 != Task Verified
        if exec_res.get("exit_code") == 0:
            return AttributionDiagnosis(
                diagnosis_id=diagnosis_id,
                task_id=task.task_id,
                attempt_id=attempt_id,
                attributed_cause=FailureAttribution.AGENT,
                is_skill_penalizable=False,
                confidence=0.95,
                evidence={"exit_code": 0, "reason": "Command exited 0 but independent verification rejected"},
                recommended_recovery="RETRY_WITH_EXPLICIT_VERIFICATION_CONSTRAINTS"
            )

        # 2. Concurrency Conflicts -> ENVIRONMENT
        if "ConcurrencyConflictError" in log_snippet or "concurrency" in log_snippet.lower():
            return AttributionDiagnosis(
                diagnosis_id=diagnosis_id,
                task_id=task.task_id,
                attempt_id=attempt_id,
                attributed_cause=FailureAttribution.ENVIRONMENT,
                is_skill_penalizable=False,
                confidence=0.95,
                evidence={"log_snippet": log_snippet[:200]},
                recommended_recovery="RETRY_WITH_FRESH_REPARSE"
            )

        # 3. Timeout or Process Termination -> ENVIRONMENT / NODE
        if attempt and attempt.failure_class == FailureClass.TIMEOUT:
            return AttributionDiagnosis(
                diagnosis_id=diagnosis_id,
                task_id=task.task_id,
                attempt_id=attempt_id,
                attributed_cause=FailureAttribution.ENVIRONMENT,
                is_skill_penalizable=False,
                confidence=0.90,
                evidence={"failure_class": "TIMEOUT"},
                recommended_recovery="INCREASE_TIMEOUT_OR_DELEGATE_NODE"
            )

        # 4. External Service / Connection Reset -> EXTERNAL_SERVICE
        net_errors = ["connection refused", "timeout error", "network unreachable", "dns lookup failed", "http 502", "http 503"]
        if any(err in log_snippet.lower() for err in net_errors):
            return AttributionDiagnosis(
                diagnosis_id=diagnosis_id,
                task_id=task.task_id,
                attempt_id=attempt_id,
                attributed_cause=FailureAttribution.EXTERNAL_SERVICE,
                is_skill_penalizable=False,
                confidence=0.88,
                evidence={"matched_pattern": "Network / Remote Outage"},
                recommended_recovery="EXPONENTIAL_BACKOFF_RETRY"
            )

        # 5. Agent Planning / Parameter Mismatch -> AGENT
        agent_errors = ["unexpected keyword argument", "missing required positional argument", "invalid tool parameters", "hallucinated argument"]
        if any(err in log_snippet.lower() for err in agent_errors):
            return AttributionDiagnosis(
                diagnosis_id=diagnosis_id,
                task_id=task.task_id,
                attempt_id=attempt_id,
                attributed_cause=FailureAttribution.AGENT,
                is_skill_penalizable=False,
                confidence=0.85,
                evidence={"matched_pattern": "Parameter / Schema Calling Error"},
                recommended_recovery="RETRY_WITH_PROMPT_CONSTRAINTS"
            )

        # 6. Syntax error or code defect in skill script -> SKILL
        skill_errors = ["syntaxerror", "nameerror", "attributeerror", "typeerror", "zerodivisionerror", "assertionerror", "indexerror"]
        if any(err in log_snippet.lower() for err in skill_errors):
            return AttributionDiagnosis(
                diagnosis_id=diagnosis_id,
                task_id=task.task_id,
                attempt_id=attempt_id,
                attributed_cause=FailureAttribution.SKILL,
                is_skill_penalizable=True,
                confidence=0.92,
                evidence={"matched_pattern": "Internal Code Exception in Skill"},
                recommended_recovery="DISPATCH_SWE_PATCH_OR_FALLBACK_SKILL"
            )

        # Default fallback: Unknown / Tool
        return AttributionDiagnosis(
            diagnosis_id=diagnosis_id,
            task_id=task.task_id,
            attempt_id=attempt_id,
            attributed_cause=FailureAttribution.UNKNOWN,
            is_skill_penalizable=False,
            confidence=0.50,
            evidence={"log": log_snippet[:150]},
            recommended_recovery="INVESTIGATE_TELEMETRY_LOGS"
        )
