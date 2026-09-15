"""
decision_receipt.py // J.A.R.V.I.S. Universal Decision Receipt System
Pure Python 3.12 Standard Library (Zero PIP Dependencies)

Implements Phase 28 of the Autonomous Evolution Protocol:
- Unified, immutable audit receipt for all autonomous routing decisions
  (Agent, Skill, Tool, Model, Node, Replanning, Context Compaction)
- Preserves original estimates (cost, tokens, risk, confidence) immutable
- Attaches actual observed outcomes afterward without rewriting estimates
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

SCHEMA_VERSION = "2.0.0"


class DecisionType(str, Enum):
    AGENT_SELECTION = "agent_selection"
    SKILL_SELECTION = "skill_selection"
    TOOL_ROUTING = "tool_routing"
    MODEL_ROUTING = "model_routing"
    NODE_SELECTION = "node_selection"
    CONTEXT_COMPACTION = "context_compaction"
    REPLANNING = "replanning"


@dataclass(frozen=True)
class CandidateEvidence:
    """Immutable empirical evidence considered only after hard routing filters."""

    sample_count: int
    verified_success_rate: Optional[float]
    median_latency_ms: Optional[float]
    measured_cost_usd: Optional[float]
    environment_fingerprint: Optional[str]
    freshness_utc: Optional[str]

    def __post_init__(self) -> None:
        if type(self.sample_count) is not int or self.sample_count < 0:
            raise ValueError("INVALID_EVIDENCE_SAMPLE_COUNT")
        if self.verified_success_rate is not None:
            if (
                isinstance(self.verified_success_rate, bool)
                or not isinstance(self.verified_success_rate, (int, float))
                or not math.isfinite(self.verified_success_rate)
                or not 0 <= self.verified_success_rate <= 1
            ):
                raise ValueError("INVALID_VERIFIED_SUCCESS_RATE")
        for value, name in (
            (self.median_latency_ms, "INVALID_MEDIAN_LATENCY_MS"),
            (self.measured_cost_usd, "INVALID_MEASURED_COST_USD"),
        ):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(name)
        if self.environment_fingerprint is not None and (
            not isinstance(self.environment_fingerprint, str)
            or not self.environment_fingerprint.strip()
        ):
            raise ValueError("INVALID_ENVIRONMENT_FINGERPRINT")
        if self.freshness_utc is not None:
            self._parse_timestamp(self.freshness_utc, "INVALID_EVIDENCE_FRESHNESS")

    @staticmethod
    def _parse_timestamp(value: str, error_code: str) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(error_code)
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(error_code) from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError(error_code)
        return parsed.astimezone(timezone.utc)

    def qualification_status(
        self,
        *,
        environment_fingerprint: Optional[str] = None,
        evidence_now_utc: Optional[str] = None,
        max_evidence_age_seconds: Optional[float] = None,
    ) -> str:
        if self.sample_count == 0:
            return "UNKNOWN_ZERO_SAMPLES"
        if environment_fingerprint is not None:
            if not isinstance(environment_fingerprint, str) or not environment_fingerprint.strip():
                raise ValueError("INVALID_EXPECTED_ENVIRONMENT_FINGERPRINT")
            if self.environment_fingerprint is None:
                return "UNKNOWN_ENVIRONMENT"
            if self.environment_fingerprint != environment_fingerprint:
                return "ENVIRONMENT_MISMATCH"
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
            now = self._parse_timestamp(evidence_now_utc, "INVALID_EVIDENCE_NOW")
            if self.freshness_utc is None:
                return "UNKNOWN_FRESHNESS"
            fresh = self._parse_timestamp(self.freshness_utc, "INVALID_EVIDENCE_FRESHNESS")
            age_seconds = (now - fresh).total_seconds()
            if age_seconds < 0:
                return "FUTURE_EVIDENCE"
            if age_seconds > max_evidence_age_seconds:
                return "STALE_EVIDENCE"
        if self.verified_success_rate is None:
            return "UNKNOWN_SUCCESS_RATE"
        return "QUALIFIED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_count": self.sample_count,
            "verified_success_rate": self.verified_success_rate,
            "median_latency_ms": self.median_latency_ms,
            "measured_cost_usd": self.measured_cost_usd,
            "environment_fingerprint": self.environment_fingerprint,
            "freshness_utc": self.freshness_utc,
        }


@dataclass
class DecisionReceipt:
    decision_id: str
    decision_type: DecisionType | str
    receipt_id: Optional[str] = None
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    attempt_id: Optional[str] = None
    trace_id: Optional[str] = None
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    candidates: List[str] = field(default_factory=list)
    rejected_candidates: Dict[str, str] = field(default_factory=dict)
    scores: Dict[str, float] = field(default_factory=dict)
    selected_candidate: str = ""
    selection_reason: str = ""
    confidence: float = 1.0
    estimated_cost_usd: Optional[float] = None
    estimated_tokens: Optional[int] = None
    estimated_risk: str = "R0"
    actual_cost_usd: Optional[float] = None
    actual_tokens: Optional[int] = None
    actual_outcome: Optional[str] = None
    resolved_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actual_attached_utc: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if isinstance(self.decision_type, str):
            try:
                self.decision_type = DecisionType(self.decision_type)
            except ValueError:
                pass
        if self.receipt_id is None:
            self.receipt_id = self.decision_id

    def attach_actual_outcome(
        self,
        actual_cost_usd: Optional[float] = None,
        actual_tokens: Optional[int] = None,
        actual_outcome: Optional[str] = None
    ) -> None:
        """
        Attaches actual measured execution outcome without mutating the
        original estimated_cost_usd, estimated_tokens, or confidence.
        """
        if actual_cost_usd is not None:
            self.actual_cost_usd = round(float(actual_cost_usd), 6)
        if actual_tokens is not None:
            self.actual_tokens = int(actual_tokens)
        if actual_outcome is not None:
            self.actual_outcome = str(actual_outcome)
        self.actual_attached_utc = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        dtype = self.decision_type.value if hasattr(self.decision_type, "value") else str(self.decision_type)
        return {
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "trace_id": self.trace_id,
            "created_utc": self.created_utc,
            "decision_id": self.decision_id,
            "decision_type": dtype,
            "candidates": sorted(self.candidates),
            "rejected_candidates": self.rejected_candidates,
            "scores": self.scores,
            "selected_candidate": self.selected_candidate,
            "selection_reason": self.selection_reason,
            "confidence": self.confidence,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_tokens": self.estimated_tokens,
            "estimated_risk": self.estimated_risk,
            "actual_cost_usd": self.actual_cost_usd,
            "actual_tokens": self.actual_tokens,
            "actual_outcome": self.actual_outcome,
            "resolved_utc": self.resolved_utc,
            "actual_attached_utc": self.actual_attached_utc,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionReceipt":
        resolved = data.get("resolved_utc", datetime.now(timezone.utc).isoformat())
        return cls(
            decision_id=data["decision_id"],
            decision_type=data["decision_type"],
            receipt_id=data.get("receipt_id", data["decision_id"]),
            mission_id=data.get("mission_id"),
            task_id=data.get("task_id"),
            attempt_id=data.get("attempt_id"),
            trace_id=data.get("trace_id"),
            created_utc=data.get("created_utc", resolved),
            candidates=list(data.get("candidates", [])),
            rejected_candidates=dict(data.get("rejected_candidates", {})),
            scores=dict(data.get("scores", {})),
            selected_candidate=data.get("selected_candidate", ""),
            selection_reason=data.get("selection_reason", ""),
            confidence=data.get("confidence", 1.0),
            estimated_cost_usd=data.get("estimated_cost_usd"),
            estimated_tokens=data.get("estimated_tokens"),
            estimated_risk=data.get("estimated_risk", "R0"),
            actual_cost_usd=data.get("actual_cost_usd"),
            actual_tokens=data.get("actual_tokens"),
            actual_outcome=data.get("actual_outcome"),
            resolved_utc=resolved,
            actual_attached_utc=data.get("actual_attached_utc"),
            metadata=dict(data.get("metadata", {})),
            schema_version=data.get("schema_version", SCHEMA_VERSION)
        )
