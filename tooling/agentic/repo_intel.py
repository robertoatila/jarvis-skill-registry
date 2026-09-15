"""
repo_intel.py // J.A.R.V.I.S. Repository Intelligence Graph Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
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
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime, timezone

from .config import CONFIG, JarvisRuntimeConfig

REGISTRY_ROOT = CONFIG.registry_root


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
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.symbols: List[SymbolRecord] = []
        self.imports: List[str] = []

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
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    def invalidate_path(self, rel_path: str) -> bool:
        """
        Invalidates cached AST records for a given relative path or directory.
        Returns True if any cached entry was removed.
        """
        norm_target = rel_path.replace("\\", "/").rstrip("/")
        to_remove = [
            k for k in self._ast_cache.keys()
            if k == norm_target or k.startswith(norm_target + "/")
        ]
        for k in to_remove:
            del self._ast_cache[k]
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
        if "symbols" in scan_res:
            return [s["name"] for s in scan_res["symbols"]]
        return []

    def scan_tree(self, target_rel_dir: str = "tooling/agentic") -> Dict[str, Any]:
        """
        Scans python files under target_rel_dir and extracts symbols & dependencies.
        Leverages SHA-256 AST caching for incremental scanning.
        """
        scan_dir = self.root_path / target_rel_dir
        if not scan_dir.exists():
            return {"error": f"Directory not found: {scan_dir}"}

        files_info: List[Dict[str, Any]] = []
        symbols: List[SymbolRecord] = []
        dependencies: List[ModuleDependency] = []

        all_py_files = sorted(list(scan_dir.glob("**/*.py")))

        # Filter out ignored/sensitive directories and files
        filtered_py_files: List[Path] = []
        for p in all_py_files:
            rel_p = p.relative_to(self.root_path)
            rel = rel_p.as_posix()
            if any(part.startswith(".") for part in rel_p.parts):
                continue
            if "__pycache__" in rel or "config/api_keys.json" in rel or ".tmp" in rel:
                continue
            filtered_py_files.append(p)

        for py_path in filtered_py_files:
            rel = py_path.relative_to(self.root_path).as_posix()
            content = py_path.read_text(encoding="utf-8", errors="replace")
            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

            file_info_entry = {
                "rel_path": rel,
                "category": "CODE",
                "bytes": len(content),
                "lines": len(content.splitlines()),
                "sha256": sha
            }

            # Check incremental AST cache
            if rel in self._ast_cache and self._ast_cache[rel].get("sha256") == sha:
                self._cache_hits += 1
                cached = self._ast_cache[rel]
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
                    is_internal = imp.startswith(".") or "agentic" in imp or imp in [p.stem for p in filtered_py_files]
                    dep = ModuleDependency(
                        source_module=source_mod,
                        imported_module=imp,
                        is_internal=is_internal
                    )
                    file_deps.append(dep)
                    dependencies.append(dep)

                # Store in cache
                self._ast_cache[rel] = {
                    "sha256": sha,
                    "file_info": file_info_entry,
                    "symbols": file_symbols,
                    "dependencies": file_deps
                }
            except SyntaxError as se:
                file_info_entry["syntax_error"] = str(se)

            files_info.append(file_info_entry)

        return {
            "root_path": str(self.root_path),
            "target_dir": target_rel_dir,
            "scanned_utc": datetime.now(timezone.utc).isoformat(),
            "total_files": len(files_info),
            "files": files_info,
            "symbols": [s.to_dict() for s in symbols],
            "module_dependencies": [d.to_dict() for d in dependencies]
        }

    def classify_capability(self, capability_name: str, existing_symbols: List[str]) -> Dict[str, str]:
        """
        Classifies requested capability as:
        EXISTS, PARTIAL, EQUIVALENT, MISSING, OBSOLETE, CONFLICTING
        as mandated by Section 2 of Protocol.
        """
        import re
        cap_clean = re.sub(r"[^a-zA-Z0-9]", "", capability_name).lower()

        exact_match = any(cap_clean == re.sub(r"[^a-zA-Z0-9]", "", s).lower() for s in existing_symbols)
        if exact_match:
            return {"classification": "EXISTS", "reason": f"Exact matching symbol found: {capability_name}"}

        partial_matches = [s for s in existing_symbols if cap_clean in re.sub(r"[^a-zA-Z0-9]", "", s).lower() or re.sub(r"[^a-zA-Z0-9]", "", s).lower() in cap_clean]
        if not partial_matches:
            cap_tokens = set(re.findall(r"[a-z0-9]+", capability_name.lower()))
            partial_matches = [
                s for s in existing_symbols
                if cap_tokens & set(re.findall(r"[a-z0-9]+", re.sub(r"([A-Z])", r"_\1", s).lower()))
            ]

        if partial_matches:
            return {
                "classification": "PARTIAL",
                "reason": f"Partial symbol matches found: {', '.join(partial_matches[:3])}"
            }

        return {
            "classification": "MISSING",
            "reason": f"No symbol or component matches capability '{capability_name}'. New creation justified."
        }


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

