#!/usr/bin/env python3
"""Durability and idempotency contracts for J.A.R.V.I.S. remote sessions."""

import json
import tempfile
import unittest
from pathlib import Path

from tooling.remote_sessions import RemoteSessionError, RemoteSessionStore


class TestRemoteSessionStore(unittest.TestCase):
    def test_event_cursor_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            ids = iter(["session-1"])
            store = RemoteSessionStore(
                Path(tmp),
                clock=lambda: 1000.0,
                id_factory=lambda: next(ids),
            )
            session = store.create_session("phone-1")
            first = store.append_event(
                session["session_id"], "host_status", {"status": "ONLINE"}
            )
            second = store.append_event(
                session["session_id"], "assistant_message", {"text": "ok"}
            )
            self.assertEqual((first["seq"], second["seq"]), (1, 2))

            reopened = RemoteSessionStore(Path(tmp), clock=lambda: 1001.0)
            events = reopened.events_after("session-1", after=1)
            self.assertEqual([event["seq"] for event in events], [2])
            self.assertEqual(events[0]["payload"]["text"], "ok")

    def test_duplicate_request_id_is_idempotent_across_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")
            first, created_first = store.remember_request(
                "session-1", "req-1", {"event_seq": 1}
            )

            reopened = RemoteSessionStore(Path(tmp))
            second, created_second = reopened.remember_request(
                "session-1", "req-1", {"event_seq": 999}
            )

            self.assertTrue(created_first)
            self.assertFalse(created_second)
            self.assertEqual(second, first)
            self.assertEqual(second["event_seq"], 1)

    def test_ack_is_monotonic_and_cannot_exceed_latest_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            session = store.create_session("phone-1")
            store.append_event(session["session_id"], "host_status", {"status": "ONLINE"})
            store.append_event(session["session_id"], "assistant_message", {"text": "ok"})

            acknowledged = store.ack("session-1", 2)
            self.assertEqual(acknowledged["last_ack_seq"], 2)

            with self.assertRaises(RemoteSessionError):
                store.ack("session-1", 1)
            with self.assertRaises(RemoteSessionError):
                store.ack("session-1", 3)

    def test_rejects_unsupported_future_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "remote_sessions.json").write_text(
                json.dumps({"schema_version": 999, "sessions": {}}),
                encoding="utf-8",
            )
            with self.assertRaises(RemoteSessionError):
                RemoteSessionStore(root)

    def test_closed_session_rejects_new_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            session = store.create_session("phone-1")
            closed = store.close_session(session["session_id"])
            self.assertEqual(closed["status"], "CLOSED")

            with self.assertRaises(RemoteSessionError):
                store.append_event(
                    session["session_id"], "assistant_message", {"text": "late"}
                )


if __name__ == "__main__":
    unittest.main()
