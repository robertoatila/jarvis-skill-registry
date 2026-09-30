"""Read-only Obsidian-style graph projection for the J.A.R.V.I.S. second brain.

The graph is derived from the existing repository/vault. It does not create a
parallel memory store and it never grants execution authority to note content.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+\.md)(?:#[^)]*)?\)", re.IGNORECASE)
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

_IGNORED_PARTS = {
    ".git",
    ".github",
    ".obsidian",
    "node_modules",
    "cache",
    "logs",
    "releases",
    "reports",
    "site",
    "skills",
    "staging",
    "state",
    "tests",
    "tooling",
    "ui",
}

_KIND_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("decision", ("decision", "decisao", "decisão", "adr")),
    ("meeting", ("meeting", "reuniao", "reunião", "ata")),
    ("proposal", ("proposal", "proposta", "pitch")),
    ("client", ("client", "cliente", "customer")),
    ("project", ("project", "projeto", "briefing")),
    ("memory", ("memory", "memoria", "memória", "episodic", "second-brain")),
    ("agent", ("agent", "agente", "subagent", "swarm")),
    ("security", ("security", "seguranca", "segurança", "quarantine")),
    ("architecture", ("architecture", "arquitetura", "design", "spec")),
)


def _clean_scalar(value: str) -> str:
    return value.strip().strip("\"'")


def _parse_frontmatter(text: str) -> Dict[str, Any]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    block = match.group(1)
    result: Dict[str, Any] = {}
    active_list_key: Optional[str] = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        list_match = re.match(r"^\s*-\s+(.+)$", line)
        if list_match and active_list_key:
            result.setdefault(active_list_key, []).append(_clean_scalar(list_match.group(1)))
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not key_match:
            active_list_key = None
            continue
        key, value = key_match.group(1).lower(), key_match.group(2).strip()
        if not value:
            result[key] = []
            active_list_key = key
            continue
        active_list_key = None
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = [_clean_scalar(item) for item in inner.split(",") if item.strip()]
        else:
            result[key] = _clean_scalar(value)
    return result


def _normalize_target(value: str) -> str:
    target = value.strip().replace("\\", "/")
    target = re.sub(r"^\./", "", target)
    if target.lower().endswith(".md"):
        target = target[:-3]
    return target.strip("/").casefold()


def _kind_for(path: Path, metadata: Dict[str, Any], title: str) -> str:
    explicit_type = str(metadata.get("type", "")).casefold()
    for kind, tokens in _KIND_RULES:
        if explicit_type and any(token.casefold() in explicit_type for token in tokens):
            return kind
    tags_value = metadata.get("tags", [])
    tags_text = " ".join(tags_value if isinstance(tags_value, list) else [str(tags_value)])
    haystack = " ".join([path.stem, title, tags_text]).casefold()
    for kind, tokens in _KIND_RULES:
        if any(token.casefold() in haystack for token in tokens):
            return kind
    return "note"


@dataclass(frozen=True)
class _Note:
    path: Path
    rel: str
    title: str
    kind: str
    note_type: str
    tags: Tuple[str, ...]
    links: Tuple[str, ...]


class SecondBrainGraphBuilder:
    """Build a bounded read-only graph from canonical Markdown/Canvas sources."""

    def __init__(self, root: Path, *, max_nodes: int = 320, max_edges: int = 1200):
        self.root = Path(root).resolve()
        self.max_nodes = max(20, min(int(max_nodes), 500))
        self.max_edges = max(20, min(int(max_edges), 2500))

    def _eligible(self, path: Path) -> bool:
        try:
            rel = path.resolve().relative_to(self.root)
        except (ValueError, OSError):
            return False
        if any(part in _IGNORED_PARTS for part in rel.parts[:-1]):
            return False
        return path.is_file() and path.suffix.lower() in {".md", ".canvas"}

    def _iter_markdown(self) -> Iterable[Path]:
        for path in self.root.rglob("*.md"):
            if self._eligible(path):
                yield path

    def _read_note(self, path: Path) -> Optional[_Note]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        metadata = _parse_frontmatter(text)
        title = str(metadata.get("title") or "").strip()
        if not title:
            heading = _TITLE_RE.search(text)
            title = heading.group(1).strip() if heading else path.stem
        tags_value = metadata.get("tags", [])
        if isinstance(tags_value, str):
            tags = tuple(part.strip() for part in tags_value.split(",") if part.strip())
        elif isinstance(tags_value, list):
            tags = tuple(str(part).strip() for part in tags_value if str(part).strip())
        else:
            tags = ()
        links = tuple(dict.fromkeys(
            [m.group(1).strip() for m in _WIKILINK_RE.finditer(text)]
            + [m.group(1).strip() for m in _MD_LINK_RE.finditer(text)]
        ))
        rel = path.relative_to(self.root).as_posix()
        return _Note(
            path=path,
            rel=rel,
            title=title[:180],
            kind=_kind_for(path, metadata, title),
            note_type=str(metadata.get("type") or "").strip()[:120],
            tags=tags[:20],
            links=links,
        )

    @staticmethod
    def _aliases(note: _Note) -> Iterable[str]:
        rel_no_ext = note.rel[:-3] if note.rel.lower().endswith(".md") else note.rel
        yield _normalize_target(rel_no_ext)
        yield _normalize_target(note.path.stem)
        yield _normalize_target(note.title)

    def _resolve_target(
        self,
        source: _Note,
        raw_target: str,
        aliases: Dict[str, str],
    ) -> Optional[str]:
        target = raw_target.split("#", 1)[0].split("|", 1)[0].strip()
        if not target:
            return None
        candidates = []
        source_parent = Path(source.rel).parent
        if "/" in target or "\\" in target or target.lower().endswith(".md"):
            candidates.append(_normalize_target((source_parent / target).as_posix()))
            candidates.append(_normalize_target(target))
        else:
            candidates.append(_normalize_target(target))
        for candidate in candidates:
            resolved = aliases.get(candidate)
            if resolved:
                return resolved
        return None

    def _canvas_edges(self, selected_ids: set[str]) -> List[Dict[str, str]]:
        edges: List[Dict[str, str]] = []
        for path in self.root.rglob("*.canvas"):
            if not self._eligible(path):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except (OSError, json.JSONDecodeError, TypeError):
                continue
            nodes_by_id: Dict[str, str] = {}
            for node in payload.get("nodes", []) if isinstance(payload, dict) else []:
                if not isinstance(node, dict) or node.get("type") != "file":
                    continue
                file_value = node.get("file")
                if not isinstance(file_value, str):
                    continue
                rel = Path(file_value).as_posix()
                if rel in selected_ids:
                    nodes_by_id[str(node.get("id"))] = rel
            for edge in payload.get("edges", []) if isinstance(payload, dict) else []:
                if not isinstance(edge, dict):
                    continue
                source = nodes_by_id.get(str(edge.get("fromNode")))
                target = nodes_by_id.get(str(edge.get("toNode")))
                if source and target and source != target:
                    edges.append({"source": source, "target": target, "relation": "canvas"})
        return edges

    def build(self) -> Dict[str, Any]:
        notes = [note for path in self._iter_markdown() if (note := self._read_note(path))]
        aliases: Dict[str, str] = {}
        for note in notes:
            for alias in self._aliases(note):
                aliases.setdefault(alias, note.rel)

        raw_edges: List[Dict[str, str]] = []
        degree: Dict[str, int] = {note.rel: 0 for note in notes}
        for note in notes:
            for raw_target in note.links:
                target = self._resolve_target(note, raw_target, aliases)
                if not target or target == note.rel:
                    continue
                raw_edges.append({"source": note.rel, "target": target, "relation": "link"})
                degree[note.rel] = degree.get(note.rel, 0) + 1
                degree[target] = degree.get(target, 0) + 1

        notes.sort(
            key=lambda note: (
                0 if len(Path(note.rel).parts) == 1 else 1,
                -degree.get(note.rel, 0),
                note.rel.casefold(),
            )
        )
        selected = notes[: self.max_nodes]
        selected_ids = {note.rel for note in selected}

        dedup: set[Tuple[str, str, str]] = set()
        edges: List[Dict[str, str]] = []
        for edge in raw_edges + self._canvas_edges(selected_ids):
            if edge["source"] not in selected_ids or edge["target"] not in selected_ids:
                continue
            key = (edge["source"], edge["target"], edge["relation"])
            if key in dedup:
                continue
            dedup.add(key)
            edges.append(edge)
            if len(edges) >= self.max_edges:
                break

        visible_degree: Dict[str, int] = {note.rel: 0 for note in selected}
        for edge in edges:
            visible_degree[edge["source"]] += 1
            visible_degree[edge["target"]] += 1

        nodes = [
            {
                "id": note.rel,
                "label": note.title,
                "kind": note.kind,
                "type": note.note_type or None,
                "tags": list(note.tags),
                "path": note.rel,
                "degree": visible_degree.get(note.rel, 0),
            }
            for note in selected
        ]
        kind_counts: Dict[str, int] = {}
        for node in nodes:
            kind_counts[node["kind"]] = kind_counts.get(node["kind"], 0) + 1

        return {
            "status": "SUCCESS",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "repository_vault_projection",
            "read_only": True,
            "nodes": nodes,
            "edges": edges,
            "metrics": {
                "nodes_total": len(nodes),
                "edges_total": len(edges),
                "notes_scanned": len(notes),
                "truncated_nodes": max(0, len(notes) - len(nodes)),
                "kind_counts": kind_counts,
            },
        }
