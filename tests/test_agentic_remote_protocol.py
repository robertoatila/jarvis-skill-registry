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

    def test_rejects_reserved_but_unimplemented_kinds(self):
        for kind in ("ping", "cancel_request", "resume_mission"):
            with self.subTest(kind=kind), self.assertRaises(RemoteProtocolError):
                parse_client_envelope(
                    {
                        "protocol": PROTOCOL_VERSION,
                        "session_id": "session-1",
                        "device_id": "phone-1",
                        "request_id": "req-1",
                        "kind": kind,
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


    def test_accepts_structured_command(self):
        result = parse_client_envelope(
            {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-command",
                "kind": "command",
                "payload": {
                    "argv": ["python", "tooling/validate_v020_plan4.py", "--gate", "portable-runtime"],
                    "cwd": ".",
                    "timeout_seconds": 300,
                },
            }
        )
        self.assertEqual(result["kind"], "command")
        self.assertEqual(result["payload"]["argv"][0], "python")
        self.assertEqual(result["payload"]["timeout_seconds"], 300)

    def test_rejects_inline_command_code(self):
        with self.assertRaises(RemoteProtocolError):
            parse_client_envelope(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-command",
                    "kind": "command",
                    "payload": {"argv": ["python", "-c", "print('no')"]},
                }
            )

    def test_accepts_natural_language_task(self):
        result = parse_client_envelope(
            {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-task",
                "kind": "task",
                "payload": {"goal": "corrija o login e rode os testes focados"},
            }
        )
        self.assertEqual(result["kind"], "task")
        self.assertEqual(
            result["payload"]["goal"],
            "corrija o login e rode os testes focados",
        )

    def test_rejects_oversized_task_goal(self):
        with self.assertRaises(RemoteProtocolError):
            parse_client_envelope(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-task",
                    "kind": "task",
                    "payload": {"goal": "x" * 6001},
                }
            )

    def test_accepts_digest_bound_plan_approval(self):
        result = parse_client_envelope(
            {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-plan",
                "kind": "approve_plan",
                "payload": {
                    "task_id": "rtask-" + ("a" * 24),
                    "plan_digest": "b" * 64,
                },
            }
        )
        self.assertEqual(result["kind"], "approve_plan")
        self.assertEqual(result["payload"]["task_id"], "rtask-" + ("a" * 24))

    def test_accepts_digest_bound_approval(self):
        result = parse_client_envelope(
            {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-approval",
                "kind": "approve_action",
                "payload": {
                    "action_id": "rcmd-" + ("a" * 24),
                    "action_digest": "b" * 64,
                },
            }
        )
        self.assertEqual(result["kind"], "approve_action")
        self.assertEqual(result["payload"]["action_id"], "rcmd-" + ("a" * 24))


if __name__ == "__main__":
    unittest.main()
