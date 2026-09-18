#!/usr/bin/env python3
"""Narrow deterministic audit for current-facing JARVIS documentation claims."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "evidence" / "current.json"
SCHEMA_VERSION = "1.0.0"
HISTORICAL_MARKER = "Status: HISTORICAL"

DIRECT_AUTHORITY_PHRASES = (
    "CI runs this portable Python/runtime path on Windows, Ubuntu and macOS",
    "CI additionally exercises Windows compatibility/governance",
    "Changes are not complete until the relevant test matrix is green",
    "broader governance/distribution suites used by CI",
    "documented in CI",
    "CI green on the launch PR and on the merged main commit",
    "CI is red",
)

NODE_ABSENCE_PATTERNS = (
    re.compile(r"\bno current Node test entry point is present\b", re.IGNORECASE),
    re.compile(r"\bno Node test entry point(?:s)? (?:is|are) present\b", re.IGNORECASE),
)

POSITIVE_SAVINGS_PATTERNS = (
    re.compile(r"\b(?:save|saves|saved|saving|reduce|reduces|reduced|reducing)\b[^\n.]{0,80}\b(?:tokens?|token costs?|costs?|dollars?)\b", re.IGNORECASE),
    re.compile(r"\b(?:token|cost|dollar)[ -]?(?:saving|savings|reduction)s?\b", re.IGNORECASE),
)

WHOLE_SYSTEM_PATTERNS = (
    re.compile(r"\b(?:fully|completely)\s+(?:validated|certified|production[- ]ready)\b", re.IGNORECASE),
    re.compile(r"\b(?:whole|entire)[ -]system\b[^\n.]{0,50}\b(?:validated|certified|production[- ]ready)\b", re.IGNORECASE),
)

NEGATION_MARKERS = (
    "does not claim",
    "do not claim",
    "not claim",
    "no claim",
    "is not certified",
    "not certified",
    "not validated",
    "unvalidated",
    "not production-ready",
    "not production ready",
)


@dataclass(frozen=True)
class Violation:
    code: str
    path: str
    line: int
    message: str
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to load evidence manifest: {path}") from exc

    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported evidence manifest schema")

    validation = value.get("validation")
    if not isinstance(validation, dict):
        raise ValueError("validation evidence section is required")
    if validation.get("authority") != "direct_evidence_gates":
        raise ValueError("validation authority must be direct_evidence_gates")
    if validation.get("github_actions_authority") is not False:
        raise ValueError("github_actions_authority must be false")

    release = value.get("release")
    if not isinstance(release, dict) or release.get("version") != "0.2.0":
        raise ValueError("release evidence must identify v0.2.0")
    if release.get("evidence_status") not in {"INCOMPLETE", "PASS"}:
        raise ValueError("invalid release evidence_status")

    context = value.get("context_benchmark")
    if not isinstance(context, dict) or context.get("metric") != "serialized_utf8_bytes":
        raise ValueError("context benchmark metric must be serialized_utf8_bytes")

    provider = value.get("provider_fixture")
    if not isinstance(provider, dict):
        raise ValueError("provider_fixture evidence is required")
    if provider.get("network") is not False or provider.get("credentials") is not False:
        raise ValueError("deterministic provider fixture must declare network=false and credentials=false")

    node = value.get("node_tests")
    if not isinstance(node, dict) or node.get("status") != "PRESENT":
        raise ValueError("node_tests status must be PRESENT")
    if not isinstance(node.get("entrypoints"), list) or not node["entrypoints"]:
        raise ValueError("node_tests entrypoints must be non-empty")

    claim = value.get("claim_audit")
    if not isinstance(claim, dict) or claim.get("status") != "IMPLEMENTED":
        raise ValueError("claim_audit status must be IMPLEMENTED")
    if not isinstance(claim.get("governed_docs"), list) or not claim["governed_docs"]:
        raise ValueError("claim_audit governed_docs must be non-empty")

    return value


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_negated(line: str) -> bool:
    lowered = line.casefold()
    return any(marker in lowered for marker in NEGATION_MARKERS)


def _historical(text: str) -> bool:
    head = "\n".join(text.splitlines()[:8])
    return HISTORICAL_MARKER.casefold() in head.casefold()


def _violation(code: str, path: str, line: int, message: str, excerpt: str) -> Violation:
    clean = " ".join(excerpt.strip().split())
    return Violation(code, path, line, message, clean[:240])


def validate_manifest_sources(root: Path, manifest: dict[str, Any]) -> list[Violation]:
    violations: list[Violation] = []

    def require_file(path: str, code: str) -> None:
        if not (root / path).is_file():
            violations.append(_violation(
                code,
                path,
                1,
                "machine evidence references a file that does not exist",
                path,
            ))

    for path in manifest["node_tests"]["entrypoints"]:
        require_file(path, "EVIDENCE_NODE_ENTRYPOINT_MISSING")
    require_file(manifest["provider_fixture"]["fixture"], "EVIDENCE_PROVIDER_FIXTURE_MISSING")
    require_file(manifest["context_benchmark"]["benchmark"], "EVIDENCE_CONTEXT_BENCHMARK_MISSING")
    for path in manifest["claim_audit"]["governed_docs"]:
        require_file(path, "EVIDENCE_GOVERNED_DOC_MISSING")
    return violations


def audit_text(path: str, text: str, manifest: dict[str, Any], *, node_tests_present: bool) -> list[Violation]:
    violations: list[Violation] = []
    historical = _historical(text)
    actions_authority = manifest["validation"]["github_actions_authority"]
    release_pass = manifest["release"]["evidence_status"] == "PASS"
    token_savings_allowed = manifest["context_benchmark"].get("token_savings_claim") is True
    cost_savings_allowed = manifest["context_benchmark"].get("cost_savings_claim") is True

    if node_tests_present:
        for pattern in NODE_ABSENCE_PATTERNS:
            for match in pattern.finditer(text):
                violations.append(_violation(
                    "NODE_TEST_ABSENCE_STALE",
                    path,
                    _line_number(text, match.start()),
                    "documentation says no Node test entry point exists, but current evidence lists Node entrypoints",
                    match.group(0),
                ))

    if not actions_authority and not historical:
        for phrase in DIRECT_AUTHORITY_PHRASES:
            start = 0
            while True:
                index = text.find(phrase, start)
                if index < 0:
                    break
                violations.append(_violation(
                    "GITHUB_ACTIONS_AUTHORITY_STALE",
                    path,
                    _line_number(text, index),
                    "current-facing documentation treats CI/GitHub Actions as validation authority",
                    phrase,
                ))
                start = index + len(phrase)

    for line_number, line in enumerate(text.splitlines(), start=1):
        if _is_negated(line):
            continue
        for pattern in POSITIVE_SAVINGS_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            lowered = match.group(0).casefold()
            is_token = "token" in lowered
            allowed = token_savings_allowed if is_token else cost_savings_allowed
            if not allowed:
                violations.append(_violation(
                    "UNSUPPORTED_RESOURCE_SAVINGS_CLAIM",
                    path,
                    line_number,
                    "resource-savings wording requires an explicit machine evidence metric",
                    line,
                ))
                break

        if not release_pass:
            for pattern in WHOLE_SYSTEM_PATTERNS:
                if pattern.search(line):
                    violations.append(_violation(
                        "WHOLE_SYSTEM_VALIDATION_REQUIRES_RELEASE_EVIDENCE",
                        path,
                        line_number,
                        "whole-system validation/certification wording requires release evidence_status=PASS",
                        line,
                    ))
                    break

    return violations


def audit_repository(root: Path = ROOT, manifest_path: Path | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    manifest_path = Path(manifest_path) if manifest_path is not None else root / "evidence" / "current.json"
    manifest = load_manifest(manifest_path)
    violations = validate_manifest_sources(root, manifest)
    node_tests_present = all((root / path).is_file() for path in manifest["node_tests"]["entrypoints"])

    audited_docs: list[str] = []
    for path in manifest["claim_audit"]["governed_docs"]:
        target = root / path
        if not target.is_file():
            continue
        audited_docs.append(path)
        text = target.read_text(encoding="utf-8")
        violations.extend(
            audit_text(path, text, manifest, node_tests_present=node_tests_present)
        )

    violations = sorted(violations, key=lambda item: (item.path, item.line, item.code))
    try:
        rendered_manifest = str(manifest_path.relative_to(root))
    except ValueError:
        rendered_manifest = str(manifest_path)

    return {
        "schema_version": SCHEMA_VERSION,
        "audit": "documentation-claims",
        "status": "PASS" if not violations else "FAIL",
        "manifest": rendered_manifest,
        "validation_authority": manifest["validation"]["authority"],
        "github_actions_authority": manifest["validation"]["github_actions_authority"],
        "release_evidence_status": manifest["release"]["evidence_status"],
        "audited_docs": audited_docs,
        "violation_count": len(violations),
        "violations": [item.to_dict() for item in violations],
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Audit current-facing documentation claims against machine evidence.")
    value.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    value.add_argument("--output", type=Path)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        report = audit_repository(ROOT, args.manifest)
    except (ValueError, OSError) as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "audit": "documentation-claims",
            "status": "FAIL",
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "violation_count": None,
            "violations": [],
        }

    if args.output is not None:
        write_report(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
