"""
state_store.py // J.A.R.V.I.S. Authoritative Runtime State Store
Pure Python Standard Library (Zero PIP Dependencies)
Enforces:
- Section 4 Authoritative State Store (Single Source of Truth)
- Atomic File Swapping via save_json_atomic (.tmp -> .json)
- Fail-Closed Corrupted State Quarantine (moves invalid files to state/corrupted/)
- Clear separation: Authoritative State vs Audit Events vs Derived State vs Cache
"""

from __future__ import annotations
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from .models import Mission, MissionStatus, TaskStatus, RiskLevel, SCHEMA_VERSION, validate_schema_version
from .schema_migrations import migrate_mission_record
from .dag import save_json_atomic
from .config import CONFIG, JarvisRuntimeConfig
from .authorization import (
    AuthorizationDeniedError,
    AuthorizationGrantStore,
    task_authorization_context,
)


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

    def _annotate_recovery_authority(self, mission: Mission) -> None:
        """Attach non-persisted restart guards derived from current durable grants.

        These annotations are deliberately excluded from Mission/Task serialization.
        Loading state never rewrites authority or invents a grant; it only records
        whether the authority referenced by the durable task is still valid now.
        """
        grant_store = AuthorizationGrantStore(config=self.config)
        for task in mission.dag.nodes.values():
            if task.status == TaskStatus.VERIFIED:
                continue

            try:
                context = task_authorization_context(task, subject=task.agent_profile)
                risk = task.canonical_risk_level
                if risk == RiskLevel.R5_DESTRUCTIVE:
                    task._recovery_authority_error = "R5 destructive tasks are not replayable authority"
                    continue

                requires_grant = risk == RiskLevel.R4_INFRA_MUTATION
                if not requires_grant and context.grant_id is None:
                    continue

                grant_store.verify_task_grant(task, subject=task.agent_profile)
                task._recovery_authority_grant_id = context.grant_id
            except AuthorizationDeniedError as exc:
                reason = str(exc)
                if reason == "DURABLE_AUTHORIZATION_GRANT_REQUIRED":
                    task._recovery_authority_error = "Missing durable authorization grant for recovery"
                else:
                    task._recovery_authority_error = f"Authorization grant invalid during recovery: {reason}"

    def load_mission(self, mission_id: str) -> Optional[Mission]:
        """
        Loads a mission from the authoritative state directory.
        If the file is corrupt, isolates it into state/corrupted/ with diagnostics.
        Current durable authorization is revalidated as a non-persisted recovery
        guard before the mission can be replayed.
        """
        target_path = self.get_mission_path(mission_id)
        if not target_path.exists():
            return None

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data = migrate_mission_record(data)
            validate_schema_version(data)
            mission = Mission.from_dict(data)
            self._annotate_recovery_authority(mission)
            return mission
        except CorruptedStateFileError:
            raise
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

    @staticmethod
    def _mission_status_cache_file(missions_dir: Path) -> Path:
        import hashlib
        import tempfile

        key = hashlib.sha1(str(missions_dir.resolve()).encode("utf-8")).hexdigest()[:12]
        return Path(tempfile.gettempdir()) / f"jarvis_missions_status_v1_{key}.json"

    def list_active_missions(self) -> List[str]:
        """Lists IDs of all non-terminal (PENDING, PLANNING, RUNNING, SCHEDULED) missions."""
        active: List[str] = []
        if not self.missions_dir.exists():
            return active

        cache_path = self._mission_status_cache_file(self.missions_dir)
        cached_entries: Dict[str, Any] = {}
        try:
            if cache_path.is_file():
                loaded = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    cached_entries = loaded
        except Exception:
            cached_entries = {}

        active_statuses = {
            MissionStatus.PENDING.value,
            MissionStatus.PLANNING.value,
            MissionStatus.SCHEDULED.value,
            MissionStatus.RUNNING.value,
            MissionStatus.VERIFYING.value,
        }
        updated_entries: Dict[str, Any] = {}
        cache_dirty = False

        try:
            entries = sorted(
                (e for e in os.scandir(self.missions_dir) if e.name.endswith(".json")),
                key=lambda e: e.name,
            )
        except OSError:
            return active

        for entry in entries:
            try:
                st = entry.stat(follow_symlinks=False)
                sig = [st.st_mtime_ns, st.st_size]
                prev = cached_entries.get(entry.name)
                if (
                    isinstance(prev, list)
                    and len(prev) == 4
                    and prev[0] == sig[0]
                    and prev[1] == sig[1]
                ):
                    mission_id, status = prev[2], prev[3]
                    updated_entries[entry.name] = prev
                else:
                    with open(entry.path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    status = data.get("status")
                    mission_id = data.get("mission_id", entry.name[:-5])
                    updated_entries[entry.name] = [sig[0], sig[1], mission_id, status]
                    cache_dirty = True
                if status in active_statuses:
                    active.append(mission_id)
            except Exception:
                continue

        if cache_dirty or len(updated_entries) != len(cached_entries):
            try:
                cache_path.write_text(
                    json.dumps(updated_entries, separators=(",", ":")),
                    encoding="utf-8",
                )
            except Exception:
                pass
        return active

    def delete_mission(self, mission_id: str) -> bool:
        p = self.get_mission_path(mission_id)
        if p.exists():
            p.unlink()
            return True
        return False
