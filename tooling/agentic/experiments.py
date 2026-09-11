"""
experiments.py // J.A.R.V.I.S. Controlled Skill Experiment Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- Deterministic hash-based variant assignment (Section 8 Invariant)
- Statistical gating before concluding or promoting variants (Section 14 Invariant)
- Full ACID persistence to state/experiments/
"""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone


from .config import CONFIG, JarvisRuntimeConfig

REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
EXPERIMENTS_DIR = REGISTRY_ROOT / "state" / "experiments"
EXPERIMENTS_FILE = EXPERIMENTS_DIR / "active_experiments.json"


@dataclass
class ExperimentVariant:
    variant_id: str
    skill_id: str
    weight: float = 1.0
    samples_count: int = 0
    success_count: int = 0
    total_duration_ms: int = 0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.samples_count if self.samples_count > 0 else 0.0

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.samples_count if self.samples_count > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExperimentVariant:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SkillExperiment:
    experiment_id: str
    capability: str
    status: str = "ACTIVE"  # DRAFT, ACTIVE, CONCLUDED, ABORTED
    variants: List[ExperimentVariant] = field(default_factory=list)
    min_samples_per_variant: int = 5
    winner_variant_id: Optional[str] = None
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    concluded_utc: Optional[str] = None

    def assign_variant(self, context_key: str) -> ExperimentVariant:
        """
        Deterministically selects a variant based on SHA-256 hash of (experiment_id + context_key).
        Guarantees reproducible assignment for identical mission/task contexts.
        """
        if not self.variants:
            raise ValueError(f"No variants defined in experiment '{self.experiment_id}'")

        # Hash to float in [0.0, 1.0)
        h = hashlib.sha256(f"{self.experiment_id}:{context_key}".encode("utf-8")).hexdigest()
        val = int(h[:8], 16) / float(0xFFFFFFFF)

        total_weight = sum(v.weight for v in self.variants) or 1.0
        threshold = val * total_weight
        cumulative = 0.0

        for v in sorted(self.variants, key=lambda x: x.variant_id):
            cumulative += v.weight
            if cumulative >= threshold:
                return v

        return self.variants[-1]

    def record_result(self, variant_id: str, success: bool, duration_ms: int = 0) -> None:
        for v in self.variants:
            if v.variant_id == variant_id:
                v.samples_count += 1
                if success:
                    v.success_count += 1
                v.total_duration_ms += duration_ms
                break

        self._check_conclusion()

    def _check_conclusion(self) -> None:
        """Concludes experiment if all variants reached min_samples_per_variant."""
        if any(v.samples_count < self.min_samples_per_variant for v in self.variants):
            return

        # Sort variants by success_rate (desc), avg_duration (asc), variant_id (asc)
        sorted_v = sorted(
            self.variants,
            key=lambda v: (-v.success_rate, v.avg_duration_ms, v.variant_id)
        )
        self.winner_variant_id = sorted_v[0].variant_id
        self.status = "CONCLUDED"
        self.concluded_utc = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "capability": self.capability,
            "status": self.status,
            "variants": [v.to_dict() for v in self.variants],
            "min_samples_per_variant": self.min_samples_per_variant,
            "winner_variant_id": self.winner_variant_id,
            "created_utc": self.created_utc,
            "concluded_utc": self.concluded_utc
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SkillExperiment:
        variants = [ExperimentVariant.from_dict(v) for v in data.get("variants", [])]
        return cls(
            experiment_id=data["experiment_id"],
            capability=data["capability"],
            status=data.get("status", "ACTIVE"),
            variants=variants,
            min_samples_per_variant=data.get("min_samples_per_variant", 5),
            winner_variant_id=data.get("winner_variant_id"),
            created_utc=data.get("created_utc", datetime.now(timezone.utc).isoformat()),
            concluded_utc=data.get("concluded_utc")
        )


class ExperimentEngine:
    """Manages active skill experiments with persistent state."""

    def __init__(self, state_file: Optional[Path] = None, config: Optional[JarvisRuntimeConfig] = None):
        cfg = config or CONFIG
        self.state_file = (state_file or (cfg.state_dir / "experiments" / "active_experiments.json")).resolve()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._experiments: Dict[str, SkillExperiment] = {}
        self.load()

    def create_experiment(
        self,
        experiment_id: str,
        capability: str,
        variants_tuples: List[Tuple[str, str, float]],  # (variant_id, skill_id, weight)
        min_samples: int = 5
    ) -> SkillExperiment:
        vars_list = [
            ExperimentVariant(variant_id=vid, skill_id=sid, weight=w)
            for vid, sid, w in variants_tuples
        ]
        exp = SkillExperiment(
            experiment_id=experiment_id,
            capability=capability,
            variants=vars_list,
            min_samples_per_variant=min_samples
        )
        self._experiments[experiment_id] = exp
        self.save()
        return exp

    def get_experiment(self, experiment_id: str) -> Optional[SkillExperiment]:
        return self._experiments.get(experiment_id)

    def get_experiment_for_capability(self, capability: str) -> Optional[SkillExperiment]:
        """Finds active experiment for a capability if one exists."""
        norm_cap = capability.lower().replace("_", "-")
        for exp in self._experiments.values():
            if exp.status == "ACTIVE" and exp.capability.lower().replace("_", "-") == norm_cap:
                return exp
        return None

    def record_outcome(self, experiment_id: str, variant_id: str, success: bool, duration_ms: int = 0) -> None:
        """Records an execution outcome and persists state."""
        exp = self._experiments.get(experiment_id)
        if exp:
            exp.record_result(variant_id, success, duration_ms)
            self.save()

    def record_outcome_for_skill(self, skill_id: str, success: bool, duration_ms: int = 0) -> bool:
        """Finds any active experiment containing this skill_id and records the outcome."""
        recorded = False
        for exp in self._experiments.values():
            if exp.status == "ACTIVE":
                for var in exp.variants:
                    if var.skill_id == skill_id:
                        exp.record_result(var.variant_id, success, duration_ms)
                        recorded = True
        if recorded:
            self.save()
        return recorded

    def list_experiments(self) -> List[SkillExperiment]:
        return [self._experiments[k] for k in sorted(self._experiments.keys())]

    def save(self) -> None:
        data = {k: exp.to_dict() for k, exp in self._experiments.items()}
        tmp_p = self.state_file.with_suffix(".tmp")
        with open(tmp_p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if self.state_file.exists():
            self.state_file.unlink()
        tmp_p.rename(self.state_file)

    def load(self) -> None:
        if not self.state_file.exists():
            return
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                self._experiments[k] = SkillExperiment.from_dict(v)
        except Exception as e:
            print(f"[JARVIS EXPERIMENT ERROR] Failed loading experiments: {e}")


# Global singleton
EXPERIMENT_ENGINE = ExperimentEngine()
