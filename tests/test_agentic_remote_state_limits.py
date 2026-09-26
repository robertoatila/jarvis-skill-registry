#!/usr/bin/env python3
"""Capacity and retention contracts for J.A.R.V.I.S. remote persistent state."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tooling.remote_commands as remote_commands
import tooling.remote_devices as remote_devices
import tooling.remote_sessions as remote_sessions
import tooling.remote_tasks as remote_tasks
from tooling.remote_commands import RemoteCommandController, RemoteCommandError
from tooling.remote_devices import RemoteDeviceError, RemoteDeviceRegistry
from tooling.remote_sessions import RemoteSessionError, RemoteSessionStore
from tooling.remote_tasks import RemoteTaskController, RemoteTaskError, RemoteTaskPlanner


class _Ids:
    def __init__(self, *values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


class TestRemoteSessionCapacity(unittest.TestCase):
    def test_active_sessions_are_bounded_per_device(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_sessions, "MAX_ACTIVE_SESSIONS_PER_DEVICE", 2
        ):
            store = RemoteSessionStore(
                Path(tmp),
                id_factory=_Ids("session-1", "session-2", "session-3"),
            )
            store.create_session("phone-1")
            store.create_session("phone-1")
            with self.assertRaisesRegex(RemoteSessionError, "too many active sessions"):
                store.create_session("phone-1")

    def test_closed_session_is_pruned_when_store_reaches_capacity(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(remote_sessions, "MAX_SESSIONS_TOTAL", 2),
            mock.patch.object(remote_sessions, "MAX_ACTIVE_SESSIONS_PER_DEVICE", 4),
        ):
            store = RemoteSessionStore(
                Path(tmp),
                id_factory=_Ids("session-1", "session-2", "session-3"),
            )
            first = store.create_session("phone-1")
            store.create_session("phone-2")
            store.close_session(first["session_id"])

            third = store.create_session("phone-3")

            self.assertIsNone(store.get_session(first["session_id"]))
            self.assertEqual(third["session_id"], "session-3")

    def test_global_event_storage_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_sessions, "MAX_EVENT_STORAGE_BYTES", 1
        ):
            store = RemoteSessionStore(Path(tmp), id_factory=_Ids("session-1"))
            session = store.create_session("phone-1")
            with self.assertRaisesRegex(RemoteSessionError, "global size limit"):
                store.append_event(session["session_id"], "status", {"ok": True})

    def test_request_result_size_is_bounded_before_persistence(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_sessions, "MAX_REQUEST_RESULT_BYTES", 32
        ):
            store = RemoteSessionStore(Path(tmp), id_factory=_Ids("session-1"))
            session = store.create_session("phone-1")
            with self.assertRaisesRegex(RemoteSessionError, "result exceeds size limit"):
                store.remember_request(
                    session["session_id"],
                    "request-1",
                    {"output": "x" * 128},
                    request_fingerprint="a" * 64,
                )


class TestRemoteDeviceCapacity(unittest.TestCase):
    def test_pending_pairing_offers_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_devices, "MAX_PENDING_PAIRING_OFFERS", 2
        ):
            registry = RemoteDeviceRegistry(
                Path(tmp),
                id_factory=_Ids("offer-1", "offer-2", "offer-3"),
            )
            registry.create_pairing_offer(label_hint="Phone")
            registry.create_pairing_offer(label_hint="Tablet")
            with self.assertRaisesRegex(RemoteDeviceError, "too many pending pairing offers"):
                registry.create_pairing_offer(label_hint="Other")

    def test_expired_pairing_offers_do_not_consume_pending_capacity(self):
        now = [1000.0]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_devices, "MAX_PENDING_PAIRING_OFFERS", 1
        ):
            registry = RemoteDeviceRegistry(
                Path(tmp),
                clock=lambda: now[0],
                id_factory=_Ids("offer-1", "offer-2"),
                pairing_ttl_seconds=1,
            )
            registry.create_pairing_offer(label_hint="Phone")
            now[0] = 1002.0
            second = registry.create_pairing_offer(label_hint="Tablet")
            self.assertEqual(second["offer_id"], "offer-2")

    def test_active_device_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_devices, "MAX_ACTIVE_DEVICES", 1
        ):
            registry = RemoteDeviceRegistry(
                Path(tmp),
                id_factory=_Ids("offer-1", "device-1", "offer-2"),
            )
            first = registry.create_pairing_offer(label_hint="Phone")
            registry.complete_pairing(
                first["offer_id"],
                {
                    "pairing_secret": first["pairing_secret"],
                    "credential": "a" * 64,
                    "label": "Phone",
                },
            )
            second = registry.create_pairing_offer(label_hint="Tablet")
            with self.assertRaisesRegex(RemoteDeviceError, "too many active remote devices"):
                registry.complete_pairing(
                    second["offer_id"],
                    {
                        "pairing_secret": second["pairing_secret"],
                        "credential": "b" * 64,
                        "label": "Tablet",
                    },
                )

    def test_revoked_device_is_pruned_at_record_capacity(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(remote_devices, "MAX_DEVICE_RECORDS", 1),
            mock.patch.object(remote_devices, "MAX_ACTIVE_DEVICES", 2),
        ):
            registry = RemoteDeviceRegistry(
                Path(tmp),
                id_factory=_Ids("offer-1", "device-1", "offer-2", "device-2"),
            )
            first = registry.create_pairing_offer(label_hint="Phone")
            device = registry.complete_pairing(
                first["offer_id"],
                {
                    "pairing_secret": first["pairing_secret"],
                    "credential": "a" * 64,
                    "label": "Phone",
                },
            )
            registry.revoke(device.device_id)

            second = registry.create_pairing_offer(label_hint="Tablet")
            replacement = registry.complete_pairing(
                second["offer_id"],
                {
                    "pairing_secret": second["pairing_secret"],
                    "credential": "b" * 64,
                    "label": "Tablet",
                },
            )

            self.assertIsNone(registry.get(device.device_id))
            self.assertEqual(replacement.device_id, "device-2")


class _Inference:
    def __init__(self, *outputs):
        self.outputs = list(outputs)

    def __call__(self, _prompt):
        if not self.outputs:
            raise AssertionError("unexpected inference call")
        return self.outputs.pop(0)


class TestRemoteCommandCapacity(unittest.TestCase):
    def test_pending_command_actions_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_commands, "MAX_PENDING_COMMANDS", 1
        ):
            root = Path(tmp)
            controller = RemoteCommandController(
                root / "state",
                workspace_root=root,
                id_factory=_Ids("rcmd-" + ("a" * 24), "rcmd-" + ("b" * 24)),
            )
            controller.prepare(
                {"argv": ["python", "--version"]},
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            with self.assertRaisesRegex(RemoteCommandError, "too many pending"):
                controller.prepare(
                    {"argv": ["python", "--version"]},
                    session_id="session-1",
                    device_id="phone-1",
                    request_id="request-2",
                )

    def test_completed_command_is_pruned_at_record_capacity(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(remote_commands, "MAX_COMMAND_RECORDS", 1),
            mock.patch.object(remote_commands, "MAX_PENDING_COMMANDS", 2),
        ):
            root = Path(tmp)
            controller = RemoteCommandController(
                root / "state",
                workspace_root=root,
                id_factory=_Ids("rcmd-" + ("a" * 24), "rcmd-" + ("b" * 24)),
            )
            first = controller.prepare(
                {"argv": ["python", "--version"]},
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            controller._state["actions"][first["action_id"]]["status"] = "COMPLETED"
            controller._state["actions"][first["action_id"]]["result"] = {"status": "PASS"}
            controller._save()

            second = controller.prepare(
                {"argv": ["python", "--version"]},
                session_id="session-1",
                device_id="phone-1",
                request_id="request-2",
            )

            self.assertIsNone(controller.get(first["action_id"]))
            self.assertEqual(second["action_id"], "rcmd-" + ("b" * 24))


class TestRemoteTaskCapacity(unittest.TestCase):
    @staticmethod
    def _planner(root, repetitions=1):
        outputs = []
        for _ in range(repetitions):
            outputs.extend(
                [
                    json.dumps({"files": ["app.py"], "reason": "target"}),
                    json.dumps(
                        {
                            "summary": "verify app",
                            "actions": [
                                {
                                    "type": "command",
                                    "argv": ["python", "-m", "compileall", "app.py"],
                                    "purpose": "verify syntax",
                                }
                            ],
                        }
                    ),
                ]
            )
        return RemoteTaskPlanner(root, inference_adapter=_Inference(*outputs))

    def test_pending_tasks_are_bounded_before_extra_inference(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            remote_tasks, "MAX_PENDING_TASKS", 1
        ):
            root = Path(tmp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            commands = RemoteCommandController(root / "state", workspace_root=root)
            controller = RemoteTaskController(
                root / "state",
                workspace_root=root,
                planner=self._planner(root, repetitions=1),
                command_controller=commands,
                id_factory=_Ids("rtask-" + ("a" * 24)),
            )
            controller.prepare(
                "verify app",
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            with self.assertRaisesRegex(RemoteTaskError, "too many pending"):
                controller.prepare(
                    "verify app again",
                    session_id="session-1",
                    device_id="phone-1",
                    request_id="request-2",
                )

    def test_completed_task_is_pruned_at_record_capacity(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(remote_tasks, "MAX_TASK_RECORDS", 1),
            mock.patch.object(remote_tasks, "MAX_PENDING_TASKS", 2),
        ):
            root = Path(tmp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            commands = RemoteCommandController(root / "state", workspace_root=root)
            controller = RemoteTaskController(
                root / "state",
                workspace_root=root,
                planner=self._planner(root, repetitions=2),
                command_controller=commands,
                id_factory=_Ids(
                    "rtask-" + ("a" * 24),
                    "rtask-" + ("b" * 24),
                ),
            )
            first = controller.prepare(
                "verify app",
                session_id="session-1",
                device_id="phone-1",
                request_id="request-1",
            )
            controller._state["tasks"][first["task_id"]]["status"] = "COMPLETED"
            controller._state["tasks"][first["task_id"]]["result"] = {"status": "COMPLETED"}
            controller._save()

            second = controller.prepare(
                "verify app again",
                session_id="session-1",
                device_id="phone-1",
                request_id="request-2",
            )

            self.assertIsNone(controller.get(first["task_id"]))
            self.assertEqual(second["task_id"], "rtask-" + ("b" * 24))


if __name__ == "__main__":
    unittest.main()
