#!/usr/bin/env python3
"""Bridge contracts for natural-language remote tasks."""

import json
import tempfile
import unittest
from pathlib import Path

from tooling.remote_commands import RemoteCommandController
from tooling.remote_protocol import PROTOCOL_VERSION
from tooling.remote_runtime_bridge import RemoteRuntimeBridge
from tooling.remote_sessions import RemoteSessionStore
from tooling.remote_tasks import RemoteTaskController, RemoteTaskPlanner


class _Inference:
    def __init__(self, outputs):
        self.outputs = list(outputs)

    def __call__(self, _prompt):
        return self.outputs.pop(0)


class TestRemoteTaskBridge(unittest.TestCase):
    def test_task_plans_without_effect_then_executes_exact_approved_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("VALUE=1\n", encoding="utf-8")
            inference = _Inference(
                [
                    json.dumps({"files": ["app.py"], "reason": "target"}),
                    json.dumps(
                        {
                            "summary": "update value",
                            "actions": [
                                {
                                    "type": "write_text",
                                    "path": "app.py",
                                    "content": "VALUE=2\n",
                                    "purpose": "requested edit",
                                }
                            ],
                        }
                    ),
                ]
            )
            store = RemoteSessionStore(
                root / "state",
                id_factory=lambda: "session-1",
            )
            store.create_session("phone-1")
            commands = RemoteCommandController(root / "state", workspace_root=root)
            tasks = RemoteTaskController(
                root / "state",
                workspace_root=root,
                planner=RemoteTaskPlanner(root, inference_adapter=inference),
                command_controller=commands,
                id_factory=lambda: "rtask-" + ("d" * 24),
            )
            bridge = RemoteRuntimeBridge(
                store,
                runtime_adapter=lambda request: {
                    "status": "UNVERIFIED",
                    "reply": request["text"],
                },
                command_controller=commands,
                task_controller=tasks,
            )

            planned = bridge.handle(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-task",
                    "kind": "task",
                    "payload": {"goal": "change VALUE to 2"},
                }
            )
            self.assertEqual(planned["status"], "PLAN_APPROVAL_REQUIRED")
            self.assertEqual(
                (root / "app.py").read_text(encoding="utf-8"),
                "VALUE=1\n",
            )

            events = store.events_after("session-1")
            self.assertEqual(
                [event["kind"] for event in events],
                ["task_requested", "task_plan_required"],
            )
            plan_event = events[-1]["payload"]
            self.assertEqual(plan_event["task_id"], planned["task_id"])
            self.assertEqual(plan_event["plan_digest"], planned["plan_digest"])
            self.assertNotIn(
                "content",
                plan_event["plan"]["actions"][0],
            )

            executed = bridge.handle(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-approve",
                    "kind": "approve_plan",
                    "payload": {
                        "task_id": planned["task_id"],
                        "plan_digest": planned["plan_digest"],
                    },
                }
            )
            self.assertEqual(executed["status"], "COMPLETED")
            self.assertEqual(
                (root / "app.py").read_text(encoding="utf-8"),
                "VALUE=2\n",
            )

            events = store.events_after("session-1")
            self.assertEqual(
                [event["kind"] for event in events],
                [
                    "task_requested",
                    "task_plan_required",
                    "task_plan_approval_submitted",
                    "task_receipt",
                ],
            )
            receipt = events[-1]["payload"]["receipt"]
            self.assertEqual(receipt["status"], "COMPLETED")
            self.assertEqual(receipt["plan_digest"], planned["plan_digest"])

    def test_task_planning_failure_records_error_without_workspace_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("VALUE=1\n", encoding="utf-8")
            store = RemoteSessionStore(
                root / "state",
                id_factory=lambda: "session-1",
            )
            store.create_session("phone-1")
            commands = RemoteCommandController(root / "state", workspace_root=root)
            tasks = RemoteTaskController(
                root / "state",
                workspace_root=root,
                planner=RemoteTaskPlanner(
                    root,
                    inference_adapter=lambda _prompt: "not-json",
                ),
                command_controller=commands,
                id_factory=lambda: "rtask-" + ("e" * 24),
            )
            bridge = RemoteRuntimeBridge(
                store,
                runtime_adapter=lambda request: {
                    "status": "UNVERIFIED",
                    "reply": request["text"],
                },
                command_controller=commands,
                task_controller=tasks,
            )

            result = bridge.handle(
                {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-1",
                    "device_id": "phone-1",
                    "request_id": "req-task",
                    "kind": "task",
                    "payload": {"goal": "change value"},
                }
            )
            self.assertEqual(result["status"], "ERROR")
            self.assertEqual(result["reason"], "REMOTE_TASK_PLANNING_REJECTED")
            self.assertEqual(
                (root / "app.py").read_text(encoding="utf-8"),
                "VALUE=1\n",
            )


if __name__ == "__main__":
    unittest.main()
