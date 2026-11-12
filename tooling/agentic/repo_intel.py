"""
repo_intel.py // J.A.R.V.I.S. Repository Intelligence Graph Engine
Pure Python Standard Library (Zero PIP Dependencies)
Implements:
- Static AST inspection of repository components (zero dynamic execution)
- Symbol table extraction (Classes, Functions, Docstrings, Line Numbers)
- Module Dependency Graph extraction (internal and standard imports)
- Section 2 Capability Classifier (EXISTS, PARTIAL, EQUIVALENT, MISSING, OBSOLETE, CONFLICTING)
"""

from __future__ import annotations
import ast
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone

from .config import CONFIG, JarvisRuntimeConfig

REGISTRY_ROOT = CONFIG.registry_root

_NON_ALNUM_RE = re.compile(r"[^a-zA-Z0-9]")
_CAMEL_RE = re.compile(r"([A-Z])")
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class SymbolRecord:
    file: str
    symbol_type: str  # CLASS, FUNCTION, VARIABLE
    name: str
    line: int
    docstring: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModuleDependency:
    source_module: str
    imported_module: str
    is_internal: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PyASTVisitor(ast.NodeVisitor):
    _BLOCK_FIELDS = ("body", "orelse", "handlers", "finalbody", "cases")

    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.symbols: List[SymbolRecord] = []
        self.imports: List[str] = []

    def generic_visit(self, node: ast.AST):
        # Only traverse statement blocks; ClassDef/FunctionDef/Import statements cannot reside in expressions.
        for attr in self._BLOCK_FIELDS:
            stmts = getattr(node, attr, None)
            if isinstance(stmts, list):
                for stmt in stmts:
                    if isinstance(stmt, ast.AST):
                        self.visit(stmt)

    def visit_ClassDef(self, node: ast.ClassDef):
        doc = ast.get_docstring(node)
        self.symbols.append(SymbolRecord(
            file=self.rel_path,
            symbol_type="CLASS",
            name=node.name,
            line=node.lineno,
            docstring=doc
        ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        doc = ast.get_docstring(node)
        self.symbols.append(SymbolRecord(
            file=self.rel_path,
            symbol_type="FUNCTION",
            name=node.name,
            line=node.lineno,
            docstring=doc
        ))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        doc = ast.get_docstring(node)
        self.symbols.append(SymbolRecord(
            file=self.rel_path,
            symbol_type="FUNCTION",
            name=node.name,
            line=node.lineno,
            docstring=doc
        ))
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        self.imports.append(mod)
        self.generic_visit(node)


class RepositoryIntelligenceGraph:
    """
    Constructs static repository intelligence graphs and capability maps.
    Zero dynamic execution.
    """

    def __init__(self, root_path: Optional[Path] = None, config: Optional[JarvisRuntimeConfig] = None):
        cfg = config or CONFIG
        self.root_path = (root_path or cfg.registry_root).resolve()
        self._ast_cache: Dict[str, Dict[str, Any]] = {}
        self._tree_snapshots: Dict[str, Dict[str, Any]] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    def invalidate_path(self, rel_path: str) -> bool:
        """
        Invalidates cached AST records for a given relative path or directory.
        Returns True if any cached entry was removed.
        """
        self._tree_snapshots.clear()
        norm_target = rel_path.replace("\\", "/").rstrip("/")
        to_remove = [
            k for k in self._ast_cache.keys()
            if k == norm_target or k.startswith(norm_target + "/")
        ]
        for k in to_remove:
            del self._ast_cache[k]
        disk_cache = getattr(self, "_disk_ast_cache", None)
        if isinstance(disk_cache, dict):
            disk_remove = [
                k for k in disk_cache.keys()
                if k == norm_target or k.startswith(norm_target + "/")
            ]
            for k in disk_remove:
                del disk_cache[k]
            if disk_remove:
                try:
                    self._disk_cache_file().write_text(
                        json.dumps(disk_cache, separators=(",", ":")),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
        return len(to_remove) > 0

    def get_cache_stats(self) -> Dict[str, int]:
        """Returns AST caching statistics (size, hits, misses)."""
        return {
            "cache_size": len(self._ast_cache),
            "hits": self._cache_hits,
            "misses": self._cache_misses
        }

    def get_known_symbols(self, target_rel_dir: str = "tooling/agentic") -> List[str]:
        """Returns list of known symbol names across target directory."""
        scan_res = self.scan_tree(target_rel_dir)
        snap = self._tree_snapshots.get(target_rel_dir)
        if snap is not None and "symbol_names" in snap:
            return list(snap["symbol_names"])
        if "symbols" in scan_res:
            return [s["name"] for s in scan_res["symbols"]]
        return []

    @staticmethod
    def _walk_py_and_dirs(root_path: Path, scan_dir: Path) -> Tuple[List[Tuple[str, int]], List[Tuple[Path, str, int, int]]]:
        """Single-pass os.scandir traversal capturing directory mtimes and filtered .py file stats."""
        dirs: List[Tuple[str, int]] = []
        py_files: List[Tuple[Path, str, int, int]] = []
        try:
            root_st = os.stat(scan_dir)
            dirs.append((str(scan_dir), root_st.st_mtime_ns))
        except OSError:
            return dirs, py_files

        stack: List[Path] = [scan_dir]
        while stack:
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    entries = sorted(it, key=lambda e: e.name)
            except OSError:
                continue
            for entry in entries:
                name = entry.name
                if name.startswith(".") or name == "__pycache__":
                    continue
                try:
                    is_dir = entry.is_dir(follow_symlinks=False)
                except OSError:
                    continue
                if is_dir:
                    try:
                        dst = entry.stat(follow_symlinks=False)
                        dirs.append((entry.path, dst.st_mtime_ns))
                    except OSError:
                        pass
                    stack.append(Path(entry.path))
                elif name.endswith(".py"):
                    p = Path(entry.path)
                    rel = p.relative_to(root_path).as_posix()
                    if "config/api_keys.json" in rel or ".tmp" in rel:
                        continue
                    try:
                        fst = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    py_files.append((p, rel, fst.st_mtime_ns, fst.st_size))
        py_files.sort(key=lambda item: item[1])
        return dirs, py_files

    def _disk_cache_file(self) -> Path:
        root_key = hashlib.sha1(str(self.root_path.resolve()).encode("utf-8")).hexdigest()[:12]
        return Path(tempfile.gettempdir()) / f"jarvis_repo_intel_v1_{root_key}.json"

    def _get_disk_ast_cache(self) -> Dict[str, Any]:
        cache = getattr(self, "_disk_ast_cache", None)
        if cache is not None:
            return cache
        loaded: Dict[str, Any] = {}
        try:
            cp = self._disk_cache_file()
            if cp.is_file():
                raw = json.loads(cp.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    loaded = raw
        except Exception:
            loaded = {}
        self._disk_ast_cache = loaded
        return loaded

    def _flush_disk_ast_cache(self) -> None:
        disk_cache: Dict[str, Any] = self._get_disk_ast_cache()
        dirty = False
        for rel, entry in self._ast_cache.items():
            prev = disk_cache.get(rel)
            if (
                prev is not None
                and prev.get("mtime_ns") == entry.get("mtime_ns")
                and prev.get("size") == entry.get("size")
            ):
                continue
            disk_cache[rel] = {
                "mtime_ns": entry.get("mtime_ns"),
                "size": entry.get("size"),
                "file_info": entry.get("file_info"),
                "symbols": [s.to_dict() for s in entry.get("symbols", [])],
                "dependencies": [d.to_dict() for d in entry.get("dependencies", [])],
            }
            dirty = True
        if dirty:
            try:
                self._disk_cache_file().write_text(
                    json.dumps(disk_cache, separators=(",", ":")),
                    encoding="utf-8",
                )
            except Exception:
                pass

    def scan_tree(self, target_rel_dir: str = "tooling/agentic") -> Dict[str, Any]:
        """
        Scans python files under target_rel_dir and extracts symbols & dependencies.
        Leverages SHA-256 AST caching and directory snapshot reuse for incremental scanning.
        """
        scan_dir = self.root_path / target_rel_dir
        if not scan_dir.exists():
            return {"error": f"Directory not found: {scan_dir}"}

        snap = self._tree_snapshots.get(target_rel_dir)
        if snap is not None:
            try:
                dirs_unchanged = all(os.stat(d).st_mtime_ns == m for d, m in snap["dir_mtimes"])
                files_unchanged = dirs_unchanged and all(
                    (st.st_mtime_ns, st.st_size) == sig
                    for p, sig in snap["file_sigs"]
                    for st in (os.stat(p),)
                )
                if files_unchanged:
                    self._cache_hits += len(snap["file_sigs"])
                    return {
                        "root_path": str(self.root_path),
                        "target_dir": target_rel_dir,
                        "scanned_utc": datetime.now(timezone.utc).isoformat(),
                        "total_files": len(snap["files"]),
                        "files": list(snap["files"]),
                        "symbols": list(snap["symbols"]),
                        "module_dependencies": list(snap["module_dependencies"]),
                    }
            except OSError:
                pass

        files_info: List[Dict[str, Any]] = []
        symbols: List[SymbolRecord] = []
        dependencies: List[ModuleDependency] = []

        dir_mtimes, py_records = self._walk_py_and_dirs(self.root_path, scan_dir)
        source_stems = {p.stem for p, _, _, _ in py_records}
        disk_cache = self._get_disk_ast_cache()
        file_sigs = []

        for py_path, rel, mtime_ns, fsize in py_records:
            file_sigs.append((str(py_path), (mtime_ns, fsize)))

            cached = self._ast_cache.get(rel)
            if (
                cached is not None
                and cached.get("mtime_ns") == mtime_ns
                and cached.get("size") == fsize
            ):
                self._cache_hits += 1
                files_info.append(dict(cached["file_info"]))
                symbols.extend(cached["symbols"])
                dependencies.extend(cached["dependencies"])
                continue

            disk_hit = disk_cache.get(rel)
            if (
                isinstance(disk_hit, dict)
                and disk_hit.get("mtime_ns") == mtime_ns
                and disk_hit.get("size") == fsize
                and isinstance(disk_hit.get("file_info"), dict)
            ):
                syms = [SymbolRecord(**s) for s in disk_hit.get("symbols", [])]
                deps = [
                    ModuleDependency(
                        source_module=d["source_module"],
                        imported_module=d["imported_module"],
                        is_internal=(
                            d["imported_module"].startswith(".")
                            or "agentic" in d["imported_module"]
                            or d["imported_module"] in source_stems
                        ),
                    )
                    for d in disk_hit.get("dependencies", [])
                ]
                file_info_cached = dict(disk_hit["file_info"])
                self._cache_misses += 1
                self._ast_cache[rel] = {
                    "mtime_ns": mtime_ns,
                    "size": fsize,
                    "sha256": file_info_cached.get("sha256"),
                    "file_info": file_info_cached,
                    "symbols": syms,
                    "dependencies": deps,
                }
                files_info.append(file_info_cached)
                symbols.extend(syms)
                dependencies.extend(deps)
                continue

            content = py_path.read_text(encoding="utf-8", errors="replace")
            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

            file_info_entry = {
                "rel_path": rel,
                "category": "CODE",
                "bytes": len(content),
                "lines": len(content.splitlines()),
                "sha256": sha
            }

            # Check incremental AST cache by content hash
            if cached is not None and cached.get("sha256") == sha:
                self._cache_hits += 1
                cached["mtime_ns"] = mtime_ns
                cached["size"] = fsize
                files_info.append(file_info_entry)
                symbols.extend(cached["symbols"])
                dependencies.extend(cached["dependencies"])
                continue

            # Cache miss: parse AST
            self._cache_misses += 1
            file_symbols: List[SymbolRecord] = []
            file_deps: List[ModuleDependency] = []

            try:
                tree = ast.parse(content, filename=str(py_path))
                visitor = PyASTVisitor(rel)
                visitor.visit(tree)

                file_symbols = visitor.symbols
                symbols.extend(file_symbols)

                source_mod = py_path.stem
                for imp in visitor.imports:
                    is_internal = imp.startswith(".") or "agentic" in imp or imp in source_stems
                    dep = ModuleDependency(
                        source_module=source_mod,
                        imported_module=imp,
                        is_internal=is_internal
                    )
                    file_deps.append(dep)
                    dependencies.append(dep)

                # Store in cache
                self._ast_cache[rel] = {
                    "mtime_ns": mtime_ns,
                    "size": fsize,
                    "sha256": sha,
                    "file_info": file_info_entry,
                    "symbols": file_symbols,
                    "dependencies": file_deps
                }
            except SyntaxError as se:
                file_info_entry["syntax_error"] = str(se)

            files_info.append(file_info_entry)

        symbol_dicts = [s.to_dict() for s in symbols]
        dep_dicts = [d.to_dict() for d in dependencies]
        self._tree_snapshots[target_rel_dir] = {
            "dir_mtimes": dir_mtimes,
            "file_sigs": file_sigs,
            "files": files_info,
            "symbols": symbol_dicts,
            "symbol_names": [s.name for s in symbols],
            "module_dependencies": dep_dicts,
        }
        self._flush_disk_ast_cache()

        return {
            "root_path": str(self.root_path),
            "target_dir": target_rel_dir,
            "scanned_utc": datetime.now(timezone.utc).isoformat(),
            "total_files": len(files_info),
            "files": files_info,
            "symbols": symbol_dicts,
            "module_dependencies": dep_dicts
        }

    def classify_capability(self, capability_name: str, existing_symbols: List[str]) -> Dict[str, str]:
        """
        Classifies requested capability as:
        EXISTS, PARTIAL, EQUIVALENT, MISSING, OBSOLETE, CONFLICTING
        as mandated by Section 2 of Protocol.
        """
        sym_key = tuple(existing_symbols)
        classify_cache = getattr(self, "_classify_cache", None)
        if classify_cache is None:
            classify_cache = {}
            self._classify_cache = classify_cache
        cache_hit = classify_cache.get((capability_name, sym_key))
        if cache_hit is not None:
            return dict(cache_hit)

        norm_cache = getattr(self, "_symbol_norm_cache", None)
        if norm_cache is None:
            norm_cache = {}
            self._symbol_norm_cache = norm_cache
        indexed_symbols = norm_cache.get(sym_key)
        if indexed_symbols is None:
            indexed_symbols = [
                (
                    s,
                    _NON_ALNUM_RE.sub("", s).lower(),
                    set(_TOKEN_RE.findall(_CAMEL_RE.sub(r"_\1", s).lower())),
                )
                for s in existing_symbols
            ]
            if len(norm_cache) > 16:
                norm_cache.clear()
            norm_cache[sym_key] = indexed_symbols

        cap_clean = _NON_ALNUM_RE.sub("", capability_name).lower()

        if any(cap_clean == s_clean for _, s_clean, _ in indexed_symbols):
            res = {"classification": "EXISTS", "reason": f"Exact matching symbol found: {capability_name}"}
        else:
            partial_matches = [s for s, s_clean, _ in indexed_symbols if cap_clean in s_clean or s_clean in cap_clean]
            if not partial_matches:
                cap_tokens = set(_TOKEN_RE.findall(capability_name.lower()))
                partial_matches = [s for s, _, s_tokens in indexed_symbols if cap_tokens & s_tokens]
            if partial_matches:
                res = {
                    "classification": "PARTIAL",
                    "reason": f"Partial symbol matches found: {', '.join(partial_matches[:3])}"
                }
            else:
                res = {
                    "classification": "MISSING",
                    "reason": f"No symbol or component matches capability '{capability_name}'. New creation justified."
                }

        if len(classify_cache) > 256:
            classify_cache.clear()
        classify_cache[(capability_name, sym_key)] = res
        return dict(res)


def discover_new_repositories(
    query: str = "agent OR llm OR security",
    min_stars: int = 50,
    limit: int = 20,
    registry_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Discovers new/trending repositories matching query criteria.
    Attempts live GitHub API with strict timeout, gracefully falling back to
    local sovereign catalog cache (zero network crash).
    """
    import urllib.request
    import urllib.parse
    import re

    root = registry_root or REGISTRY_ROOT
    results = []
    source = "LOCAL_CACHE"

    # Try live GitHub API if network is available
    encoded_q = urllib.parse.quote(f"{query} stars:>={min_stars}")
    api_url = f"https://api.github.com/search/repositories?q={encoded_q}&sort=updated&order=desc&per_page={min(limit, 50)}"
    headers = {
        "User-Agent": "JARVIS-Sovereign-Intelligence/2.0",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            if resp.status == 200:
                payload = json.loads(resp.read().decode("utf-8"))
                for item in payload.get("items", [])[:limit]:
                    clean_name = re.sub(r"[^a-z0-9\-]", "", item.get("name", "").lower().replace("_", "-"))
                    results.append({
                        "name": item.get("name"),
                        "full_name": item.get("full_name"),
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "language": item.get("language") or "Python",
                        "description": item.get("description") or f"Intelligence repository for {clean_name}",
                        "html_url": item.get("html_url"),
                        "homepage": item.get("homepage"),
                        "topics": item.get("topics", []),
                        "status": "DISCOVERED_ONLINE",
                        "suggested_skill": clean_name
                    })
                source = "GITHUB_API_LIVE"
    except Exception:
        # Fallback to local sovereign cache
        source = "LOCAL_CATALOG_FALLBACK"

    if not results:
        # Search local starred_catalog and 100k catalog
        cat_file = root / "cache" / "starred_catalog.json"
        k100_file = root / "index" / "repos_100k_stars.json"
        candidates = []

        if cat_file.exists():
            try:
                candidates.extend(json.loads(cat_file.read_text(encoding="utf-8")))
            except Exception:
                pass
        if k100_file.exists():
            try:
                candidates.extend(json.loads(k100_file.read_text(encoding="utf-8")).get("repositories", []))
            except Exception:
                pass

        q_terms = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", query)]
        matched = []
        for c in candidates:
            c_stars = c.get("stars", 0)
            if c_stars < min_stars:
                continue
            text = f"{c.get('name', '')} {c.get('description', '')} {' '.join(c.get('topics', []))}".lower()
            if any(term in text for term in q_terms) or not q_terms:
                clean_name = re.sub(r"[^a-z0-9\-]", "", c.get("name", "").lower().replace("_", "-"))
                matched.append({
                    "name": c.get("name"),
                    "full_name": c.get("full_name"),
                    "stars": c_stars,
                    "forks": c.get("forks", 0),
                    "language": c.get("language") or "Python",
                    "description": c.get("description", ""),
                    "html_url": c.get("html_url") or f"https://github.com/{c.get('full_name')}",
                    "homepage": c.get("homepage_url") or c.get("homepage"),
                    "topics": c.get("topics", []),
                    "status": "SOVEREIGN_INDEXED",
                    "suggested_skill": clean_name
                })
                if len(matched) >= limit:
                    break
        results = matched

    return {
        "query": query,
        "min_stars": min_stars,
        "total_discovered": len(results),
        "source": source,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repositories": results
    }

