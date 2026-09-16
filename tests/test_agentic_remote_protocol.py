#!/usr/bin/env python3
"""Contracts for the versioned J.A.R.V.I.S. remote companion protocol."""

import unittest

from tooling.remote_protocol import (
    PROTOCOL_VERSION,
    RemoteProtocolError,
    parse_client_envelope,
)


class TestRemoteProtocol(unittest.TestCase):
    def test_accepts_versioned_message(self):
        result = parse_client_envelope(
            {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-1",
                "kind": "message",
                "payload": {"text": "continue"},
            }
        )

        self.assertEqual(result["protocol"], "jarvis-remote/1")
        self.assertEqual(result["kind"], "message")
        self.assertEqual(result["payload"]["text"], "continue")

    def test_rejects_unknown_protocol(self):
        with self.assertRaises(RemoteProtocolError):
            parse_client_envelope(
                {
                    "protocol": "jarvis-remote/999",
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-1",
                    "kind": "message",
                    "payload": {"text": "continue"},
                }
            )

    def test_rejects_unknown_kind(self):
        with self.assertRaises(RemoteProtocolError):
            parse_client_envelope(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-1",
                    "kind": "execute_everything",
                    "payload": {},
                }
            )

    def test_rejects_invalid_identifiers(self):
        for field in ("session_id", "device_id", "request_id"):
            request = {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-1",
                "kind": "ping",
                "payload": {},
            }
            request[field] = "bad\nvalue"
            with self.subTest(field=field), self.assertRaises(RemoteProtocolError):
                parse_client_envelope(request)

    def test_rejects_oversized_message(self):
        with self.assertRaises(RemoteProtocolError):
            parse_client_envelope(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-1",
                    "kind": "message",
                    "payload": {"text": "x" * 32_769},
                }
            )


if __name__ == "__main__":
    unittest.main()
