#!/usr/bin/env python3
"""Truthful lifecycle contracts for the resident J.A.R.V.I.S. home-PC host."""

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import jarvis
import tooling.remote_host as remote_host
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

    def test_start_foreground_publishes_live_state_then_clean_offline_state(self):
        self.assertTrue(hasattr(RemoteHostController, "start_foreground"))
        with tempfile.TemporaryDirectory() as tmp:
            controller = RemoteHostController(
                Path(tmp),
                clock=lambda: 5000.0,
                pid_probe=lambda pid: pid == 321,
            )
            observed = []

            class Server:
                closed = False

                def serve_forever(inner_self):
                    observed.append(controller.status())

                def server_close(inner_self):
                    inner_self.closed = True

            server = Server()
            controller.start_foreground(
                server,
                host_id="home-pc",
                pid=321,
                port=8899,
                remote_enabled=True,
                transport="lan",
            )

            self.assertEqual(observed[0]["status"], "ONLINE")
            self.assertEqual(observed[0]["pid"], 321)
            final = controller.status()
            self.assertEqual(final["status"], "OFFLINE")
            self.assertEqual(final["reason"], "STOPPED")
            self.assertTrue(server.closed)

    def test_remote_server_factory_wires_truthful_host_status_provider(self):
        self.assertTrue(hasattr(remote_host, "create_remote_server"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = RemoteHostController(root, pid_probe=lambda _pid: True)
            controller.publish_online(
                host_id="home-pc-test",
                pid=os.getpid(),
                port=8899,
                remote_enabled=True,
                transport="local",
            )
            server = remote_host.create_remote_server(
                ("127.0.0.1", 0),
                state_dir=root,
                runtime_adapter=lambda _request: {
                    "status": "UNVERIFIED",
                    "reply": "ok",
                },
                host_controller=controller,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{server.server_port}/api/remote/v1/host",
                    timeout=3,
                ) as response:
                    body = json.loads(response.read().decode("utf-8"))
                self.assertEqual(body["status"], "ONLINE")
                self.assertEqual(body["host_id"], "home-pc-test")
                self.assertEqual(body["pid"], os.getpid())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_resident_runtime_adapter_uses_pc_side_chat_config_without_http_or_phone_secrets(self):
        self.assertTrue(hasattr(remote_host, "build_resident_runtime_adapter"))
        captured = {}

        def execute(provider, model, api_key, message, authorization):
            captured.update(
                provider=provider,
                model=model,
                api_key=api_key,
                message=message,
                authorization=authorization,
            )
            return {"status": "UNVERIFIED", "reply": "same resident runtime"}

        with (
            unittest.mock.patch.object(
                remote_host,
                "_resident_chat_executor",
                return_value=execute,
                create=True,
            ),
            unittest.mock.patch(
                "tooling.jarvis_server.get_configured_keys",
                return_value={
                    "preferred_provider": "groq",
                    "groq_model": "openai/gpt-oss-120b",
                    "groq": "pc-secret-key",
                },
            ),
            unittest.mock.patch.dict(
                os.environ,
                {
                    "JARVIS_CHAT_TOKEN": "pc-chat-token",
                    "JARVIS_CHAT_ALLOW_CLOUD": "1",
                    "JARVIS_CHAT_PROVIDERS": "groq",
                },
                clear=False,
            ),
            unittest.mock.patch("urllib.request.urlopen", side_effect=AssertionError("resident adapter must not use HTTP")),
        ):
            adapter = remote_host.build_resident_runtime_adapter()
            result = adapter(
                {
                    "text": "continue",
                    "payload": {
                        "apiKey": "must-never-cross-from-phone",
                    },
                }
            )

        self.assertEqual(result["reply"], "same resident runtime")
        self.assertEqual(
            captured,
            {
                "provider": "groq",
                "model": "openai/gpt-oss-120b",
                "api_key": "",
                "message": "continue",
                "authorization": "Bearer pc-chat-token",
            },
        )

    def test_loopback_runtime_adapter_reuses_local_chat_without_remote_api_key(self):
        self.assertTrue(hasattr(remote_host, "build_loopback_runtime_adapter"))
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(inner_self):
                length = int(inner_self.headers.get("Content-Length", "0"))
                captured.update(json.loads(inner_self.rfile.read(length).decode("utf-8")))
                payload = json.dumps(
                    {"status": "UNVERIFIED", "reply": "same local runtime"}
                ).encode("utf-8")
                inner_self.send_response(200)
                inner_self.send_header("Content-Type", "application/json")
                inner_self.send_header("Content-Length", str(len(payload)))
                inner_self.end_headers()
                inner_self.wfile.write(payload)

            def log_message(self, _format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            adapter = remote_host.build_loopback_runtime_adapter(server.server_port)
            result = adapter(
                {
                    "text": "continue",
                    "payload": {
                        "provider": "openai",
                        "model": "gpt-test",
                        "apiKey": "must-never-cross-from-phone",
                    },
                }
            )
            self.assertEqual(result["status"], "UNVERIFIED")
            self.assertEqual(result["reply"], "same local runtime")
            self.assertEqual(
                captured,
                {
                    "message": "continue",
                    "provider": "openai",
                    "model": "gpt-test",
                    "apiKey": "",
                },
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_host_launcher_command_is_additive_and_legacy_command_is_unchanged(self):
        self.assertEqual(
            jarvis.build_server_command(8899, remote=True),
            [sys.executable, str(jarvis.SERVER), "--port", "8899", "--remote"],
        )
        self.assertTrue(hasattr(jarvis, "build_host_server_command"))
        self.assertEqual(
            jarvis.build_host_server_command(8899, remote=True),
            [
                sys.executable,
                "-m",
                "tooling.remote_host",
                "--port",
                "8899",
                "--remote",
            ],
        )
        args = jarvis.build_parser().parse_args(["host", "--remote", "--no-browser"])
        self.assertEqual(args.command, "host")
        self.assertTrue(args.remote)
        self.assertTrue(args.no_browser)


if __name__ == "__main__":
    unittest.main()
