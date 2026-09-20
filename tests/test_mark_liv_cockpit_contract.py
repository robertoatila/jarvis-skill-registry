#!/usr/bin/env python3
"""Static contracts for the Mark-LIV Holomat Quantum Cockpit."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"


class TestMarkLivCockpitContract(unittest.TestCase):
    def test_shell_mounts_mark_liv_assets_after_existing_runtime_scripts(self):
        html = (UI / "index.html").read_text(encoding="utf-8")
        self.assertIn("J.A.R.V.I.S. Mark-LIV // Holomat Quantum Cockpit", html)
        self.assertIn('href="mark-liv.css"', html)
        self.assertIn('src="mark-liv-cockpit.js"', html)
        self.assertLess(html.index('src="jarvis.js"'), html.index('src="mark-liv-cockpit.js"'))

    def test_cockpit_has_four_phases_and_six_runtime_modules(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        for phase in ("decompose", "skills", "execute", "synthesis"):
            self.assertIn(f'data-phase="{phase}"', source)
        for module in ("terminal", "dag", "skills", "radar", "memory", "telemetry"):
            self.assertIn(f"id: '{module}'", source)

    def test_cockpit_reads_existing_truthful_runtime_endpoints(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        expected = (
            "/api/status",
            "/api/system/telemetry",
            "/api/keys/status",
            "/api/agentic/telemetry",
            "/api/memory",
            "/api/agentic/dag/active",
        )
        for endpoint in expected:
            self.assertIn(endpoint, source)
        self.assertIn("canonical_active_skills_count", source)
        self.assertIn("total_starred_catalog_count", source)
        self.assertNotIn("319 SKILLS", source)
        self.assertNotIn("3.706 REPOS", source)

    def test_dynamic_memory_content_uses_text_nodes_not_template_html(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("document.createTextNode", source)
        self.assertIn("category.textContent", source)
        self.assertNotIn("memory.fact}</", source)

    def test_voice_controls_reuse_existing_profile_and_never_auto_send_dictation(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        legacy = (UI / "jarvis.js").read_text(encoding="utf-8")
        self.assertIn("markLivVoiceProfile", cockpit)
        self.assertIn("selectVoiceProfile", cockpit)
        self.assertIn("SpeechRecognition", cockpit)
        self.assertIn("webkitSpeechRecognition", cockpit)
        self.assertIn("neuralInputMsg", cockpit)
        self.assertIn("composer.value = transcript", cockpit)
        self.assertNotIn("btnSendNeuralMsg.click()", cockpit)
        self.assertIn("jarvis:voice-speaking", legacy)
        self.assertIn("jarvis:voice-speaking", cockpit)

    def test_microphone_degrades_when_browser_recognition_is_missing(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("micButton.disabled = true", source)
        self.assertIn("Reconhecimento de voz indisponível", source)

    def test_quick_dock_reuses_existing_real_actions(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("btnMobileCompanion", source)
        self.assertIn("btnRunMasterPipeline", source)
        self.assertIn("btnSyncObsidianVault", source)
        self.assertIn("auditButton.click()", source)
        self.assertIn("syncButton.click()", source)
        self.assertIn("requestFullscreen", source)

    def test_native_code_highlighting_runs_after_html_escape(self):
        source = (UI / "jarvis.js").read_text(encoding="utf-8")
        self.assertIn("function highlightEscapedCode", source)
        self.assertIn("const escCode = escapeHtml(b.code)", source)
        self.assertIn("highlightEscapedCode(escCode, b.lang)", source)
        self.assertIn("chat-syntax-keyword", source)

    def test_visual_contract_supports_responsive_and_reduced_motion(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn("@media (max-width: 880px)", css)
        self.assertIn("@media (max-width: 620px)", css)
        self.assertIn("backdrop-filter: blur(16px)", css)
        for token in ("#030712", "#00f2ff", "#ffaa00", "#00ff88", "#ff3366"):
            self.assertIn(token, css)

    def test_service_worker_caches_mark_liv_assets(self):
        source = (UI / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("/mark-liv.css", source)
        self.assertIn("/mark-liv-cockpit.js", source)
        self.assertIn("jarvis-mark-liv-shell-v2", source)

    def test_manifest_remains_standalone_and_uses_local_icon(self):
        manifest = json.loads((UI / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["scope"], "/")
        self.assertEqual(manifest["icons"][0]["src"], "/assets/jarvis_core.png")


if __name__ == "__main__":
    unittest.main()
