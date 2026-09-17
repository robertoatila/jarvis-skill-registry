#!/usr/bin/env python3
"""Reproducible repository-scale Context Governor admission benchmark.

The benchmark measures serialized UTF-8 bytes admitted by compile_context
against an explicit naive envelope containing every fixture item. It does not
claim provider token counts, quality gains, latency gains or dollar savings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.agentic.context_governor import (
    ContextItem,
    ContextOverflowError,
    compile_context,
)

FIXTURE_PATH = ROOT / "benchmarks" / "fixtures" / "repository_context_task.json"
BUDGET_BYTES = 2200
NOW = 1_800_000_000.0
BENCHMARK_ID = "repository-context-admission-v2"
CLAIM_BOUNDARY = (
    "serialized UTF-8 bytes only; not provider token counts, quality, latency or cost"
)


def _canonical_fixture_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_fixture(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("benchmark fixture must be a JSON object")
    if value.get("schema_version") != 1:
        raise ValueError("unsupported benchmark fixture schema")
    if value.get("benchmark") != BENCHMARK_ID:
        raise ValueError("unexpected benchmark fixture id")
    task = value.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("benchmark fixture task is required")

    budget = value.get("budget_bytes")
    if type(budget) is not int or budget <= 0:
        raise ValueError("benchmark fixture budget_bytes must be positive")

    now = value.get("now")
    if (
        isinstance(now, bool)
        or not isinstance(now, (int, float))
        or not math.isfinite(float(now))
    ):
        raise ValueError("benchmark fixture now must be finite")

    raw_items = value.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("benchmark fixture items must be non-empty")

    allowed_fields = {"source", "content", "priority", "required", "valid_until"}
    seen_sources: set[str] = set()
    normalized_items: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict) or set(raw) - allowed_fields:
            raise ValueError("benchmark fixture contains invalid item fields")
        source = raw.get("source")
        content = raw.get("content")
        priority = raw.get("priority", 5)
        required = raw.get("required", False)
        valid_until = raw.get("valid_until")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("benchmark item source is required")
        if source in seen_sources:
            raise ValueError(f"duplicate benchmark source: {source}")
        seen_sources.add(source)
        if not isinstance(content, str) or not content:
            raise ValueError(f"benchmark item content is required: {source}")
        if type(priority) is not int:
            raise ValueError(f"benchmark item priority is invalid: {source}")
        if type(required) is not bool:
            raise ValueError(f"benchmark item required flag is invalid: {source}")
        if valid_until is not None and (
            isinstance(valid_until, bool)
            or not isinstance(valid_until, (int, float))
            or not math.isfinite(float(valid_until))
        ):
            raise ValueError(f"benchmark item valid_until is invalid: {source}")
        normalized = {
            "source": source,
            "content": content,
            "priority": priority,
            "required": required,
        }
        if valid_until is not None:
            normalized["valid_until"] = float(valid_until)
        normalized_items.append(normalized)

    return {
        "schema_version": 1,
        "benchmark": BENCHMARK_ID,
        "task": task.strip(),
        "budget_bytes": budget,
        "now": float(now),
        "items": normalized_items,
    }


def load_fixture(path: Path | str = FIXTURE_PATH) -> dict[str, Any]:
    target = Path(path)
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to load benchmark fixture: {target}") from exc
    return _validate_fixture(value)


def _context_items(value: dict[str, Any]) -> list[ContextItem]:
    return [
        ContextItem(
            source=raw["source"],
            content=raw["content"],
            priority=raw.get("priority", 5),
            required=raw.get("required", False),
            valid_until=raw.get("valid_until"),
        )
        for raw in value["items"]
    ]


def fixture() -> list[ContextItem]:
    """Compatibility accessor for callers of the original v1 benchmark."""
    return _context_items(load_fixture())


def naive_envelope_bytes(items: list[ContextItem], now: float = NOW) -> int:
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


def evaluate_fixture(value: dict[str, Any], *, commit_sha: str) -> dict[str, Any]:
    fixture_value = _validate_fixture(value)
    items = _context_items(fixture_value)
    now = fixture_value["now"]
    budget = fixture_value["budget_bytes"]
    sources_considered = sorted(item.source for item in items)
    required_sources = sorted(
        item.source
        for item in items
        if item.required and (item.valid_until is None or item.valid_until > now)
    )
    naive_bytes = naive_envelope_bytes(items, now)
    fixture_sha256 = hashlib.sha256(_canonical_fixture_bytes(fixture_value)).hexdigest()

    base = {
        "benchmark": BENCHMARK_ID,
        "status": "FAIL",
        "failure_reason": None,
        "commit_sha": str(commit_sha),
        "fixture_sha256": fixture_sha256,
        "task": fixture_value["task"],
        "budget_bytes": budget,
        "naive_serialized_bytes": naive_bytes,
        "bounded_serialized_bytes": None,
        "bytes_not_admitted": None,
        "bounded_fraction_of_naive": None,
        "sources_considered": sources_considered,
        "sources_loaded": [],
        "sources_omitted": list(sources_considered),
        "required_sources": required_sources,
        "required_sources_missing": list(required_sources),
        "selection_reason": None,
        "estimator": "serialized_utf8_bytes_upper_bound",
        "byte_measurement_method": "serialized_utf8_bytes",
        "token_estimate": None,
        "token_estimation_method": None,
        "claim_boundary": CLAIM_BOUNDARY,
        "invariants": {
            "receipt_matches_payload": False,
            "no_unqualified_token_estimate": True,
            "bounded_within_budget": False,
            "required_context_admitted": False,
            "source_accounting_complete": False,
            "demonstrates_bounded_admission": False,
        },
    }

    try:
        compiled, receipt = compile_context(items, budget, now=now)
    except ContextOverflowError as exc:
        base["failure_reason"] = str(exc)
        return base
    except ValueError as exc:
        base["failure_reason"] = str(exc)
        return base

    admitted_bytes = receipt.serialized_bytes
    loaded = sorted(receipt.sources_loaded)
    omitted = sorted(receipt.provenance.get("omitted_sources", []))
    missing_required = sorted(set(required_sources) - set(loaded))
    source_accounting = sorted(loaded + omitted) == sources_considered

    invariants = {
        "receipt_matches_payload": admitted_bytes == len(compiled.encode("utf-8")),
        "no_unqualified_token_estimate": (
            receipt.token_estimate is None
            and receipt.token_estimation_method is None
        ),
        "bounded_within_budget": admitted_bytes <= budget,
        "required_context_admitted": not missing_required,
        "source_accounting_complete": source_accounting,
        "demonstrates_bounded_admission": naive_bytes > admitted_bytes,
    }
    failed = [name for name, passed in invariants.items() if not passed]

    base.update(
        {
            "status": "PASS" if not failed else "FAIL",
            "failure_reason": (
                None if not failed else "INVARIANT_FAILURE:" + ",".join(sorted(failed))
            ),
            "bounded_serialized_bytes": admitted_bytes,
            "bytes_not_admitted": naive_bytes - admitted_bytes,
            "bounded_fraction_of_naive": (
                round(admitted_bytes / naive_bytes, 4) if naive_bytes else None
            ),
            "sources_loaded": loaded,
            "sources_omitted": omitted,
            "required_sources_missing": missing_required,
            "selection_reason": receipt.selection_reason,
            "estimator": receipt.provenance.get("estimator"),
            "byte_measurement_method": receipt.provenance.get(
                "byte_measurement_method"
            ),
            "token_estimate": receipt.token_estimate,
            "token_estimation_method": receipt.token_estimation_method,
            "content_hash": receipt.content_hash,
            "invariants": invariants,
        }
    )
    return base


def _display_fixture_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _write_json(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure repository-scale bounded context admission in serialized UTF-8 bytes."
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE_PATH,
        help="Public deterministic benchmark fixture JSON.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path for archivable machine-readable result JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        value = load_fixture(args.fixture)
        result = evaluate_fixture(value, commit_sha=resolve_commit_sha())
    except (ValueError, OSError) as exc:
        result = {
            "benchmark": BENCHMARK_ID,
            "status": "FAIL",
            "failure_reason": str(exc),
            "commit_sha": resolve_commit_sha(),
            "fixture_path": _display_fixture_path(args.fixture),
            "claim_boundary": CLAIM_BOUNDARY,
        }
    else:
        result["fixture_path"] = _display_fixture_path(args.fixture)

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json_output is not None:
        _write_json(args.json_output, result)
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
