"""
resilience.py // J.A.R.V.I.S. Failure Recovery & Restart Resilience Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces Section 7 Persistence & Recovery Invariants:
- Atomic JSON checkpointing for Missions, DAGs, and Tasks
- Strict idempotency: VERIFIED tasks are never re-executed on restart
- Automatic recovery of interrupted (RUNNING) tasks with retry counting
- Validation of restored state to handle corrupt or incomplete checkpoints
"""

from __future__ import annotations
import os
import json
import uuid
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import (
    Mission,
    MissionStatus,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
    VerificationStatus,
    RiskLevel,
    IdempotencySemantics
)
from .dag import ExecutionDAG
from .config import CONFIG, JarvisRuntimeConfig


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
CHECKPOINTS_DIR = REGISTRY_ROOT / "state" / "checkpoints"


@dataclass
class MissionCheckpoint:
    checkpoint_id: str
    mission_id: str
    schema_version: str = "1.0.0"
    saved_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "RUNNING"
    current_wave: int = 0
    active_task_ids: List[str] = field(default_factory=list)
    dag_snapshot: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "mission_id": self.mission_id,
            "schema_version": self.schema_version,
            "saved_utc": self.saved_utc,
            "status": self.status,
            "current_wave": self.current_wave,
            "active_task_ids": self.active_task_ids,
            "dag_snapshot": self.dag_snapshot,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MissionCheckpoint:
        return cls(
            checkpoint_id=data["checkpoint_id"],
            mission_id=data["mission_id"],
            schema_version=data.get("schema_version", "1.0.0"),
            saved_utc=data.get("saved_utc", datetime.now(timezone.utc).isoformat()),
            status=data.get("status", "RUNNING"),
            current_wave=data.get("current_wave", 0),
            active_task_ids=list(data.get("active_task_ids", [])),
            dag_snapshot=data.get("dag_snapshot", {}),
            metadata=data.get("metadata", {})
        )


