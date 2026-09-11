"""
composite.py // J.A.R.V.I.S. Composite Skills & Dependency Graph Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Supports:
- Declarative Composite Skills (multi-skill workflows)
- Sub-graph DAG expansion into parent Missions
- Skill dependency graph resolution (transitive dependencies & cycle checks)
- Progressive Disclosure levels (L0 Catalog, L1 Manifest, L2 Execution)
"""

from __future__ import annotations
import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any

from .models import TaskNode, TaskStatus, VerificationRequirement, VerificationType, SCHEMA_VERSION, validate_schema_version, _identifier, _strings
from .dag import ExecutionDAG, CycleDetectedError, save_json_atomic


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
SKILLS_DIR = REGISTRY_ROOT / "skills"


@dataclass
class SubSkillReference:
    skill_id: str
    alias: Optional[str] = None
    read_scopes: List[str] = field(default_factory=list)
    write_scopes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _identifier(self.skill_id, "skill_id")
        if self.alias is not None:
            _identifier(self.alias, "alias")
        _strings(self.read_scopes, "read_scopes")
        _strings(self.write_scopes, "write_scopes")
        for rs in self.read_scopes:
            clean = rs.replace("\\", "/").strip()
            if clean.startswith("/") or re.match(r"^[a-zA-Z]:", clean) or ".." in clean.split("/"):
                raise ValueError(f"Scope confinement violation: '{rs}' must be a relative canonical path without traversal")
        for ws in self.write_scopes:
            clean = ws.replace("\\", "/").strip()
            if clean.startswith("/") or re.match(r"^[a-zA-Z]:", clean) or ".." in clean.split("/"):
                raise ValueError(f"Scope confinement violation: '{ws}' must be a relative canonical path without traversal")

    @property
    def node_name(self) -> str:
        return self.alias or self.skill_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "alias": self.alias,
            "read_scopes": sorted(self.read_scopes),
            "write_scopes": sorted(self.write_scopes)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SubSkillReference:
        return cls(
            skill_id=data["skill_id"],
            alias=data.get("alias"),
            read_scopes=list(data.get("read_scopes", [])),
            write_scopes=list(data.get("write_scopes", []))
        )


