"""
scheduler.py // J.A.R.V.I.S. Wave Scheduler & Concurrency Isolation Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- READ(A) + READ(A) = ALLOWED
- WRITE(A) + WRITE(A) = CONFLICT
- WRITE(A) + READ(A)  = CONFLICT
- Scope hierarchical containment (e.g., 'src/' conflicts with 'src/main.py')
- Agent capacity bounds & deterministic wave ordering
"""

from __future__ import annotations
import os
import json
import posixpath
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone
from pathlib import PurePath

from .models import TaskNode, TaskStatus, _nonnegative
from .dag import ExecutionDAG


def normalize_scope(scope: str) -> str:
    """Normalizes path-like or logical resource scope for consistent matching."""
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("Scope must be a nonempty string")
    s = posixpath.normpath(scope.strip().replace("\\", "/"))
    return s.lower() if os.name == "nt" else s


def scopes_conflict(scope_a: str, scope_b: str) -> bool:
    """
    Returns True if scope_a and scope_b overlap (exact match or parent/child hierarchy).
    Example: 'src' and 'src/main.py' conflict.
    """
    na = normalize_scope(scope_a)
    nb = normalize_scope(scope_b)

    if na == nb:
        return True
    if na == "." or nb == ".":
        return True
    if na == "/" and nb.startswith("/") or nb == "/" and na.startswith("/"):
        return True

    # Check hierarchical prefix
    # 'src' overlaps with 'src/sub' if na + '/' is prefix of nb
    if nb.startswith(na + "/"):
        return True
    if na.startswith(nb + "/"):
        return True

    return False


def has_concurrency_conflict(task_a: TaskNode, task_b: TaskNode) -> Tuple[bool, str]:
    """
    Checks if task_a and task_b conflict according to Section 9 of the Protocol:
    WRITE(A) + WRITE(A) = CONFLICT
    WRITE(A) + READ(A)  = CONFLICT
    READ(A)  + WRITE(A) = CONFLICT
    READ(A)  + READ(A)  = ALLOWED
    """
    # 1. WRITE + WRITE conflict
    for wa in task_a.write_scopes:
        for wb in task_b.write_scopes:
            if scopes_conflict(wa, wb):
                return True, f"WRITE-WRITE conflict on scope: '{wa}' vs '{wb}'"

    # 2. WRITE(A) + READ(B) conflict
    for wa in task_a.write_scopes:
        for rb in task_b.read_scopes:
            if scopes_conflict(wa, rb):
                return True, f"WRITE-READ conflict on scope: '{wa}' vs '{rb}'"

    # 3. READ(A) + WRITE(B) conflict
    for ra in task_a.read_scopes:
        for wb in task_b.write_scopes:
            if scopes_conflict(ra, wb):
                return True, f"READ-WRITE conflict on scope: '{ra}' vs '{wb}'"

    return False, ""


@dataclass
class Wave:
    wave_index: int
    tasks: List[TaskNode] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    rejections: Dict[str, str] = field(default_factory=dict)

    @property
    def task_ids(self) -> List[str]:
        return [t.task_id for t in self.tasks]

    @property
    def read_scopes(self) -> List[str]:
        res: Set[str] = set()
        for t in self.tasks:
            res.update(t.read_scopes)
        return sorted(res)

    @property
    def write_scopes(self) -> List[str]:
        res: Set[str] = set()
        for t in self.tasks:
            res.update(t.write_scopes)
        return sorted(res)

    @property
    def agent_assignments(self) -> Dict[str, str]:
        return {t.task_id: t.agent_profile for t in self.tasks}

    def can_accept_task(
        self,
        candidate: TaskNode,
        max_parallel: int = 4,
        allow_agent_concurrency: bool = False
    ) -> Tuple[bool, str]:
        """Validates if candidate can be safely packed into this Wave."""
        if len(self.tasks) >= max_parallel:
            return False, f"Wave capacity limit reached ({max_parallel})"

        # Agent profile concurrency check
        if not allow_agent_concurrency:
            for existing in self.tasks:
                if existing.agent_profile == candidate.agent_profile:
                    return False, f"Agent '{candidate.agent_profile}' is already occupied in this wave by task '{existing.task_id}'"

        # Concurrency scope conflicts check
        for existing in self.tasks:
            conflict, reason = has_concurrency_conflict(existing, candidate)
            if conflict:
                return False, reason

        return True, ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wave_index": self.wave_index,
            "task_ids": self.task_ids,
            "status": self.status,
            "read_scopes": self.read_scopes,
            "write_scopes": self.write_scopes,
            "agent_assignments": self.agent_assignments
            ,"node_assignments": {t.task_id: t.node_id for t in self.tasks},
            "rejections": dict(sorted(self.rejections.items()))
        }


