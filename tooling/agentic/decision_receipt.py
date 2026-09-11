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
import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple, Any
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


@dataclass
class DecisionReceipt:
    decision_id: str
    decision_type: DecisionType | str
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
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
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "decision_type": dtype,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
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
    def from_dict(cls, data: Dict[str, Any]) -> DecisionReceipt:
        return cls(
            decision_id=data["decision_id"],
            decision_type=data["decision_type"],
            mission_id=data.get("mission_id"),
            task_id=data.get("task_id"),
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
            resolved_utc=data.get("resolved_utc", datetime.now(timezone.utc).isoformat()),
            actual_attached_utc=data.get("actual_attached_utc"),
            metadata=dict(data.get("metadata", {})),
            schema_version=data.get("schema_version", SCHEMA_VERSION)
        )
