"""v0.2.0 Plan 3 Task 3 contracts for read-only runtime observability HTTP APIs."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import tooling.jarvis_server as jarvis_server
from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import Mission, MissionStatus
from tooling.agentic.observability import ReceiptLedger
from tooling.agentic.state_store import AuthoritativeStateStore


MISSION_ID = "mis-api-observability"
CREATED = "2026-09-17T23:55:00+00:00"


class TestRuntimeObservabilityApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / "ui").mkdir(parents=True, exist_ok=True)

        self._old_root = jarvis_server.REGISTRY_ROOT
        self._old_ui = jarvis_server.UI_DIR
        self._old_state = jarvis_server.STATE_DIR
        jarvis_server.REGISTRY_ROOT = self.root
        jarvis_server.UI_DIR = self.root / "ui"
        jarvis_server.STATE_DIR = self.root / "state"
        self.addCleanup(self._restore_globals)

        self.httpd = jarvis_server.ThreadingJarvisServer(
            ("127.0.0.1", 0),
            jarvis_server.JarvisHttpHandler,
        )
        self.httpd.remote_auth = None
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop_server)

        host, port = self.httpd.server_address[:2]
        self.base_url = f"http://{host}:{port}"

    def _restore_globals(self):
        jarvis_server.REGISTRY_ROOT = self._old_root
        jarvis_server.UI_DIR = self._old_ui
        jarvis_server.STATE_DIR = self._old_state

    def _stop_server(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=3)

    def _config(self):
        return JarvisRuntimeConfig(registry_root=self.root)

    def _seed_mission(self, mission_id=MISSION_ID, *, status=MissionStatus.SUCCEEDED):
        mission = Mission(
            mission_id=mission_id,
            goal="Observable runtime mission",
            dag=ExecutionDAG(),
            status=status,
        )
        AuthoritativeStateStore(config=self._config()).save_mission(mission)
        return mission

    def _seed_receipts(self, mission_id=MISSION_ID):
        ledger = ReceiptLedger(self._config().receipts_dir)
        ledger.append({
            "schema_version": "1.0.0",
            "receipt_id": "rcp-api-exec",
            "mission_id": mission_id,
            "task_id": "tsk-api",
            "attempt_id": "att-api",
            "trace_id": "trc-api",
            "created_utc": CREATED,
            "adapter": "local.read_file",
            "invocation_occurred": True,
            "execution_state": "FINISHED",
            "resource_usage": {
                "tokens": {
                    "status": "NOT_APPLICABLE",
                    "value": None,
                    "unit": "tokens",
                    "method": "no_model_invocation",
                },
                "cost_usd": {
                    "status": "NOT_APPLICABLE",
                    "value": None,
                    "unit": "USD",
                    "method": "no_model_invocation",
                },
            },
            "metadata": {
                "authorization": "Bearer never-expose-this",
                "api_key": "sk-never-expose-this",
            },
        })
        ledger.append({
            "schema_version": "1.0.0",
            "receipt_id": "rcp-api-ver",
            "mission_id": mission_id,
            "task_id": "tsk-api",
            "attempt_id": "att-api",
            "trace_id": "trc-api",
            "created_utc": "2026-09-17T23:55:01+00:00",
            "execution_receipt_id": "rcp-api-exec",
            "verification_state": "VERIFIED",
            "evidence_ids": ["ev-api"],
        })

    def _get(self, path):
        request = urllib.request.Request(
            self.base_url + path,
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            response = urllib.request.urlopen(request, timeout=5)
            body = response.read().decode("utf-8")
            return response.status, response.headers, json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            return exc.code, exc.headers, json.loads(body)

    def test_empty_runtime_missions_endpoint_returns_no_demo_data(self):
        status, headers, payload = self._get("/api/runtime/missions")

        self.assertEqual(status, 200)
        self.assertTrue(headers.get_content_type() == "application/json")
        self.assertEqual(payload, {"missions": [], "count": 0})

    def test_runtime_missions_lists_authoritative_and_receipt_backed_missions_deterministically(self):
        self._seed_mission()
        self._seed_receipts()
        receipt_only = "mis-receipt-only"
        ledger = ReceiptLedger(self._config().receipts_dir)
        ledger.append({
            "schema_version": "1.0.0",
            "receipt_id": "rcp-receipt-only",
            "mission_id": receipt_only,
            "task_id": None,
            "attempt_id": None,
            "trace_id": None,
            "created_utc": CREATED,
            "decision_type": "model_routing",
            "selected_candidate": "local-fixture",
        })

        status, _, payload = self._get("/api/runtime/missions")

        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(
            [item["mission_id"] for item in payload["missions"]],
            [MISSION_ID, receipt_only],
        )
        primary = payload["missions"][0]
        self.assertEqual(primary["status"], "SUCCEEDED")
        self.assertEqual(primary["receipt_count"], 2)
        self.assertTrue(primary["authoritative_state"])
        secondary = payload["missions"][1]
        self.assertIsNone(secondary["status"])
        self.assertEqual(secondary["receipt_count"], 1)
        self.assertFalse(secondary["authoritative_state"])

    def test_summary_combines_authoritative_state_and_truthful_receipt_metrics(self):
        self._seed_mission()
        self._seed_receipts()

        status, headers, payload = self._get(
            f"/api/runtime/missions/{MISSION_ID}/summary"
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers.get_content_type(), "application/json")
        self.assertEqual(payload["mission_id"], MISSION_ID)
        self.assertEqual(payload["status"], "SUCCEEDED")
        self.assertTrue(payload["authoritative_state"])
        self.assertEqual(payload["receipt_count"], 2)
        self.assertEqual(payload["resource_summary"]["attempt_count"], 1)
        self.assertEqual(
            payload["resource_summary"]["tokens"]["status"],
            "NOT_APPLICABLE",
        )
        self.assertEqual(payload["verification_summary"]["count"], 1)
        self.assertEqual(payload["verification_summary"]["verification_rate"], 1.0)
        self.assertEqual(
            payload["verification_summary"]["verification_rate_status"],
            "MEASURED",
        )

    def test_timeline_endpoint_returns_structured_events_and_never_credentials(self):
        self._seed_mission()
        self._seed_receipts()

        status, headers, payload = self._get(
            f"/api/runtime/missions/{MISSION_ID}/timeline"
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers.get_content_type(), "application/json")
        self.assertEqual(payload["mission_id"], MISSION_ID)
        self.assertEqual(
            [event["event_type"] for event in payload["events"]],
            ["EXECUTION", "VERIFICATION"],
        )
        encoded = json.dumps(payload, sort_keys=True)
        self.assertNotIn("never-expose-this", encoded)
        self.assertNotIn("sk-never-expose-this", encoded)
        self.assertNotIn("authorization", encoded.casefold())
        self.assertNotIn("api_key", encoded.casefold())

    def test_receipt_only_mission_has_no_invented_authoritative_status(self):
        receipt_only = "mis-receipt-only"
        ledger = ReceiptLedger(self._config().receipts_dir)
        ledger.append({
            "schema_version": "1.0.0",
            "receipt_id": "rcp-only-context",
            "mission_id": receipt_only,
            "task_id": "tsk-only",
            "attempt_id": None,
            "trace_id": None,
            "created_utc": CREATED,
            "sources_loaded": ["fixture"],
            "serialized_bytes": 10,
            "token_estimate": None,
        })

        status, _, summary = self._get(
            f"/api/runtime/missions/{receipt_only}/summary"
        )

        self.assertEqual(status, 200)
        self.assertEqual(summary["mission_id"], receipt_only)
        self.assertIsNone(summary["status"])
        self.assertFalse(summary["authoritative_state"])
        self.assertEqual(summary["receipt_count"], 1)
        self.assertEqual(
            summary["verification_summary"]["verification_rate_status"],
            "NO_DATA",
        )

    def test_unknown_mission_is_deterministic_json_404(self):
        for suffix in ("summary", "timeline"):
            with self.subTest(suffix=suffix):
                status, headers, payload = self._get(
                    f"/api/runtime/missions/mis-does-not-exist/{suffix}"
                )
                self.assertEqual(status, 404)
                self.assertEqual(headers.get_content_type(), "application/json")
                self.assertEqual(
                    payload,
                    {
                        "error": "MISSION_NOT_FOUND",
                        "mission_id": "mis-does-not-exist",
                    },
                )

    def test_invalid_mission_ids_are_rejected_before_any_state_lookup(self):
        bad_paths = (
            "/api/runtime/missions/%2e%2e/summary",
            "/api/runtime/missions/%2fetc%2fpasswd/timeline",
            "/api/runtime/missions/bad%20id/summary",
            "/api/runtime/missions/%5cwindows%5csystem32/timeline",
        )
        for path in bad_paths:
            with self.subTest(path=path):
                status, headers, payload = self._get(path)
                self.assertEqual(status, 400)
                self.assertEqual(headers.get_content_type(), "application/json")
                self.assertEqual(payload["error"], "INVALID_MISSION_ID")


if __name__ == "__main__":
    unittest.main()
