"""Failure and restart contracts for approval-bound remote tasks."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tooling.remote_commands import RemoteCommandController
from tooling.remote_tasks import RemoteTaskController, RemoteTaskError, RemoteTaskPlanner


class TestRemoteTaskLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "app.py").write_text("VALUE=1\n", encoding="utf-8")
        self.actions = [
            {"type": "write_text", "path": "app.py", "content": "VALUE=2\n"},
        ]

    def controller(self):
        outputs = iter([
            json.dumps({"files": ["app.py"]}),
            json.dumps({"summary": "Update example", "actions": self.actions}),
        ])
        return RemoteTaskController(
            self.root / "state", workspace_root=self.root,
            planner=RemoteTaskPlanner(self.root, inference_adapter=lambda _: next(outputs)),
            command_controller=RemoteCommandController(
                self.root / "state", workspace_root=self.root,
            ),
        )

    def prepare(self, controller):
        return controller.prepare(
            "Update example", session_id="session-1", device_id="phone-1",
            request_id="request-1",
        )

    def approve(self, controller, plan, **overrides):
        args = dict(task_id=plan["task_id"], plan_digest=plan["plan_digest"],
                    session_id="session-1", device_id="phone-1")
        args.update(overrides)
        return controller.approve_and_execute(**args)

    def test_other_device_or_session_cannot_approve(self):
        controller = self.controller()
        plan = self.prepare(controller)
        for override in ({"device_id": "phone-2"}, {"session_id": "session-2"}):
            with self.subTest(override=override), self.assertRaises(RemoteTaskError):
                self.approve(controller, plan, **override)
        self.assertEqual((self.root / "app.py").read_text(), "VALUE=1\n")
        self.assertEqual(controller.get(plan["task_id"])["status"], "PENDING")

    def test_digest_covers_full_plan_and_original_request_ownership(self):
        controller = self.controller()
        pending = self.prepare(controller)
        material = {key: pending[key] for key in (
            "session_id", "device_id", "request_id", "plan",
        )}

        def digest(value):
            return hashlib.sha256(json.dumps(
                value, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            ).encode("utf-8")).hexdigest()

        self.assertEqual(digest(material), pending["plan_digest"])
        for field in ("session_id", "device_id", "request_id"):
            altered = {**material, field: "different"}
            self.assertNotEqual(digest(altered), pending["plan_digest"])
        material["plan"]["actions"][0]["content"] = "VALUE=3\n"
        self.assertNotEqual(digest(material), pending["plan_digest"])
        self.assertEqual(controller.get(pending["task_id"])["plan"]["actions"][0]["content"], "VALUE=2\n")

    def test_pending_plan_survives_restart_and_terminal_receipt_is_idempotent(self):
        plan = self.prepare(self.controller())
        restarted = self.controller()
        receipt = self.approve(restarted, plan)
        self.assertEqual(receipt["status"], "COMPLETED")
        backups = list((self.root / "backups" / "local-adapter").glob("*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(self.approve(self.controller(), plan), receipt)
        self.assertEqual(list((self.root / "backups" / "local-adapter").glob("*.bak")), backups)

    def test_restart_during_execution_is_unknown_and_never_replayed(self):
        controller = self.controller()
        plan = self.prepare(controller)
        state = json.loads(controller.state_path.read_text(encoding="utf-8"))
        state["tasks"][plan["task_id"]]["status"] = "RUNNING"
        controller.state_path.write_text(json.dumps(state), encoding="utf-8")
        restarted = self.controller()
        self.assertEqual(restarted.get(plan["task_id"])["status"], "UNKNOWN")
        with self.assertRaises(RemoteTaskError):
            self.approve(restarted, plan)
        self.assertEqual((self.root / "app.py").read_text(), "VALUE=1\n")
        self.assertEqual(self.controller().get(plan["task_id"])["status"], "UNKNOWN")

    def test_failed_command_preserves_earlier_write_and_skips_later_actions(self):
        (self.root / "fail.py").write_text("raise SystemExit(7)\n", encoding="utf-8")
        self.actions.extend([
            {"type": "command", "argv": ["python", "fail.py"], "timeout_seconds": 10},
            {"type": "write_text", "path": "later.txt", "content": "must not exist"},
        ])
        controller = self.controller()
        plan = self.prepare(controller)
        receipt = self.approve(controller, plan)
        self.assertEqual(receipt["status"], "FAILED")
        self.assertEqual(receipt["actions_total"], 3)
        self.assertEqual(receipt["actions_executed"], 2)
        self.assertEqual(receipt["receipts"][1]["exit_code"], 7)
        self.assertEqual((self.root / "app.py").read_text(), "VALUE=2\n")
        self.assertFalse((self.root / "later.txt").exists())
        self.assertEqual(self.approve(self.controller(), plan), receipt)

    def test_new_file_collision_rejects_whole_plan_before_first_write(self):
        self.actions.append({"type": "write_text", "path": "new.txt", "content": "planned"})
        controller = self.controller()
        plan = self.prepare(controller)
        (self.root / "new.txt").write_text("external", encoding="utf-8")
        with self.assertRaises(RemoteTaskError):
            self.approve(controller, plan)
        self.assertEqual((self.root / "app.py").read_text(), "VALUE=1\n")
        self.assertEqual((self.root / "new.txt").read_text(), "external")


if __name__ == "__main__":
    unittest.main()
