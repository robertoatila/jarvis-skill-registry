#!/usr/bin/env python3
"""Deterministic, offline contract checks for the files this repository distributes.

Pure Python standard library.  The checks answer narrow structural questions:

- ``adapters``          every ``adapters/*/adapter.json`` conforms to ``schemas/adapter.schema.json``
- ``schema-instances``  every ``schemas/<x>.json`` conforms to its sibling ``schemas/<x>.schema.json``
- ``json-parse``        distributed ``.json``/``.jsonl`` files parse (legacy export text markers excluded)
- ``agents``            every ``agents/*.md`` has usable frontmatter (name == file stem, description, tools)
- ``skills``            every ``skills/*/SKILL.md`` declares name == directory and a one-line description
- ``python-compat``     Python sources parse as 3.10 and do not call 3.12-only ``Path.is_junction`` unguarded
- ``vault-links``       wikilinks in the numbered root vault notes resolve inside the checkout (warnings)

What a PASS means: these structural rules held for this checkout.  It is not a
security audit, not release evidence and not a substitute for the direct
evidence gates; ``evidence/current.json`` stays the release authority.

The embedded JSON Schema evaluator implements only the keywords the repository
schemas use.  A schema that uses any other validation keyword is reported as an
error instead of being silently accepted.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0.0"

# Sixteen historical text-marker artifacts under exports/ carry a .json extension
# without being JSON (documented in reports/reanalysis/2026-10-01-public-system-audit.md).
# They are preserved as legacy history and deliberately not parsed here.
JSON_PARSE_EXCLUDED_DIRS = ("exports",)
WALK_SKIPPED_DIRS = frozenset(
    {".git", "node_modules", "__pycache__", ".venv", "venv", "test-results", "playwright-report", "JARVIS"}
)
PYTHON_SOURCE_DIRS = ("tooling", "tests", "benchmarks", "examples")
PYTHON_SOURCE_FILES = ("jarvis.py", "run_tests.py")
MINIMUM_PYTHON = (3, 10)


# --------------------------------------------------------------------------- #
# Minimal JSON Schema evaluator (draft 2020-12 subset used by schemas/)
# --------------------------------------------------------------------------- #

_ANNOTATION_KEYWORDS = frozenset(
    {"$schema", "$id", "$comment", "title", "description", "default", "examples", "format", "deprecated", "readOnly", "writeOnly"}
)
_SUPPORTED_KEYWORDS = frozenset(
    {
        "type", "enum", "const", "properties", "required", "additionalProperties", "items",
        "pattern", "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems",
        "uniqueItems", "anyOf", "allOf", "oneOf", "not", "if", "then", "else", "$ref", "$defs", "definitions",
    }
)


class UnsupportedSchemaError(ValueError):
    """The schema uses a validation keyword this evaluator does not implement."""


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    if expected == "integer":
        return (isinstance(value, int) and not isinstance(value, bool)) or (
            isinstance(value, float) and value.is_integer()
        )
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    raise UnsupportedSchemaError(f"unsupported type name: {expected!r}")


def _json_equal(left: Any, right: Any) -> bool:
    """JSON equality: booleans are not numbers, 1 == 1.0."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_json_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_json_equal(left[k], right[k]) for k in left)
    return type(left) is type(right) and left == right


def _resolve_ref(ref: str, root_schema: Any) -> Any:
    if not ref.startswith("#"):
        raise UnsupportedSchemaError(f"only local $ref is supported: {ref!r}")
    node = root_schema
    for raw_part in ref[1:].split("/"):
        if not raw_part:
            continue
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise UnsupportedSchemaError(f"unresolvable $ref: {ref!r}")
        node = node[part]
    return node


