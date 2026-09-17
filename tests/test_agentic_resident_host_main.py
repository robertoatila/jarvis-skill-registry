#!/usr/bin/env python3
"""Production launcher contracts for one authoritative resident context."""

from __future__ import annotations

import unittest
from unittest import mock

import tooling.remote_host as remote_host
from tooling import jarvis_server
from tooling.remote_transport import RemoteTransportStatus, TransportState


class _Controller:
    def __init__(self, _state_dir) -> None:
        self.start_foreground = mock.Mock()


class ResidentHostMainTests(unittest.TestCase):
    def _run_main(
        self,
        argv,
        *,
        detected_ip="192.168.50.20",
        tailscale_status: RemoteTransportStatus | None = None,
    ):
        controller = _Controller(jarvis_server.STATE_DIR)
        device_registry = object()
        runtime_adapter = object()
        resident_context = object()
        server = object()
        local_transport = object()
        lan_transport = object()
        tailscale_transport = mock.Mock()
        tailscale_transport.start.return_value = tailscale_status or RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.ACTIVE,
            public_or_private_endpoint="http://100.101.102.103:8899",
            last_verified_at="2026-09-17T21:00:00+00:00",
            detail="verified active tailnet endpoint",
        )

        with (
            mock.patch.object(jarvis_server, "load_starred_catalog"),
            mock.patch.object(jarvis_server, "load_canonical_skills"),
            mock.patch.object(remote_host, "RemoteHostController", return_value=controller),
            mock.patch("tooling.remote_devices.RemoteDeviceRegistry", return_value=device_registry),
            mock.patch.object(remote_host, "build_resident_runtime_adapter", return_value=runtime_adapter) as build_adapter,
            mock.patch.object(remote_host, "build_loopback_runtime_adapter") as loopback_adapter,
            mock.patch("tooling.resident_host_context.ResidentHostContext", return_value=resident_context) as context_cls,
            mock.patch("tooling.remote_transport_local.LocalRemoteTransport", return_value=local_transport) as local_cls,
            mock.patch("tooling.remote_transport_local.LanRemoteTransport", return_value=lan_transport) as lan_cls,
            mock.patch("tooling.remote_transport_tailscale.TailscaleRemoteTransport", return_value=tailscale_transport) as tailscale_cls,
            mock.patch("tooling.remote_auth.detect_local_ip", return_value=detected_ip),
            mock.patch.object(remote_host, "create_remote_server", return_value=server) as create_server,
        ):
            try:
                result = remote_host.main(argv)
                error = None
            except remote_host.RemoteHostError as exc:
                result = None
                error = exc

        return {
            "result": result,
            "error": error,
            "controller": controller,
            "device_registry": device_registry,
            "runtime_adapter": runtime_adapter,
            "resident_context": resident_context,
            "server": server,
            "local_transport": local_transport,
            "lan_transport": lan_transport,
            "tailscale_transport": tailscale_transport,
            "build_adapter": build_adapter,
            "loopback_adapter": loopback_adapter,
            "context_cls": context_cls,
            "local_cls": local_cls,
            "lan_cls": lan_cls,
            "tailscale_cls": tailscale_cls,
            "create_server": create_server,
        }

    def test_local_launcher_uses_one_context_for_server_and_lifecycle(self):
        observed = self._run_main(["--port", "8899"])

        self.assertEqual(observed["result"], 0)
        self.assertIsNone(observed["error"])
        observed["build_adapter"].assert_called_once_with()
        observed["loopback_adapter"].assert_not_called()
        observed["local_cls"].assert_called_once_with(port=8899)
        observed["lan_cls"].assert_not_called()
        observed["tailscale_cls"].assert_not_called()
        observed["context_cls"].assert_called_once_with(
            jarvis_server.REGISTRY_ROOT,
            state_dir=jarvis_server.STATE_DIR,
            runtime_adapter=observed["runtime_adapter"],
            remote_transport=observed["local_transport"],
        )
        observed["create_server"].assert_called_once_with(
            ("127.0.0.1", 8899),
            state_dir=jarvis_server.STATE_DIR,
            resident_context=observed["resident_context"],
            host_controller=observed["controller"],
            remote_auth=None,
            device_registry=observed["device_registry"],
        )
        kwargs = observed["controller"].start_foreground.call_args.kwargs
        self.assertIs(kwargs["resident_context"], observed["resident_context"])
        self.assertEqual(kwargs["transport"], "local")

    def test_remote_launcher_uses_verified_private_lan_transport_in_same_context(self):
        observed = self._run_main(["--port", "8899", "--remote"], detected_ip="192.168.50.20")

        self.assertEqual(observed["result"], 0)
        self.assertIsNone(observed["error"])
        observed["local_cls"].assert_not_called()
        observed["lan_cls"].assert_called_once_with(host="192.168.50.20", port=8899)
        observed["tailscale_cls"].assert_not_called()
        observed["context_cls"].assert_called_once_with(
            jarvis_server.REGISTRY_ROOT,
            state_dir=jarvis_server.STATE_DIR,
            runtime_adapter=observed["runtime_adapter"],
            remote_transport=observed["lan_transport"],
        )
        observed["create_server"].assert_called_once_with(
            ("0.0.0.0", 8899),
            state_dir=jarvis_server.STATE_DIR,
            resident_context=observed["resident_context"],
            host_controller=observed["controller"],
            remote_auth=jarvis_server.REMOTE_AUTH,
            device_registry=observed["device_registry"],
        )
        kwargs = observed["controller"].start_foreground.call_args.kwargs
        self.assertIs(kwargs["resident_context"], observed["resident_context"])
        self.assertEqual(kwargs["transport"], "lan")

    def test_tailscale_launcher_binds_only_verified_tailnet_endpoint(self):
        observed = self._run_main(["--port", "8899", "--transport", "tailscale"])

        self.assertEqual(observed["result"], 0)
        self.assertIsNone(observed["error"])
        observed["local_cls"].assert_not_called()
        observed["lan_cls"].assert_not_called()
        observed["tailscale_cls"].assert_called_once_with(port=8899)
        observed["tailscale_transport"].start.assert_called_once_with()
        observed["context_cls"].assert_called_once_with(
            jarvis_server.REGISTRY_ROOT,
            state_dir=jarvis_server.STATE_DIR,
            runtime_adapter=observed["runtime_adapter"],
            remote_transport=observed["tailscale_transport"],
        )
        observed["create_server"].assert_called_once_with(
            ("100.101.102.103", 8899),
            state_dir=jarvis_server.STATE_DIR,
            resident_context=observed["resident_context"],
            host_controller=observed["controller"],
            remote_auth=jarvis_server.REMOTE_AUTH,
            device_registry=observed["device_registry"],
        )
        kwargs = observed["controller"].start_foreground.call_args.kwargs
        self.assertTrue(kwargs["remote_enabled"])
        self.assertEqual(kwargs["transport"], "overlay")

    def test_tailscale_launcher_fails_closed_without_verified_endpoint(self):
        unavailable = RemoteTransportStatus(
            transport_id="tailscale",
            state=TransportState.UNAVAILABLE,
            public_or_private_endpoint=None,
            last_verified_at=None,
            detail="Tailscale CLI unavailable",
        )
        observed = self._run_main(
            ["--port", "8899", "--transport", "tailscale"],
            tailscale_status=unavailable,
        )

        self.assertIsNone(observed["result"])
        self.assertIsInstance(observed["error"], remote_host.RemoteHostError)
        observed["create_server"].assert_not_called()
        observed["context_cls"].assert_not_called()

    def test_remote_launcher_fails_closed_when_no_private_lan_address_is_detected(self):
        with mock.patch("tooling.remote_auth.detect_local_ip", return_value="127.0.0.1"):
            with self.assertRaises(remote_host.RemoteHostError):
                remote_host.build_default_remote_transport(port=8899, remote_enabled=True)


if __name__ == "__main__":
    unittest.main()
