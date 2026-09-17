#!/usr/bin/env python3
"""Contracts for one authoritative resident J.A.R.V.I.S. host context."""

from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path

from tooling.remote_transport import RemoteTransport, RemoteTransportStatus, TransportState
from tooling.resident_host_context import ResidentHostContext


class _FakeTransport(RemoteTransport):
    def __init__(self) -> None:
        self.start_calls = 0
        self.stop_calls = 0
        self._status = RemoteTransportStatus(
            transport_id="fake",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="stopped",
        )

    def start(self) -> RemoteTransportStatus:
        self.start_calls += 1
        self._status = RemoteTransportStatus(
            transport_id="fake",
            state=TransportState.ACTIVE,
            public_or_private_endpoint="http://100.64.0.10:8899",
            last_verified_at="2026-09-17T18:00:00Z",
            detail="active",
        )
        return self._status

    def status(self) -> RemoteTransportStatus:
        return self._status

    def stop(self) -> RemoteTransportStatus:
        self.stop_calls += 1
        self._status = RemoteTransportStatus(
            transport_id="fake",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="stopped",
        )
        return self._status


class _FakeVaultBridge:
    def __init__(self, outcomes=None) -> None:
        self.memory_fabric = object()
        self.calls = 0
        self.called = threading.Event()
        self._outcomes = list(outcomes or [{"status": "SUCCESS", "admitted": 0}])

    def reconcile_once(self):
        self.calls += 1
        self.called.set()
        if self._outcomes:
            outcome = self._outcomes.pop(0)
        else:
            outcome = {"status": "SUCCESS", "admitted": 0}
        if isinstance(outcome, BaseException):
            raise outcome
        return dict(outcome)

    def status(self):
        return {"checkpoint_present": True, "memory_snapshot_present": True}


class TestResidentHostContext(unittest.TestCase):
    def test_context_owns_one_runtime_adapter_and_one_memory_fabric(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = lambda request: {"status": "SUCCESS", "reply": request["text"]}
            bridge = _FakeVaultBridge()
            context = ResidentHostContext(
                Path(tmp),
                runtime_adapter=adapter,
                vault_bridge=bridge,
                reconcile_interval_seconds=60,
            )

            self.assertIs(context.runtime_adapter, adapter)
            self.assertIs(context.vault_bridge, bridge)
            self.assertIs(context.memory_fabric, bridge.memory_fabric)
            self.assertIs(context.runtime_adapter, context.runtime_adapter)
            self.assertIs(context.memory_fabric, context.memory_fabric)

    def test_start_and_stop_are_idempotent_and_control_transport_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            transport = _FakeTransport()
            bridge = _FakeVaultBridge()
            context = ResidentHostContext(
                Path(tmp),
                runtime_adapter=lambda _request: {"status": "SUCCESS", "reply": "ok"},
                vault_bridge=bridge,
                remote_transport=transport,
                reconcile_interval_seconds=60,
            )

            context.start()
            context.start()
            self.assertTrue(bridge.called.wait(timeout=2))
            self.assertTrue(context.status()["running"])
            self.assertEqual(transport.start_calls, 1)

            context.stop()
            context.stop()
            self.assertFalse(context.status()["running"])
            self.assertEqual(transport.stop_calls, 1)

    def test_reconciliation_failure_degrades_without_raising_and_can_recover(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = _FakeVaultBridge([
                RuntimeError("vault temporarily unavailable"),
                {"status": "SUCCESS", "admitted": 1},
            ])
            context = ResidentHostContext(
                Path(tmp),
                runtime_adapter=lambda _request: {"status": "SUCCESS", "reply": "ok"},
                vault_bridge=bridge,
                reconcile_interval_seconds=60,
            )

            failed = context.reconcile_once()
            self.assertEqual(failed["status"], "DEGRADED")
            self.assertIn("RuntimeError", failed["error"])
            self.assertEqual(context.status()["reconciliation"]["status"], "DEGRADED")

            recovered = context.reconcile_once()
            self.assertEqual(recovered["status"], "SUCCESS")
            status = context.status()["reconciliation"]
            self.assertEqual(status["status"], "ACTIVE")
            self.assertEqual(status["last_success"]["admitted"], 1)
            self.assertIsNone(status["last_error"])

    def test_restart_reuses_persisted_vault_checkpoint_without_reemitting_note(self):
        from tooling.agentic.bidirectional_vault import BidirectionalVaultBridge

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "state"
            note = root / "Project.md"
            note.write_bytes(b"# Project\nPersistent fact for restart.\n")

            first_bridge = BidirectionalVaultBridge(root, state_dir=state_dir)
            first = ResidentHostContext(
                root,
                runtime_adapter=lambda _request: {"status": "SUCCESS", "reply": "ok"},
                vault_bridge=first_bridge,
                reconcile_interval_seconds=60,
            )
            first_result = first.reconcile_once()
            self.assertGreaterEqual(first_result.get("admitted", 0), 1)

            second_bridge = BidirectionalVaultBridge(root, state_dir=state_dir)
            second = ResidentHostContext(
                root,
                runtime_adapter=lambda _request: {"status": "SUCCESS", "reply": "ok"},
                vault_bridge=second_bridge,
                reconcile_interval_seconds=60,
            )
            second_result = second.reconcile_once()
            self.assertEqual(second_result.get("human_events"), 0)
            self.assertEqual(second_result.get("admitted"), 0)
            self.assertTrue(second.status()["vault"]["checkpoint_present"])

    def test_status_never_exposes_runtime_adapter_or_memory_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = _FakeVaultBridge()
            context = ResidentHostContext(
                Path(tmp),
                runtime_adapter=lambda _request: {"status": "SUCCESS", "reply": "secret"},
                vault_bridge=bridge,
                reconcile_interval_seconds=60,
            )
            status = context.status()
            serialized = repr(status)
            self.assertNotIn("runtime_adapter", serialized)
            self.assertNotIn("memory_fabric", serialized)
            self.assertIn("vault", status)
            self.assertIn("reconciliation", status)


if __name__ == "__main__":
    unittest.main()