def validate_instance(instance: Any, schema: Any, root_schema: Any | None = None, path: str = "$") -> list[str]:
    """Return human-readable violations of ``schema`` by ``instance`` (empty when valid)."""
    root_schema = schema if root_schema is None else root_schema
    if schema is True:
        return []
    if schema is False:
        return [f"{path}: no value is allowed here"]
    if not isinstance(schema, dict):
        raise UnsupportedSchemaError(f"schema at {path} is not an object or boolean")

    unknown = [
        key for key in schema
        if key not in _SUPPORTED_KEYWORDS and key not in _ANNOTATION_KEYWORDS and not key.startswith("x-")
    ]
    if unknown:
        raise UnsupportedSchemaError(f"unsupported schema keyword(s) at {path}: {sorted(unknown)}")

    errors: list[str] = []

    if "$ref" in schema:
        errors += validate_instance(instance, _resolve_ref(schema["$ref"], root_schema), root_schema, path)

    if "type" in schema:
        expected = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_json_type_matches(instance, name) for name in expected):
            errors.append(f"{path}: expected type {'/'.join(expected)}, found {type(instance).__name__}")
            return errors

    if "const" in schema and not _json_equal(instance, schema["const"]):
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and not any(_json_equal(instance, option) for option in schema["enum"]):
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']!r}")

    if isinstance(instance, str):
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: {instance!r} does not match pattern {schema['pattern']!r}")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} is below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} is above maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems") is True:
            for index, item in enumerate(instance):
                if any(_json_equal(item, earlier) for earlier in instance[:index]):
                    errors.append(f"{path}[{index}]: duplicate item violates uniqueItems")
                    break
        if "items" in schema:
            for index, item in enumerate(instance):
                errors += validate_instance(item, schema["items"], root_schema, f"{path}[{index}]")

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in instance:
                errors.append(f"{path}: missing required property {name!r}")
        for name, value in instance.items():
            if name in properties:
                errors += validate_instance(value, properties[name], root_schema, f"{path}.{name}")
            elif "additionalProperties" in schema:
                additional = schema["additionalProperties"]
                if additional is False:
                    errors.append(f"{path}: unexpected property {name!r}")
                elif additional is not True:
                    errors += validate_instance(value, additional, root_schema, f"{path}.{name}")

    for index, branch in enumerate(schema.get("allOf", [])):
        errors += validate_instance(instance, branch, root_schema, f"{path}<allOf {index}>")
    if "anyOf" in schema and not any(
        not validate_instance(instance, branch, root_schema, path) for branch in schema["anyOf"]
    ):
        errors.append(f"{path}: does not satisfy any anyOf branch")
    if "oneOf" in schema:
        matches = sum(1 for branch in schema["oneOf"] if not validate_instance(instance, branch, root_schema, path))
        if matches != 1:
            errors.append(f"{path}: satisfies {matches} oneOf branches, expected exactly 1")
    if "not" in schema and not validate_instance(instance, schema["not"], root_schema, path):
        errors.append(f"{path}: matches a schema it must not match")
    if "if" in schema:
        if not validate_instance(instance, schema["if"], root_schema, path):
            if "then" in schema:
                errors += validate_instance(instance, schema["then"], root_schema, path)
        elif "else" in schema:
            errors += validate_instance(instance, schema["else"], root_schema, path)

    return errors


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


@dataclass
class CheckResult:
    name: str
    checked: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.errors:
            return "FAIL"
        return "PASS_WITH_WARNINGS" if self.warnings else "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "checked": self.checked,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _load_json(path: Path) -> Any:
    # utf-8-sig: several Windows-authored files carry a BOM.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _walk_files(root: Path, suffixes: Sequence[str]) -> Iterable[Path]:
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda item: item.name)
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name not in WALK_SKIPPED_DIRS:
                    stack.append(entry)
            elif entry.suffix.lower() in suffixes:
                yield entry


def _distributed_files(root: Path, suffixes: Sequence[str]) -> list[Path]:
    """Files Git distributes, so ignored local runtime state is never judged.

    Falls back to a filesystem walk when the checkout has no Git metadata
    (for example an extracted source archive).
    """
    try:
        listing = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=True,
            timeout=60,
        ).stdout.decode("utf-8", errors="surrogateescape")
    except (OSError, subprocess.SubprocessError):
        return list(_walk_files(root, suffixes))
    files = []
    for name in listing.split("\0"):
        if name and Path(name).suffix.lower() in suffixes:
            candidate = root / name
            if candidate.is_file() and not candidate.is_symlink():
                files.append(candidate)
    return sorted(files)


_FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_FRONTMATTER_ANYWHERE = re.compile(r"(?m)^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*$", re.DOTALL)


def read_frontmatter(text: str) -> tuple[dict[str, Any] | None, bool]:
    """Parse the small YAML subset used by agents/ and skills/.

    Returns ``(mapping, at_start)``.  ``mapping`` is None when no frontmatter
    block exists.  Values are top-level ``key: scalar`` pairs and
    ``key:`` + ``- item`` lists; nested mappings are kept as raw strings.
    """
    body = text.lstrip("\ufeff")
    match = _FRONTMATTER.match(body)
    at_start = match is not None
    if match is None:
        match = _FRONTMATTER_ANYWHERE.search(body)
    if match is None:
        return None, False

    mapping: dict[str, Any] = {}
    current_key: str | None = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$", line)
        if top:
            current_key = top.group(1)
            value = top.group(2).strip()
            mapping[current_key] = _unquote(value) if value else []
            continue
        item = re.match(r"^[ \t]+-[ \t]+(.*)$", line)
        if item and current_key is not None and isinstance(mapping.get(current_key), list):
            mapping[current_key].append(_unquote(item.group(1).strip()))
    return mapping, at_start


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def check_adapters(root: Path) -> CheckResult:
    result = CheckResult("adapters")
    schema_path = root / "schemas" / "adapter.schema.json"
    try:
        schema = _load_json(schema_path)
    except (OSError, ValueError) as exc:
        result.errors.append(f"schemas/adapter.schema.json: unreadable ({exc})")
        return result

    seen_ids: dict[str, str] = {}
    adapter_dirs = sorted(p for p in (root / "adapters").iterdir() if p.is_dir()) if (root / "adapters").is_dir() else []
    if not adapter_dirs:
        result.errors.append("adapters/: no adapter directories found")
    for directory in adapter_dirs:
        manifest = directory / "adapter.json"
        rel = _rel(manifest, root)
        result.checked += 1
        if not manifest.is_file():
            result.errors.append(f"{rel}: missing")
            continue
        try:
            data = _load_json(manifest)
            violations = validate_instance(data, schema)
        except (OSError, ValueError) as exc:
            result.errors.append(f"{rel}: {exc}")
            continue
        result.errors += [f"{rel}: {violation}" for violation in violations]
        adapter_id = data.get("adapter_id") if isinstance(data, dict) else None
        if isinstance(adapter_id, str):
            if adapter_id in seen_ids:
                result.errors.append(f"{rel}: adapter_id {adapter_id!r} duplicates {seen_ids[adapter_id]}")
            seen_ids[adapter_id] = rel
            if not adapter_id.startswith(f"adp-{directory.name}-"):
                result.errors.append(
                    f"{rel}: adapter_id {adapter_id!r} does not start with 'adp-{directory.name}-'"
                )
    return result


def check_schema_instances(root: Path) -> CheckResult:
    result = CheckResult("schema-instances")
    schemas_dir = root / "schemas"
    if not schemas_dir.is_dir():
        result.errors.append("schemas/: missing")
        return result
    for schema_path in sorted(schemas_dir.glob("*.schema.json")):
        rel_schema = _rel(schema_path, root)
        try:
            schema = _load_json(schema_path)
        except (OSError, ValueError) as exc:
            result.errors.append(f"{rel_schema}: unreadable ({exc})")
            continue
        instance_path = schemas_dir / (schema_path.name[: -len(".schema.json")] + ".json")
        if not instance_path.is_file():
            continue
        result.checked += 1
        rel_instance = _rel(instance_path, root)
        try:
            violations = validate_instance(_load_json(instance_path), schema)
        except (OSError, ValueError) as exc:
            result.errors.append(f"{rel_instance}: {exc}")
            continue
        result.errors += [f"{rel_instance}: {violation}" for violation in violations[:10]]
    return result