class CheckpointManager:
    """
    Manages persistent checkpoints for missions and execution DAGs.
    Guarantees seamless restart recovery without re-running verified tasks.
    """

    def __init__(self, checkpoints_dir: Optional[Path] = None, config: Optional[JarvisRuntimeConfig] = None):
        cfg = config or CONFIG
        self.config = cfg
        self.checkpoints_dir = (checkpoints_dir or (cfg.state_dir / "checkpoints")).resolve()
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        mission: Mission,
        dag: ExecutionDAG,
        current_wave: int = 0,
        active_task_ids: Optional[List[str]] = None,
        checkpoint_id: Optional[str] = None
    ) -> MissionCheckpoint:
        chk_id = checkpoint_id or f"chk-{mission.mission_id}-{int(time.time()*1000)}"
        active = active_task_ids or [
            t.task_id for t in dag.nodes.values() if t.status in (TaskStatus.RUNNING, TaskStatus.READY)
        ]

        checkpoint = MissionCheckpoint(
            checkpoint_id=chk_id,
            mission_id=mission.mission_id,
            status=str(mission.status.value if isinstance(mission.status, MissionStatus) else mission.status),
            current_wave=current_wave,
            active_task_ids=active,
            dag_snapshot=dag.to_dict(),
            metadata={"goal": mission.goal}
        )

        file_path = self.checkpoints_dir / f"{chk_id}.json"
        tmp_path = self.checkpoints_dir / f"{chk_id}.tmp"

        # Atomic write
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)
        tmp_path.replace(file_path)

        return checkpoint

    def load_checkpoint(self, checkpoint_id: str) -> Tuple[Mission, ExecutionDAG, int]:
        file_path = self.checkpoints_dir / f"{checkpoint_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {file_path}")

        data = json.loads(file_path.read_text(encoding="utf-8"))
        chk = MissionCheckpoint.from_dict(data)

        # Restore DAG
        dag = ExecutionDAG.from_dict(chk.dag_snapshot)

        # Restore Mission
        mission_status = chk.status
        try:
            mission_status = MissionStatus(mission_status)
        except ValueError:
            pass

        mission = Mission(
            mission_id=chk.mission_id,
            goal=chk.metadata.get("goal", ""),
            status=mission_status
        )
        mission.dag = dag

        return mission, dag, chk.current_wave

    def recover_mission(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Recovers a mission after process interruption or failure:
        - Leaves VERIFIED tasks untouched (idempotency).
        - Recovers RUNNING tasks back to READY if retry_count < max_retries.
        - Increments retry_count.
        - Marks FAILED if retries are exhausted.
        """
        mission, dag, current_wave = self.load_checkpoint(checkpoint_id)
        recovered_tasks: List[str] = []
        exhausted_tasks: List[str] = []
        untouched_verified_tasks: List[str] = []

        for task_id, task in dag.nodes.items():
            if task.status == TaskStatus.VERIFIED:
                untouched_verified_tasks.append(task_id)
                continue

            if task.status in (TaskStatus.RUNNING, TaskStatus.PENDING, TaskStatus.READY, TaskStatus.FAILED):
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.READY
                    recovered_tasks.append(task_id)
                else:
                    task.status = TaskStatus.FAILED
                    exhausted_tasks.append(task_id)

        # Save recovered state back
        self.save_checkpoint(
            mission=mission,
            dag=dag,
            current_wave=current_wave,
            active_task_ids=recovered_tasks,
            checkpoint_id=checkpoint_id
        )

        return {
            "checkpoint_id": checkpoint_id,
            "mission_id": mission.mission_id,
            "recovered_tasks": recovered_tasks,
            "exhausted_tasks": exhausted_tasks,
            "untouched_verified_tasks": untouched_verified_tasks,
            "current_wave": current_wave,
            "dag_ready": len(dag.get_ready_tasks()) > 0 or dag.is_complete()
        }

    @staticmethod
    def can_automatically_compensate(record: Any) -> bool:
        """
        Validates mandatory rule: NO PROVENANCE -> NO AUTOMATIC COMPENSATION.
        Requires both a non-empty provenance_hash and compensation_action.
        """
        prov = getattr(record, "provenance_hash", None) or (record.get("provenance_hash") if isinstance(record, dict) else None)
        action = getattr(record, "compensation_action", None) or (record.get("compensation_action") if isinstance(record, dict) else None)
        return bool(prov and action)

    def generate_compensating_action_dag(self, failed_task: TaskNode, base_dir: Optional[Path] = None) -> Optional[ExecutionDAG]:
        """
        Generates a compensating DAG for rollback if a task fails after mutating files.
        Enforces Table in Section 8 (REQUIRES_COMPENSATION).
        Strictly enforces: NO PROVENANCE -> NO AUTOMATIC COMPENSATION.
        """
        if not failed_task.write_scopes:
            return None

        # If attempts exist, check side effects provenance
        if failed_task.attempts:
            for att in failed_task.attempts:
                for se in att.side_effects:
                    idemp = getattr(se, "idempotency", None)
                    idemp_str = idemp.value if hasattr(idemp, "value") else str(idemp)
                    if idemp_str == "COMPENSATION_REQUIRED":
                        if not self.can_automatically_compensate(se):
                            return None

        comp_dag = ExecutionDAG()
        clean_task = TaskNode(
            task_id=f"compensate-{failed_task.task_id}",
            title=f"Rollback mutations for {failed_task.task_id}",
            description=f"Compensating action cleaning up unverified write scopes: {failed_task.write_scopes}",
            agent_profile="Quantum-ExecutorAgent",
            read_scopes=failed_task.read_scopes,
            write_scopes=failed_task.write_scopes,
            risk_level=RiskLevel.R1_LOCAL_WRITE
        )
        comp_dag.add_node(clean_task)
        return comp_dag


class ReplayEngine:
    """
    Enforces replay safety, idempotency validation, and side-effect guarantees:
    - Never re-executes VERIFIED tasks (strict idempotency).
    - Blocks replay if task generated UNSAFE_TO_RETRY side-effects.
    - Blocks replay if task side-effect requires compensation but lacks provenance or compensating action.
    - Guards against replaying tasks with already-committed idempotency keys.
    - Enforces retry limits (max_retries).
    - Safely replays eligible tasks back to TaskStatus.READY.
    """

    def __init__(self, executed_idempotency_keys: Optional[Set[str]] = None):
        self._executed_keys: Set[str] = set(executed_idempotency_keys or [])

    def register_idempotency_key(self, key: str) -> None:
        if key:
            self._executed_keys.add(key)

    def has_idempotency_key(self, key: str) -> bool:
        return key in self._executed_keys

    def can_replay_task(self, task: TaskNode) -> Tuple[bool, str]:
        """
        Evaluates whether a task can be safely replayed.
        Returns (can_replay: bool, reason: str).
        """
        # 1. VERIFIED tasks must never be re-executed
        if task.status == TaskStatus.VERIFIED:
            return False, f"Task '{task.task_id}' is already VERIFIED (strict idempotency: verified tasks must never be re-executed)"

        # 2. Check retry bounds
        if task.retry_count >= task.max_retries:
            return False, f"Task '{task.task_id}' has exhausted max retries ({task.max_retries})"

        # 3. Check task action/metadata idempotency key
        task_idem_key = ""
        if task.action and isinstance(task.action, dict):
            task_idem_key = task.action.get("idempotency_key", "")
        if task_idem_key and task_idem_key in self._executed_keys:
            return False, f"Task '{task.task_id}' specifies already-executed idempotency key '{task_idem_key}'"

        # 4. Check past execution attempts and side-effects
        if task.attempts:
            for att in task.attempts:
                # If attempt had an idempotency key that already completed elsewhere
                if att.idempotency_key and att.idempotency_key in self._executed_keys:
                    return False, f"Task attempt already committed under idempotency key '{att.idempotency_key}'"

                for se in att.side_effects:
                    idemp = getattr(se, "idempotency", None)
                    idemp_str = idemp.value if hasattr(idemp, "value") else str(idemp)

                    if idemp_str == IdempotencySemantics.UNSAFE_TO_RETRY.value:
                        return False, f"Task '{task.task_id}' produced UNSAFE_TO_RETRY side effect '{se.side_effect_id}'"

                    if idemp_str == IdempotencySemantics.COMPENSATION_REQUIRED.value:
                        if not CheckpointManager.can_automatically_compensate(se):
                            return False, f"Task '{task.task_id}' produced side effect '{se.side_effect_id}' requiring compensation without valid provenance"

        # 5. Read-only tasks without side-effect issues are naturally idempotent
        if task.canonical_risk_level == RiskLevel.R0_READ_ONLY:
            return True, "Read-only task is naturally idempotent"

        return True, "Task is safe for replay"

    def replay_mission_dag(self, dag: ExecutionDAG, force: bool = False) -> Dict[str, Any]:
        """
        Scans all DAG nodes, validates replay safety, and prepares eligible tasks for execution.
        Preserves VERIFIED tasks untouched.
        """
        verified_preserved: List[str] = []
        replayed_tasks: List[str] = []
        blocked_tasks: List[Dict[str, str]] = []

        for task_id, task in dag.nodes.items():
            if task.status == TaskStatus.VERIFIED:
                verified_preserved.append(task_id)
                continue

            can_replay, reason = self.can_replay_task(task)
            if can_replay:
                task.status = TaskStatus.READY
                if task.retry_count > 0 or task.attempts:
                    task.retry_count += 1
                replayed_tasks.append(task_id)
            else:
                blocked_tasks.append({"task_id": task_id, "reason": reason})

        return {
            "eligible_count": len(replayed_tasks),
            "replayed_tasks": replayed_tasks,
            "verified_preserved": verified_preserved,
            "blocked_tasks": blocked_tasks,
            "all_safe": len(blocked_tasks) == 0
        }

