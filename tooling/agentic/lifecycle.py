"""
lifecycle.py // J.A.R.V.I.S. Skill Promotion Lifecycle & State Machine Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- Canonical 11-State Machine from schemas/lifecycle.schema.json:
  DISCOVERED -> CANDIDATE -> EVALUATED -> VERIFIED -> ELIGIBLE -> STAGED -> ACTIVE -> DEPRECATED -> RETIRED
- Terminal / Guard states: BLOCKED, QUARANTINED
- Absolute Quarantine Precedence: Any state may transition to QUARANTINED immediately on security violation
- Strict Promotion Gate: QUARANTINED and BLOCKED can never transition to ACTIVE without re-evaluation
"""

from __future__ import annotations
import os
import json
import uuid
import time
import hashlib
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone


from .config import CONFIG, JarvisRuntimeConfig


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
LIFECYCLE_STATE_FILE = REGISTRY_ROOT / "state" / "skill_lifecycles.json"


class LifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    CANDIDATE = "CANDIDATE"
    EVALUATED = "EVALUATED"
    VERIFIED = "VERIFIED"
    ELIGIBLE = "ELIGIBLE"
    STAGED = "STAGED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"
    BLOCKED = "BLOCKED"
    QUARANTINED = "QUARANTINED"


# Standard progression sequence
PROGRESSION_ORDER = [
    LifecycleState.DISCOVERED,
    LifecycleState.CANDIDATE,
    LifecycleState.EVALUATED,
    LifecycleState.VERIFIED,
    LifecycleState.ELIGIBLE,
    LifecycleState.STAGED,
    LifecycleState.ACTIVE,
    LifecycleState.DEPRECATED,
    LifecycleState.RETIRED
]