def check_json_parse(root: Path) -> CheckResult:
    result = CheckResult("json-parse")
    for path in _distributed_files(root, (".json", ".jsonl")):
        rel = _rel(path, root)
        if rel.split("/", 1)[0] in JSON_PARSE_EXCLUDED_DIRS:
            continue
        result.checked += 1
        try:
            if path.suffix.lower() == ".json":
                _load_json(path)
            else:
                with path.open("r", encoding="utf-8-sig") as handle:
                    for number, line in enumerate(handle, start=1):
                        if line.strip():
                            try:
                                json.loads(line)
                            except ValueError as exc:
                                raise ValueError(f"line {number}: {exc}") from exc
        except (OSError, ValueError) as exc:
            result.errors.append(f"{rel}: {str(exc)[:200]}")
    return result


def check_agents(root: Path) -> CheckResult:
    result = CheckResult("agents")
    agents_dir = root / "agents"
    files = sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []
    if not files:
        result.errors.append("agents/: no agent definitions found")
    for path in files:
        rel = _rel(path, root)
        result.checked += 1
        try:
            mapping, at_start = read_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            result.errors.append(f"{rel}: unreadable ({exc})")
            continue
        if mapping is None or not at_start:
            result.errors.append(f"{rel}: YAML frontmatter must open the file")
            continue
        if mapping.get("name") != path.stem:
            result.errors.append(f"{rel}: frontmatter name {mapping.get('name')!r} != file stem {path.stem!r}")
        description = mapping.get("description")
        if not isinstance(description, str) or not description.strip():
            result.errors.append(f"{rel}: description is missing or empty")
        tools = mapping.get("tools")
        if not isinstance(tools, list) or not tools:
            result.errors.append(f"{rel}: tools must be a non-empty list")
    return result


def check_skills(root: Path) -> CheckResult:
    result = CheckResult("skills")
    skills_dir = root / "skills"
    directories = sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []
    if not directories:
        result.errors.append("skills/: no skill directories found")
    for directory in directories:
        manifest = directory / "SKILL.md"
        rel = _rel(manifest, root)
        result.checked += 1
        if not manifest.is_file():
            result.errors.append(f"{rel}: missing")
            continue
        try:
            mapping, at_start = read_frontmatter(manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            result.errors.append(f"{rel}: unreadable ({exc})")
            continue
        if mapping is None:
            result.errors.append(f"{rel}: no YAML frontmatter block")
            continue
        if not at_start:
            # Reported, not failed: the bytes of released skills are pinned by
            # releases/*/lockfiles, so moving the block needs a re-seal.
            result.warnings.append(f"{rel}: frontmatter is not at the start of the file; strict parsers will miss it")
        if mapping.get("name") != directory.name:
            result.errors.append(f"{rel}: frontmatter name {mapping.get('name')!r} != directory {directory.name!r}")
        description = mapping.get("description")
        if not isinstance(description, str) or not description.strip():
            result.errors.append(f"{rel}: description is missing, empty or not a one-line scalar")
    return result


class _JunctionVisitor(ast.NodeVisitor):
    """Find ``x.is_junction()`` calls not guarded by ``hasattr(x, 'is_junction')``."""

    def __init__(self) -> None:
        self.unguarded: list[int] = []
        self._guard_depth = 0

    @staticmethod
    def _mentions_hasattr_guard(node: ast.AST) -> bool:
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "hasattr"
                and len(child.args) == 2
                and isinstance(child.args[1], ast.Constant)
                and child.args[1].value == "is_junction"
            ):
                return True
        return False

    def _visit_guarded(self, node: ast.AST) -> None:
        guarded = self._mentions_hasattr_guard(node)
        self._guard_depth += int(guarded)
        self.generic_visit(node)
        self._guard_depth -= int(guarded)

    visit_BoolOp = _visit_guarded
    visit_If = _visit_guarded
    visit_IfExp = _visit_guarded

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "is_junction" and not self._guard_depth:
            self.unguarded.append(node.lineno)
        self.generic_visit(node)


