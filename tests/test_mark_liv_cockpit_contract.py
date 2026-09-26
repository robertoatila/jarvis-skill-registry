#!/usr/bin/env python3
"""Static contracts for the Mark-LIV Holomat Quantum Cockpit."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"


class TestMarkLivCockpitContract(unittest.TestCase):
    def test_mark_liv_is_native_module_and_can_bind_before_legacy_domcontentloaded_work(self):
        html = (UI / "index.html").read_text(encoding="utf-8")
        legacy = (UI / "jarvis.js").read_text(encoding="utf-8")
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")

        self.assertIn('type="module" src="mark-liv-cockpit.js"', html)
        self.assertIn("document.addEventListener('DOMContentLoaded'", legacy)
        self.assertIn("if (document.readyState === 'loading')", cockpit)
        self.assertIn("document.addEventListener('DOMContentLoaded', init", cockpit)
        self.assertIn("bindRuntimeEvents()", cockpit)

    def test_shell_mounts_mark_liv_assets_after_existing_runtime_scripts(self):
        html = (UI / "index.html").read_text(encoding="utf-8")
        self.assertIn("J.A.R.V.I.S. Mark-LIV // Holomat Quantum Cockpit", html)
        self.assertIn('href="mark-liv.css"', html)
        self.assertIn('type="module" src="mark-liv-cockpit.js"', html)
        self.assertLess(html.index('src="jarvis.js"'), html.index('src="mark-liv-cockpit.js"'))

    def test_mark_liv_becomes_primary_surface_only_after_successful_mount(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")

        self.assertIn('id="markLivCommandStrip" role="banner"', cockpit)
        self.assertIn("document.body.classList.add('mark-liv-ready')", cockpit)
        self.assertIn("body.mark-liv-ready #jarvisHeader", css)
        self.assertIn("body.mark-liv-ready #telemetryCards", css)
        self.assertIn("display: none;", css)

    def test_cockpit_has_four_phases_and_six_runtime_modules(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        for phase in ("decompose", "skills", "execute", "synthesis"):
            self.assertIn(f'data-phase="{phase}"', source)
        for module in ("terminal", "dag", "skills", "radar", "memory", "telemetry"):
            self.assertIn(f"id: '{module}'", source)

    def test_master_prompt_obsidian_nodes_exist(self):
        required = (
            "00 - J.A.R.V.I.S. Cognitive Vault.md",
            "01 - Arsenal Map of Content.md",
            "06 - GitHub Starred Repositories.md",
            "18 - Inteligencia Comparativa de Motores Jarvis Ultron e Copilots.md",
            "19 - Memoria Persistente e Conhecimento Episodico.md",
            "21 - Repositorios 100k+ Estrelas e Radar de Sites Oficiais.md",
            "22 - Relatorios e Evidencias das Fases de Evolucao.md",
            "docs/OBSIDIAN_INTEGRATION_GUIDE.md",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_context_headroom_uses_receipt_backed_bytes_and_never_fixed_demo_numbers(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        governor = (ROOT / "tooling" / "agentic" / "context_governor.py").read_text(encoding="utf-8")

        self.assertIn("get_live_context_governance", server)
        self.assertIn('"serialized_bytes": serialized', server)
        self.assertIn('"budget_bytes": budget', server)
        self.assertIn('"compression_savings_pct": savings', server)
        self.assertNotIn('"tokens_estimated": 4560', server)
        self.assertNotIn('"utilization_pct": 22.8', server)
        self.assertNotIn('"headroom_pct": 77.2', server)

        self.assertIn('"candidate_serialized_bytes": candidate_serialized_bytes', governor)
        self.assertIn('"savings_pct": round(', governor)

        self.assertIn("tg.serialized_bytes", cockpit)
        self.assertIn("tg.budget_bytes", cockpit)
        self.assertIn("tg.compression_savings_pct", cockpit)
        self.assertIn("tg.token_estimation_method", cockpit)
        self.assertIn("markLivContextSavings", cockpit)
        self.assertIn("markLivTokenEstimate", cockpit)

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

    def test_stepper_uses_mission_receipts_not_global_health_for_execution_and_synthesis(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn("function setPhaseState", source)
        self.assertIn("latestExecution", source)
        self.assertIn("latestVerification", source)
        self.assertIn("execution_state", source)
        self.assertIn("verification_state", source)
        self.assertIn("setPhaseState('execute', 'ready'", source)
        self.assertIn("setPhaseState('execute', 'failed'", source)
        self.assertIn("setPhaseState('synthesis', 'ready', 'VERIFIED')", source)
        self.assertIn("setPhaseState('synthesis', 'failed'", source)
        self.assertIn("setPhaseState(\n        'skills',\n        'available'", source)
        self.assertNotIn("if (executePhase && data.system_state)", source)
        self.assertNotIn("if (synthesis && Number(data.total_spans) > 0)", source)
        self.assertIn('.mark-liv-phase[data-state="running"]', css)
        self.assertIn('.mark-liv-phase[data-state="failed"]', css)
        self.assertIn('.mark-liv-phase[data-state="available"]', css)

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

    def test_live_status_and_hardware_telemetry_have_no_historical_demo_fallbacks(self):
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        status_start = server.index('if path == "/api/status":')
        status_end = server.index("# API: /api/clusters", status_start)
        status_block = server[status_start:status_end]

        self.assertIn("catalogue_status = get_current_catalog_status()", status_block)
        self.assertIn('"system_state": "ONLINE"', status_block)

        catalogue_start = server.index("def get_current_catalog_status():")
        catalogue_end = server.index("ASSISTANTS_COMPARATIVE_MATRIX", catalogue_start)
        catalogue_block = server[catalogue_start:catalogue_end]
        self.assertIn("active_skills = len(skills_snapshot)", catalogue_block)
        self.assertIn('re.fullmatch(r"[0-9a-fA-F]{64}"', catalogue_block)
        self.assertNotIn("145", status_block)
        self.assertNotIn('"c6d7e89f..."', status_block)
        self.assertNotIn("135", status_block)
        self.assertNotIn("870", status_block)
        self.assertNotIn('"tombstones_count": 118', status_block)

        hardware_start = server.index("class HardwareTelemetry:")
        hardware_end = server.index("HARDWARE_TELEMETRY = HardwareTelemetry()", hardware_start)
        hardware_block = server[hardware_start:hardware_end]
        self.assertIn("ram_load = None", hardware_block)
        self.assertIn("cpu_load = None", hardware_block)
        self.assertIn("uptime_str = None", hardware_block)
        self.assertIn('"armor_integrity_pct": None', hardware_block)
        self.assertIn('"armor_integrity_status": "NOT_MEASURED"', hardware_block)
        self.assertIn('"protocol": "SSP-v13.2"', hardware_block)
        self.assertNotIn('"armor_integrity_pct": 99.8', hardware_block)
        self.assertNotIn("cpu_load = 15.0", hardware_block)
        self.assertNotIn("ram_load = 50", hardware_block)

    def test_sealed_badge_requires_current_merkle_evidence(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")

        self.assertIn('"canonical_merkle_status": "CURRENT" if merkle_root else "UNKNOWN_OR_STALE"', server)
        self.assertIn('"CURRENT" if merkle_root else "UNKNOWN_OR_STALE"', server)
        self.assertIn("evidence_count == active_skills", server)

        self.assertIn("const merkleCurrent = (", cockpit)
        self.assertIn("merkleStatus === 'CURRENT'", cockpit)
        self.assertIn("const sealed = governanceSealed && merkleCurrent", cockpit)
        self.assertIn("const staleSeal = governanceSealed && !merkleCurrent", cockpit)
        self.assertIn("EVIDENCE STALE", cockpit)

    def test_governance_badge_is_neutral_until_sealed_or_attention_is_observed(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn('data-trust-state="unknown"', source)
        self.assertIn("const trustState = sealed ? 'sealed' : (staleSeal ? 'attention' : (unknown ? 'unknown' : 'attention'))", source)
        self.assertIn("if (trustState === 'sealed') badge.dataset.tone = 'green'", source)
        self.assertIn("else delete badge.dataset.tone", source)
        self.assertIn("badge.classList.toggle('mark-liv-offline', trustState === 'attention')", source)
        self.assertNotIn('data-tone="green" id="markLivGovernanceBadge"', source)

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

    def test_omniroute_distinguishes_configured_routable_and_local_discovery(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")

        self.assertIn("get_routable_chat_providers", server)
        self.assertIn("get_ollama_local_status", server)
        self.assertIn('"ollama_local_online"', server)
        self.assertIn('"ollama_routable"', server)
        self.assertIn('"local_heuristic_available": True', server)
        self.assertNotIn('keys.get("groq_model", "openai/gpt-oss-120b")', server)
        self.assertNotIn('keys.get("gemini_model", "gemini-3.8-flash")', server)

        self.assertIn("markLivRouteChain", source)
        self.assertIn("DISCOVERED · NOT ROUTABLE", source)
        self.assertIn("setRouteChip(\n      'local',", source)
        self.assertIn("modelByProvider", source)
        self.assertIn("'modelo não configurado'", source)

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

    def test_amber_disk_tone_never_overrides_unavailable_state(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn(
            '.mark-liv-gauge[data-tone="amber"]:not([data-mode="unavailable"])',
            css,
        )
        self.assertNotIn('.mark-liv-gauge[data-tone="amber"] {', css)

    def test_unknown_gauges_render_unavailable_instead_of_visual_zero(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("gauge.dataset.mode = 'unavailable'", source)
        self.assertIn("gauge.style.removeProperty('--gauge-value')", source)
        self.assertIn("setGauge('markLivContextGauge', utilization)", source)
        self.assertIn("setGauge('markLivCpuGauge', cpu)", source)
        self.assertIn("setGauge('markLivRamGauge', ram)", source)
        self.assertIn("setGauge('markLivDiskGauge', disk)", source)
        self.assertNotIn("setGauge('markLivContextGauge', utilization || 0)", source)
        self.assertNotIn("cpu === null ? 0 : cpu", source)
        self.assertIn('data-mode="unavailable" id="markLivCpuGauge"', source)
        self.assertIn('data-mode="unavailable" id="markLivContextGauge"', source)

    def test_missing_numeric_metrics_do_not_coerce_null_to_zero(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        for field in (
            "data.canonical_active_skills_count",
            "data.total_starred_catalog_count",
            "tg.utilization_pct",
            "tg.headroom_pct",
            "tg.tokens_estimated",
            "tg.budget_bytes",
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

    def test_mark_liv_reuses_legacy_repository_catalog_events_before_refetching(self):
        cockpit = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        legacy = (UI / "jarvis.js").read_text(encoding="utf-8")
        self.assertIn("jarvis:starred-repos", legacy)
        self.assertIn("jarvis:100k-repos", legacy)
        self.assertIn("jarvis:starred-repos", cockpit)
        self.assertIn("jarvis:100k-repos", cockpit)
        self.assertIn("radarSourceReady", cockpit)
        self.assertIn("options.force || !state.radarSourceReady.starred", cockpit)
        self.assertIn("options.force || !state.radarSourceReady.giant", cockpit)
        self.assertIn("if (!fetchStarred && !fetchGiant)", cockpit)

    def test_radar_catalogs_lazy_load_near_viewport_or_on_interaction(self):
        source = (UI / "mark-liv-cockpit.js").read_text(encoding="utf-8")
        self.assertIn("function bindRadarLazyLoad", source)
        self.assertIn("IntersectionObserver", source)
        self.assertIn("rootMargin: '360px 0px'", source)
        self.assertIn("function ensureRadarCatalogs", source)
        self.assertIn("state.radarLoaded", source)
        self.assertIn("state.radarLoading", source)
        self.assertIn("moduleId === 'radar'", source)
        self.assertIn("search.addEventListener('focus'", source)
        self.assertIn("getBoundingClientRect()", source)
        self.assertNotIn("refresh(true);\n    loadRadarCatalogs();", source)

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
        self.assertNotRegex(css, r"#[0-9A-Fa-f]{3,8}\b")
        self.assertNotRegex(css, r"rgba?\(")
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

    def test_existing_arsenal_fulfills_mark_liv_search_filter_badge_and_skill_md_contract(self):
        html = (UI / "index.html").read_text(encoding="utf-8")
        source = (UI / "jarvis.js").read_text(encoding="utf-8")

        self.assertIn('id="skillSearchInput"', html)
        self.assertIn('id="filterCategorySelect"', html)
        self.assertIn('id="filterSecuritySelect"', html)
        for squad in (
            "Hyperion-Autonomous-Agents",
            "Hyperion-CyberSec",
            "Hyperion-Core-Systems",
            "Hyperion-FullStack",
            "Hyperion-DevTools",
        ):
            self.assertIn(squad, html)

        self.assertIn("skillSearchInput.addEventListener('input', applyFilters)", source)
        self.assertIn("FLAGGED_FOR_REVIEW", source)
        self.assertIn("observed_invocations", source)
        self.assertIn("/api/skills/${encodeURIComponent(skill.name)}", source)
        self.assertIn("Copiar SKILL.md", source)

    def test_optional_holomat_audio_is_native_web_audio_without_external_files(self):
        source = (UI / "jarvis.js").read_text(encoding="utf-8")
        self.assertIn("window.AudioContext || window.webkitAudioContext", source)
        self.assertIn("ctx.createOscillator()", source)
        self.assertIn("ctx.createGain()", source)
        self.assertIn("osc.type = 'sine'", source)
        self.assertIn("osc.type = 'triangle'", source)

    def test_visual_contract_has_explicit_ultrawide_notebook_and_mobile_breakpoints(self):
        css = (UI / "mark-liv.css").read_text(encoding="utf-8")
        self.assertIn("@media (min-width: 1600px)", css)
        self.assertIn("@media (max-width: 1180px)", css)
        self.assertIn("@media (max-width: 880px)", css)
        self.assertIn("@media (max-width: 620px)", css)

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
        self.assertIn("jarvis-mark-liv-shell-v3", source)
        self.assertIn("REMOTE_OWNED_PATHS", source)
        self.assertIn("name.startsWith('jarvis-mark-liv-shell-')", source)
        self.assertNotIn("'jarvis-remote-companion-v1'", source)

    def test_remote_service_worker_owns_only_remote_cache_family(self):
        source = (UI / "remote-service-worker.js").read_text(encoding="utf-8")
        self.assertIn("jarvis-remote-companion-v1", source)
        self.assertIn("name.startsWith('jarvis-remote-companion-')", source)
        self.assertIn("requestUrl.pathname.startsWith('/api/')", source)
        self.assertNotIn("jarvis-mark-liv-shell-", source)

    def test_remote_manifest_remains_companion_scoped_and_standalone(self):
        manifest = json.loads((UI / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "J.A.R.V.I.S. Remote Companion")
        self.assertEqual(manifest["display"], "standalone")
        self.assertIn("remote=1", manifest["start_url"])
        self.assertEqual(manifest["scope"], "/remote/")
        self.assertEqual(manifest["icons"][0]["src"], "/assets/jarvis_core.png")


if __name__ == "__main__":
    unittest.main()
