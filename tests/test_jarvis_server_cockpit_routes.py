"""Tests for new J.A.R.V.I.S. cockpit HTTP routes in tooling/jarvis_server.py."""

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling import jarvis_server


class TestJarvisServerCockpitRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        jarvis_server.load_canonical_skills()
        jarvis_server.load_starred_catalog()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), jarvis_server.JarvisHttpHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def _request(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def test_rf_status_route(self):
        status, _, raw = self._request("GET", "/api/rf/status")
        self.assertEqual(status, 200)
        body = json.loads(raw.decode("utf-8"))
        self.assertIn(body.get("status"), {"ONLINE", "UNAVAILABLE"})
        self.assertIn("sqlite_total_repos", body)
        self.assertGreater(body.get("total_skills_indexed", 0), 0)

    def test_arsenal_stats_and_search_routes(self):
        status, _, raw = self._request("GET", "/api/arsenal/stats")
        self.assertEqual(status, 200)
        stats = json.loads(raw.decode("utf-8"))
        self.assertIn(stats.get("status"), {"SQLITE_READY", "MEMORY_FALLBACK"})
        self.assertIsInstance(stats.get("squads"), dict)
        self.assertIn("Hyperion", stats["squads"])

        s_code, _, s_raw = self._request("GET", "/api/arsenal/search?q=agent&limit=5")
        self.assertEqual(s_code, 200)
        search = json.loads(s_raw.decode("utf-8"))
        self.assertEqual(search.get("limit"), 5)
        self.assertLessEqual(len(search.get("tools", [])), 5)
        self.assertGreaterEqual(search.get("total", 0), len(search.get("tools", [])))

        all_code, _, all_raw = self._request("GET", "/api/arsenal/search?q=&squad=ALL&limit=3")
        self.assertEqual(all_code, 200)
        all_res = json.loads(all_raw.decode("utf-8"))
        self.assertLessEqual(len(all_res.get("tools", [])), 3)

    def test_benchmarks_insane_and_run_routes(self):
        i_code, _, i_raw = self._request("GET", "/api/benchmarks/insane")
        self.assertEqual(i_code, 200)
        insane = json.loads(i_raw.decode("utf-8"))
        self.assertIn("token_compression", insane)
        self.assertIn("micro_latencies", insane)
        self.assertIn("ide_governance", insane)
        self.assertIn("sqlite_arsenal", insane)

        r_code, _, r_raw = self._request("GET", "/api/benchmarks/run")
        self.assertEqual(r_code, 200)
        run_res = json.loads(r_raw.decode("utf-8"))
        self.assertEqual(run_res.get("status"), "SUCCESS")
        metrics = run_res.get("live_metrics", {})
        self.assertGreater(metrics.get("skills_hashed", 0), 0)
        self.assertGreater(metrics.get("manifest_chars_scanned", 0), 0)
        self.assertGreaterEqual(metrics.get("total_measured_time_ms", -1), 0)

    def test_voice_synthesize_validation_success_and_offline_fallback(self):
        bad_code, _, bad_raw = self._request("POST", "/api/voice/synthesize", {"text": "   "})
        self.assertEqual(bad_code, 400)
        self.assertEqual(json.loads(bad_raw.decode("utf-8")).get("error"), "INVALID_TTS_TEXT")

        fake_mp3 = b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x00"
        with mock.patch.object(jarvis_server, "_synthesize_voice_mp3", return_value=fake_mp3):
            ok_code, ok_headers, ok_raw = self._request(
                "POST",
                "/api/voice/synthesize",
                {"text": "Systems nominal.", "profile": "british"},
            )
        self.assertEqual(ok_code, 200)
        self.assertEqual(ok_headers.get("Content-Type"), "audio/mpeg")
        self.assertEqual(ok_raw, fake_mp3)

        with mock.patch.object(jarvis_server, "_synthesize_voice_mp3", side_effect=RuntimeError("offline")):
            err_code, _, err_raw = self._request(
                "POST",
                "/api/voice/synthesize",
                {"text": "Systems nominal.", "profile": "british"},
            )
        self.assertEqual(err_code, 503)
        self.assertEqual(json.loads(err_raw.decode("utf-8")).get("status"), "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
