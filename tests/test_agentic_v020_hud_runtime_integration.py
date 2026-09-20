"""Plan 3 Task 7: served runtime-observability + HUD integration fixture."""

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

import tooling.jarvis_server as jarvis_server
from tooling.agentic.observability import ReceiptLedger
from tooling.jarvis_server import JarvisHttpHandler, ThreadingJarvisServer


class HudRuntimeIntegrationTests(unittest.TestCase):
    MISSION_ID = "mis-hud-runtime-001"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.original_state_dir = jarvis_server.STATE_DIR
        jarvis_server.STATE_DIR = Path(self.tmp.name) / "state"
        self.addCleanup(setattr, jarvis_server, "STATE_DIR", self.original_state_dir)

        ledger = ReceiptLedger(jarvis_server.STATE_DIR / "receipts")
        for receipt in (
            {
                "schema_version": "1.0.0",
                "receipt_id": "rcp-hud-context",
                "mission_id": self.MISSION_ID,
                "task_id": "tsk-hud",
                "attempt_id": "att-hud",
                "trace_id": "trc-hud",
                "created_utc": "2026-09-18T01:00:00+00:00",
                "sources_loaded": ["README.md", "ui/index.html"],
                "serialized_bytes": 512,
                "token_estimate": None,
            },
            {
                "schema_version": "1.0.0",
                "receipt_id": "rcp-hud-execution",
                "mission_id": self.MISSION_ID,
                "task_id": "tsk-hud",
                "attempt_id": "att-hud",
                "trace_id": "trc-hud",
                "created_utc": "2026-09-18T01:00:01+00:00",
                "adapter": "local.read_file",
                "invocation_occurred": True,
                "execution_state": "FINISHED",
                "resource_usage": {
                    "tokens": {
                        "status": "MEASURED",
                        "value": 0,
                        "unit": "tokens",
                        "method": "fixture",
                    },
                    "cost_usd": {
                        "status": "UNKNOWN",
                        "value": None,
                        "unit": "USD",
                        "method": None,
                    },
                    "latency_ms": {
                        "status": "NOT_APPLICABLE",
                        "value": None,
                        "unit": "ms",
                        "method": None,
                    },
                },
            },
            {
                "schema_version": "1.0.0",
                "receipt_id": "rcp-hud-verification",
                "mission_id": self.MISSION_ID,
                "task_id": "tsk-hud",
                "attempt_id": "att-hud",
                "trace_id": "trc-hud",
                "created_utc": "2026-09-18T01:00:02+00:00",
                "execution_receipt_id": "rcp-hud-execution",
                "verification_state": "VERIFIED",
                "evidence_ids": ["ev-hud-001"],
            },
        ):
            ledger.append(receipt)

        self.server = ThreadingJarvisServer(
            ("127.0.0.1", 0),
            JarvisHttpHandler,
        )
        self.server.remote_auth = None
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()
        self.addCleanup(self._shutdown_server)

    def _shutdown_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _get(self, path):
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
            timeout=2,
        )
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read()
            return (
                response.status,
                response.getheader("Content-Type"),
                body,
            )
        finally:
            connection.close()

    def test_runtime_summary_and_timeline_flow_over_actual_http_server(self):
        summary_status, summary_type, summary_body = self._get(
            f"/api/runtime/missions/{self.MISSION_ID}/summary"
        )
        timeline_status, timeline_type, timeline_body = self._get(
            f"/api/runtime/missions/{self.MISSION_ID}/timeline"
        )

        self.assertEqual(summary_status, 200)
        self.assertEqual(timeline_status, 200)
        self.assertEqual(summary_type, "application/json; charset=utf-8")
        self.assertEqual(timeline_type, "application/json; charset=utf-8")

        summary = json.loads(summary_body)
        timeline = json.loads(timeline_body)

        self.assertEqual(summary["mission_id"], self.MISSION_ID)
        self.assertEqual(summary["event_count"], 3)
        self.assertEqual(
            summary["resource_summary"]["tokens"],
            {"status": "MEASURED", "value": 0.0, "unit": "tokens"},
        )
        self.assertEqual(
            summary["resource_summary"]["cost_usd"],
            {"status": "UNKNOWN", "value": None, "unit": "USD"},
        )
        self.assertEqual(
            summary["resource_summary"]["latency_ms"],
            {"status": "NOT_APPLICABLE", "value": None, "unit": "ms"},
        )
        self.assertIn("resources.cost_usd", summary["unknown_fields"])

        self.assertEqual(timeline["mission_id"], self.MISSION_ID)
        self.assertEqual(
            [event["event_type"] for event in timeline["events"]],
            ["CONTEXT", "EXECUTION", "VERIFICATION"],
        )
        for event in timeline["events"]:
            self.assertEqual(event["task_id"], "tsk-hud")
            self.assertEqual(event["attempt_id"], "att-hud")
            self.assertEqual(event["trace_id"], "trc-hud")

        self.assertEqual(
            timeline["events"][-1]["data"]["evidence_ids"],
            ["ev-hud-001"],
        )

    def test_mission_listing_exposes_only_persisted_fixture(self):
        status, content_type, body = self._get("/api/runtime/missions")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        payload = json.loads(body)

        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["missions"][0]["mission_id"], self.MISSION_ID)
        self.assertEqual(payload["missions"][0]["receipt_count"], 3)
        self.assertEqual(
            payload["missions"][0]["last_event_utc"],
            "2026-09-18T01:00:02+00:00",
        )

    def test_cockpit_and_existing_hud_assets_are_served(self):
        cases = (
            ("/", "text/html", b'id="operationalCockpit"'),
            (
                "/runtime-observability.js",
                "application/javascript",
                b"JarvisRuntimeObservability",
            ),
            (
                "/remote-companion.css",
                "text/css",
                b".remote-companion-app",
            ),
            (
                "/remote-companion.js",
                "application/javascript",
                b"Universal Remote Companion",
            ),
            (
                "/manifest.webmanifest",
                "application/manifest+json",
                b"J.A.R.V.I.S. Remote Companion",
            ),
            (
                "/service-worker.js",
                "application/javascript",
                b"jarvis-mark-liv-shell-v2",
            ),
            (
                "/mark-liv.css",
                "text/css",
                b".mark-liv-cockpit",
            ),
            (
                "/mark-liv-cockpit.js",
                "application/javascript",
                b"Holomat Quantum Cockpit",
            ),
            (
                "/assets/operational-cockpit.js",
                "application/javascript",
                b"JarvisOperationalCockpit",
            ),
            (
                "/assets/design-system/index.html",
                "text/html",
                b"Operational Cockpit",
            ),
            (
                "/assets/design-system/components.css",
                "text/css",
                b".jv-cockpit",
            ),
            (
                "/jarvis.js",
                "application/javascript",
                b"operationalCockpitController",
            ),
        )

        for path, expected_type, marker in cases:
            with self.subTest(path=path):
                status, content_type, body = self._get(path)
                self.assertEqual(status, 200)
                self.assertTrue(
                    content_type.startswith(expected_type),
                    (path, content_type),
                )
                self.assertIn(marker, body)

    def test_mark_liv_hardware_telemetry_exposes_threads_and_sensor_availability(self):
        status, content_type, body = self._get("/api/system/telemetry")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        payload = json.loads(body)

        self.assertIsInstance(payload["runtime_threads_active"], int)
        self.assertGreaterEqual(payload["runtime_threads_active"], 1)

        self.assertIn("temperature_c", payload)
        self.assertIn("temperature_status", payload)
        if payload["temperature_c"] is None:
            self.assertTrue(payload["temperature_status"].startswith("UNAVAILABLE"))

        self.assertIn("power_watts", payload)
        self.assertIn("power_status", payload)
        if payload["power_watts"] is None:
            self.assertTrue(payload["power_status"].startswith("UNAVAILABLE"))

    def test_unknown_mission_stays_deterministic_404(self):
        for suffix in ("summary", "timeline"):
            with self.subTest(suffix=suffix):
                status, content_type, body = self._get(
                    f"/api/runtime/missions/mis-not-present/{suffix}"
                )
                self.assertEqual(status, 404)
                self.assertEqual(
                    content_type,
                    "application/json; charset=utf-8",
                )
                self.assertEqual(
                    json.loads(body),
                    {
                        "error": "MISSION_NOT_FOUND",
                        "mission_id": "mis-not-present",
                    },
                )


if __name__ == "__main__":
    unittest.main()
