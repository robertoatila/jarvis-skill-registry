#!/usr/bin/env python3
"""Deterministic actual-server fixture for Playwright HUD smoke tests."""

from __future__ import annotations

import signal
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tooling.jarvis_server as jarvis_server
from tooling.agentic.observability import ReceiptLedger
from tooling.jarvis_server import JarvisHttpHandler, ThreadingJarvisServer


MISSION_ID = "mis-browser-smoke"
TASK_ID = "tsk-browser-smoke"
ATTEMPT_ID = "att-browser-smoke"
TRACE_ID = "trc-browser-smoke"


def seed_receipts(state_dir: Path) -> None:
    ledger = ReceiptLedger(state_dir / "receipts")
    ledger.append({
        "schema_version": "1.0.0",
        "receipt_id": "rcp-browser-context",
        "mission_id": MISSION_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "trace_id": TRACE_ID,
        "created_utc": "2026-09-18T09:30:00+00:00",
        "sources_loaded": ["browser-fixture-source"],
        "serialized_bytes": 96,
        "token_estimate": None,
        "provenance": {
            "budget_bytes": 400,
            "candidate_serialized_bytes": 320,
            "admitted_serialized_bytes": 96,
            "savings_pct": 70.0,
        },
    })
    ledger.append({
        "schema_version": "1.0.0",
        "receipt_id": "rcp-browser-execution",
        "mission_id": MISSION_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "trace_id": TRACE_ID,
        "created_utc": "2026-09-18T09:30:01+00:00",
        "adapter": "inference:deterministic-browser-fixture",
        "invocation_occurred": True,
        "execution_state": "FINISHED",
        "resource_usage": {
            "tokens": {
                "status": "UNKNOWN",
                "value": None,
                "unit": "tokens",
                "method": None,
            },
            "cost_usd": {
                "status": "UNKNOWN",
                "value": None,
                "unit": "USD",
                "method": None,
            },
            "latency_ms": {
                "status": "UNKNOWN",
                "value": None,
                "unit": "ms",
                "method": None,
            },
        },
    })


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jarvis-browser-smoke-") as directory:
        jarvis_server.STATE_DIR = Path(directory) / "state"
        seed_receipts(jarvis_server.STATE_DIR)

        server = ThreadingJarvisServer(
            ("127.0.0.1", 0),
            JarvisHttpHandler,
        )
        server.remote_auth = None

        def stop(_signum, _frame):
            raise KeyboardInterrupt

        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, stop)
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, stop)

        print(f"JARVIS_BROWSER_PORT={server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
