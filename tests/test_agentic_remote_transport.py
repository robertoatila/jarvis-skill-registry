import json
import subprocess
import unittest

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


if __name__ == "__main__":
    unittest.main()
