#!/usr/bin/env python3
"""Reproducible Context Governor budget benchmark.

This benchmark measures serialized UTF-8 bytes admitted by ``compile_context``
against an explicit naive envelope containing every fixture item. It does not
claim provider token counts, quality gains or dollar savings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.agentic.context_governor import ContextItem, compile_context

BUDGET_BYTES = 1800
NOW = 1_800_000_000.0


def fixture() -> list[ContextItem]:
    return [
        ContextItem(
            source="mission-contract.md",
            content="authority=read-only; verify=tests+source; stop_on_insufficient_evidence=true;" * 5,
            priority=0,
            required=True,
        ),
        ContextItem(
            source="src/router.py",
            content="router candidate evidence " * 45,
            priority=1,
        ),
        ContextItem(
            source="tests/test_router.py",
            content="router verification fixture " * 42,
            priority=2,
        ),
        ContextItem(
            source="docs/architecture.md",
            content="architecture background " * 65,
            priority=7,
        ),
        ContextItem(
            source="CHANGELOG.md",
            content="historical release note " * 70,
            priority=8,
        ),
        # Duplicate content under another source demonstrates deduplication with provenance.
        ContextItem(
            source="mirror/router-copy.txt",
            content="router candidate evidence " * 45,
            priority=5,
        ),
    ]


def naive_envelope_bytes(items: list[ContextItem]) -> int:
    payload = [
        {"content": item.content, "sources": [item.source]}
        for item in items
        if item.valid_until is None or item.valid_until > NOW
    ]
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return len(text.encode("utf-8"))


def main() -> int:
    items = fixture()
    naive_bytes = naive_envelope_bytes(items)
    compiled, receipt = compile_context(items, BUDGET_BYTES, now=NOW)
    admitted_bytes = receipt.serialized_bytes
    omitted = receipt.provenance.get("omitted_sources", [])

    result = {
        "benchmark": "context-budget-v1",
        "budget_bytes": BUDGET_BYTES,
        "naive_serialized_bytes": naive_bytes,
        "bounded_serialized_bytes": admitted_bytes,
        "bytes_not_admitted": naive_bytes - admitted_bytes,
        "bounded_fraction_of_naive": round(admitted_bytes / naive_bytes, 4),
        "sources_considered": receipt.sources_considered,
        "sources_loaded": receipt.sources_loaded,
        "sources_omitted": omitted,
        "selection_reason": receipt.selection_reason,
        "estimator": receipt.provenance.get("estimator"),
        "byte_measurement_method": receipt.provenance.get("byte_measurement_method"),
        "token_estimate": receipt.token_estimate,
        "token_estimation_method": receipt.token_estimation_method,
        "claim_boundary": "serialized UTF-8 bytes only; not provider token counts, quality, latency or cost",
    }

    print(json.dumps(result, indent=2, sort_keys=True))

    if admitted_bytes != len(compiled.encode("utf-8")):
        print("ERROR: receipt byte measurement diverged from serialized payload", file=sys.stderr)
        return 1
    if receipt.token_estimate is not None or receipt.token_estimation_method is not None:
        print("ERROR: benchmark invented token estimates without an estimator", file=sys.stderr)
        return 1
    if admitted_bytes > BUDGET_BYTES:
        print("ERROR: bounded context exceeded declared budget", file=sys.stderr)
        return 1
    if "mission-contract.md" not in receipt.sources_loaded:
        print("ERROR: required context was not admitted", file=sys.stderr)
        return 1
    if naive_bytes <= admitted_bytes:
        print("ERROR: fixture did not demonstrate bounded admission", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
