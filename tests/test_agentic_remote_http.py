#!/usr/bin/env python3
"""In-process HTTP contracts for the versioned Remote Companion API."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from tooling.remote_commands import RemoteCommandController
from tooling.remote_devices import RemoteDeviceRegistry
from tooling.remote_http import RemoteJarvisServer, RemoteJarvisHttpHandler
from tooling.remote_protocol import PROTOCOL_VERSION
from tooling.remote_runtime_bridge import RemoteRuntimeBridge
from tooling.remote_sessions import RemoteSessionStore
from tooling.remote_transport import RemoteTransport, RemoteTransportStatus, TransportState


class _HttpsProxyTransport(RemoteTransport):
    @property
    def trusted_reverse_proxy_endpoint(self):
        return "https://home-pc.example.ts.net"

    @property
    def requires_device_auth_on_loopback(self):
        return True

    def start(self):
        return self.status()

    def status(self):
        return RemoteTransportStatus(
            transport_id="tailscale-serve",
            state=TransportState.ACTIVE,
            public_or_private_endpoint="https://home-pc.example.ts.net",
            last_verified_at="2026-09-19T18:30:00Z",
            detail="test proxy",
        )

    def stop(self):
        return RemoteTransportStatus(
            transport_id="tailscale-serve",
            state=TransportState.STOPPED,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="stopped",
        )


class TestRemoteCompanionApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        ids = iter(["session-1", "session-2", "session-3"])
        self.store = RemoteSessionStore(Path(self.tmp.name), id_factory=lambda: next(ids))
        self.runtime_calls = []

        def runtime_adapter(request):
            self.runtime_calls.append(dict(request))
            return {
                "status": "UNVERIFIED",
                "mission_id": "mission-1",
                "reply": "reply from home PC",
            }

        self.command_controller = RemoteCommandController(
            Path(self.tmp.name),
            workspace_root=Path(self.tmp.name),
            id_factory=lambda: "rcmd-" + ("e" * 24),
        )
        self.bridge = RemoteRuntimeBridge(
            self.store,
            runtime_adapter=runtime_adapter,
            command_controller=self.command_controller,
        )
        self.server = RemoteJarvisServer(
            ("127.0.0.1", 0),
            RemoteJarvisHttpHandler,
            session_store=self.store,
            runtime_bridge=self.bridge,
            host_status_provider=lambda: {
                "schema_version": 1,
                "host_id": "home-pc-test",
                "status": "ONLINE",
                "remote_enabled": True,
                "transport": "local",
            },
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        data = None
        request_headers = dict(headers or {})
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            self.base + path,
            data=data,
            headers=request_headers,
            method=method,
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            raw = response.read()
            return response.status, json.loads(raw.decode("utf-8")) if raw else None

    def test_host_session_message_event_ack_and_close_flow(self):
        status, host = self.request("GET", "/api/remote/v1/host")
        self.assertEqual(status, 200)
        self.assertEqual(host["status"], "ONLINE")
        self.assertEqual(host["host_id"], "home-pc-test")

        status, opened = self.request(
            "POST", "/api/remote/v1/sessions", {"device_id": "phone-1"}
        )
        self.assertEqual(status, 201)
        self.assertEqual(opened["session_id"], "session-1")

        envelope = {
            "protocol": PROTOCOL_VERSION,
            "session_id": "session-1",
            "device_id": "phone-1",
            "request_id": "req-1",
            "kind": "message",
            "payload": {"text": "continue"},
        }
        status, accepted = self.request(
            "POST", "/api/remote/v1/sessions/session-1/messages", envelope
        )
        self.assertEqual(status, 202)
        self.assertEqual(accepted["request_id"], "req-1")
        self.assertEqual(accepted["mission_id"], "mission-1")
        self.assertEqual(len(self.runtime_calls), 1)

        status, events = self.request(
            "GET",
            "/api/remote/v1/sessions/session-1/events?after=1&limit=50",
            headers={"X-Jarvis-Device-ID": "phone-1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual([event["seq"] for event in events["events"]], [2])
        self.assertEqual(events["events"][0]["payload"]["text"], "reply from home PC")

        status, acknowledged = self.request(
            "POST",
            "/api/remote/v1/sessions/session-1/ack",
            {"device_id": "phone-1", "seq": 2},
        )
        self.assertEqual(status, 200)
        self.assertEqual(acknowledged["last_ack_seq"], 2)

        status, session = self.request(
            "GET",
            "/api/remote/v1/sessions/session-1",
            headers={"X-Jarvis-Device-ID": "phone-1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(session["last_ack_seq"], 2)

        status, closed = self.request(
            "POST",
            "/api/remote/v1/sessions/session-1/close",
            {"device_id": "phone-1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(closed["status"], "CLOSED")

    def test_local_admin_stop_control_is_loopback_only(self):
        req = urllib.request.Request(
            self.base + "/api/remote/v1/admin/stop",
            data=b"",
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            body = json.loads(response.read().decode("utf-8"))
        self.assertEqual(response.status, 202)
        self.assertEqual(body["status"], "STOPPING")
        self.thread.join(timeout=2)
        self.assertFalse(self.thread.is_alive())

    def test_remote_command_requires_approval_then_executes_on_host(self):
        Path(self.tmp.name, "gate.py").write_text(
            "print('http-gate-pass')\\n",
            encoding="utf-8",
        )
        self.request("POST", "/api/remote/v1/sessions", {"device_id": "phone-1"})
        command = {
            "protocol": PROTOCOL_VERSION,
            "session_id": "session-1",
            "device_id": "phone-1",
            "request_id": "req-command",
            "kind": "command",
            "payload": {"argv": ["python", "gate.py"], "timeout_seconds": 30},
        }
        status, pending = self.request(
            "POST", "/api/remote/v1/sessions/session-1/messages", command
        )
        self.assertEqual(status, 202)
        self.assertEqual(pending["status"], "APPROVAL_REQUIRED")

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
        status, executed = self.request(
            "POST", "/api/remote/v1/sessions/session-1/messages", approval
        )
        self.assertEqual(status, 202)
        self.assertEqual(executed["status"], "PASS")
        self.assertEqual(executed["exit_code"], 0)

        _, events = self.request(
            "GET",
            "/api/remote/v1/sessions/session-1/events?after=0&limit=50",
            headers={"X-Jarvis-Device-ID": "phone-1"},
        )
        receipt_events = [event for event in events["events"] if event["kind"] == "action_receipt"]
        self.assertEqual(len(receipt_events), 1)
        self.assertIn("http-gate-pass", receipt_events[0]["payload"]["receipt"]["stdout"])

    def test_remote_companion_static_assets_are_served_by_remote_host(self):
        expected = {
            "/remote": "text/html",
            "/remote-companion.js": "javascript",
            "/remote-companion.css": "text/css",
            "/manifest.webmanifest": "application/manifest+json",
            "/service-worker.js": "javascript",
        }
        for path, content_type_fragment in expected.items():
            with self.subTest(path=path):
                with urllib.request.urlopen(self.base + path, timeout=3) as response:
                    payload = response.read()
                    content_type = response.headers.get("Content-Type", "")
                self.assertEqual(response.status, 200)
                self.assertTrue(payload)
                self.assertIn(content_type_fragment, content_type)

    def test_https_reverse_proxy_serves_shell_but_remote_api_still_requires_device_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = RemoteDeviceRegistry(root / "devices")
            offer = registry.create_pairing_offer(label_hint="Phone")
            credential = "c" * 64
            device = registry.complete_pairing(
                offer["offer_id"],
                {
                    "pairing_secret": offer["pairing_secret"],
                    "credential": credential,
                    "label": "Phone",
                },
            )
            store = RemoteSessionStore(root / "sessions", device_validator=registry.is_active)
            bridge = RemoteRuntimeBridge(
                store,
                runtime_adapter=lambda request: {
                    "status": "UNVERIFIED",
                    "reply": request["text"],
                },
            )
            transport = _HttpsProxyTransport()
            server = RemoteJarvisServer(
                ("127.0.0.1", 0),
                RemoteJarvisHttpHandler,
                session_store=store,
                runtime_bridge=bridge,
                host_status_provider=lambda: {
                    "schema_version": 1,
                    "host_id": "home-pc",
                    "status": "ONLINE",
                    "transport_status": transport.status().to_dict(),
                },
                device_registry=registry,
                remote_transport=transport,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            proxy_headers = {
                "Host": "home-pc.example.ts.net",
                "Origin": "https://home-pc.example.ts.net",
                "Sec-Fetch-Site": "same-origin",
            }
            try:
                shell_req = urllib.request.Request(
                    base + "/remote",
                    headers=proxy_headers,
                    method="GET",
                )
                with urllib.request.urlopen(shell_req, timeout=3) as response:
                    shell = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn("J.A.R.V.I.S. Remote Companion", shell)

                host_req = urllib.request.Request(
                    base + "/api/remote/v1/host",
                    headers=proxy_headers,
                    method="GET",
                )
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(host_req, timeout=3)
                self.assertEqual(caught.exception.code, 403)

                authorized_headers = {
                    **proxy_headers,
                    "X-Jarvis-Device-ID": device.device_id,
                    "X-Jarvis-Device-Credential": credential,
                }
                host_req = urllib.request.Request(
                    base + "/api/remote/v1/host",
                    headers=authorized_headers,
                    method="GET",
                )
                with urllib.request.urlopen(host_req, timeout=3) as response:
                    host = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.status, 200)
                self.assertEqual(host["status"], "ONLINE")

                stop_req = urllib.request.Request(
                    base + "/api/remote/v1/admin/stop",
                    data=b"",
                    headers=authorized_headers,
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(stop_req, timeout=3)
                self.assertEqual(caught.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_unknown_session_returns_404(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.request(
                "GET",
                "/api/remote/v1/sessions/missing",
                headers={"X-Jarvis-Device-ID": "phone-1"},
            )
        self.assertEqual(caught.exception.code, 404)

    def test_wrong_device_cannot_read_session(self):
        self.request("POST", "/api/remote/v1/sessions", {"device_id": "phone-1"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.request(
                "GET",
                "/api/remote/v1/sessions/session-1",
                headers={"X-Jarvis-Device-ID": "other-phone"},
            )
        self.assertEqual(caught.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
