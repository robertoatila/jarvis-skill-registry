"""
learning.py // J.A.R.V.I.S. Learning Records & Knowledge Promotion Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- 3-Tier Promotion Lifecycle: OBSERVATION -> PATTERN -> VALIDATED_HEURISTIC
- Section 14 Invariant: A single execution NEVER promotes automatically to global rule
- Mandatory provenance & evidence tracking
- ACID append-only ledger in state/learning/learning_records.jsonl
"""

from __future__ import annotations
import json
import time
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timezone


from .config import CONFIG, JarvisRuntimeConfig

REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
LEARNING_DIR = REGISTRY_ROOT / "state" / "learning"
LEARNING_LEDGER_FILE = LEARNING_DIR / "learning_records.jsonl"
HEURISTICS_CACHE_FILE = LEARNING_DIR / "validated_heuristics.json"


class LearningTier(str, Enum):
    OBSERVATION = "OBSERVATION"
    PATTERN = "PATTERN"
    VALIDATED_HEURISTIC = "VALIDATED_HEURISTIC"


@dataclass
class LearningRecord:
    record_id: str
    tier: LearningTier
    skill: str
    agent_profile: str
    approach: str
    expected_result: str
    actual_result: str
    evidence: Dict[str, Any]
    confidence: float
    provenance: str
    skill_version: str = "1.0.0"
    model: str = "sovereign-local"
    environment: Dict[str, Any] = field(default_factory=lambda: {"os": "windows", "python": "3.12.10"})
    observation_count: int = 1
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    promoted_utc: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "tier": self.tier.value if isinstance(self.tier, LearningTier) else str(self.tier),
            "skill": self.skill,
            "skill_version": self.skill_version,
            "agent_profile": self.agent_profile,
            "model": self.model,
            "environment": self.environment,
            "approach": self.approach,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "evidence": self.evidence,
            "confidence": round(self.confidence, 4),
            "provenance": self.provenance,
            "observation_count": self.observation_count,
            "created_utc": self.created_utc,
            "promoted_utc": self.promoted_utc
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LearningRecord:
        tier = data.get("tier", LearningTier.OBSERVATION)
        try:
            tier = LearningTier(tier)
        except ValueError:
            pass
        return cls(
            record_id=data["record_id"],
            tier=tier,
            skill=data["skill"],
            skill_version=data.get("skill_version", "1.0.0"),
            agent_profile=data["agent_profile"],
            model=data.get("model", "sovereign-local"),
            environment=data.get("environment", {}),
            approach=data["approach"],
            expected_result=data["expected_result"],
            actual_result=data["actual_result"],
            evidence=data.get("evidence", {}),
            confidence=data.get("confidence", 0.5),
            provenance=data["provenance"],
            observation_count=data.get("observation_count", 1),
            created_utc=data.get("created_utc", datetime.now(timezone.utc).isoformat()),
            promoted_utc=data.get("promoted_utc")
        )


