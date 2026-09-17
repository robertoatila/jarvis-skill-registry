import inspect
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tooling import remote_host
from tooling.http_security import validate_authorized_request
from tooling.remote_devices import RemoteDeviceRegistry
from tooling.remote_http import RemoteJarvisHttpHandler, RemoteJarvisServer
from tooling.remote_runtime_bridge import RemoteRuntimeBridge
from tooling.remote_sessions import RemoteSessionStore
from tooling.remote_transport import RemoteTransportStatus, TransportState
from tooling.remote_transport_local import LanRemoteTransport, LocalRemoteTransport
from tooling.remote_transport_tailscale import TailscaleRemoteTransport


class RemoteTransportTests(unittest.TestCase):
    def test_local_transport_start_status_stop_is_truthful(self):
        transport = LocalRemoteTransport(port=8899, clock=lambda: 10.0)

        started = transport.start()
        self.assertEqual(started.transport_id, "local")
        self.assertEqual(started.state, TransportState.ACTIVE)
        self.assertEqual(started.public_or_private_endpoint, "http://127.0.0.1:8899")
        self.assertIsNotNone(started.last_verified_at)
        self.assertEqual(transport.status(), started)

        stopped = transport.stop()
        self.assertEqual(stopped.state, TransportState.STOPPED)
        self.assertIsNone(stopped.public_or_private_endpoint)
        self.assertIsNone(transport.status().public_or_private_endpoint)

    def test_lan_transport_rejects_public_endpoint(self):
        lan = LanRemoteTransport(host="192.168.10.20", port=8899, clock=lambda: 10.0)
        self.assertEqual(lan.start().public_or_private_endpoint, "http://192.168.10.20:8899")
        with self.assertRaises(ValueError):
            LanRemoteTransport(host="8.8.8.8", port=8899)

    def test_tailscale_transport_uses_verified_tailnet_endpoint(self):
        calls = []

        def runner(args, **kwargs):
            calls.append(list(args))
            payload = {
                "BackendState": "Running",
                "Self": {
                    "Online": True,
                    "TailscaleIPs": ["100.101.102.103"],
                },
            }
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")

        transport = TailscaleRemoteTransport(port=8899, runner=runner, clock=lambda: 20.0)
        status = transport.start()

        self.assertEqual(status.transport_id, "tailscale")
        self.assertEqual(status.state, TransportState.ACTIVE)
        self.assertEqual(status.public_or_private_endpoint, "http://100.101.102.103:8899")
        self.assertIsNotNone(status.last_verified_at)
        self.assertEqual(calls, [["tailscale", "status", "--json"]])

        transport.stop()
        self.assertEqual(calls, [["tailscale", "status", "--json"]])

    def test_tailscale_transport_reports_unavailable_without_fabricating_endpoint(self):
        def runner(args, **kwargs):
            raise FileNotFoundError("tailscale")

        status = TailscaleRemoteTransport(port=8899, runner=runner).start()
        self.assertEqual(status.state, TransportState.UNAVAILABLE)
        self.assertIsNone(status.public_or_private_endpoint)
        self.assertIsNone(status.last_verified_at)

    def test_tailscale_transport_rejects_non_tailnet_ip_even_if_cli_claims_running(self):
        def runner(args, **kwargs):
            payload = {
                "BackendState": "Running",
                "Self": {"Online": True, "TailscaleIPs": ["192.168.1.50"]},
            }
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")

        status = TailscaleRemoteTransport(port=8899, runner=runner).start()
        self.assertEqual(status.state, TransportState.UNAVAILABLE)
        self.assertIsNone(status.public_or_private_endpoint)

    def test_transport_status_serializes_without_credentials(self):
        status = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.ACTIVE,
            public_or_private_endpoint="http://100.64.0.10:8899",
            last_verified_at="2026-09-16T21:00:00Z",
            detail="verified tailnet endpoint",
        )
        data = status.to_dict()
        self.assertEqual(data["transport_id"], "tailscale")
        self.assertEqual(data["state"], "ACTIVE")
        self.assertNotIn("token", data)
        self.assertNotIn("credential", data)
        self.assertNotIn("secret", data)

    def test_security_guard_accepts_overlay_range_only_when_transport_declares_it(self):
        signature = inspect.signature(validate_authorized_request)
        self.assertIn("allowed_networks", signature.parameters)
        args = ("100.101.102.103", "100.101.102.103:8899", "", 8899, "")
        self.assertFalse(
            validate_authorized_request(*args, token="cred", expected_token="cred")
        )
        self.assertTrue(
            validate_authorized_request(
                *args,
                token="cred",
                expected_token="cred",
                allowed_networks=("100.64.0.0/10",),
            )
        )

    def test_host_status_provider_exposes_verified_transport_status(self):
        self.assertTrue(hasattr(remote_host, "build_transport_status_provider"))
        transport = LocalRemoteTransport(port=8899, clock=lambda: 10.0)
        transport.start()
        provider = remote_host.build_transport_status_provider(
            lambda: {"status": "ONLINE", "transport": "local"}, transport
        )
        status = provider()
        self.assertEqual(status["status"], "ONLINE")
        self.assertEqual(status["transport_status"]["state"], "ACTIVE")
        self.assertEqual(
            status["transport_status"]["public_or_private_endpoint"],
            "http://127.0.0.1:8899",
        )

    def test_verified_transport_endpoint_can_drive_specific_bind_host(self):
        self.assertTrue(hasattr(remote_host, "bind_host_for_transport"))
        status = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.ACTIVE,
            public_or_private_endpoint="http://100.101.102.103:8899",
            last_verified_at="2026-09-16T21:00:00Z",
            detail="verified active tailnet endpoint",
        )
        self.assertEqual(remote_host.bind_host_for_transport(status), "100.101.102.103")
        unavailable = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.UNAVAILABLE,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="unavailable",
        )
        with self.assertRaises(Exception):
            remote_host.bind_host_for_transport(unavailable)

    def test_remote_server_accepts_transport_for_status_and_network_guard(self):
        signature = inspect.signature(RemoteJarvisServer.__init__)
        self.assertIn("remote_transport", signature.parameters)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = RemoteDeviceRegistry(root / "devices")
            store = RemoteSessionStore(root / "sessions")
            bridge = RemoteRuntimeBridge(
                store,
                runtime_adapter=lambda request: {"status": "UNVERIFIED", "reply": request["text"]},
            )
            transport = LocalRemoteTransport(port=8899)
            server = RemoteJarvisServer(
                ("127.0.0.1", 0),
                RemoteJarvisHttpHandler,
                session_store=store,
                runtime_bridge=bridge,
                host_status_provider=lambda: {"status": "ONLINE"},
                device_registry=registry,
                remote_transport=transport,
            )
            try:
                self.assertIs(server.remote_transport, transport)
            finally:
                server.server_close()

    def test_remote_server_factory_projects_transport_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = remote_host.RemoteHostController(root, pid_probe=lambda _pid: True)
            controller.publish_online(
                host_id="home-pc",
                pid=123,
                port=8899,
                remote_enabled=False,
                transport="local",
            )
            transport = LocalRemoteTransport(port=8899, clock=lambda: 10.0)
            transport.start()
            server = remote_host.create_remote_server(
                ("127.0.0.1", 0),
                state_dir=root,
                runtime_adapter=lambda request: {"status": "UNVERIFIED", "reply": request["text"]},
                host_controller=controller,
                remote_transport=transport,
            )
            try:
                self.assertIs(server.remote_transport, transport)
                status = server.host_status_provider()
                self.assertEqual(status["status"], "ONLINE")
                self.assertEqual(status["transport_status"]["transport_id"], "local")
                self.assertEqual(status["transport_status"]["state"], "ACTIVE")
            finally:
                server.server_close()


if __name__ == "__main__":
    unittest.main()
