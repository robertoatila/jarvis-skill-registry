#!/usr/bin/env python3
"""Contracts for natural-language remote task planning and execution."""

import json
import tempfile
import unittest
from pathlib import Path

from tooling.remote_commands import RemoteCommandController
from tooling.remote_tasks import (
    RemoteTaskController,
    RemoteTaskError,
    RemoteTaskPlanner,
    public_plan_view,
)


class _InferenceSequence:
    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if not self.outputs:
            raise AssertionError("unexpected inference call")
        return self.outputs.pop(0)


class TestRemoteTaskPlanner(unittest.TestCase):
    def test_plan_reads_bounded_selected_file_and_binds_overwrite_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "app.py"
            target.write_text("VALUE = 1\n", encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["app.py"], "reason": "target"}),
                json.dumps(
                    {
                        "summary": "Update value and verify",
                        "actions": [
                            {
                                "type": "write_text",
                                "path": "app.py",
                                "content": "VALUE = 2\n",
                                "purpose": "apply requested change",
                            },
                            {
                                "type": "command",
                                "argv": ["python", "app.py"],
                                "cwd": ".",
                                "timeout_seconds": 30,
                                "purpose": "syntax/runtime smoke test",
                            },
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            plan = planner.plan("change VALUE to 2")

            self.assertEqual(plan["selected_files"], ["app.py"])
            self.assertEqual(plan["actions"][0]["path"], "app.py")
            self.assertEqual(
                plan["actions"][0]["expected_before_sha256"],
                plan["observed_hashes"]["app.py"],
            )
            view = public_plan_view(plan)
            self.assertNotIn("content", view["actions"][0])
            self.assertEqual(view["actions"][0]["type"], "write_text")
            self.assertEqual(len(view["actions"][0]["content_sha256"]), 64)
            self.assertIn("-VALUE = 1", view["actions"][0]["diff_preview"])
            self.assertIn("+VALUE = 2", view["actions"][0]["diff_preview"])
            self.assertIn("VALUE = 1", inference.prompts[1])

    def test_selected_source_larger_than_planner_file_budget_is_rejected_before_plan_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large.py").write_text("x = 1\n" * 6000, encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["large.py"], "reason": "target"}),
                json.dumps({"summary": "should not run", "actions": []}),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            with self.assertRaises(RemoteTaskError):
                planner.plan("inspect large file")
            self.assertEqual(len(inference.prompts), 1)

    def test_planner_cannot_overwrite_file_it_did_not_inspect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("A=1\n", encoding="utf-8")
            (root / "b.py").write_text("B=1\n", encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["a.py"], "reason": "only a"}),
                json.dumps(
                    {
                        "summary": "bad overwrite",
                        "actions": [
                            {
                                "type": "write_text",
                                "path": "b.py",
                                "content": "B=2\n",
                                "purpose": "uninspected overwrite",
                            }
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            with self.assertRaises(RemoteTaskError):
                planner.plan("change b")

    def test_planner_rejects_destructive_git_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('x')\n", encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["app.py"], "reason": "target"}),
                json.dumps(
                    {
                        "summary": "unsafe",
                        "actions": [
                            {
                                "type": "command",
                                "argv": ["git", "reset", "--hard", "HEAD~1"],
                                "purpose": "unsafe rollback",
                            }
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            with self.assertRaises(RemoteTaskError):
                planner.plan("reset repository")


    def test_autonomous_plan_rejects_npx_and_mutating_git(self):
        cases = [
            ["npx", "pytest"],
            ["git", "checkout", "--", "app.py"],
            ["git", "commit", "-am", "x"],
            ["npm", "publish"],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / "app.py").write_text("VALUE=1\n", encoding="utf-8")
                    inference = _InferenceSequence(
                        json.dumps({"files": ["app.py"], "reason": "target"}),
                        json.dumps(
                            {
                                "summary": "unsafe command",
                                "actions": [
                                    {
                                        "type": "command",
                                        "argv": argv,
                                        "purpose": "unsafe",
                                    }
                                ],
                            }
                        ),
                    )
                    planner = RemoteTaskPlanner(root, inference_adapter=inference)
                    with self.assertRaises(RemoteTaskError):
                        planner.plan("unsafe")

    def test_autonomous_plan_allows_read_only_git_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("VALUE=1\n", encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["app.py"], "reason": "target"}),
                json.dumps(
                    {
                        "summary": "inspect status",
                        "actions": [
                            {
                                "type": "command",
                                "argv": ["git", "status", "--short"],
                                "purpose": "inspect workspace state",
                            }
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            plan = planner.plan("inspect status")
            self.assertEqual(plan["actions"][0]["argv"], ["git", "status", "--short"])

class TestRemoteTaskController(unittest.TestCase):
    def test_exact_plan_approval_executes_write_and_command_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "verify.py").write_text(
                "from pathlib import Path\n"
                "assert 'VALUE = 2' in Path('app.py').read_text(encoding='utf-8')\n"
                "p=Path('runs.txt')\n"
                "p.write_text((p.read_text() if p.exists() else '') + 'x', encoding='utf-8')\n"
                "print('task-pass')\n",
                encoding="utf-8",
            )
            inference = _InferenceSequence(
                json.dumps({"files": ["app.py", "verify.py"], "reason": "edit and verify"}),
                json.dumps(
                    {
                        "summary": "Update and verify",
                        "actions": [
                            {
                                "type": "write_text",
                                "path": "app.py",
                                "content": "VALUE = 2\n",
                                "purpose": "update value",
                            },
                            {
                                "type": "command",
                                "argv": ["python", "verify.py"],
                                "cwd": ".",
                                "timeout_seconds": 30,
                                "purpose": "verify requested behavior",
                            },
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            commands = RemoteCommandController(root / "state", workspace_root=root)
            tasks = RemoteTaskController(
                root / "state",
                workspace_root=root,
                planner=planner,
                command_controller=commands,
                id_factory=lambda: "rtask-" + ("a" * 24),
            )

            pending = tasks.prepare(
                "change VALUE to 2",
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            self.assertEqual(pending["status"], "PENDING")
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "VALUE = 1\n")
            self.assertFalse((root / "runs.txt").exists())

            first = tasks.approve_and_execute(
                task_id=pending["task_id"],
                plan_digest=pending["plan_digest"],
                session_id="session-1",
                device_id="phone-1",
            )
            second = tasks.approve_and_execute(
                task_id=pending["task_id"],
                plan_digest=pending["plan_digest"],
                session_id="session-1",
                device_id="phone-1",
            )

            self.assertEqual(first["status"], "COMPLETED")
            self.assertEqual(second, first)
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "VALUE = 2\n")
            self.assertEqual((root / "runs.txt").read_text(encoding="utf-8"), "x")
            self.assertIn("task-pass", first["receipts"][1]["stdout"])

    def test_persisted_plan_tampering_is_rejected_on_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "state"
            (root / "app.py").write_text("VALUE=1\n", encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["app.py"], "reason": "target"}),
                json.dumps(
                    {
                        "summary": "update",
                        "actions": [
                            {
                                "type": "write_text",
                                "path": "app.py",
                                "content": "VALUE=2\n",
                                "purpose": "approved replacement",
                            }
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            commands = RemoteCommandController(state, workspace_root=root)
            tasks = RemoteTaskController(
                state,
                workspace_root=root,
                planner=planner,
                command_controller=commands,
                id_factory=lambda: "rtask-" + ("f" * 24),
            )
            pending = tasks.prepare(
                "update app",
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )

            state_path = state / "remote_tasks.json"
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            persisted["tasks"][pending["task_id"]]["plan"]["actions"][0]["content"] = (
                "VALUE=999\n"
            )
            state_path.write_text(
                json.dumps(persisted, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            reloader_planner = RemoteTaskPlanner(
                root,
                inference_adapter=lambda _prompt: "{}",
            )
            with self.assertRaisesRegex(
                RemoteTaskError,
                "persisted digest mismatch",
            ):
                RemoteTaskController(
                    state,
                    workspace_root=root,
                    planner=reloader_planner,
                    command_controller=commands,
                )

            self.assertEqual(
                (root / "app.py").read_text(encoding="utf-8"),
                "VALUE=1\n",
            )

    def test_wrong_plan_digest_never_mutates_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("VALUE=1\n", encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["app.py"], "reason": "target"}),
                json.dumps(
                    {
                        "summary": "update",
                        "actions": [
                            {
                                "type": "write_text",
                                "path": "app.py",
                                "content": "VALUE=2\n",
                                "purpose": "update",
                            }
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            commands = RemoteCommandController(root / "state", workspace_root=root)
            tasks = RemoteTaskController(
                root / "state",
                workspace_root=root,
                planner=planner,
                command_controller=commands,
                id_factory=lambda: "rtask-" + ("b" * 24),
            )
            pending = tasks.prepare(
                "update app",
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            with self.assertRaises(RemoteTaskError):
                tasks.approve_and_execute(
                    task_id=pending["task_id"],
                    plan_digest="0" * 64,
                    session_id="session-1",
                    device_id="phone-1",
                )
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "VALUE=1\n")

    def test_preflight_hash_change_blocks_entire_plan_before_first_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("A=1\n", encoding="utf-8")
            (root / "b.py").write_text("B=1\n", encoding="utf-8")
            inference = _InferenceSequence(
                json.dumps({"files": ["a.py", "b.py"], "reason": "two edits"}),
                json.dumps(
                    {
                        "summary": "two writes",
                        "actions": [
                            {"type": "write_text", "path": "a.py", "content": "A=2\n", "purpose": "a"},
                            {"type": "write_text", "path": "b.py", "content": "B=2\n", "purpose": "b"},
                        ],
                    }
                ),
            )
            planner = RemoteTaskPlanner(root, inference_adapter=inference)
            commands = RemoteCommandController(root / "state", workspace_root=root)
            tasks = RemoteTaskController(
                root / "state",
                workspace_root=root,
                planner=planner,
                command_controller=commands,
                id_factory=lambda: "rtask-" + ("c" * 24),
            )
            pending = tasks.prepare(
                "edit both",
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            (root / "b.py").write_text("B=changed externally\n", encoding="utf-8")

            with self.assertRaises(Exception):
                tasks.approve_and_execute(
                    task_id=pending["task_id"],
                    plan_digest=pending["plan_digest"],
                    session_id="session-1",
                    device_id="phone-1",
                )
            self.assertEqual((root / "a.py").read_text(encoding="utf-8"), "A=1\n")


if __name__ == "__main__":
    unittest.main()