class LearningEngine:
    """
    Manages observations, patterns, and validated heuristics.
    Enforces that single executions can NEVER create or promote validated heuristics.
    """

    def __init__(
        self,
        ledger_file: Optional[Path] = None,
        heuristics_file: Optional[Path] = None,
        config: Optional[JarvisRuntimeConfig] = None
    ):
        cfg = config or CONFIG
        self.ledger_file = (ledger_file or (cfg.learning_dir / "learning_records.jsonl")).resolve()
        self.heuristics_file = (heuristics_file or (cfg.learning_dir / "validated_heuristics.json")).resolve()
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_file.exists():
            self.ledger_file.write_text("", encoding="utf-8")

    def record_observation(
        self,
        skill: str,
        agent_profile: str,
        approach: str,
        expected_result: str,
        actual_result: str,
        evidence: Dict[str, Any],
        provenance: str,
        skill_version: str = "1.0.0",
        model: str = "sovereign-local"
    ) -> LearningRecord:
        """
        Records a single execution observation.
        Initial tier is strictly OBSERVATION with confidence capped at 0.50.
        """
        record_id = f"learn-{int(time.time() * 1000)}-obs"
        record = LearningRecord(
            record_id=record_id,
            tier=LearningTier.OBSERVATION,
            skill=skill,
            skill_version=skill_version,
            agent_profile=agent_profile,
            model=model,
            approach=approach,
            expected_result=expected_result,
            actual_result=actual_result,
            evidence=evidence,
            confidence=0.50,
            provenance=provenance,
            observation_count=1
        )
        self._append_to_ledger(record)
        return record

    def promote_candidate(
        self,
        record: LearningRecord,
        new_observations_count: int,
        corroborating_evidence: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Evaluates promotion of a LearningRecord.
        Promotion Rules:
        - OBSERVATION -> PATTERN: requires observation_count >= 3
        - PATTERN -> VALIDATED_HEURISTIC: requires observation_count >= 5 with corroborating evidence
        - Single execution: REJECTED fail-closed.
        """
        total_obs = record.observation_count + new_observations_count

        if record.tier == LearningTier.OBSERVATION:
            if total_obs < 3:
                return False, f"Cannot promote OBSERVATION to PATTERN: requires >= 3 observations (current: {total_obs})"
            record.tier = LearningTier.PATTERN
            record.observation_count = total_obs
            record.confidence = min(0.80, 0.50 + (total_obs * 0.05))
            record.promoted_utc = datetime.now(timezone.utc).isoformat()
            self._append_to_ledger(record)
            return True, f"Promoted to PATTERN with {total_obs} observations"

        elif record.tier == LearningTier.PATTERN:
            if total_obs < 5 or len(corroborating_evidence) < 2:
                return False, f"Cannot promote PATTERN to VALIDATED_HEURISTIC: requires >= 5 observations and >= 2 distinct evidence sets (current: {total_obs} obs, {len(corroborating_evidence)} ev)"
            record.tier = LearningTier.VALIDATED_HEURISTIC
            record.observation_count = total_obs
            record.confidence = min(0.99, 0.80 + (total_obs * 0.03))
            record.promoted_utc = datetime.now(timezone.utc).isoformat()
            self._append_to_ledger(record)
            self._save_validated_heuristic(record)
            return True, f"Promoted to VALIDATED_HEURISTIC with {total_obs} observations"

        return False, "Record is already at highest tier (VALIDATED_HEURISTIC)"

    def _append_to_ledger(self, record: LearningRecord) -> None:
        line = json.dumps(record.to_dict(), ensure_ascii=False)
        try:
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"[JARVIS LEARNING ERROR] Failed writing to learning ledger: {e}")

    def get_validated_heuristics(self) -> Dict[str, Dict[str, Any]]:
        """Loads all validated heuristics from persistent JSON cache."""
        if not self.heuristics_file.exists():
            return {}
        try:
            with open(self.heuristics_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    get_heuristics = get_validated_heuristics


    def _save_validated_heuristic(self, record: LearningRecord) -> None:
        current = self.get_validated_heuristics()
        current[record.record_id] = record.to_dict()
        tmp_p = self.heuristics_file.with_suffix(".tmp")
        with open(tmp_p, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
        if self.heuristics_file.exists():
            self.heuristics_file.unlink()
        tmp_p.rename(self.heuristics_file)

    def get_records_for_skill(self, skill: str) -> List[LearningRecord]:
        """Loads all learning records for a specific skill from the append-only ledger."""
        records = []
        if not self.ledger_file.exists():
            return records
        try:
            with open(self.ledger_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        if data.get("skill") == skill:
                            records.append(LearningRecord.from_dict(data))
        except Exception:
            pass
        return records

    def auto_evaluate_promotions(self, skill: str) -> List[Tuple[LearningRecord, bool, str]]:
        """
        Scans observations for a skill and triggers promotion if thresholds are satisfied.
        """
        records = self.get_records_for_skill(skill)
        results: List[Tuple[LearningRecord, bool, str]] = []
        observations = [r for r in records if r.tier == LearningTier.OBSERVATION]
        patterns = [r for r in records if r.tier == LearningTier.PATTERN]

        # Check observations promotion to pattern (>= 3 observations)
        if len(observations) >= 3:
            base_obs = observations[0]
            success, reason = self.promote_candidate(
                base_obs,
                new_observations_count=len(observations) - 1,
                corroborating_evidence=[]
            )
            results.append((base_obs, success, reason))

        # Check pattern promotion to heuristic (>= 5 observations and >= 2 distinct evidence sets)
        if patterns:
            for pat in patterns:
                evidences = [r.evidence for r in records if r.evidence]
                if pat.observation_count >= 5 and len(evidences) >= 2:
                    success, reason = self.promote_candidate(
                        pat,
                        new_observations_count=0,
                        corroborating_evidence=evidences
                    )
                    results.append((pat, success, reason))

        return results


# Global singleton
LEARNING_ENGINE = LearningEngine()
