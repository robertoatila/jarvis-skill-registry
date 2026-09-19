#!/usr/bin/env python3
"""End-to-end bridge contract for remote PC command approval and receipts."""

import tempfile
import unittest
from pathlib import Path

from tooling.remote_commands import RemoteCommandController
from tooling.remote_protocol import PROTOCOL_VERSION
from tooling.remote_runtime_bridge import RemoteRuntimeBridge
from tooling.remote_sessions import RemoteSessionStore


class TestRemotePcCommandBridge(unittest.TestCase):
    def test_command_is_not_executed_before_approval_and_receipt_is_correlated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gate.py").write_text(
                "from pathlib import Path\n"
                "Path('executed.txt').write_text('yes', encoding='utf-8')\n"
                "print('gate-pass')\n",
                encoding="utf-8",
            )
            session_ids = iter(["session-1"])
            store = RemoteSessionStore(
                root / "state",
                id_factory=lambda: next(session_ids),
                clock=lambda: 1000.0,
            )
            store.create_session("phone-1")
            controller = RemoteCommandController(
                root / "state",
                workspace_root=root,
                id_factory=lambda: "rcmd-" + ("c" * 24),
                clock=lambda: 1000.0,
            )
            bridge = RemoteRuntimeBridge(
                store,
                runtime_adapter=lambda _request: {
                    "status": "UNVERIFIED",
                    "reply": "chat path",
                },
                command_controller=controller,
            )

            request = {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-command",
                "kind": "command",
                "payload": {
                    "argv": ["python", "gate.py"],
                    "cwd": ".",
                    "timeout_seconds": 30,
                },
            }
            pending = bridge.handle(request)
            self.assertEqual(pending["status"], "APPROVAL_REQUIRED")
            self.assertFalse((root / "executed.txt").exists())

            approval = {
                "protocol": PROTOCOL_VERSION,
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-approval",
                "kind": "approve_action",
                "payload": {
                    "action_id": pending["action_id"],
                    "action_digest": pending["action_digest"],
                },
            }
            result = bridge.handle(approval)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual((root / "executed.txt").read_text(encoding="utf-8"), "yes")

            events = store.events_after("session-1")
            self.assertEqual(
                [event["kind"] for event in events],
                [
                    "command_requested",
                    "approval_required",
                    "approval_submitted",
                    "action_receipt",
                ],
            )
            receipt = events[-1]["payload"]["receipt"]
            self.assertEqual(receipt["action_digest"], pending["action_digest"])
            self.assertIn("gate-pass", receipt["stdout"])

    def test_second_approval_request_does_not_repeat_completed_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "once.py").write_text(
                "from pathlib import Path\n"
                "p=Path('count.txt')\n"
                "p.write_text((p.read_text() if p.exists() else '') + '1')\n",
                encoding="utf-8",
            )
            store = RemoteSessionStore(
                root / "state",
                id_factory=lambda: "session-1",
            )
            store.create_session("phone-1")
            controller = RemoteCommandController(
                root / "state",
                workspace_root=root,
                id_factory=lambda: "rcmd-" + ("d" * 24),
            )
            bridge = RemoteRuntimeBridge(
                store,
                runtime_adapter=lambda _request: {"status": "UNVERIFIED", "reply": "chat"},
                command_controller=controller,
            )
            pending = bridge.handle(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-command",
                    "kind": "command",
                    "payload": {"argv": ["python", "once.py"]},
                }
            )

            for request_id in ("req-approval-1", "req-approval-2"):
                result = bridge.handle(
                    {
                        "protocol": PROTOCOL_VERSION,
                        "session_id": "session-1",
                        "device_id": "phone-1",
                        "request_id": request_id,
                        "kind": "approve_action",
                        "payload": {
                            "action_id": pending["action_id"],
                            "action_digest": pending["action_digest"],
                        },
                    }
                )
                self.assertEqual(result["status"], "PASS")

            self.assertEqual((root / "count.txt").read_text(encoding="utf-8"), "1")


if __name__ == "__main__":
    unittest.main()
