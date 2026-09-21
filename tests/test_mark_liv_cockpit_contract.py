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

    def test_hippocampus_exposes_bounded_obsidian_note19_projection_health(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        self.assertIn("obsidian_projection", server)
        self.assertIn("OBSIDIAN_MEMORY_PATH.name", server)
        self.assertIn('"status": "SYNCED"', server)
        self.assertIn('"status": "ERROR"', server)
        self.assertIn("markLivObsidianProjection", cockpit)
        self.assertIn("markLivMemoryCount", cockpit)
        self.assertIn("markLivMemoryUpdated", cockpit)
        self.assertIn("projection.note_name", cockpit)
        self.assertNotIn("OBSIDIAN_MEMORY_PATH.resolve", server)

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

    def test_wave_studio_uses_real_dag_states_waves_and_receipts(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("dag.edges", source)
        self.assertIn("schedule.waves", source)
        self.assertIn("taskStateClass", source)
        self.assertIn("PENDING", source)
        self.assertIn("RUNNING", source)
        self.assertIn("VERIFIED", source)
        self.assertIn("/api/runtime/missions", source)
        self.assertIn("/timeline", source)
        self.assertIn("markLivReceipts", source)
        self.assertIn("data-mark-task-id", source)

    def test_mark_liv_telemetry_is_truthful_about_threads_and_missing_sensors(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        self.assertIn("runtime_threads_active", server)
        self.assertIn("threading.active_count()", server)
        self.assertIn('"temperature_c": None', server)
        self.assertIn('"temperature_status": "UNAVAILABLE_NO_STANDARD_SENSOR"', server)
        self.assertIn('"power_watts": None', server)
        self.assertIn("markLivThreads", cockpit)
        self.assertIn("markLivTemp", cockpit)
        self.assertIn("Sensor de temperatura indisponível", cockpit)

    def test_topbar_grid_matches_all_six_runtime_blocks_and_has_valid_spacing(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn(
            "grid-template-columns: minmax(210px, 1.25fr) auto auto auto auto minmax(210px, .7fr);",
            css,
        )
        self.assertIn("gap: var(--jv-space-2);", css)
        self.assertIn("padding: var(--jv-space-2) var(--jv-space-3);", css)
        self.assertNotIn("0var(", css)

    def test_module_deck_tracks_legacy_navigation_accessibly(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn('aria-pressed="false"', source)
        self.assertIn("function setActiveModule", source)
        self.assertIn("function syncModuleFromLegacyNavigation", source)
        self.assertIn('.nav-tab[aria-selected="true"]', source)
        self.assertIn("attributeFilter: ['aria-selected']", source)
        self.assertIn("item.setAttribute('aria-pressed', String(active))", source)

    def test_omniroute_shows_only_models_exposed_by_runtime(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        self.assertIn("groq_model", server)
        self.assertIn("gemini_model", server)
        self.assertIn("data.groq_model", source)
        self.assertIn("data.gemini_model", source)
        self.assertIn("LOCAL / HEURÍSTICA", source)
        self.assertIn("modelo/provider não medido pelo host", source)
        self.assertNotIn("ollama_model", source)

    def test_topbar_exposes_live_latency_and_context_budget(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn("markLivTopLatency", source)
        self.assertIn("markLivTopContext", source)
        self.assertIn("markLivNeuralBadge", source)
        self.assertIn("data-budget-state=\"unknown\"", source)
        self.assertIn("neuralBadge.dataset.budgetState", source)
        self.assertIn(".mark-liv-neural-badge[data-budget-state=\"safe\"]", css)
        self.assertIn(".mark-liv-neural-badge[data-budget-state=\"warn\"]", css)
        self.assertIn(".mark-liv-neural-badge[data-budget-state=\"critical\"]", css)

    def test_context_budget_visually_distinguishes_under_thirty_percent(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn("utilization < 30 ? 'safe'", source)
        self.assertIn('data-budget-state="safe"', css)
        self.assertIn('data-budget-state="warn"', css)
        self.assertIn('data-budget-state="critical"', css)

    def test_unknown_latency_remains_unmeasured(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        self.assertIn("hasFiniteNumber(data.avg_duration_ms)", cockpit)
        self.assertIn("latency === null ? '—'", cockpit)
        self.assertIn('"avg_duration_ms": None', server)
        self.assertIn('"spans": spans', server)
        self.assertNotIn("[s.to_dict() for s in spans]", server)

    def test_missing_numeric_metrics_do_not_coerce_null_to_zero(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        for field in (
            "data.canonical_active_skills_count",
            "data.total_starred_catalog_count",
            "tg.utilization_pct",
            "tg.headroom_pct",
            "tg.tokens_estimated",
            "tg.budget_limit",
            "data.cpu_usage_pct",
            "ramValue",
            "disks[0].used_pct",
            "data.runtime_threads_active",
            "data.armor_integrity_pct",
            "data.total_spans",
        ):
            self.assertIn(f"hasFiniteNumber({field})", source)
        self.assertNotIn("finite(Number(data.cpu_usage_pct))", source)
        self.assertNotIn("finite(Number(tg.utilization_pct))", source)
        self.assertNotIn(
            "Number.isFinite(Number(data.canonical_active_skills_count))",
            source,
        )

    def test_unavailable_sensors_never_coerce_null_to_zero(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("function hasFiniteNumber", source)
        self.assertIn("value !== null", source)
        self.assertIn("hasFiniteNumber(data.temperature_c)", source)
        self.assertIn("hasFiniteNumber(data.power_watts)", source)
        self.assertNotIn("finite(Number(data.temperature_c))", source)
        self.assertNotIn("finite(Number(data.power_watts))", source)

    def test_fitness_endpoint_uses_existing_rank_skills_contract(self):
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        self.assertIn('if path == "/api/agentic/fitness":', server)
        self.assertIn("fit.rank_skills(skill_ids)", server)
        self.assertNotIn("fit.get_top_skills(", server)
        self.assertIn('"observed_invocations"', server)
        self.assertIn('"observed_invocations_window"', server)

    def test_combined_radar_searches_starred_and_100k_catalogs(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("/api/starred?limit=all", source)
        self.assertIn("/api/repos/100k?limit=all", source)
        self.assertIn("normalizedRadarRows", source)
        self.assertIn("new Map()", source)
        self.assertIn("filtered.slice(0, 80)", source)
        self.assertIn("safeHttpUrl", source)
        self.assertIn("noopener noreferrer", source)
        self.assertIn("markLivRadarSearch", source)
        self.assertIn("markLivRadarOpenLegacy", source)

    def test_mark_liv_backend_routes_used_by_cockpit_are_unique(self):
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        for route in (
            "/api/agentic/telemetry",
            "/api/agentic/dag/active",
            "/api/agentic/execute",
        ):
            self.assertEqual(
                server.count(f'path == "{route}"'),
                1,
                route,
            )
        self.assertEqual(
            server.count('path == "/api/repos/scan-new"'),
            2,
            "repository discovery must keep distinct GET and POST contracts",
        )

    def test_tactical_typefaces_and_topbar_reactor_are_wired(self):
        html = (UI / "index.html").read_text(encoding="utf-8")
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        for family in ("Orbitron", "Rajdhani", "Inter", "JetBrains+Mono"):
            self.assertIn(family, html)
        self.assertIn(".mark-liv-brand__mark::before", css)
        self.assertIn(".mark-liv-brand__mark::after", css)
        self.assertIn(".mark-liv-brand__mark::before,", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_mark_liv_visuals_consume_canonical_design_tokens(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        tokens = (ROOT / "design-system" / "tokens.css").read_text(encoding="utf-8")
        runtime_tokens = (
            ROOT / "ui" / "assets" / "design-system" / "tokens.css"
        ).read_text(encoding="utf-8")
        components = (
            ROOT / "design-system" / "components.css"
        ).read_text(encoding="utf-8")
        runtime_components = (
            ROOT / "ui" / "assets" / "design-system" / "components.css"
        ).read_text(encoding="utf-8")
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")

        self.assertEqual(tokens, runtime_tokens)
        self.assertEqual(components, runtime_components)
        self.assertIn("--jv-mark-bg-deep", tokens)
        self.assertIn("--jv-font-display-tactical", tokens)
        self.assertIn(".jv-holomat-panel", components)
        self.assertIn("jv-holomat-panel", cockpit)
        self.assertIn("var(--jv-mark-cyan)", css)
        self.assertIn("var(--jv-font-display-tactical)", css)
        self.assertNotRegex(css, r"#[0-9A-Fa-f]{3,8}\\b")
        self.assertNotRegex(css, r"rgba?\\(")
        self.assertNotIn("Orbitron,", css)
        self.assertNotIn("JetBrains Mono", css)

    def test_mark_liv_motion_and_blur_are_tokenized(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn("var(--jv-mark-motion-reactor)", css)
        self.assertIn("var(--jv-mark-motion-spin-normal)", css)
        self.assertIn("var(--jv-mark-motion-wave)", css)
        self.assertIn("var(--jv-mark-panel-blur)", css)
        self.assertNotIn("2.8s", css)
        self.assertNotIn("3.2s", css)
        self.assertNotIn("19s", css)
        self.assertNotIn("blur(14px)", css)
        self.assertNotIn("blur(16px)", css)

    def test_hardware_telemetry_is_shared_with_stale_fallback_and_visibility_pause(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        legacy = (UI / "jarvis.js").read_text(encoding="utf-8")

        self.assertIn("jarvis:hardware-telemetry", legacy)
        self.assertIn("jarvis:hardware-telemetry", cockpit)
        self.assertIn("HARDWARE_FALLBACK_DELAY_MS = 7000", cockpit)
        self.assertIn("hardwareAge >= 15000", cockpit)
        self.assertIn("requests.push(['hardware', '/api/system/telemetry', renderHardware])", cockpit)
        self.assertIn("if (!force && document.hidden) return", cockpit)
        self.assertIn("visibilitychange", cockpit)
        self.assertIn("pagehide", cockpit)

        self.assertIn("if (!document.hidden) loadHardwareTelemetry()", legacy)
        self.assertIn("visibilitychange", legacy)
        self.assertIn("clearInterval(hardwareTelemetryTimer)", legacy)

    def test_polling_is_staggered_and_panel_failures_are_visible(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        components = (
            ROOT / "design-system" / "components.css"
        ).read_text(encoding="utf-8")

        self.assertIn("const REFRESH_TICK_MS = 5000", source)
        for contract in (
            "status: 15000",
            "hardware: 5000",
            "keys: 30000",
            "telemetry: 5000",
            "memory: 15000",
            "dag: 10000",
            "receipts: 5000",
        ):
            self.assertIn(contract, source)
        self.assertIn("function isDue(", source)
        self.assertIn("function setSourceHealth(", source)
        self.assertIn("panel.classList.toggle('is-loading'", source)
        self.assertIn("panel.classList.toggle('is-error'", source)
        self.assertIn(".jv-holomat-panel.is-loading", components)
        self.assertIn(".jv-holomat-panel.is-error", components)

    def test_mark_liv_keyboard_focus_is_explicit_and_not_outline_suppressed(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn(".mark-liv-cockpit button:focus-visible", css)
        self.assertIn(".mark-liv-cockpit input:focus-visible", css)
        self.assertIn(".mark-liv-cockpit select:focus-visible", css)
        self.assertIn(".mark-liv-cockpit a:focus-visible", css)
        self.assertIn("outline: 2px solid var(--jv-mark-cyan);", css)
        self.assertIn("outline-offset: 2px;", css)

    def test_visual_contract_supports_responsive_and_reduced_motion(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        tokens = (ROOT / "design-system" / "tokens.css").read_text(encoding="utf-8")
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn("@media (max-width: 880px)", css)
        self.assertIn("@media (max-width: 620px)", css)
        self.assertIn("backdrop-filter: blur(var(--jv-mark-panel-blur))", css)
        for token in (
            "--jv-mark-bg-deep: #030712",
            "--jv-mark-cyan: #00f2ff",
            "--jv-mark-amber: #ffaa00",
            "--jv-mark-green: #00ff88",
            "--jv-mark-red: #ff3366",
        ):
            self.assertIn(token, tokens)

    def test_service_worker_caches_mark_liv_assets(self):
        source = (UI / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("/mark-liv.css", source)
        self.assertIn("/mark-liv-cockpit.js", source)
        self.assertIn("jarvis-mark-liv-shell-v2", source)

    def test_remote_manifest_remains_companion_scoped_and_standalone(self):
        manifest = json.loads((UI / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "J.A.R.V.I.S. Remote Companion")
        self.assertEqual(manifest["display"], "standalone")
        self.assertIn("remote=1", manifest["start_url"])
        self.assertEqual(manifest["scope"], "/")
        self.assertEqual(manifest["icons"][0]["src"], "/assets/jarvis_core.png")


if __name__ == "__main__":
    unittest.main()
