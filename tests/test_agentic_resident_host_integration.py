#!/usr/bin/env python3
"""Integration contracts between resident context and the remote host lifecycle."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tooling.remote_host import RemoteHostController, create_remote_server
from tooling.remote_transport_local import LocalRemoteTransport
from tooling.resident_host_context import ResidentHostContext


class _FakeVaultBridge:
    def __init__(self) -> None:
        self.memory_fabric = object()

    def reconcile_once(self):
        return {"status": "SUCCESS", "admitted": 0}

    def status(self):
        return {"checkpoint_present": True, "memory_snapshot_present": True}


class _LifecycleContext:
    def __init__(self) -> None:
        self.start_calls = 0
        self.stop_calls = 0

    def start(self):
        self.start_calls += 1
        return {"running": True}

    def stop(self):
        self.stop_calls += 1
        return {"running": False}


class ResidentHostIntegrationTests(unittest.TestCase):
    def test_foreground_host_starts_context_before_serving_and_stops_it_on_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller = RemoteHostController(
                Path(tmp),
                clock=lambda: 7000.0,
                pid_probe=lambda pid: pid == 654,
            )
            context = _LifecycleContext()
            observed = []

            class Server:
                closed = False

                def serve_forever(inner_self):
                    observed.append(context.start_calls)

                def server_close(inner_self):
                    inner_self.closed = True

            server = Server()
            controller.start_foreground(
                server,
                host_id="home-pc",
                pid=654,
                port=8899,
                remote_enabled=True,
                transport="lan",
                resident_context=context,
            )

            self.assertEqual(observed, [1])
            self.assertEqual(context.start_calls, 1)
            self.assertEqual(context.stop_calls, 1)
            self.assertTrue(server.closed)
            self.assertEqual(controller.status()["status"], "OFFLINE")

    def test_remote_server_factory_uses_exact_resident_runtime_and_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = lambda _request: {"status": "SUCCESS", "reply": "same runtime"}
            transport = LocalRemoteTransport(port=8899, clock=lambda: 1_789_600_000.0)
            context = ResidentHostContext(
                root,
                runtime_adapter=adapter,
                vault_bridge=_FakeVaultBridge(),
                remote_transport=transport,
                reconcile_interval_seconds=60,
            )
            controller = RemoteHostController(root, pid_probe=lambda _pid: True)

            server = create_remote_server(
                ("127.0.0.1", 0),
                state_dir=root,
                resident_context=context,
                host_controller=controller,
            )
            try:
                self.assertIs(server.runtime_bridge.runtime_adapter, context.runtime_adapter)
                self.assertIs(server.remote_transport, context.remote_transport)
                self.assertIs(context.memory_fabric, context.vault_bridge.memory_fabric)
            finally:
                server.server_close()


if __name__ == "__main__":
    unittest.main()
