"""
state_store.py // J.A.R.V.I.S. Authoritative Runtime State Store
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- Section 4 Authoritative State Store (Single Source of Truth)
- Atomic File Swapping via save_json_atomic (.tmp -> .json)
- Fail-Closed Corrupted State Quarantine (moves invalid files to state/corrupted/)
- Clear separation: Authoritative State vs Audit Events vs Derived State vs Cache
"""

from __future__ import annotations
import os
import json
import time
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import Mission, MissionStatus, SCHEMA_VERSION, validate_schema_version
from .dag import save_json_atomic
from .config import CONFIG, JarvisRuntimeConfig


class CorruptedStateFileError(RuntimeError):
    """Raised when an authoritative state file fails parsing and is quarantined."""
    def __init__(self, original_path: Path, quarantine_path: Path, reason: str):
        super().__init__(f"Corrupted state file quarantined: {original_path.name} -> {quarantine_path.name} ({reason})")
        self.original_path = original_path
        self.quarantine_path = quarantine_path
        self.reason = reason


class AuthoritativeStateStore:
    """
    Authoritative state storage manager for missions and runtime DAGs.
    Guarantees atomic persistence, single-source-of-truth semantics, and corruption quarantine.
    """

    def __init__(self, config: Optional[JarvisRuntimeConfig] = None):
        self.config = config or CONFIG
        self.missions_dir = self.config.missions_dir
        self.corrupted_dir = self.config.corrupted_dir
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.corrupted_dir.mkdir(parents=True, exist_ok=True)

    def get_mission_path(self, mission_id: str) -> Path:
        # Sanitize filename
        safe_id = "".join(c for c in mission_id if c.isalnum() or c in "-_")
        return self.missions_dir / f"{safe_id}.json"

    def save_mission(self, mission: Mission) -> Path:
        """Persists mission state atomically to disk."""
        target_path = self.get_mission_path(mission.mission_id)
        data = mission.to_dict()
        save_json_atomic(target_path, data)
        return target_path

    def load_mission(self, mission_id: str) -> Optional[Mission]:
        """
        Loads a mission from the authoritative state directory.
        If the file is corrupt, isolates it into state/corrupted/ with diagnostics.
        """
        target_path = self.get_mission_path(mission_id)
        if not target_path.exists():
            return None

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validate_schema_version(data)
            return Mission.from_dict(data)
        except Exception as e:
            # Corrupted State Quarantine
            quarantine_path = self._quarantine_corrupted_file(target_path, reason=str(e))
            raise CorruptedStateFileError(target_path, quarantine_path, reason=str(e))

    def _quarantine_corrupted_file(self, target_path: Path, reason: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest_filename = f"{timestamp}_{target_path.name}"
        quarantine_target = self.corrupted_dir / dest_filename

        try:
            shutil.move(str(target_path), str(quarantine_target))
        except Exception:
            # Fallback if move fails (e.g. cross-device)
            shutil.copy2(str(target_path), str(quarantine_target))
            target_path.unlink(missing_ok=True)

        # Write diagnostic metadata
        diag_path = self.corrupted_dir / f"{dest_filename}.diagnostic.json"
        diag_data = {
            "schema_version": SCHEMA_VERSION,
            "corrupted_filename": target_path.name,
            "quarantined_utc": datetime.now(timezone.utc).isoformat(),
            "failure_reason": reason,
            "quarantine_path": str(quarantine_target)
        }
        try:
            with open(diag_path, "w", encoding="utf-8") as f:
                json.dump(diag_data, f, indent=2)
        except Exception:
            pass

        return quarantine_target

    def list_active_missions(self) -> List[str]:
        """Lists IDs of all non-terminal (PENDING, PLANNING, RUNNING, SCHEDULED) missions."""
        active = []
        if not self.missions_dir.exists():
            return active

        for item in sorted(self.missions_dir.glob("*.json")):
            try:
                with open(item, "r", encoding="utf-8") as f:
                    data = json.load(f)
                status = data.get("status")
                if status in (
                    MissionStatus.PENDING.value,
                    MissionStatus.PLANNING.value,
                    MissionStatus.SCHEDULED.value,
                    MissionStatus.RUNNING.value,
                    MissionStatus.VERIFYING.value
                ):
                    active.append(data.get("mission_id", item.stem))
            except Exception:
                continue
        return active

    def delete_mission(self, mission_id: str) -> bool:
        p = self.get_mission_path(mission_id)
        if p.exists():
            p.unlink()
            return True
        return False
