#!/usr/bin/env python3
"""Truthful lifecycle contracts for the resident J.A.R.V.I.S. home-PC host."""

import json
import tempfile
import unittest
from pathlib import Path

from tooling.remote_host import RemoteHostController, RemoteHostError


class TestRemoteHostController(unittest.TestCase):
    def test_online_state_survives_restart_when_pid_is_alive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = RemoteHostController(
                root,
                clock=lambda: 1000.0,
                pid_probe=lambda pid: pid == 4321,
            )
            published = controller.publish_online(
                host_id="home-pc",
                pid=4321,
                port=8899,
                remote_enabled=True,
                transport="lan",
            )
            self.assertEqual(published["status"], "ONLINE")
            self.assertEqual(published["started_at"], 1000.0)

            reopened = RemoteHostController(
                root,
                clock=lambda: 1001.0,
                pid_probe=lambda pid: pid == 4321,
            )
            status = reopened.status()
            self.assertEqual(status["status"], "ONLINE")
            self.assertEqual(status["host_id"], "home-pc")
            self.assertEqual(status["pid"], 4321)
            self.assertEqual(status["port"], 8899)

    def test_stale_pid_is_reported_offline_not_online(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller = RemoteHostController(
                Path(tmp),
                clock=lambda: 2000.0,
                pid_probe=lambda _pid: False,
            )
            controller.publish_online(
                host_id="home-pc",
                pid=9876,
                port=8899,
                remote_enabled=True,
                transport="overlay",
            )

            status = controller.status()
            self.assertEqual(status["status"], "OFFLINE")
            self.assertEqual(status["reason"], "STALE_PID")
            self.assertEqual(status["last_known_pid"], 9876)
            self.assertNotIn("pid", status)

    def test_explicit_offline_state_is_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = RemoteHostController(
                root,
                clock=lambda: 3000.0,
                pid_probe=lambda _pid: True,
            )
            controller.publish_online(
                host_id="home-pc",
                pid=111,
                port=8899,
                remote_enabled=False,
                transport="none",
            )
            offline = controller.publish_offline("STOPPED")
            self.assertEqual(offline["status"], "OFFLINE")
            self.assertEqual(offline["reason"], "STOPPED")
            self.assertNotIn("pid", offline)

            reopened = RemoteHostController(root, clock=lambda: 3001.0)
            self.assertEqual(reopened.status()["status"], "OFFLINE")
            self.assertEqual(reopened.status()["reason"], "STOPPED")

    def test_missing_state_is_truthfully_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller = RemoteHostController(Path(tmp), clock=lambda: 4000.0)
            status = controller.status()
            self.assertEqual(status["status"], "OFFLINE")
            self.assertEqual(status["reason"], "NOT_STARTED")

    def test_rejects_unsupported_future_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.mkdir(parents=True, exist_ok=True)
            (root / "remote_host.json").write_text(
                json.dumps({"schema_version": 999, "status": "ONLINE"}),
                encoding="utf-8",
            )
            controller = RemoteHostController(root)
            with self.assertRaises(RemoteHostError):
                controller.status()

    def test_rejects_invalid_port_and_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller = RemoteHostController(Path(tmp), pid_probe=lambda _pid: True)
            with self.assertRaises(RemoteHostError):
                controller.publish_online(
                    host_id="home-pc",
                    pid=1,
                    port=70000,
                    remote_enabled=True,
                    transport="lan",
                )
            with self.assertRaises(RemoteHostError):
                controller.publish_online(
                    host_id="home-pc",
                    pid=1,
                    port=8899,
                    remote_enabled=True,
                    transport="magic",
                )


if __name__ == "__main__":
    unittest.main()
