#!/usr/bin/env python3
"""Durability and idempotency contracts for J.A.R.V.I.S. remote sessions."""

import json
import tempfile
import unittest
from unittest import mock
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
                "session-1",
                "req-1",
                {"event_seq": 1},
                request_fingerprint="a" * 64,
            )

            reopened = RemoteSessionStore(Path(tmp))
            second, created_second = reopened.remember_request(
                "session-1",
                "req-1",
                {"event_seq": 999},
                request_fingerprint="a" * 64,
            )

            self.assertTrue(created_first)
            self.assertFalse(created_second)
            self.assertEqual(second, first)
            self.assertEqual(second["event_seq"], 1)

    def test_duplicate_request_id_with_different_fingerprint_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")
            store.remember_request(
                "session-1",
                "req-1",
                {"event_seq": 1},
                request_fingerprint="a" * 64,
            )
            with self.assertRaisesRegex(
                RemoteSessionError,
                "request_id reuse with different payload",
            ):
                store.remember_request(
                    "session-1",
                    "req-1",
                    {"event_seq": 2},
                    request_fingerprint="b" * 64,
                )

    def test_legacy_request_cache_loads_but_replay_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = {
                "schema_version": 1,
                "sessions": {
                    "session-1": {
                        "session_id": "session-1",
                        "device_id": "phone-1",
                        "status": "OPEN",
                        "created_at": 1000.0,
                        "last_seen_at": 1000.0,
                        "mission_id": None,
                        "next_seq": 1,
                        "last_ack_seq": 0,
                        "requests": {
                            "req-old": {
                                "result": {"event_seq": 1},
                                "created_at": 1000.0,
                            }
                        },
                    }
                },
            }
            (root / "remote_sessions.json").write_text(
                json.dumps(legacy),
                encoding="utf-8",
            )
            store = RemoteSessionStore(root)

            with self.assertRaisesRegex(
                RemoteSessionError,
                "without matching fingerprint",
            ):
                store.remember_request(
                    "session-1",
                    "req-old",
                    {"event_seq": 999},
                    request_fingerprint="a" * 64,
                )

            result, created = store.remember_request(
                "session-1",
                "req-new",
                {"event_seq": 2},
                request_fingerprint="b" * 64,
            )
            self.assertTrue(created)
            self.assertEqual(result["event_seq"], 2)

    def test_event_payload_size_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")
            with mock.patch("tooling.remote_sessions.MAX_EVENT_PAYLOAD_BYTES", 32):
                with self.assertRaisesRegex(RemoteSessionError, "payload exceeds size limit"):
                    store.append_event(
                        "session-1",
                        "assistant_message",
                        {"text": "x" * 128},
                    )

    def test_event_journal_size_limit_fails_closed_without_partial_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = RemoteSessionStore(root, id_factory=lambda: "session-1")
            store.create_session("phone-1")
            first = store.append_event(
                "session-1",
                "assistant_message",
                {"text": "first"},
            )
            path = root / "remote_events" / "session-1.jsonl"
            before = path.read_bytes()
            with mock.patch(
                "tooling.remote_sessions.MAX_EVENT_JOURNAL_BYTES",
                len(before) + 8,
            ):
                with self.assertRaisesRegex(RemoteSessionError, "journal exceeds size limit"):
                    store.append_event(
                        "session-1",
                        "assistant_message",
                        {"text": "second event cannot fit"},
                    )
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(store.get_session("session-1")["next_seq"], first["seq"] + 1)

    def test_request_index_limit_preserves_existing_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")
            with mock.patch("tooling.remote_sessions.MAX_REQUESTS_PER_SESSION", 1):
                first, created = store.remember_request(
                    "session-1",
                    "req-1",
                    {"event_seq": 1},
                    request_fingerprint="a" * 64,
                )
                self.assertTrue(created)

                replay, replay_created = store.remember_request(
                    "session-1",
                    "req-1",
                    {"event_seq": 999},
                    request_fingerprint="a" * 64,
                )
                self.assertFalse(replay_created)
                self.assertEqual(replay, first)

                with self.assertRaisesRegex(
                    RemoteSessionError,
                    "request index exceeds per-session limit",
                ):
                    store.remember_request(
                        "session-1",
                        "req-2",
                        {"event_seq": 2},
                        request_fingerprint="b" * 64,
                    )

    def test_tampered_event_session_ownership_is_rejected_on_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = RemoteSessionStore(root, id_factory=lambda: "session-1")
            store.create_session("phone-1")
            store.append_event(
                "session-1",
                "assistant_message",
                {"text": "ok"},
            )
            path = root / "remote_events" / "session-1.jsonl"
            event = json.loads(path.read_text(encoding="utf-8").strip())
            event["session_id"] = "session-other"
            path.write_text(
                json.dumps(event, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                RemoteSessionError,
                "session ownership",
            ):
                RemoteSessionStore(root)

    def test_tampered_event_protocol_is_rejected_during_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = RemoteSessionStore(root, id_factory=lambda: "session-1")
            store.create_session("phone-1")
            store.append_event(
                "session-1",
                "assistant_message",
                {"text": "ok"},
            )
            path = root / "remote_events" / "session-1.jsonl"
            event = json.loads(path.read_text(encoding="utf-8").strip())
            event["protocol"] = "jarvis-remote/999"
            path.write_text(
                json.dumps(event, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RemoteSessionError, "event protocol"):
                store.events_after("session-1")

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