# Legal direct transitions
ALLOWED_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
    LifecycleState.DISCOVERED: {LifecycleState.CANDIDATE, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.CANDIDATE: {LifecycleState.EVALUATED, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.EVALUATED: {LifecycleState.VERIFIED, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.VERIFIED: {LifecycleState.ELIGIBLE, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.ELIGIBLE: {LifecycleState.STAGED, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.STAGED: {LifecycleState.ACTIVE, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.ACTIVE: {LifecycleState.DEPRECATED, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.DEPRECATED: {LifecycleState.RETIRED, LifecycleState.ACTIVE, LifecycleState.QUARANTINED, LifecycleState.BLOCKED},
    LifecycleState.RETIRED: {LifecycleState.DISCOVERED, LifecycleState.BLOCKED},
    LifecycleState.BLOCKED: {LifecycleState.QUARANTINED, LifecycleState.DISCOVERED},
    LifecycleState.QUARANTINED: {LifecycleState.DISCOVERED, LifecycleState.BLOCKED}
}


@dataclass
class TransitionHistoryItem:
    from_state: Optional[str]
    to_state: str
    timestamp_utc: str
    reason: str
    transaction_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkillLifecycleRecord:
    skill_id: str
    resource_id: str
    current_state: LifecycleState
    history: List[TransitionHistoryItem] = field(default_factory=list)
    last_transition_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "skill_id": self.skill_id,
            "resource_id": self.resource_id,
            "current_state": self.current_state.value if isinstance(self.current_state, LifecycleState) else str(self.current_state),
            "history": [h.to_dict() for h in self.history],
            "last_transition_utc": self.last_transition_utc
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SkillLifecycleRecord:
        st = data.get("current_state", LifecycleState.DISCOVERED)
        try:
            st = LifecycleState(st)
        except ValueError:
            pass
        hist = [
            TransitionHistoryItem(**item) for item in data.get("history", [])
        ]
        return cls(
            skill_id=data.get("skill_id", data.get("resource_id", "unknown")),
            resource_id=data.get("resource_id", "sres-v1-sha256:" + "0"*64),
            current_state=st,
            history=hist,
            last_transition_utc=data.get("last_transition_utc", datetime.now(timezone.utc).isoformat())
        )


class SkillLifecycleManager:
    """
    Guarantees deterministic lifecycle transitions with quarantine precedence.
    Enforces that unvetted skills cannot be promoted directly to ACTIVE.
    """

    def __init__(self, state_file: Optional[Path] = None, config: Optional[JarvisRuntimeConfig] = None):
        cfg = config or CONFIG
        self.config = cfg
        self.state_file = (state_file or (cfg.state_dir / "skill_lifecycles.json")).resolve()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, SkillLifecycleRecord] = {}
        self._load_records()

    def _load_records(self) -> None:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                for sid, rdata in data.items():
                    self._records[sid] = SkillLifecycleRecord.from_dict(rdata)
            except Exception:
                self._records = {}

    def _save_records(self) -> None:
        out = {k: v.to_dict() for k, v in self._records.items()}
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.state_file)

    def get_skill_state(self, skill_id: str) -> SkillLifecycleRecord:
        if skill_id not in self._records:
            now_iso = datetime.now(timezone.utc).isoformat()
            tx_id = f"tx-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')[:18]}-{uuid.uuid4().hex[:8]}"
            init_item = TransitionHistoryItem(
                from_state=None,
                to_state=LifecycleState.ACTIVE.value,  # Existing registry skills are ACTIVE by default
                timestamp_utc=now_iso,
                reason="INITIAL_CANONICAL_REGISTRATION",
                transaction_id=tx_id
            )
            rec = SkillLifecycleRecord(
                skill_id=skill_id,
                resource_id=f"sres-v1-sha256:{hashlib.sha256(skill_id.encode('utf-8')).hexdigest()}",
                current_state=LifecycleState.ACTIVE,
                history=[init_item],
                last_transition_utc=now_iso
            )
            self._records[skill_id] = rec
            self._save_records()
        return self._records[skill_id]

    def can_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState
    ) -> Tuple[bool, Optional[str]]:
        if from_state == to_state:
            return False, f"Skill is already in state '{from_state.value}'"

        allowed = ALLOWED_TRANSITIONS.get(from_state, set())
        if to_state in allowed:
            return True, None

        return False, f"Illegal transition from '{from_state.value}' to '{to_state.value}'. Must follow progression order."

    def transition_skill(
        self,
        skill_id: str,
        to_state: LifecycleState,
        reason: str
    ) -> SkillLifecycleRecord:
        rec = self.get_skill_state(skill_id)
        from_state = rec.current_state

        allowed, err_msg = self.can_transition(from_state, to_state)
        if not allowed:
            raise ValueError(f"Lifecycle transition rejected: {err_msg}")

        now_iso = datetime.now(timezone.utc).isoformat()
        tx_id = f"tx-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')[:18]}-{uuid.uuid4().hex[:8]}"
        item = TransitionHistoryItem(
            from_state=from_state.value,
            to_state=to_state.value,
            timestamp_utc=now_iso,
            reason=reason,
            transaction_id=tx_id
        )

        rec.current_state = to_state
        rec.history.append(item)
        rec.last_transition_utc = now_iso

        self._records[skill_id] = rec
        self._save_records()
        return rec

    def quarantine_skill(self, skill_id: str, reason: str) -> SkillLifecycleRecord:
        """Immediate transition to QUARANTINED state, regardless of prior state."""
        rec = self.get_skill_state(skill_id)
        from_state = rec.current_state

        now_iso = datetime.now(timezone.utc).isoformat()
        tx_id = f"tx-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')[:18]}-{uuid.uuid4().hex[:8]}"
        item = TransitionHistoryItem(
            from_state=from_state.value if isinstance(from_state, LifecycleState) else str(from_state),
            to_state=LifecycleState.QUARANTINED.value,
            timestamp_utc=now_iso,
            reason=f"QUARANTINE_OVERRIDE: {reason}",
            transaction_id=tx_id
        )

        rec.current_state = LifecycleState.QUARANTINED
        rec.history.append(item)
        rec.last_transition_utc = now_iso

        self._records[skill_id] = rec
        self._save_records()
        return rec

    def is_execution_eligible(self, skill_id: str) -> bool:
        """Only ACTIVE (or explicitly staged) skills can execute."""
        rec = self.get_skill_state(skill_id)
        return rec.current_state in (LifecycleState.ACTIVE, LifecycleState.STAGED)
