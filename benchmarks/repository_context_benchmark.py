#!/usr/bin/env python3
"""Repository-scale deterministic context-admission benchmark for J.A.R.V.I.S. v0.2.0.

This benchmark reports raw serialized UTF-8 byte measurements and source
admission decisions. It does not convert byte reduction into provider-token,
quality, latency or dollar-savings claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.agentic.context_governor import ContextItem, ContextOverflowError, compile_context


BENCHMARK_ID = "repository-context-admission-v1"
FIXTURE_DIR = ROOT / "benchmarks" / "fixtures" / "repository_task"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
CLAIM_BOUNDARY = (
    "serialized UTF-8 bytes and source admission only; "
    "not provider token savings, quality gains, latency gains or dollar savings"
)
_ALLOWED_ROLES = {"required", "relevant", "duplicate", "stale", "irrelevant"}
_REQUIRED_ROLES = frozenset(_ALLOWED_ROLES)


def resolve_commit_sha() -> str:
    github_sha = os.environ.get("GITHUB_SHA", "").strip()
    if len(github_sha) == 40 and all(ch in "0123456789abcdefABCDEF" for ch in github_sha):
        return github_sha.lower()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"
    value = completed.stdout.strip()
    return value if value else "UNKNOWN"


def _safe_source_path(fixture_dir: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("fixture source path must be a non-empty string")
    raw = Path(relative)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError(f"fixture source escapes fixture directory: {relative}")
    resolved = (fixture_dir / raw).resolve()
    try:
        resolved.relative_to(fixture_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"fixture source escapes fixture directory: {relative}") from exc
    return resolved


def _validate_manifest(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("repository benchmark manifest must be an object")
    if value.get("schema_version") != 1:
        raise ValueError("unsupported repository benchmark manifest schema")
    if value.get("benchmark") != BENCHMARK_ID:
        raise ValueError("unexpected repository benchmark id")

    task = value.get("task")
    budget = value.get("budget_bytes")
    now = value.get("now")
    raw_items = value.get("items")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("repository benchmark task is required")
    if type(budget) is not int or budget <= 0:
        raise ValueError("budget_bytes must be a positive integer")
    if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(float(now)):
        raise ValueError("now must be a finite number")
    if not isinstance(raw_items, list) or len(raw_items) <= 6:
        raise ValueError("repository benchmark fixture must contain more than six items")

    allowed = {"source", "path", "priority", "required", "role", "valid_until"}
    sources: set[str] = set()
    paths: set[str] = set()
    roles: set[str] = set()
    items: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict) or set(raw) - allowed:
            raise ValueError("invalid repository benchmark item")
        source = raw.get("source")
        path = raw.get("path")
        priority = raw.get("priority")
        required = raw.get("required")
        role = raw.get("role")
        valid_until = raw.get("valid_until")

        if not isinstance(source, str) or not source.strip() or source in sources:
            raise ValueError("benchmark sources must be unique non-empty strings")
        if not isinstance(path, str) or not path.strip() or path in paths:
            raise ValueError("benchmark source paths must be unique non-empty strings")
        if type(priority) is not int:
            raise ValueError(f"invalid priority for {source}")
        if type(required) is not bool:
            raise ValueError(f"invalid required flag for {source}")
        if role not in _ALLOWED_ROLES:
            raise ValueError(f"invalid role for {source}")
        if role == "required" and not required:
            raise ValueError(f"required role must set required=true: {source}")
        if role != "required" and required:
            raise ValueError(f"only required role may set required=true: {source}")
        if role == "stale" and valid_until is None:
            raise ValueError(f"stale role requires valid_until: {source}")
        if valid_until is not None and (
            isinstance(valid_until, bool)
            or not isinstance(valid_until, (int, float))
            or not math.isfinite(float(valid_until))
        ):
            raise ValueError(f"invalid valid_until for {source}")

        normalized = {
            "source": source,
            "path": path,
            "priority": priority,
            "required": required,
            "role": role,
            "valid_until": float(valid_until) if valid_until is not None else None,
        }
        items.append(normalized)
        sources.add(source)
        paths.add(path)
        roles.add(role)

    if not _REQUIRED_ROLES.issubset(roles):
        raise ValueError("fixture must represent required/relevant/duplicate/stale/irrelevant roles")

    return {
        "schema_version": 1,
        "benchmark": BENCHMARK_ID,
        "task": task.strip(),
        "budget_bytes": budget,
        "now": float(now),
        "items": items,
    }


def load_fixture(manifest_path: Path | str = MANIFEST_PATH) -> dict[str, Any]:
    manifest_path = Path(manifest_path).resolve()
    fixture_dir = manifest_path.parent
    try:
        manifest_raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to load repository benchmark manifest: {manifest_path}") from exc

    manifest = _validate_manifest(manifest_raw)
    loaded_items: list[dict[str, Any]] = []
    for item in manifest["items"]:
        source_path = _safe_source_path(fixture_dir, item["path"])
        try:
            content = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"unable to load benchmark source: {item['path']}") from exc
        if not content.strip():
            raise ValueError(f"benchmark source is empty: {item['path']}")
        loaded_items.append({**item, "content": content.rstrip("\n")})

    return {**manifest, "items": loaded_items}


def _context_items(fixture: dict[str, Any]) -> list[ContextItem]:
    return [
        ContextItem(
            content=item["content"],
            source=item["source"],
            priority=item["priority"],
            required=item["required"],
            valid_until=item["valid_until"],
        )
        for item in fixture["items"]
    ]


def _canonical_fixture_sha256(fixture: dict[str, Any]) -> str:
    payload = json.dumps(
        fixture,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _naive_serialized_bytes(items: list[ContextItem], now: float) -> int:
    payload = [
        {"content": item.content, "sources": [item.source]}
        for item in items
        if item.valid_until is None or item.valid_until > now
    ]
    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return len(text.encode("utf-8"))


def evaluate_fixture(
    fixture: dict[str, Any],
    *,
    commit_sha: str,
    token_estimator: Callable[[str], int] | None = None,
    token_estimation_method: str | None = None,
) -> dict[str, Any]:
    if token_estimator is not None and (
        not isinstance(token_estimation_method, str)
        or not token_estimation_method.strip()
    ):
        raise ValueError("TOKEN_ESTIMATION_METHOD_REQUIRED")
    if token_estimator is None and token_estimation_method is not None:
        raise ValueError("TOKEN_ESTIMATOR_REQUIRED")

    fixture = _validate_manifest({
        key: value
        for key, value in fixture.items()
        if key != "items"
    } | {
        "items": [
            {key: value for key, value in item.items() if key != "content"}
            for item in fixture.get("items", [])
        ]
    }) | {
        "items": fixture.get("items", [])
    }

    items = _context_items(fixture)
    now = fixture["now"]
    budget = fixture["budget_bytes"]
    sources_considered = sorted(item.source for item in items)
    required_sources = sorted(
        item["source"]
        for item in fixture["items"]
        if item["required"] and (item["valid_until"] is None or item["valid_until"] > now)
    )
    stale_sources = sorted(
        item["source"]
        for item in fixture["items"]
        if item["valid_until"] is not None and item["valid_until"] <= now
    )
    irrelevant_sources = sorted(
        item["source"] for item in fixture["items"] if item["role"] == "irrelevant"
    )
    duplicate_sources = sorted(
        item["source"] for item in fixture["items"] if item["role"] == "duplicate"
    )
    role_counts = dict(sorted(Counter(item["role"] for item in fixture["items"]).items()))
    raw_source_bytes = sum(len(item["content"].encode("utf-8")) for item in fixture["items"])
    naive_bytes = _naive_serialized_bytes(items, now)

    base = {
        "schema_version": "1.0.0",
        "benchmark": BENCHMARK_ID,
        "status": "FAIL",
        "failure_reason": None,
        "commit_sha": str(commit_sha),
        "fixture_sha256": _canonical_fixture_sha256(fixture),
        "task": fixture["task"],
        "declared_budget": {"value": budget, "unit": "serialized_utf8_bytes"},
        "raw_source_bytes": raw_source_bytes,
        "naive_serialized_bytes": naive_bytes,
        "bounded_serialized_bytes": None,
        "bytes_not_admitted": None,
        "sources_considered": sources_considered,
        "sources_loaded": [],
        "sources_omitted": list(sources_considered),
        "required_sources": required_sources,
        "stale_sources": stale_sources,
        "irrelevant_sources": irrelevant_sources,
        "duplicate_sources": duplicate_sources,
        "role_counts": role_counts,
        "token_estimate": {
            "status": "UNKNOWN",
            "value": None,
            "method": None,
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "invariants": {},
    }

    try:
        compiled, receipt = compile_context(
            items,
            budget,
            now=now,
            token_estimator=token_estimator,
            token_estimation_method=token_estimation_method,
        )
    except (ContextOverflowError, ValueError) as exc:
        base["failure_reason"] = str(exc)
        return base

    loaded = sorted(receipt.sources_loaded)
    omitted = sorted(receipt.provenance.get("omitted_sources", []))
    missing_required = sorted(set(required_sources) - set(loaded))
    source_accounting = sorted(set(loaded) | set(omitted)) == sources_considered
    token_qualified = (
        receipt.token_estimate is None
        and receipt.token_estimation_method is None
    ) or (
        receipt.token_estimate is not None
        and isinstance(receipt.token_estimation_method, str)
        and bool(receipt.token_estimation_method.strip())
    )

    invariants = {
        "fixture_scale_gt_six": len(fixture["items"]) > 6,
        "all_required_roles_present": _REQUIRED_ROLES.issubset(role_counts),
        "receipt_matches_payload": receipt.serialized_bytes == len(compiled.encode("utf-8")),
        "bounded_within_declared_budget": receipt.serialized_bytes <= budget,
        "required_context_admitted": not missing_required,
        "stale_context_omitted": set(stale_sources).issubset(omitted),
        "source_accounting_complete": source_accounting,
        "duplicate_role_represented": bool(duplicate_sources),
        "irrelevant_role_represented": bool(irrelevant_sources),
        "qualified_token_estimate_only": token_qualified,
        "demonstrates_bounded_admission": naive_bytes > receipt.serialized_bytes,
    }
    failed = [name for name, passed in invariants.items() if not passed]

    base.update({
        "status": "PASS" if not failed else "FAIL",
        "failure_reason": None if not failed else "INVARIANT_FAILURE:" + ",".join(sorted(failed)),
        "bounded_serialized_bytes": receipt.serialized_bytes,
        "bytes_not_admitted": naive_bytes - receipt.serialized_bytes,
        "sources_loaded": loaded,
        "sources_omitted": omitted,
        "required_sources_missing": missing_required,
        "selection_reason": receipt.selection_reason,
        "content_hash": receipt.content_hash,
        "byte_measurement_method": receipt.provenance.get("byte_measurement_method"),
        "token_estimate": {
            "status": "ESTIMATED" if receipt.token_estimate is not None else "UNKNOWN",
            "value": receipt.token_estimate,
            "method": receipt.token_estimation_method,
        },
        "invariants": invariants,
    })
    return base


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the repository-scale JARVIS context-admission benchmark."
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=MANIFEST_PATH,
        help="Path to the public deterministic fixture manifest.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional canonical JSON output path.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        fixture = load_fixture(args.fixture)
        result = evaluate_fixture(fixture, commit_sha=resolve_commit_sha())
    except (ValueError, OSError) as exc:
        result = {
            "schema_version": "1.0.0",
            "benchmark": BENCHMARK_ID,
            "status": "FAIL",
            "failure_reason": str(exc),
            "commit_sha": resolve_commit_sha(),
            "claim_boundary": CLAIM_BOUNDARY,
        }

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.output is not None:
        _write_json(args.output, result)
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
