#!/usr/bin/env python3
"""Per-device identity, one-time pairing and revocation contracts."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from tooling.remote_devices import RemoteDeviceError, RemoteDeviceRegistry
from tooling.remote_http import RemoteJarvisHttpHandler, RemoteJarvisServer
from tooling.remote_runtime_bridge import RemoteRuntimeBridge
from tooling.remote_sessions import RemoteSessionStore


class MutableClock:
    def __init__(self, value: float = 1_800_000_000.0):
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class RemoteDeviceRegistryTests(unittest.TestCase):
    def _registry(self, root: Path, clock: MutableClock, ids=None) -> RemoteDeviceRegistry:
        values = iter(ids or ["offer-1", "device-1", "offer-2", "device-2"])
        return RemoteDeviceRegistry(
            root,
            clock=clock,
            id_factory=lambda: next(values),
            pairing_ttl_seconds=120,
        )

    def test_pairing_offer_is_short_lived_one_time_and_never_persists_raw_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = MutableClock()
            registry = self._registry(root, clock)

            offer = registry.create_pairing_offer(label_hint="Roberto phone")
            self.assertEqual(offer["offer_id"], "offer-1")
            self.assertIn("pairing_secret", offer)
            self.assertGreater(offer["expires_at"], offer["created_at"])

            credential = "device-credential-" + "a" * 48
            device = registry.complete_pairing(
                offer["offer_id"],
                {
                    "pairing_secret": offer["pairing_secret"],
                    "credential": credential,
                    "label": "Roberto phone",
                },
            )
            self.assertEqual(device.device_id, "device-1")
            self.assertEqual(device.status, "ACTIVE")
            self.assertNotEqual(device.credential_fingerprint, credential)

            persisted = (root / "remote_devices.json").read_text(encoding="utf-8")
            self.assertNotIn(offer["pairing_secret"], persisted)
            self.assertNotIn(credential, persisted)
            self.assertIn(device.credential_fingerprint, persisted)

            with self.assertRaisesRegex(RemoteDeviceError, "used|consumed|pairing"):
                registry.complete_pairing(
                    offer["offer_id"],
                    {
                        "pairing_secret": offer["pairing_secret"],
                        "credential": "b" * 64,
                        "label": "Replay",
                    },
                )

    def test_expired_pairing_offer_cannot_create_device(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = MutableClock()
            registry = self._registry(root, clock)
            offer = registry.create_pairing_offer(label_hint="Tablet")
            clock.advance(121)

            with self.assertRaisesRegex(RemoteDeviceError, "expired"):
                registry.complete_pairing(
                    offer["offer_id"],
                    {
                        "pairing_secret": offer["pairing_secret"],
                        "credential": "c" * 64,
                        "label": "Tablet",
                    },
                )
            self.assertEqual(registry.list_devices(), [])

    def test_each_device_has_independent_credential_and_revocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = MutableClock()
            registry = self._registry(root, clock)

            first_offer = registry.create_pairing_offer(label_hint="Phone")
            first_credential = "p" * 64
            first = registry.complete_pairing(
                first_offer["offer_id"],
                {
                    "pairing_secret": first_offer["pairing_secret"],
                    "credential": first_credential,
                    "label": "Phone",
                },
            )
            second_offer = registry.create_pairing_offer(label_hint="Tablet")
            second_credential = "t" * 64
            second = registry.complete_pairing(
                second_offer["offer_id"],
                {
                    "pairing_secret": second_offer["pairing_secret"],
                    "credential": second_credential,
                    "label": "Tablet",
                },
            )

            self.assertTrue(registry.authenticate(first.device_id, {"credential": first_credential}))
            self.assertTrue(registry.authenticate(second.device_id, {"credential": second_credential}))
            self.assertFalse(registry.authenticate(first.device_id, {"credential": second_credential}))

            revoked = registry.revoke(first.device_id)
            self.assertEqual(revoked.status, "REVOKED")
            self.assertFalse(registry.authenticate(first.device_id, {"credential": first_credential}))
            self.assertTrue(registry.authenticate(second.device_id, {"credential": second_credential}))
            self.assertTrue(registry.is_active(second.device_id))

    def test_device_authentication_and_revocation_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = MutableClock()
            registry = self._registry(root, clock, ids=["offer-a", "device-a"])
            offer = registry.create_pairing_offer(label_hint="Laptop")
            credential = "l" * 64
            device = registry.complete_pairing(
                offer["offer_id"],
                {
                    "pairing_secret": offer["pairing_secret"],
                    "credential": credential,
                    "label": "Laptop",
                },
            )
            self.assertTrue(registry.authenticate(device.device_id, {"credential": credential}))

            reopened = RemoteDeviceRegistry(root, clock=clock)
            loaded = reopened.get(device.device_id)
            self.assertIsNotNone(loaded)
            self.assertIsNotNone(loaded.last_seen_at)
            self.assertTrue(reopened.authenticate(device.device_id, {"credential": credential}))
            reopened.revoke(device.device_id)

            reopened_again = RemoteDeviceRegistry(root, clock=clock)
            self.assertEqual(reopened_again.get(device.device_id).status, "REVOKED")
            self.assertFalse(reopened_again.authenticate(device.device_id, {"credential": credential}))

    def test_remote_session_store_can_reject_unknown_or_revoked_device_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = MutableClock()
            registry = self._registry(root, clock, ids=["offer-1", "device-1"])
            offer = registry.create_pairing_offer()
            credential = "s" * 64
            device = registry.complete_pairing(
                offer["offer_id"],
                {
                    "pairing_secret": offer["pairing_secret"],
                    "credential": credential,
                    "label": "Phone",
                },
            )
            store = RemoteSessionStore(root / "sessions", device_validator=registry.is_active)
            session = store.create_session(device.device_id)
            self.assertEqual(session["device_id"], device.device_id)

            registry.revoke(device.device_id)
            with self.assertRaisesRegex(Exception, "device"):
                store.create_session(device.device_id)
            with self.assertRaisesRegex(Exception, "device"):
                store.create_session("unknown-device")


class RemoteDeviceHttpIntegrationTests(unittest.TestCase):
    def _post(self, base: str, path: str, body: dict, headers=None):
        encoded = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            base + path,
            data=encoded,
            method="POST",
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def _get(self, base: str, path: str, headers=None):
        request = urllib.request.Request(base + path, headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_pairing_http_flow_binds_sessions_and_revocation_blocks_existing_device(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clock = MutableClock()
            ids = iter(["offer-http", "device-http", "session-http"])
            registry = RemoteDeviceRegistry(
                root / "devices",
                clock=clock,
                id_factory=lambda: next(ids),
                pairing_ttl_seconds=120,
            )
            store = RemoteSessionStore(
                root / "sessions",
                clock=clock,
                id_factory=lambda: next(ids),
                device_validator=registry.is_active,
            )
            bridge = RemoteRuntimeBridge(
                store,
                runtime_adapter=lambda request: {"status": "UNVERIFIED", "reply": request["text"]},
            )
            server = RemoteJarvisServer(
                ("127.0.0.1", 0),
                RemoteJarvisHttpHandler,
                session_store=store,
                runtime_bridge=bridge,
                host_status_provider=lambda: {"status": "ONLINE"},
                device_registry=registry,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                status, offer = self._post(
                    base,
                    "/api/remote/v1/pairing/offers",
                    {"label_hint": "Phone"},
                )
                self.assertEqual(status, 201)
                credential = "h" * 64
                status, paired = self._post(
                    base,
                    "/api/remote/v1/pairing/complete",
                    {
                        "offer_id": offer["offer_id"],
                        "pairing_secret": offer["pairing_secret"],
                        "credential": credential,
                        "label": "Phone",
                    },
                )
                self.assertEqual(status, 201)
                self.assertEqual(paired["device_id"], "device-http")
                self.assertNotIn("credential", paired)

                device_headers = {
                    "X-Jarvis-Device-ID": paired["device_id"],
                    "X-Jarvis-Device-Credential": credential,
                }
                status, session = self._post(
                    base,
                    "/api/remote/v1/sessions",
                    {"device_id": paired["device_id"]},
                    headers=device_headers,
                )
                self.assertEqual(status, 201)
                self.assertEqual(session["device_id"], paired["device_id"])

                registry.revoke(paired["device_id"])
                status, body = self._get(
                    base,
                    f"/api/remote/v1/sessions/{session['session_id']}",
                    headers=device_headers,
                )
                self.assertEqual(status, 403)
                self.assertIn("DEVICE", body.get("reason", ""))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
