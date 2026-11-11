"""Read-only Obsidian-style graph projection for the J.A.R.V.I.S. second brain.

The graph is derived from the existing repository/vault. It does not create a
parallel memory store and it never grants execution authority to note content.
"""
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import tempfile
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
    ".jarvis-profile",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "archives",
    "backups",
    "node_modules",
    "playwright-report",
    "cache",
    "logs",
    "releases",
    "reports",
    "scratch",
    "site",
    "skills",
    "staging",
    "state",
    "test-results",
    "tests",
    "tooling",
    "transactions",
    "ui",
}

_NOTE_PARSE_CACHE: Dict[str, Tuple[int, int, "_Note"]] = {}
_DISK_NOTE_CACHE_BY_ROOT: Dict[str, Dict[str, Any]] = {}
_GRAPH_RESULT_CACHE: Dict[Tuple[str, int, int], Tuple[str, Dict[str, Any]]] = {}

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

    def _scan_sources(self) -> Tuple[List[Tuple[Path, str, int, int]], List[Path]]:
        """Single pruned os.scandir traversal collecting eligible .md and .canvas files."""
        md_entries: List[Tuple[Path, str, int, int]] = []
        canvas_paths: List[Path] = []
        stack: List[Tuple[Path, Tuple[str, ...]]] = [(self.root, ())]
        while stack:
            current_dir, rel_parts = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    entries = list(it)
            except OSError:
                continue
            for entry in entries:
                name = entry.name
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if name in _IGNORED_PARTS or name.startswith("."):
                            continue
                        stack.append((Path(entry.path), rel_parts + (name,)))
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                except OSError:
                    continue
                lower = name.lower()
                if lower.endswith(".md"):
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    rel_str = "/".join(rel_parts + (name,))
                    md_entries.append((Path(entry.path), rel_str, st.st_mtime_ns, st.st_size))
                elif lower.endswith(".canvas"):
                    canvas_paths.append(Path(entry.path))
        return md_entries, canvas_paths

    def _iter_markdown(self) -> Iterable[Path]:
        md_entries, _ = self._scan_sources()
        for path, _, _, _ in md_entries:
            yield path

    def _disk_cache_path(self) -> Path:
        root_key = hashlib.sha1(str(self.root).encode("utf-8")).hexdigest()[:12]
        return Path(tempfile.gettempdir()) / f"jarvis_second_brain_notes_v1_{root_key}.json"

    def _get_disk_note_cache(self) -> Dict[str, Any]:
        root_key = str(self.root)
        loaded = _DISK_NOTE_CACHE_BY_ROOT.get(root_key)
        if loaded is not None:
            return loaded
        cache: Dict[str, Any] = {}
        try:
            cp = self._disk_cache_path()
            if cp.is_file():
                raw = json.loads(cp.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    cache = raw
        except Exception:
            cache = {}
        _DISK_NOTE_CACHE_BY_ROOT[root_key] = cache
        return cache

    def _read_note_cached(
        self,
        path: Path,
        rel: str,
        mtime_ns: int,
        size: int,
        disk_cache: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[_Note], bool]:
        cache_key = str(path)
        cached = _NOTE_PARSE_CACHE.get(cache_key)
        if cached is not None and cached[0] == mtime_ns and cached[1] == size:
            return cached[2], False

        if disk_cache is not None:
            raw_hit = disk_cache.get(rel)
            if (
                isinstance(raw_hit, list)
                and len(raw_hit) == 7
                and raw_hit[0] == mtime_ns
                and raw_hit[1] == size
            ):
                note = _Note(
                    path=path,
                    rel=rel,
                    title=raw_hit[2],
                    kind=raw_hit[3],
                    note_type=raw_hit[4],
                    tags=tuple(raw_hit[5]),
                    links=tuple(raw_hit[6]),
                )
                if len(_NOTE_PARSE_CACHE) > 20000:
                    _NOTE_PARSE_CACHE.clear()
                _NOTE_PARSE_CACHE[cache_key] = (mtime_ns, size, note)
                return note, False

        note = self._read_note(path, rel=rel)
        if note is not None:
            if len(_NOTE_PARSE_CACHE) > 20000:
                _NOTE_PARSE_CACHE.clear()
            _NOTE_PARSE_CACHE[cache_key] = (mtime_ns, size, note)
            if disk_cache is not None:
                disk_cache[rel] = [
                    mtime_ns,
                    size,
                    note.title,
                    note.kind,
                    note.note_type,
                    list(note.tags),
                    list(note.links),
                ]
                return note, True
        return note, False

    def _read_note(self, path: Path, *, rel: Optional[str] = None) -> Optional[_Note]:
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
        rel_str = rel if rel is not None else path.relative_to(self.root).as_posix()
        return _Note(
            path=path,
            rel=rel_str,
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
        if "/" in target or "\\" in target or target.lower().endswith(".md"):
            clean_t = target.replace("\\", "/")
            if "/" in source.rel:
                source_parent = source.rel.rsplit("/", 1)[0]
                joined = posixpath.normpath(f"{source_parent}/{clean_t}")
            else:
                joined = posixpath.normpath(clean_t)
            resolved = aliases.get(_normalize_target(joined))
            if resolved:
                return resolved
            return aliases.get(_normalize_target(clean_t))
        return aliases.get(_normalize_target(target))

    def _canvas_edges(self, selected_ids: set[str], canvas_paths: Optional[List[Path]] = None) -> List[Dict[str, str]]:
        edges: List[Dict[str, str]] = []
        if canvas_paths is None:
            _, canvas_paths = self._scan_sources()
        for path in canvas_paths:
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
        md_entries, canvas_paths = self._scan_sources()

        h = hashlib.md5()
        for _, rel, mtime_ns, fsize in md_entries:
            h.update(f"{rel}:{mtime_ns}:{fsize}\n".encode("utf-8", errors="ignore"))
        for cp in canvas_paths:
            try:
                cst = cp.stat()
                h.update(f"C:{cp.name}:{cst.st_mtime_ns}:{cst.st_size}\n".encode("utf-8", errors="ignore"))
            except OSError:
                pass
        sig_digest = h.hexdigest()

        cache_key = (str(self.root), self.max_nodes, self.max_edges)
        cached_res = _GRAPH_RESULT_CACHE.get(cache_key)
        if cached_res is not None and cached_res[0] == sig_digest:
            payload = dict(cached_res[1])
            payload["generated_at"] = datetime.now(timezone.utc).isoformat()
            return payload

        disk_cache = self._get_disk_note_cache()
        disk_dirty = False
        notes: List[_Note] = []
        for path, rel, mtime_ns, fsize in md_entries:
            note, wrote = self._read_note_cached(path, rel, mtime_ns, fsize, disk_cache=disk_cache)
            if wrote:
                disk_dirty = True
            if note is not None:
                notes.append(note)

        if disk_dirty:
            try:
                self._disk_cache_path().write_text(
                    json.dumps(disk_cache, separators=(",", ":")),
                    encoding="utf-8",
                )
            except Exception:
                pass

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
                0 if "/" not in note.rel else 1,
                -degree.get(note.rel, 0),
                note.rel.casefold(),
            )
        )
        selected = notes[: self.max_nodes]
        selected_ids = {note.rel for note in selected}

        dedup: set[Tuple[str, str, str]] = set()
        edges: List[Dict[str, str]] = []
        for edge in raw_edges + self._canvas_edges(selected_ids, canvas_paths=canvas_paths):
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

        result = {
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
        if len(_GRAPH_RESULT_CACHE) > 8:
            _GRAPH_RESULT_CACHE.clear()
        _GRAPH_RESULT_CACHE[cache_key] = (sig_digest, result)
        return dict(result)
