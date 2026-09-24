#!/usr/bin/env python3
"""Static and dependency-free behavior gates for the universal Remote Companion PWA."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"


class RemoteCompanionPwaTests(unittest.TestCase):
    def test_required_pwa_files_exist(self):
        for relative in (
            "remote-companion.js",
            "remote-companion.css",
            "manifest.webmanifest",
            "service-worker.js",
            "remote-service-worker.js",
        ):
            self.assertTrue((UI / relative).is_file(), relative)

    def test_manifest_is_installable_and_device_neutral(self):
        manifest = json.loads((UI / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["display"], "standalone")
        self.assertIn("remote=1", manifest["start_url"])
        self.assertEqual(manifest["scope"], "/remote/")
        self.assertTrue(manifest.get("name"))
        self.assertTrue(manifest.get("short_name"))
        self.assertNotIn("android", json.dumps(manifest).lower())
        self.assertNotIn("iphone", json.dumps(manifest).lower())

    def test_service_worker_never_serves_cached_api_as_live_state(self):
        source = (UI / "remote-service-worker.js").read_text(encoding="utf-8")
        self.assertIn("/api/", source)
        self.assertRegex(source, r"startsWith\(['\"]\/api\/")
        self.assertRegex(source, r"fetch\(event\.request\)")
        self.assertNotRegex(source, r"cache\.put\([^\n]*\/api\/")

    def test_bootstrap_loads_remote_module_without_rewriting_main_hud(self):
        bootstrap = (UI / "chat-session.js").read_text(encoding="utf-8")
        self.assertIn("remote-companion.js", bootstrap)
        self.assertIn("remote-companion.css", bootstrap)
        self.assertIn("manifest.webmanifest", bootstrap)
        main_source = (UI / "jarvis.js").read_text(encoding="utf-8")
        self.assertIn("/api/status", main_source)

    def test_remote_module_exposes_all_required_states_and_cursor_resume(self):
        source = (UI / "remote-companion.js").read_text(encoding="utf-8")
        for state in (
            "HOST_OFFLINE",
            "HOST_ONLINE",
            "PAIR_DEVICE",
            "DEVICE_TRUSTED",
            "DEVICE_REVOKED",
            "CONNECTING",
            "CONNECTED",
            "RECONNECTING",
            "SESSION_RESUMED",
            "MISSION_RUNNING",
            "MISSION_WAITING",
            "ERROR",
        ):
            self.assertIn(state, source)
        self.assertIn("events?after=", source)
        self.assertIn("X-Jarvis-Device-ID", source)
        self.assertIn("X-Jarvis-Device-Credential", source)
        self.assertNotRegex(
            source,
            r"localStorage\.setItem\([^\n]*(credential|pairing_secret|pairingSecret)",
        )

    def test_companion_css_has_narrow_mobile_layout_and_touch_sized_controls(self):
        source = (UI / "remote-companion.css").read_text(encoding="utf-8")
        self.assertRegex(source, r"@media\s*\(max-width:\s*720px\)")
        self.assertRegex(source, r"min-height:\s*(44|4[5-9]|[5-9][0-9])px")
        self.assertIn("remote-companion-mode", source)

    def test_service_worker_registration_is_remote_scoped(self):
        source = (UI / "remote-companion.js").read_text(encoding="utf-8")
        self.assertIn("scope: '/remote/'", source)
        self.assertIn("'/remote-service-worker.js'", source)
        self.assertIn("'/service-worker.js'", source)
        self.assertIn("root.location.pathname.startsWith('/remote')", source)

    def test_approval_ui_exposes_bound_context_and_consumes_receipts(self):
        source = (UI / "remote-companion.js").read_text(encoding="utf-8")
        for required in (
            "action sha256:",
            "plan sha256:",
            "command.cwd",
            "command.timeout_seconds",
            "action.cwd",
            "action.timeout_seconds",
            "dataset.actionId",
            "dataset.taskId",
            "Ação consumida",
            "Plano consumido",
        ):
            self.assertIn(required, source)

    def test_node_behavior_contract_when_node_is_available(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed in this portable environment")
        completed = subprocess.run(
            [node, str(ROOT / "tests" / "remote_companion_node_test.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