class WaveScheduler:
    """
    Schedules an ExecutionDAG into an ordered series of conflict-free execution Waves.
    Strictly deterministic and capacity-aware.
    """

    def __init__(
        self,
        max_parallel_tasks: int = 4,
        allow_agent_concurrency: bool = False,
        agent_capacities: Optional[Dict[str, int]] = None,
        node_capacities: Optional[Dict[str, int]] = None
    ):
        limits = [max_parallel_tasks, *(agent_capacities or {}).values(), *(node_capacities or {}).values()]
        if any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in limits):
            raise ValueError("Scheduling capacities must be positive integers")
        self.max_parallel_tasks = max_parallel_tasks
        self.allow_agent_concurrency = allow_agent_concurrency
        self.agent_capacities = dict(agent_capacities or {})
        self.node_capacities = dict(node_capacities) if node_capacities is not None else {"local": max_parallel_tasks}

    def _can_place(self, candidate: TaskNode, occupied: List[TaskNode]) -> Tuple[bool, str]:
        if len(occupied) >= self.max_parallel_tasks:
            return False, "Global capacity exhausted"
        node_limit = self.node_capacities.get(candidate.node_id)
        if node_limit is None:
            return False, f"Unknown node: {candidate.node_id}"
        if sum(t.node_id == candidate.node_id for t in occupied) >= node_limit:
            return False, f"Node capacity exhausted: {candidate.node_id}"
        agent_limit = self.agent_capacities.get(candidate.agent_profile,
                                              self.max_parallel_tasks if self.allow_agent_concurrency else 1)
        if sum(t.agent_profile == candidate.agent_profile for t in occupied) >= agent_limit:
            return False, f"Agent capacity exhausted: {candidate.agent_profile}"
        for existing in sorted(occupied, key=lambda t: t.task_id):
            conflict, reason = has_concurrency_conflict(existing, candidate)
            if conflict:
                return False, reason
        return True, ""

    def next_wave(self, dag: ExecutionDAG, *, wave_index: int = 0,
                  cancelled: bool = False, deadline_utc: Optional[datetime] = None,
                  now_utc: Optional[datetime] = None, allowed_risks: Optional[Set[str]] = None,
                  remaining_tokens: Optional[int] = None, remaining_cost_usd: Optional[float] = None) -> Wave:
        """Dispatch selection from current verified state, never from a previous plan.

        RUNNING tasks retain locks/capacity. Cancellation and deadline are checked
        before any task becomes READY. A caller must persist RUNNING before dispatch.
        """
        dag.validate()
        if remaining_tokens is not None:
            _nonnegative(remaining_tokens, "remaining_tokens", integer=True)
        if remaining_cost_usd is not None:
            _nonnegative(remaining_cost_usd, "remaining_cost_usd")
        wave = Wave(wave_index=wave_index)
        if cancelled:
            wave.status = "CANCELLED"
            wave.rejections = {k: "Mission cancelled" for k in sorted(dag.nodes)}
            return wave
        now = now_utc or datetime.now(timezone.utc)
        if deadline_utc is not None and now >= deadline_utc:
            wave.status = "CANCELLED"
            wave.rejections = {k: "Mission deadline exceeded" for k in sorted(dag.nodes)}
            return wave
        occupied = [t for t in dag.nodes.values() if t.status == TaskStatus.RUNNING]
        token_total, cost_total = 0, 0.0
        for candidate in dag.get_ready_tasks():
            reason = ""
            if allowed_risks is not None and (candidate.risk_level == "UNKNOWN" or candidate.risk_level not in allowed_risks):
                reason = "Risk is unknown or disallowed"
            elif remaining_tokens is not None and (candidate.estimated_tokens is None or token_total + candidate.estimated_tokens > remaining_tokens):
                reason = "Token estimate unknown or budget insufficient"
            elif remaining_cost_usd is not None and (candidate.estimated_cost_usd is None or cost_total + candidate.estimated_cost_usd > remaining_cost_usd):
                reason = "Cost estimate unknown or budget insufficient"
            else:
                accepted, reason = self._can_place(candidate, occupied + wave.tasks)
                if accepted:
                    wave.tasks.append(candidate)
                    token_total += candidate.estimated_tokens or 0
                    cost_total += candidate.estimated_cost_usd or 0.0
                    continue
            wave.rejections[candidate.task_id] = reason
        return wave

    def schedule(self, dag: ExecutionDAG) -> List[Wave]:
        """
        Transforms DAG into ordered Waves.
        Algorithm:
        1. Validate DAG is acyclic.
        2. Track unsatisfied dependency counts for each node.
        3. Partition into waves respecting:
           - Prerequisite satisfaction (dependencies must complete in an earlier wave)
           - Resource read/write scope isolation
           - Agent capacity bounds
           - Max parallel tasks bound
        """
        dag.validate()

        # In-degree tracking
        pending_deps: Dict[str, Set[str]] = {
            t_id: set(dag.reverse_adj.get(t_id, set()))
            for t_id in dag.nodes
        }

        completed_tasks: Set[str] = {
            t_id for t_id, t in dag.nodes.items() if t.status == TaskStatus.VERIFIED
        }
        waves: List[Wave] = []
        wave_idx = 0

        while len(completed_tasks) < len(dag.nodes):
            # 1. Identify ready candidates (all prereqs in completed_tasks)
            ready_candidates: List[TaskNode] = []
            for t_id in sorted(dag.nodes.keys()):
                if t_id not in completed_tasks:
                    if pending_deps[t_id].issubset(completed_tasks):
                        ready_candidates.append(dag.nodes[t_id])

            if not ready_candidates:
                raise RuntimeError("Deadlock detected during wave scheduling: candidates blocked without satisfaction.")

            # 2. Pack current wave greedily and deterministically
            current_wave = Wave(wave_index=wave_idx)
            wave_selected: Set[str] = set()

            for candidate in ready_candidates:
                can_accept, reason = self._can_place(candidate, current_wave.tasks)
                if can_accept:
                    current_wave.tasks.append(candidate)
                    wave_selected.add(candidate.task_id)
                else:
                    current_wave.rejections[candidate.task_id] = reason

            if not current_wave.tasks:
                raise RuntimeError(f"Could not schedule any candidate task: {current_wave.rejections}")

            waves.append(current_wave)
            completed_tasks.update(wave_selected)
            wave_idx += 1

        return waves

    def to_schedule_dict(self, mission_id: str, waves: List[Wave]) -> Dict[str, Any]:
        return {
            "schedule_id": f"SCHED-{int(datetime.now(timezone.utc).timestamp())}",
            "mission_id": mission_id,
            "total_waves": len(waves),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "waves": [w.to_dict() for w in waves]
        }
