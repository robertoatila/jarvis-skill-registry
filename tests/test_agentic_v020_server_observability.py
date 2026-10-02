"""v0.2.0 Plan 3 Task 3 contracts for read-only runtime observability APIs."""

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import tooling.jarvis_server as jarvis_server
from tooling.agentic.observability import ReceiptLedger
from tooling.jarvis_server import JarvisHttpHandler, ThreadingJarvisServer


class TestRuntimeObservabilityApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_dir = Path(self.tmp.name) / "state"
        self.original_state_dir = jarvis_server.STATE_DIR
        jarvis_server.STATE_DIR = self.state_dir
        self.addCleanup(setattr, jarvis_server, "STATE_DIR", self.original_state_dir)

        ledger = ReceiptLedger(self.state_dir / "receipts")
        ledger.append({
            "schema_version": "1.0.0",
            "receipt_id": "rcp-context-001",
            "mission_id": "mis-observe-001",
            "task_id": "tsk-001",
            "attempt_id": "att-001",
            "trace_id": "trc-001",
            "created_utc": "2026-09-18T00:00:00+00:00",
            "sources_loaded": ["README.md"],
            "serialized_bytes": 128,
            "token_estimate": None,
        })
        ledger.append({
            "schema_version": "1.0.0",
            "receipt_id": "rcp-exec-001",
            "mission_id": "mis-observe-001",
            "task_id": "tsk-001",
            "attempt_id": "att-001",
            "trace_id": "trc-001",
            "created_utc": "2026-09-18T00:00:01+00:00",
            "adapter": "inference:fixture",
            "invocation_occurred": True,
            "execution_state": "FINISHED",
            "resource_usage": {
                "tokens": {
                    "status": "MEASURED",
                    "value": 8,
                    "unit": "tokens",
                    "method": "fixture",
                },
                "cost_usd": {
                    "status": "UNKNOWN",
                    "value": None,
                    "unit": "USD",
                    "method": None,
                },
            },
            "metadata": {
                "api_key": "super-secret-api-key",
                "authorization": "Bearer super-secret-bearer",
            },
        })
        ledger.append({
            "schema_version": "1.0.0",
            "receipt_id": "rcp-verify-001",
            "mission_id": "mis-observe-001",
            "task_id": "tsk-001",
            "attempt_id": "att-001",
            "trace_id": "trc-001",
            "created_utc": "2026-09-18T00:00:02+00:00",
            "execution_receipt_id": "rcp-exec-001",
            "verification_state": "VERIFIED",
            "evidence_ids": ["ev-001"],
        })

        self.server = ThreadingJarvisServer(("127.0.0.1", 0), JarvisHttpHandler)
        self.server.remote_auth = None
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
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
            return response.status, response.getheader("Content-Type"), body
        finally:
            connection.close()

    def _post_json(self, path, payload):
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
            timeout=2,
        )
        try:
            connection.request(
                "POST",
                path,
                body=json.dumps(payload),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            body = response.read()
            return response.status, response.getheader("Content-Type"), body
        finally:
            connection.close()

    def test_repo_catalog_reports_matches_before_response_limit(self):
        catalog_path = Path(self.tmp.name) / "repos-100k.json"
        catalog_path.write_text(json.dumps({
            "schema_version": "fixture-1",
            "generated_at": "2026-10-02T00:00:00Z",
            "total_repos": 99,
            "repositories": [
                {"name": "agent-one", "description": "agent tooling", "category": "agents", "stars": 20, "topics": ["llm"]},
                {"name": "agent-two", "description": "agent stack", "category": "agents", "stars": 10, "topics": "bad-shape"},
            ],
        }), encoding="utf-8")
        with patch.object(jarvis_server, "REPOS_100K_PATH", catalog_path):
            status, _, body = self._get("/api/repos/100k?search=agent&limit=1")

        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["total_in_index"], 2)
        self.assertEqual(payload["declared_total_in_index"], 99)
        self.assertEqual(payload["total_matched"], 2)
        self.assertEqual(payload["total_returned"], 1)
        self.assertEqual(len(payload["repositories"]), 1)

    def test_key_save_requires_a_supported_matching_provider(self):
        key_path = Path(self.tmp.name) / "api_keys.json"
        with patch.object(jarvis_server, "API_KEYS_PATH", key_path):
            status, _, body = self._post_json(
                "/api/keys/save",
                {"key": "sk-or-v1-test", "provider": "openai"},
            )
            self.assertEqual(status, 400)
            self.assertFalse(key_path.exists())

            status, _, body = self._post_json(
                "/api/keys/save",
                {"key": "sk-or-v1-test", "provider": "openrouter"},
            )

        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["provider"], "openrouter")
        self.assertNotIn("sk-or-v1-test", body.decode("utf-8"))
        self.assertEqual(json.loads(key_path.read_text(encoding="utf-8"))["openrouter"], "sk-or-v1-test")

    def test_lists_only_persisted_runtime_missions_without_demo_data(self):
        status, content_type, body = self._get("/api/runtime/missions")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        payload = json.loads(body)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["missions"],
            [{
                "mission_id": "mis-observe-001",
                "receipt_count": 3,
                "last_event_utc": "2026-09-18T00:00:02+00:00",
            }],
        )
        self.assertNotIn("MISSION-ACTIVE-DAG", body.decode("utf-8"))

    def test_summary_is_truthful_projection_not_synthetic_metrics(self):
        status, content_type, body = self._get(
            "/api/runtime/missions/mis-observe-001/summary"
        )

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        payload = json.loads(body)
        self.assertEqual(payload["mission_id"], "mis-observe-001")
        self.assertEqual(payload["event_count"], 3)
        self.assertEqual(payload["resource_summary"]["attempt_count"], 1)
        self.assertEqual(
            payload["resource_summary"]["tokens"],
            {"status": "MEASURED", "value": 8.0, "unit": "tokens"},
        )
        self.assertEqual(
            payload["resource_summary"]["cost_usd"],
            {"status": "UNKNOWN", "value": None, "unit": "USD"},
        )
        self.assertEqual(payload["verification_summary"]["verification_rate"], 1.0)
        self.assertIn("resources.cost_usd", payload["unknown_fields"])

    def test_timeline_returns_correlated_redacted_structured_events(self):
        status, content_type, body = self._get(
            "/api/runtime/missions/mis-observe-001/timeline"
        )

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json; charset=utf-8")
        payload = json.loads(body)
        self.assertEqual(payload["mission_id"], "mis-observe-001")
        self.assertEqual(
            [event["event_type"] for event in payload["events"]],
            ["CONTEXT", "EXECUTION", "VERIFICATION"],
        )
        serialized = body.decode("utf-8")
        self.assertNotIn("super-secret-api-key", serialized)
        self.assertNotIn("super-secret-bearer", serialized)
        self.assertNotIn("api_key", serialized)
        self.assertNotIn("authorization", serialized)

    def test_unknown_mission_is_deterministic_json_404(self):
        for suffix in ("summary", "timeline"):
            with self.subTest(suffix=suffix):
                status, content_type, body = self._get(
                    f"/api/runtime/missions/mis-missing/{suffix}"
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
                        "mission_id": "mis-missing",
                    },
                )

    def test_invalid_mission_id_is_rejected_without_path_resolution(self):
        invalid_paths = (
            "/api/runtime/missions/%2e%2e/summary",
            "/api/runtime/missions/mis%2Fescape/timeline",
            "/api/runtime/missions/space%20id/summary",
        )
        for path in invalid_paths:
            with self.subTest(path=path):
                status, content_type, body = self._get(path)
                self.assertEqual(status, 400)
                self.assertEqual(
                    content_type,
                    "application/json; charset=utf-8",
                )
                self.assertEqual(
                    json.loads(body),
                    {"error": "INVALID_MISSION_ID"},
                )

    def test_runtime_observability_endpoints_are_get_only(self):
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
            timeout=2,
        )
        try:
            connection.request(
                "POST",
                "/api/runtime/missions/mis-observe-001/summary",
                body=b"{}",
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            response.read()
            self.assertIn(response.status, (404, 405))
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
