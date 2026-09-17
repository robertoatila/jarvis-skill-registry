#!/usr/bin/env python3
"""Deterministic acceptance proof for the remote second-brain architecture."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from tooling.agentic.bidirectional_vault import BidirectionalVaultBridge
from tooling.agentic.chatgpt_capability_manifest import ChatGPTCapabilityManifestBridge
from tooling.agentic.external_capabilities import (
    CapabilityAvailability,
    ExternalCapabilityCatalog,
)
from tooling.agentic.memory import MemoryFabric, MemoryTier
from tooling.remote_devices import RemoteDeviceRegistry
from tooling.remote_http import RemoteJarvisHttpHandler, RemoteJarvisServer
from tooling.remote_protocol import PROTOCOL_VERSION
from tooling.remote_runtime_bridge import RemoteRuntimeBridge
from tooling.remote_sessions import RemoteSessionStore
from tooling.resident_host_context import ResidentHostContext


class FixedClock:
    def __init__(self, value: float = 1_800_000_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class RemoteSecondBrainEndToEndTests(unittest.TestCase):
    def _request(self, base: str, method: str, path: str, body: dict | None = None, headers=None):
        data = None
        request_headers = dict(headers or {})
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            base + path,
            data=data,
            method=method,
            headers=request_headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                raw = response.read()
                payload = json.loads(raw.decode("utf-8")) if raw else None
                return response.status, payload
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            payload = json.loads(raw.decode("utf-8")) if raw else None
            return exc.code, payload

    def test_remote_obsidian_memory_capability_reconnect_and_revocation_are_one_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp) / "vault"
            state_dir = vault_root / "state"
            vault_root.mkdir(parents=True)
            clock = FixedClock()

            # 1. One PC-side MemoryFabric and Vault bridge become the resident context.
            memory = MemoryFabric(storage_dir=state_dir / "memory")
            vault = BidirectionalVaultBridge(
                vault_root,
                state_dir=state_dir,
                memory_fabric=memory,
                clock=clock,
            )
            runtime_memory_ids: list[int] = []

            def runtime_adapter(request: dict) -> dict:
                runtime_memory_ids.append(id(memory))
                selected, receipt = memory.query(
                    request["text"],
                    tiers=[MemoryTier.SEMANTIC],
                    max_items=10,
                    min_confidence=0.0,
                    token_budget=8_000,
                )
                reply = " | ".join(item.content for item in selected)
                return {
                    "status": "COMPLETED",
                    "mission_id": "mission-e2e",
                    "reply": reply,
                    "receipt": receipt.to_dict(),
                }

            context = ResidentHostContext(
                vault_root,
                runtime_adapter=runtime_adapter,
                vault_bridge=vault,
                state_dir=state_dir,
                reconcile_interval_seconds=3600,
            )
            self.assertIs(context.memory_fabric, memory)
            self.assertIs(context.vault_bridge.memory_fabric, memory)

            # 2-3. Pair phone-1 and open a remote session through the real HTTP boundary.
            ids = iter(["offer-1", "phone-1"])
            devices = RemoteDeviceRegistry(
                state_dir / "devices",
                clock=clock,
                id_factory=lambda: next(ids),
                pairing_ttl_seconds=120,
            )
            session_ids = iter(["session-e2e"])
            sessions = RemoteSessionStore(
                state_dir / "sessions",
                clock=clock,
                id_factory=lambda: next(session_ids),
                device_validator=devices.is_active,
            )
            runtime_bridge = RemoteRuntimeBridge(
                sessions,
                runtime_adapter=context.runtime_adapter,
            )
            server = RemoteJarvisServer(
                ("127.0.0.1", 0),
                RemoteJarvisHttpHandler,
                session_store=sessions,
                runtime_bridge=runtime_bridge,
                host_status_provider=lambda: {
                    "schema_version": 1,
                    "host_id": "home-pc-e2e",
                    "status": "ONLINE",
                    "remote_enabled": True,
                    "transport": "local",
                },
                device_registry=devices,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"

            credential = "phone-credential-" + "x" * 48
            try:
                status, offer = self._request(
                    base,
                    "POST",
                    "/api/remote/v1/pairing/offers",
                    {"label_hint": "phone-1"},
                )
                self.assertEqual(status, 201)

                status, paired = self._request(
                    base,
                    "POST",
                    "/api/remote/v1/pairing/complete",
                    {
                        "offer_id": offer["offer_id"],
                        "pairing_secret": offer["pairing_secret"],
                        "credential": credential,
                        "label": "phone-1",
                    },
                )
                self.assertEqual(status, 201)
                self.assertEqual(paired["device_id"], "phone-1")
                self.assertTrue(devices.authenticate("phone-1", {"credential": credential}))

                status, session = self._request(
                    base,
                    "POST",
                    "/api/remote/v1/sessions",
                    {"device_id": "phone-1"},
                )
                self.assertEqual(status, 201)
                self.assertEqual(session["session_id"], "session-e2e")

                # 4-6. Human Vault evidence is admitted with source provenance.
                note = vault_root / "projects" / "atlas.md"
                note.parent.mkdir(parents=True)
                note.write_text(
                    "# Project Atlas\nDatabase: PostgreSQL.\n",
                    encoding="utf-8",
                )
                first_reconcile = context.reconcile_once()
                self.assertEqual(first_reconcile["status"], "SUCCESS")
                self.assertEqual(first_reconcile["human_events"], 1)
                self.assertEqual(first_reconcile["admitted"], 1)

                selected, _ = memory.query(
                    "Project Atlas PostgreSQL",
                    tiers=[MemoryTier.SEMANTIC],
                    min_confidence=0.0,
                )
                self.assertEqual(len(selected), 1)
                admitted = selected[0]
                self.assertEqual(admitted.metadata["source_path"], "projects/atlas.md")
                self.assertTrue(admitted.metadata["source_hash"])
                self.assertTrue(admitted.metadata["source_event_id"])

                # 7-8. The remote prompt is served by that exact PC-side memory/context.
                envelope = {
                    "protocol": PROTOCOL_VERSION,
                    "session_id": "session-e2e",
                    "device_id": "phone-1",
                    "request_id": "request-memory-1",
                    "kind": "message",
                    "payload": {"text": "Project Atlas PostgreSQL"},
                }
                status, accepted = self._request(
                    base,
                    "POST",
                    "/api/remote/v1/sessions/session-e2e/messages",
                    envelope,
                )
                self.assertEqual(status, 202)
                self.assertEqual(accepted["mission_id"], "mission-e2e")
                self.assertEqual(runtime_memory_ids, [id(context.memory_fabric)])

                status, event_page = self._request(
                    base,
                    "GET",
                    "/api/remote/v1/sessions/session-e2e/events?after=0&limit=50",
                    headers={"X-Jarvis-Device-ID": "phone-1"},
                )
                self.assertEqual(status, 200)
                assistant_events = [
                    event for event in event_page["events"]
                    if event["kind"] == "assistant_message"
                ]
                self.assertEqual(len(assistant_events), 1)
                self.assertIn("PostgreSQL", assistant_events[0]["payload"]["text"])
                cursor = assistant_events[0]["seq"]

                # 9-10. Managed runtime projection is not re-ingested as human memory.
                runtime_note = vault_root / "JARVIS" / "Second Brain Runtime.md"
                self.assertTrue(runtime_note.exists())
                self.assertIn(
                    "<!-- jarvis:projection:start -->",
                    runtime_note.read_text(encoding="utf-8"),
                )
                before_ids = {item.memory_id for item in selected}
                second_reconcile = context.reconcile_once()
                self.assertEqual(second_reconcile["status"], "SUCCESS")
                self.assertEqual(second_reconcile["projection_events_suppressed"], 1)
                self.assertEqual(second_reconcile["human_events"], 0)
                self.assertEqual(second_reconcile["admitted"], 0)
                selected_after_projection, _ = memory.query(
                    "Project Atlas PostgreSQL",
                    tiers=[MemoryTier.SEMANTIC],
                    min_confidence=0.0,
                )
                self.assertEqual(
                    {item.memory_id for item in selected_after_projection},
                    before_ids,
                )

                # 11-13. ChatGPT inventory is remembered, but executable state
                # requires fresh delegated-provider verification.
                catalog = ExternalCapabilityCatalog(state_dir, clock=clock)
                manifest_bridge = ChatGPTCapabilityManifestBridge(
                    catalog,
                    clock=clock,
                )
                observed_at = datetime.fromtimestamp(
                    clock(),
                    timezone.utc,
                ).isoformat()
                manifest_result = manifest_bridge.import_manifest(
                    {
                        "schema_version": 1,
                        "source_id": "chatgpt-browser",
                        "observed_at": observed_at,
                        "source_provenance": "explicit-e2e-manifest",
                        "capabilities": [
                            {
                                "capability_id": "skill-x",
                                "name": "Skill X",
                                "provider": "chatgpt",
                                "kind": "skill",
                                "capabilities": ["example"],
                                "availability": "KNOWN",
                            }
                        ],
                    }
                )
                self.assertEqual(manifest_result["inserted"], 1)
                remembered = catalog.get("chatgpt-browser", "skill-x")
                self.assertIn(
                    remembered.availability_state,
                    {
                        CapabilityAvailability.KNOWN,
                        CapabilityAvailability.UNVERIFIED,
                    },
                )
                self.assertNotEqual(
                    remembered.availability_state,
                    CapabilityAvailability.AVAILABLE_LOCAL,
                )

                with self.assertRaisesRegex(ValueError, "verified_at"):
                    catalog.mark_availability(
                        "chatgpt-browser",
                        "skill-x",
                        CapabilityAvailability.AVAILABLE_DELEGATED,
                        verified_at=None,
                    )
                catalog.mark_availability(
                    "chatgpt-browser",
                    "skill-x",
                    CapabilityAvailability.AVAILABLE_DELEGATED,
                    verified_at=observed_at,
                )
                delegated = catalog.get("chatgpt-browser", "skill-x")
                self.assertEqual(
                    delegated.availability_state,
                    CapabilityAvailability.AVAILABLE_DELEGATED,
                )
                self.assertEqual(delegated.invocation_mode, "delegated")

                # 14-16. Client disappears; PC-side mission/events continue, then
                # reconnect resumes strictly after the last cursor.
                mission_event = sessions.append_event(
                    "session-e2e",
                    "mission_progress",
                    {"status": "RUNNING"},
                    mission_id="mission-e2e",
                )
                self.assertGreater(mission_event["seq"], cursor)

                status, replay = self._request(
                    base,
                    "GET",
                    f"/api/remote/v1/sessions/session-e2e/events?after={cursor}&limit=50",
                    headers={"X-Jarvis-Device-ID": "phone-1"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(
                    [event["seq"] for event in replay["events"]],
                    [mission_event["seq"]],
                )
                self.assertEqual(replay["events"][0]["kind"], "mission_progress")

                # 17. Revocation invalidates the device and blocks its session.
                devices.revoke("phone-1")
                self.assertFalse(devices.authenticate("phone-1", {"credential": credential}))
                status, rejected = self._request(
                    base,
                    "GET",
                    "/api/remote/v1/sessions/session-e2e",
                    headers={"X-Jarvis-Device-ID": "phone-1"},
                )
                self.assertEqual(status, 403)
                self.assertEqual(rejected["reason"], "REMOTE_DEVICE_NOT_AUTHORIZED")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