def check_python_compat(root: Path) -> CheckResult:
    result = CheckResult("python-compat")
    sources: list[Path] = [root / name for name in PYTHON_SOURCE_FILES if (root / name).is_file()]
    for directory in PYTHON_SOURCE_DIRS:
        if (root / directory).is_dir():
            sources += list(_walk_files(root / directory, (".py",)))
    for path in sources:
        rel = _rel(path, root)
        result.checked += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=rel, feature_version=MINIMUM_PYTHON)
        except SyntaxError as exc:
            result.errors.append(f"{rel}:{exc.lineno}: not valid Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} syntax ({exc.msg})")
            continue
        except (OSError, UnicodeError) as exc:
            result.errors.append(f"{rel}: unreadable ({exc})")
            continue
        visitor = _JunctionVisitor()
        visitor.visit(tree)
        for line in visitor.unguarded:
            result.errors.append(
                f"{rel}:{line}: Path.is_junction() exists only on Python >= 3.12; guard it with hasattr()"
            )
    return result


_WIKILINK = re.compile(r"\[\[([^\]\[|#]+)(?:#[^\]\[|]*)?(?:\|[^\]\[]*)?\]\]")
_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)


def check_vault_links(root: Path) -> CheckResult:
    """Unresolved wikilinks are warnings: the vault is a human projection surface."""
    result = CheckResult("vault-links")
    notes = sorted(p for p in root.glob("[0-9][0-9] - *.md") if p.is_file())
    stems = {p.stem for p in root.glob("*.md")}
    for note in notes:
        result.checked += 1
        try:
            text = _CODE_FENCE.sub("", note.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError) as exc:
            result.errors.append(f"{note.name}: unreadable ({exc})")
            continue
        missing: list[str] = []
        for match in _WIKILINK.finditer(text):
            target = match.group(1).strip().rstrip("\\").strip()
            if not target or target.startswith("JARVIS/"):
                continue  # JARVIS/ is the ignored, locally generated projection.
            candidate = root / target
            if candidate.exists() or (root / f"{target}.md").exists() or target in stems:
                continue
            if target not in missing:
                missing.append(target)
        if missing:
            preview = ", ".join(missing[:5]) + (" …" if len(missing) > 5 else "")
            result.warnings.append(f"{note.name}: {len(missing)} unresolved wikilink(s): {preview}")
    return result


CHECKS: dict[str, Callable[[Path], CheckResult]] = {
    "adapters": check_adapters,
    "schema-instances": check_schema_instances,
    "json-parse": check_json_parse,
    "agents": check_agents,
    "skills": check_skills,
    "python-compat": check_python_compat,
    "vault-links": check_vault_links,
}


def run_checks(root: Path = ROOT, names: Sequence[str] | None = None) -> dict[str, Any]:
    selected = list(names) if names else list(CHECKS)
    results = [CHECKS[name](root) for name in selected]
    failed = [r.name for r in results if r.errors]
    warned = [r.name for r in results if r.warnings and not r.errors]
    status = "FAIL" if failed else ("PASS_WITH_WARNINGS" if warned else "PASS")
    return {
        "audit": "repository-contracts",
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "scope": "structural contract checks only; not a security audit or release evidence",
        "minimum_python": f"{MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}",
        "checks": [r.to_dict() for r in results],
        "failed_checks": failed,
        "error_count": sum(len(r.errors) for r in results),
        "warning_count": sum(len(r.warnings) for r in results),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline structural contract checks for this repository.")
    parser.add_argument("--check", action="append", choices=sorted(CHECKS), help="Run only this check (repeatable)")
    parser.add_argument("--root", type=Path, default=ROOT, help="Checkout root (default: this repository)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--summary", action="store_true", help="Print one line per check instead of JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_checks(args.root.resolve(), args.check)
    if args.summary:
        for check in report["checks"]:
            print(
                f"{check['status']:<18} {check['name']:<17} checked={check['checked']}"
                f" errors={check['error_count']} warnings={check['warning_count']}"
            )
            for line in check["errors"]:
                print(f"    ERROR   {line}")
            for line in check["warnings"]:
                print(f"    WARNING {line}")
        print(f"STATUS: {report['status']}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] == "FAIL":
        return 1
    if args.strict and report["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
