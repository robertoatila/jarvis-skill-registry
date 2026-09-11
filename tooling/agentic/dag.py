"""
dag.py // J.A.R.V.I.S. Execution Directed Acyclic Graph (DAG) Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces Determinism, Strict Cycle Detection, and Verification Gating
"""

from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from .models import TaskNode, TaskStatus, VerificationStatus, SCHEMA_VERSION, validate_schema_version


def save_json_atomic(file_path: str | Path, data: Dict[str, Any]) -> None:
    """Replace a JSON snapshot only after serializing and syncing a unique temp file."""
    p = Path(file_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp_p = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=p.parent,
                                         prefix=p.name + ".", suffix=".tmp", delete=False) as f:
            tmp_p = Path(f.name)
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_p, p)
    finally:
        if tmp_p is not None and tmp_p.exists():
            tmp_p.unlink()


class CycleDetectedError(Exception):
    """Raised when a circular dependency is detected in the Execution DAG."""
    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        super().__init__(f"Circular dependency detected in DAG: {' -> '.join(cycle_path)}")


class ExecutionDAG:
    """
    Deterministic Execution DAG.
    Guarantees:
    - Zero circular dependencies (verified at mutation time).
    - Bit-for-bit deterministic topological sorting (lexicographical tie-breaking).
    - Verification gating: prerequisite tasks must be VERIFIED before dependents become READY.
    - Full serialization round-trip with schema compatibility.
    """

    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.adjacency: Dict[str, Set[str]] = {}       # u -> {v} where u must precede v
        self.reverse_adj: Dict[str, Set[str]] = {}     # v -> {u} where v depends on u

    def add_node(self, node: TaskNode) -> None:
        node.__post_init__()
        if node.task_id in self.nodes:
            raise ValueError(f"TaskNode '{node.task_id}' already exists in DAG.")
        self.nodes[node.task_id] = node
        try:
            self._rebuild_edges()
            self.validate_acyclic()
        except Exception:
            del self.nodes[node.task_id]
            self._rebuild_edges()
            raise

    def _rebuild_edges(self) -> None:
        # Forward declarations remain on the node until the prerequisite is added.
        self.adjacency = {k: set() for k in self.nodes}
        self.reverse_adj = {k: set() for k in self.nodes}
        for task_id, node in self.nodes.items():
            for prerequisite in node.dependencies:
                if prerequisite in self.nodes:
                    self.adjacency[prerequisite].add(task_id)
                    self.reverse_adj[task_id].add(prerequisite)

    def validate(self) -> None:
        for task_id, node in self.nodes.items():
            node.__post_init__()
            if node.task_id != task_id:
                raise ValueError("Task identifier changed after insertion")
            missing = sorted(set(node.dependencies) - self.nodes.keys())
            if missing:
                raise ValueError(f"Task '{task_id}' has missing prerequisites: {missing}")
            if set(node.dependencies) != self.reverse_adj[task_id]:
                raise ValueError("Dependencies changed outside graph methods")
            if node.status == TaskStatus.VERIFIED and not self.is_task_verified(node):
                raise ValueError(f"Task '{task_id}' is VERIFIED with pending or failed checks")
        self.validate_acyclic()

    @staticmethod
    def is_task_verified(node: TaskNode) -> bool:
        return node.status == TaskStatus.VERIFIED and all(
            requirement.status == VerificationStatus.VERIFIED
            for requirement in node.verification_requirements
        )

    def add_dependency(self, prerequisite_id: str, dependent_id: str) -> None:
        """Declares that prerequisite_id must complete and verify before dependent_id can run."""
        if prerequisite_id not in self.nodes:
            raise KeyError(f"Prerequisite task '{prerequisite_id}' does not exist in DAG.")
        if dependent_id not in self.nodes:
            raise KeyError(f"Dependent task '{dependent_id}' does not exist in DAG.")
        if prerequisite_id == dependent_id:
            raise CycleDetectedError([prerequisite_id, dependent_id])

        existed = prerequisite_id in self.nodes[dependent_id].dependencies
        self.adjacency[prerequisite_id].add(dependent_id)
        self.reverse_adj[dependent_id].add(prerequisite_id)

        # Sync with dependent node's dependency list
        if prerequisite_id not in self.nodes[dependent_id].dependencies:
            self.nodes[dependent_id].dependencies.append(prerequisite_id)
            self.nodes[dependent_id].dependencies.sort()

        # Validate that addition did not introduce a cycle
        try:
            self.validate_acyclic()
        except Exception:
            if not existed:
                self.remove_dependency(prerequisite_id, dependent_id)
            raise

    def remove_dependency(self, prerequisite_id: str, dependent_id: str) -> None:
        if prerequisite_id in self.adjacency and dependent_id in self.adjacency[prerequisite_id]:
            self.adjacency[prerequisite_id].remove(dependent_id)
        if dependent_id in self.reverse_adj and prerequisite_id in self.reverse_adj[dependent_id]:
            self.reverse_adj[dependent_id].remove(prerequisite_id)
        if dependent_id in self.nodes and prerequisite_id in self.nodes[dependent_id].dependencies:
            self.nodes[dependent_id].dependencies.remove(prerequisite_id)

    def validate_acyclic(self) -> None:
        """DFS three-color cycle check (0: WHITE, 1: GRAY, 2: BLACK)."""
        visited: Dict[str, int] = {k: 0 for k in self.nodes}
        path: List[str] = []

        def dfs(node_id: str) -> Optional[List[str]]:
            visited[node_id] = 1
            path.append(node_id)
            for neighbor in sorted(self.adjacency.get(node_id, set())):
                if visited[neighbor] == 1:
                    cycle_idx = path.index(neighbor)
                    return path[cycle_idx:] + [neighbor]
                elif visited[neighbor] == 0:
                    found = dfs(neighbor)
                    if found:
                        return found
            path.pop()
            visited[node_id] = 2
            return None

        for n_id in sorted(self.nodes.keys()):
            if visited[n_id] == 0:
                cycle = dfs(n_id)
                if cycle:
                    raise CycleDetectedError(cycle)

    def topological_sort(self) -> List[str]:
        """
        Returns a deterministically ordered list of task IDs.
        Uses Kahn's algorithm with a sorted priority set for deterministic tie-breaking.
        """
        self.validate()

        in_degree: Dict[str, int] = {k: len(self.reverse_adj.get(k, set())) for k in self.nodes}
        ready: List[str] = sorted([k for k, deg in in_degree.items() if deg == 0])

        ordered: List[str] = []
        while ready:
            curr = ready.pop(0)
            ordered.append(curr)

            for neighbor in sorted(self.adjacency.get(curr, set())):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    # Insert in sorted order for determinism
                    ready.append(neighbor)
                    ready.sort()

        if len(ordered) != len(self.nodes):
            raise CycleDetectedError(["Unresolved circular dependency detected in topological sort."])

        return ordered

    def get_ready_tasks(self) -> List[TaskNode]:
        """
        Returns tasks whose prerequisite dependencies and required checks are VERIFIED,
        and whose current status is PENDING or READY.
        """
        self.validate()
        ready_tasks: List[TaskNode] = []
        for task_id in sorted(self.nodes.keys()):
            node = self.nodes[task_id]
            if node.status not in (TaskStatus.PENDING, TaskStatus.READY):
                continue

            prereqs = self.reverse_adj.get(task_id, set())
            all_prereqs_satisfied = True
            for p_id in prereqs:
                p_node = self.nodes.get(p_id)
                if not p_node:
                    all_prereqs_satisfied = False
                    break
                if not self.is_task_verified(p_node):
                    all_prereqs_satisfied = False
                    break

            if all_prereqs_satisfied:
                node.status = TaskStatus.READY
                ready_tasks.append(node)
            elif node.status == TaskStatus.READY:
                node.status = TaskStatus.PENDING

        return ready_tasks

    def mark_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[str]] = None
    ) -> TaskNode:
        if task_id not in self.nodes:
            raise KeyError(f"Task '{task_id}' not found in DAG.")

        node = self.nodes[task_id]
        status = TaskStatus(status)
        if status == TaskStatus.VERIFIED and any(
            v.status != VerificationStatus.VERIFIED for v in node.verification_requirements
        ):
            raise ValueError(f"Task '{task_id}' still has unverified requirements")
        node.status = status
        if result is not None:
            node.execution_result = result
        if artifacts:
            for art in artifacts:
                if art not in node.artifacts:
                    node.artifacts.append(art)
        return node

    def is_complete(self) -> bool:
        """Returns True only when every required task and check is verified."""
        if not self.nodes:
            return False
        self.validate()
        return all(self.is_task_verified(n) for n in self.nodes.values())

    def has_failed(self) -> bool:
        """Returns True if any task has FAILED and exhausted retries."""
        for n in self.nodes.values():
            if n.status == TaskStatus.FAILED and n.retry_count >= n.max_retries:
                return True
        return False

    def get_summary(self) -> Dict[str, Any]:
        counts = {s.value: 0 for s in TaskStatus}
        for n in self.nodes.values():
            st = n.status.value if isinstance(n.status, TaskStatus) else str(n.status)
            counts[st] = counts.get(st, 0) + 1

        return {
            "total_tasks": len(self.nodes),
            "status_counts": counts,
            "is_complete": self.is_complete(),
            "has_failed": self.has_failed(),
            "topological_order": self.topological_sort() if not self.has_failed() else []
        }

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        edges = []
        for src in sorted(self.adjacency.keys()):
            for dst in sorted(self.adjacency[src]):
                edges.append({"from": src, "to": dst})

        return {
            "schema_version": SCHEMA_VERSION,
            "nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes.keys())],
            "edges": edges
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionDAG:
        validate_schema_version(data)
        if "nodes" not in data or not isinstance(data["nodes"], list) or not isinstance(data.get("edges", []), list):
            raise ValueError("DAG must contain nodes and optional edges arrays")
        dag = cls()
        nodes_data = data.get("nodes", [])
        for nd in nodes_data:
            node = TaskNode.from_dict(nd)
            dag.add_node(node)

        edges_data = data.get("edges", [])
        for ed in edges_data:
            src = ed["from"]
            dst = ed["to"]
            dag.add_dependency(src, dst)

        dag.validate()
        return dag

    def save(self, file_path: str | Path) -> None:
        save_json_atomic(file_path, self.to_dict())

    @classmethod
    def load(cls, file_path: str | Path) -> ExecutionDAG:
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"DAG file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
