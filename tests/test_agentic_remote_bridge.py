#!/usr/bin/env python3
"""Contracts for bridging durable remote sessions into one existing runtime."""

import tempfile
import unittest
from pathlib import Path

from tooling.remote_protocol import PROTOCOL_VERSION
from tooling.remote_runtime_bridge import RemoteRuntimeBridge, RemoteRuntimeBridgeError
from tooling.remote_sessions import RemoteSessionStore


class TestRemoteRuntimeBridge(unittest.TestCase):
    def _message(self, *, session_id="session-1", device_id="phone-1", request_id="req-1"):
        return {
            "protocol": PROTOCOL_VERSION,
            "session_id": session_id,
            "device_id": device_id,
            "request_id": request_id,
            "kind": "message",
            "payload": {"text": "continue the mission"},
        }

    def test_message_delegates_to_one_injected_runtime_and_preserves_correlation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1", clock=lambda: 1000.0)
            store.create_session("phone-1")
            calls = []

            def runtime_adapter(request):
                calls.append(dict(request))
                return {
                    "status": "UNVERIFIED",
                    "mission_id": "mission-7",
                    "reply": "PC runtime reply",
                    "receipt": {"verification_state": "UNVERIFIED"},
                }

            bridge = RemoteRuntimeBridge(store, runtime_adapter=runtime_adapter)
            result = bridge.handle(self._message())

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["session_id"], "session-1")
            self.assertEqual(calls[0]["request_id"], "req-1")
            self.assertEqual(calls[0]["text"], "continue the mission")
            self.assertEqual(result["mission_id"], "mission-7")
            self.assertEqual(result["request_id"], "req-1")

            events = store.events_after("session-1")
            self.assertEqual([event["kind"] for event in events], [
                "user_message_accepted",
                "assistant_message",
            ])
            self.assertEqual(events[-1]["mission_id"], "mission-7")
            self.assertEqual(events[-1]["payload"]["status"], "UNVERIFIED")
            self.assertEqual(events[-1]["payload"]["text"], "PC runtime reply")

    def test_duplicate_request_id_does_not_repeat_runtime_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")
            calls = []

            def runtime_adapter(request):
                calls.append(request["request_id"])
                return {
                    "status": "UNVERIFIED",
                    "mission_id": "mission-1",
                    "reply": "once",
                }

            bridge = RemoteRuntimeBridge(store, runtime_adapter=runtime_adapter)
            first = bridge.handle(self._message())
            second = bridge.handle(self._message())

            self.assertEqual(calls, ["req-1"])
            self.assertEqual(second, first)
            self.assertEqual(len(store.events_after("session-1")), 2)

    def test_rejects_device_that_does_not_own_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")
            bridge = RemoteRuntimeBridge(store, runtime_adapter=lambda request: {})

            with self.assertRaises(RemoteRuntimeBridgeError):
                bridge.handle(self._message(device_id="other-phone"))

    def test_runtime_failure_is_recorded_as_error_without_fabricated_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")

            def failing_runtime(_request):
                raise RuntimeError("runtime unavailable")

            bridge = RemoteRuntimeBridge(store, runtime_adapter=failing_runtime)
            result = bridge.handle(self._message())

            self.assertEqual(result["status"], "ERROR")
            self.assertEqual(result["reason"], "RUNTIME_ADAPTER_FAILED")
            events = store.events_after("session-1")
            self.assertEqual(events[-1]["kind"], "error")
            self.assertNotEqual(result.get("status"), "SUCCESS")


if __name__ == "__main__":
    unittest.main()
