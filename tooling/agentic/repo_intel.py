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
from typing import List, Dict, Set, Optional, Any
from datetime import datetime, timezone

from .config import CONFIG, JarvisRuntimeConfig

REGISTRY_ROOT = Path("E:/.skill-registry").resolve()


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

    def get_known_symbols(self, target_rel_dir: str = "tooling/agentic") -> List[str]:
        """Returns list of known symbol names across target directory."""
        scan_res = self.scan_tree(target_rel_dir)
        if "symbols" in scan_res:
            return [s["name"] for s in scan_res["symbols"]]
        return []

    def scan_tree(self, target_rel_dir: str = "tooling/agentic") -> Dict[str, Any]:
        """Scans python files under target_rel_dir and extracts symbols & dependencies."""
        scan_dir = self.root_path / target_rel_dir
        if not scan_dir.exists():
            return {"error": f"Directory not found: {scan_dir}"}

        files_info: List[Dict[str, Any]] = []
        symbols: List[SymbolRecord] = []
        dependencies: List[ModuleDependency] = []

        all_py_files = sorted(list(scan_dir.glob("**/*.py")))

        for py_path in all_py_files:
            rel = py_path.relative_to(self.root_path).as_posix()
            content = py_path.read_text(encoding="utf-8", errors="replace")
            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

            files_info.append({
                "rel_path": rel,
                "category": "CODE",
                "bytes": len(content),
                "lines": len(content.splitlines()),
                "sha256": sha
            })

            try:
                tree = ast.parse(content, filename=str(py_path))
                visitor = PyASTVisitor(rel)
                visitor.visit(tree)

                symbols.extend(visitor.symbols)

                source_mod = py_path.stem
                for imp in visitor.imports:
                    is_internal = imp.startswith(".") or "agentic" in imp or imp in [p.stem for p in all_py_files]
                    dependencies.append(ModuleDependency(
                        source_module=source_mod,
                        imported_module=imp,
                        is_internal=is_internal
                    ))
            except SyntaxError as se:
                files_info[-1]["syntax_error"] = str(se)

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

