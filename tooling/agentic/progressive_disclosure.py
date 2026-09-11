"""
progressive_disclosure.py // J.A.R.V.I.S. Progressive Disclosure v2 Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Implements:
- Section 11 Progressive Disclosure (Level 0 Catalog, Level 1 Manifest, Level 2 Execution)
- Strict token-budget governance (never eager load skill bodies)
- Explainable disclosure metrics and token economy audit
"""

from __future__ import annotations
import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
SKILLS_DIR = REGISTRY_ROOT / "skills"
RESOURCES_INDEX = REGISTRY_ROOT / "index" / "resources.jsonl"


@dataclass
class SkillCatalogEntry:
    """Level 0 — Catalog: Minimal metadata (< 50 tokens per skill)."""
    id: str
    name: str
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    version: str = "1.0.0"
    platform: str = "cross-platform"
    risk: str = "LOW"
    tags: List[str] = field(default_factory=list)
    disclosure_level: int = 0

    @property
    def estimated_tokens(self) -> int:
        # Rough token heuristic (~4 characters per token)
        text = f"{self.id} {self.name} {' '.join(self.capabilities)} {self.description} {self.version} {self.platform} {self.risk} {' '.join(self.tags)}"
        return max(1, len(text) // 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "disclosure_level": 0,
            "skill_id": self.id,
            "name": self.name,
            "capabilities": sorted(self.capabilities),
            "description": self.description,
            "version": self.version,
            "platform": self.platform,
            "risk": self.risk,
            "tags": sorted(self.tags),
            "estimated_tokens": self.estimated_tokens
        }