@dataclass
class CompositeSkill:
    composite_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    sub_skills: List[SubSkillReference] = field(default_factory=list)
    dependency_graph: List[Tuple[str, str]] = field(default_factory=list)  # (from_alias, to_alias)

    def __post_init__(self) -> None:
        _identifier(self.composite_id, "composite_id")
        _identifier(self.name, "name")
        _strings(self.tags, "tags")
        aliases = [s.node_name for s in self.sub_skills]
        if not aliases or len(aliases) != len(set(aliases)):
            raise ValueError("Composite requires nonempty, unique sub-skill aliases")
        for sub in self.sub_skills:
            sub.__post_init__()
        for src, dst in self.dependency_graph:
            if src not in aliases or dst not in aliases:
                raise ValueError(f"Unknown composite dependency endpoint: {src} -> {dst}")

    def to_dict(self) -> Dict[str, Any]:
        self.__post_init__()
        return {
            "schema_version": SCHEMA_VERSION,
            "composite_id": self.composite_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tags": sorted(self.tags),
            "sub_skills": [s.to_dict() for s in sorted(self.sub_skills, key=lambda s: s.node_name)],
            "dependency_graph": [{"from": f, "to": t} for f, t in sorted(set(self.dependency_graph))]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CompositeSkill:
        validate_schema_version(data)
        subs = [SubSkillReference.from_dict(s) for s in data.get("sub_skills", [])]
        edges = [(e["from"], e["to"]) for e in data.get("dependency_graph", [])]
        return cls(
            composite_id=data["composite_id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            tags=list(data.get("tags", [])),
            sub_skills=subs,
            dependency_graph=edges
        )

    def expand_to_dag(self, task_prefix: str = "") -> ExecutionDAG:
        """Expands this composite skill into a standalone, verifiable ExecutionDAG."""
        self.__post_init__()
        dag = ExecutionDAG()
        prefix = f"{task_prefix}_" if task_prefix else ""

        # Map of alias -> TaskNode
        alias_to_id: Dict[str, str] = {}
        for sub in sorted(self.sub_skills, key=lambda s: s.node_name):
            task_id = f"{prefix}{sub.node_name}"
            alias_to_id[sub.node_name] = task_id
            node = TaskNode(
                task_id=task_id,
                title=f"Execute {sub.skill_id}",
                description=f"Part of composite skill: {self.name}",
                required_skills=[sub.skill_id],
                read_scopes=list(sub.read_scopes),
                write_scopes=list(sub.write_scopes)
            )
            dag.add_node(node)

        # Add edges
        for src, dst in sorted(set(self.dependency_graph)):
            dag.add_dependency(alias_to_id[src], alias_to_id[dst])

        dag.validate_acyclic()
        return dag

    def save(self, file_path: str | Path) -> None:
        self.expand_to_dag()
        save_json_atomic(file_path, self.to_dict())

    @classmethod
    def load(cls, file_path: str | Path) -> CompositeSkill:
        composite = cls.from_dict(json.loads(Path(file_path).read_text(encoding="utf-8")))
        composite.expand_to_dag()
        return composite


class SkillDependencyGraph:
    """
    Manages and resolves direct and transitive dependencies between individual skills.
    Ensures zero cyclic dependencies among skills.
    """

    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = {}  # skill -> {required_skills}

    def register_dependency(self, skill_id: str, required_skill_id: str) -> None:
        _identifier(skill_id, "skill_id")
        _identifier(required_skill_id, "required_skill_id")
        if skill_id == required_skill_id:
            raise CycleDetectedError([skill_id, required_skill_id])
        previous = {k: set(v) for k, v in self.dependencies.items()}
        if skill_id not in self.dependencies:
            self.dependencies[skill_id] = set()
        self.dependencies[skill_id].add(required_skill_id)
        try:
            self.validate_acyclic()
        except Exception:
            self.dependencies = previous
            raise

    def validate_acyclic(self) -> None:
        visited: Dict[str, int] = {}
        path: List[str] = []

        def dfs(node: str) -> Optional[List[str]]:
            visited[node] = 1
            path.append(node)
            for neighbor in sorted(self.dependencies.get(node, set())):
                if visited.get(neighbor) == 1:
                    cycle_idx = path.index(neighbor)
                    return path[cycle_idx:] + [neighbor]
                elif visited.get(neighbor) == 0 or neighbor not in visited:
                    found = dfs(neighbor)
                    if found:
                        return found
            path.pop()
            visited[node] = 2
            return None

        all_nodes = sorted(list(self.dependencies.keys()))
        for n in all_nodes:
            if visited.get(n, 0) == 0:
                cycle = dfs(n)
                if cycle:
                    raise CycleDetectedError(cycle)

    def resolve_transitive_dependencies(self, skill_ids: List[str]) -> List[str]:
        """
        Deterministically resolves all prerequisites for the given skill_ids in dependency order.
        Prerequisites appear BEFORE the skills that require them.
        """
        self.validate_acyclic()
        resolved: List[str] = []
        visited: Set[str] = set()

        def visit(s: str) -> None:
            if s in visited:
                return
            visited.add(s)
            for dep in sorted(self.dependencies.get(s, set())):
                visit(dep)
            if s not in resolved:
                resolved.append(s)

        for s in sorted(skill_ids):
            visit(s)

        return resolved


class ProgressiveDisclosureReader:
    """Compatibility reader for catalog metadata and explicitly selected content."""

    @staticmethod
    def _skill_path(skill_id: str, skills_dir: Path) -> Path:
        if not isinstance(skill_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", skill_id):
            raise ValueError("Invalid skill identifier")
        root = Path(skills_dir).resolve()
        skill = root / skill_id
        for path in (skill, skill / "SKILL.md"):
            if path.is_symlink() or path.is_junction() or not path.resolve().is_relative_to(root):
                raise ValueError("Linked or escaping skill paths are not allowed")
        return skill

    @staticmethod
    def read_level_0(skill_id: str, skills_dir: Path = SKILLS_DIR) -> Dict[str, Any]:
        """Reads lightweight metadata without loading entire body."""
        s_dir = ProgressiveDisclosureReader._skill_path(skill_id, skills_dir)
        skill_md = s_dir / "SKILL.md"
        if not skill_md.exists():
            return {"id": skill_id, "found": False}

        # Read first 10 lines for frontmatter
        lines = []
        try:
            with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
                for _ in range(15):
                    l = f.readline()
                    if not l:
                        break
                    if not lines and l.strip() != "---":
                        break
                    lines.append(l)
                    if len(lines) > 1 and l.strip() == "---":
                        break
        except OSError:
            raise

        desc = ""
        in_fm = False
        for line in lines:
            stripped = line.strip()
            if stripped == "---":
                in_fm = not in_fm
                continue
            if in_fm and stripped.startswith("description:"):
                desc = stripped.split("description:", 1)[1].strip().strip('"').strip("'")
                break

        return {
            "id": skill_id,
            "name": skill_id,
            "description": desc or "Canonical Skill",
            "found": True,
            "disclosure_level": 0
        }

    @staticmethod
    def read_level_1(skill_id: str, skills_dir: Path = SKILLS_DIR) -> Dict[str, Any]:
        """Reads Level 0 + structural manifest, inputs, outputs, scopes."""
        l0 = ProgressiveDisclosureReader.read_level_0(skill_id, skills_dir)
        s_dir = ProgressiveDisclosureReader._skill_path(skill_id, skills_dir)

        has_scripts = (s_dir / "scripts").exists()
        has_refs = (s_dir / "references").exists()
        has_examples = (s_dir / "examples").exists()

        l0.update({
            "has_scripts": has_scripts,
            "has_references": has_refs,
            "has_examples": has_examples,
            "disclosure_level": 1
        })
        return l0

    @staticmethod
    def read_level_2(skill_id: str, skills_dir: Path = SKILLS_DIR) -> Dict[str, Any]:
        """Reads full execution instructions (Level 2). Only for actively executed skills!"""
        l1 = ProgressiveDisclosureReader.read_level_1(skill_id, skills_dir)
        skill_md = ProgressiveDisclosureReader._skill_path(skill_id, skills_dir) / "SKILL.md"
        if skill_md.exists():
            l1["full_instructions"] = skill_md.read_text(encoding="utf-8", errors="replace")
        l1["disclosure_level"] = 2
        return l1