@dataclass
class SkillManifestEntry:
    """Level 1 — Manifest: Structural interfaces and operational constraints."""
    catalog: SkillCatalogEntry
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    policies: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    cost_hints: Dict[str, Any] = field(default_factory=dict)
    disclosure_level: int = 1

    @property
    def estimated_tokens(self) -> int:
        base = self.catalog.estimated_tokens
        text = json.dumps({
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": self.dependencies,
            "requirements": self.requirements,
            "policies": self.policies,
            "side_effects": self.side_effects,
            "cost_hints": self.cost_hints
        })
        return base + max(1, len(text) // 4)

    def to_dict(self) -> Dict[str, Any]:
        d = self.catalog.to_dict()
        d["disclosure_level"] = 1
        d["manifest"] = {
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": sorted(self.dependencies),
            "requirements": sorted(self.requirements),
            "policies": sorted(self.policies),
            "side_effects": sorted(self.side_effects),
            "cost_hints": self.cost_hints
        }
        d["estimated_tokens"] = self.estimated_tokens
        return d


@dataclass
class SkillExecutionPackage:
    """Level 2 — Execution: Full instructions, scripts, templates (loaded on-demand only)."""
    manifest: SkillManifestEntry
    instructions: str = ""
    scripts: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    templates: Dict[str, str] = field(default_factory=dict)
    execution_resources: List[str] = field(default_factory=list)
    disclosure_level: int = 2

    @property
    def estimated_tokens(self) -> int:
        base = self.manifest.estimated_tokens
        full_text = self.instructions + " ".join(self.scripts.values()) + " ".join(self.templates.values())
        return base + max(1, len(full_text) // 4)

    def to_dict(self) -> Dict[str, Any]:
        d = self.manifest.to_dict()
        d["disclosure_level"] = 2
        d["execution"] = {
            "instruction_length": len(self.instructions),
            "instructions": self.instructions,
            "scripts": sorted(list(self.scripts.keys())),
            "references": sorted(self.references),
            "examples": sorted(self.examples),
            "templates": sorted(list(self.templates.keys())),
            "execution_resources": sorted(self.execution_resources)
        }
        d["estimated_tokens"] = self.estimated_tokens
        return d


class ProgressiveDisclosureEngine:
    """
    Manages progressive disclosure of skills in accordance with Section 11 of the Protocol.
    Prevents context window bloat by enforcing progressive levels.
    """

    def __init__(self, skills_dir: Optional[Path] = None, resources_jsonl: Optional[Path] = None):
        self.skills_dir = (skills_dir or SKILLS_DIR).resolve()
        self.resources_jsonl = (resources_jsonl or RESOURCES_INDEX).resolve()
        self._catalog_cache: Dict[str, SkillCatalogEntry] = {}
        self._manifest_cache: Dict[str, SkillManifestEntry] = {}
        self._execution_cache: Dict[str, SkillExecutionPackage] = {}

    def load_catalog(self, force_refresh: bool = False) -> Dict[str, SkillCatalogEntry]:
        """
        Loads Level 0 Catalog for all skills.
        Never reads full file bodies; only frontmatters or resources.jsonl entries.
        """
        if self._catalog_cache and not force_refresh:
            return self._catalog_cache

        catalog: Dict[str, SkillCatalogEntry] = {}

        # 1. Prefer resources.jsonl if available for speed and zero disk I/O on skills/
        if self.resources_jsonl.exists():
            try:
                with open(self.resources_jsonl, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            if record.get("index_type") == "RESOURCES":
                                continue
                            canonical_name = record.get("canonical_name")
                            if canonical_name and record.get("lifecycle_state") != "QUARANTINED":
                                caps = record.get("capabilities", [])
                                if not caps:
                                    caps = [canonical_name]
                                catalog[canonical_name] = SkillCatalogEntry(
                                    id=canonical_name,
                                    name=record.get("display_name", canonical_name),
                                    capabilities=caps,
                                    description=record.get("description", ""),
                                    version=record.get("version", "1.0.0"),
                                    platform="cross-platform",
                                    risk="LOW" if record.get("trust_level") == "TRUSTED" else "MEDIUM",
                                    tags=[canonical_name]
                                )
                        except Exception:
                            continue
            except Exception:
                pass

        # 2. Supplement or scan from skills directory without reading bodies
        if self.skills_dir.exists():
            for child in self.skills_dir.iterdir():
                if child.is_dir():
                    skill_id = child.name
                    if skill_id not in catalog:
                        entry = self._extract_level_0_from_dir(child)
                        if entry:
                            catalog[skill_id] = entry

        self._catalog_cache = catalog
        return catalog

    def _extract_level_0_from_dir(self, skill_path: Path) -> Optional[SkillCatalogEntry]:
        """Reads at most the top 20 lines of SKILL.md to extract frontmatter metadata."""
        skill_md = skill_path / "SKILL.md"
        skill_id = skill_path.name
        if not skill_md.exists():
            return SkillCatalogEntry(
                id=skill_id,
                name=skill_id,
                capabilities=[skill_id],
                description="Canonical Registry Skill"
            )

        desc = ""
        tags: List[str] = []
        name = skill_id
        try:
            with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
                in_fm = False
                for _ in range(25):
                    line = f.readline()
                    if not line:
                        break
                    stripped = line.strip()
                    if stripped == "---":
                        in_fm = not in_fm
                        continue
                    if in_fm:
                        if stripped.startswith("description:"):
                            desc = stripped.split("description:", 1)[1].strip().strip('"').strip("'")
                        elif stripped.startswith("name:"):
                            name = stripped.split("name:", 1)[1].strip().strip('"').strip("'")
                        elif stripped.startswith("tags:"):
                            raw_tags = stripped.split("tags:", 1)[1].strip(" []")
                            tags = [t.strip().strip('"').strip("'") for t in raw_tags.split(",") if t.strip()]
        except Exception:
            pass

        return SkillCatalogEntry(
            id=skill_id,
            name=name,
            capabilities=[skill_id],
            description=desc or f"Skill {skill_id}",
            tags=tags or [skill_id]
        )

    def disclose_manifest(self, skill_id: str) -> SkillManifestEntry:
        """Loads Level 1 Manifest on demand for candidate skills."""
        if skill_id in self._manifest_cache:
            return self._manifest_cache[skill_id]

        cat = self.load_catalog().get(skill_id)
        if not cat:
            cat = SkillCatalogEntry(id=skill_id, name=skill_id, capabilities=[skill_id])

        s_dir = self.skills_dir / skill_id
        deps: List[str] = []
        reqs: List[str] = []
        policies: List[str] = ["fail-closed", "sovereign-first"]
        side_effects: List[str] = []

        if s_dir.exists():
            if (s_dir / "scripts").exists():
                side_effects.append("executes-local-script")
            if (s_dir / "dependencies.json").exists():
                try:
                    dep_data = json.loads((s_dir / "dependencies.json").read_text(encoding="utf-8"))
                    deps.extend(dep_data.get("dependencies", []))
                except Exception:
                    pass

        manifest = SkillManifestEntry(
            catalog=cat,
            inputs={"type": "context-object", "required": False},
            outputs={"type": "execution-artifact", "verifiable": True},
            dependencies=deps,
            requirements=reqs,
            policies=policies,
            side_effects=side_effects,
            cost_hints={"token_estimate": 150}
        )
        self._manifest_cache[skill_id] = manifest
        return manifest

    def disclose_execution(self, skill_id: str) -> SkillExecutionPackage:
        """
        Loads Level 2 Execution package ONLY when a skill is actively selected.
        Loads full SKILL.md, script files, and reference documentation.
        """
        if skill_id in self._execution_cache:
            return self._execution_cache[skill_id]

        manifest = self.disclose_manifest(skill_id)
        s_dir = self.skills_dir / skill_id

        instructions = ""
        scripts: Dict[str, str] = {}
        references: List[str] = []
        examples: List[str] = []
        templates: Dict[str, str] = {}
        resources: List[str] = []

        if s_dir.exists():
            skill_md = s_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    instructions = skill_md.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass

            scripts_dir = s_dir / "scripts"
            if scripts_dir.exists():
                for sf in scripts_dir.glob("*"):
                    if sf.is_file():
                        scripts[sf.name] = str(sf)

            refs_dir = s_dir / "references"
            if refs_dir.exists():
                references = [rf.name for rf in refs_dir.glob("*") if rf.is_file()]

            ex_dir = s_dir / "examples"
            if ex_dir.exists():
                examples = [ef.name for ef in ex_dir.glob("*") if ef.is_file()]

        pkg = SkillExecutionPackage(
            manifest=manifest,
            instructions=instructions,
            scripts=scripts,
            references=references,
            examples=examples,
            templates=templates,
            execution_resources=resources
        )
        self._execution_cache[skill_id] = pkg
        return pkg

    def audit_token_economy(self, sample_size: int = 20) -> Dict[str, Any]:
        """
        Compares token consumption across Level 0, Level 1, and Level 2.
        Verifies the massive token savings of Progressive Disclosure v2.
        """
        catalog = self.load_catalog()
        skills = sorted(list(catalog.keys()))[:sample_size]

        l0_total = 0
        l1_total = 0
        l2_total = 0

        for sid in skills:
            cat = catalog[sid]
            l0_total += cat.estimated_tokens
            man = self.disclose_manifest(sid)
            l1_total += man.estimated_tokens
            exe = self.disclose_execution(sid)
            l2_total += exe.estimated_tokens

        savings_ratio = 1.0 - (l0_total / l2_total) if l2_total > 0 else 0.0

        return {
            "skills_sampled": len(skills),
            "level_0_catalog_tokens": l0_total,
            "level_1_manifest_tokens": l1_total,
            "level_2_execution_tokens": l2_total,
            "token_savings_percent": round(savings_ratio * 100, 2),
            "level_0_average_tokens_per_skill": round(l0_total / max(1, len(skills)), 1)
        }
