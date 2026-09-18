from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class JarvisDesignSystemContractTests(unittest.TestCase):
    def test_root_visual_and_agent_contracts_exist(self):
        self.assertTrue((ROOT / "DESIGN.md").is_file())
        self.assertTrue((ROOT / "AGENTS.md").is_file())

    def test_canonical_design_system_library_exists(self):
        expected = {
            "README.md",
            "tokens.css",
            "components.css",
            "patterns.css",
            "reference",
        }
        design_root = ROOT / "design-system"
        self.assertTrue(design_root.is_dir())
        self.assertTrue(expected.issubset({path.name for path in design_root.iterdir()}))

    def test_runtime_projection_matches_canonical_css(self):
        for name in ("tokens.css", "components.css", "patterns.css"):
            with self.subTest(name=name):
                canonical = (ROOT / "design-system" / name).read_text(encoding="utf-8")
                runtime = (ROOT / "ui" / "assets" / "design-system" / name).read_text(encoding="utf-8")
                self.assertEqual(canonical, runtime)

    def test_foundation_tokens_cover_color_type_space_radius_and_motion(self):
        tokens = (ROOT / "design-system" / "tokens.css").read_text(encoding="utf-8")
        required = (
            "--jv-color-bg-canvas",
            "--jv-color-accent-primary",
            "--jv-font-sans",
            "--jv-font-mono",
            "--jv-space-4",
            "--jv-radius-md",
            "--jv-motion-fast",
            "[data-theme=\"light\"]",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, tokens)

    def test_component_states_are_first_class(self):
        components = (ROOT / "design-system" / "components.css").read_text(encoding="utf-8")
        required_states = (
            ":hover",
            ":focus-visible",
            ":disabled",
            ".is-loading",
            ".is-error",
            ".is-empty",
            ".is-selected",
        )
        for state in required_states:
            with self.subTest(state=state):
                self.assertIn(state, components)

    def test_showcase_covers_library_states_and_both_themes(self):
        showcase = ROOT / "ui" / "assets" / "design-system" / "index.html"
        self.assertTrue(showcase.is_file())
        html = showcase.read_text(encoding="utf-8")
        for marker in (
            "JARVIS Design System",
            "theme-toggle",
            "data-theme=\"light\"",
            "Buttons",
            "Status",
            "Metrics",
            "Forms",
            "Loading",
            "Error",
            "Empty",
            "Selected",
            "Operational Cockpit",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_hud_loader_and_experience_layer_preserve_existing_tabs(self):
        loader = (ROOT / "ui" / "chat-session.js").read_text(encoding="utf-8")
        self.assertIn("experience-system.js", loader)
        experience = (ROOT / "ui" / "experience-system.js").read_text(encoding="utf-8")
        for marker in (
            "/assets/design-system/tokens.css",
            "/assets/design-system/components.css",
            "/assets/design-system/patterns.css",
            "jarvis-sidebar",
            "sidebar-toggle",
            "tabNeural",
            "tabArsenal",
            "tabIngest",
            "tabSubagents",
            "tabSecurity",
            "tabPipeline",
            "tabObsidian",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, experience)

    def test_server_serves_browser_loader_and_asset_namespace(self):
        server = (ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        self.assertIn('if path == "/chat-session.js":', server)
        self.assertIn('UI_DIR / "chat-session.js"', server)
        self.assertIn('if path.startswith("/assets/"):', server)

    def test_sidebar_preference_is_persistent_and_keyboard_accessible(self):
        js = (ROOT / "ui" / "experience-system.js").read_text(encoding="utf-8")
        for marker in (
            "jarvis.sidebar.collapsed",
            "localStorage",
            "aria-expanded",
            "keydown",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)

    def test_runtime_experience_projection_matches_canonical_js(self):
        canonical = (ROOT / "ui" / "experience-system.js").read_text(encoding="utf-8")
        runtime = (ROOT / "ui" / "assets" / "design-system" / "experience-system.js").read_text(encoding="utf-8")
        self.assertEqual(canonical, runtime)

    def test_operational_cockpit_uses_canonical_receipt_driven_contracts(self):
        html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "experience-system.js").read_text(encoding="utf-8")
        components = (ROOT / "design-system" / "components.css").read_text(encoding="utf-8")
        patterns = (ROOT / "design-system" / "patterns.css").read_text(encoding="utf-8")

        for marker in (
            'id="operationalCockpit"',
            'id="operationalMissionSelect"',
            'id="operationalMissionState"',
            'id="operationalDAG"',
            'id="operationalAttemptsList"',
            'id="operationalContextList"',
            'id="operationalRoutingList"',
            'id="operationalVerificationList"',
            'id="operationalMemoryList"',
            'id="operationalResources"',
            'id="operationalProgression"',
            '<script src="runtime-observability.js"></script>',
            '<script src="/assets/operational-cockpit.js"></script>',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

        for marker in (
            "jarvis:operational-cockpit",
            "jv-progress-events",
            "jv-progress-attempts",
            "jv-progress-verified",
            "jv-progress-rate",
            "Sem receipts carregados",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)

        for marker in (
            ".jv-cockpit-item",
            ".jv-cockpit__status",
            ".jv-cockpit__eyebrow",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, components)

        for marker in (
            ".jv-cockpit__summary",
            ".jv-cockpit__grid",
            ".jv-cockpit__resource-grid",
            ".jv-cockpit__toolbar",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, patterns)

    def test_operational_cockpit_accessibility_and_theme_contracts(self):
        html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
        components = (ROOT / "design-system" / "components.css").read_text(encoding="utf-8")
        patterns = (ROOT / "design-system" / "patterns.css").read_text(encoding="utf-8")
        tokens = (ROOT / "design-system" / "tokens.css").read_text(encoding="utf-8")

        cockpit_start = html.index('id="operationalCockpit"')
        cockpit_end = html.index('<div class="pipeline-layout">', cockpit_start)
        self.assertGreaterEqual(cockpit_start, 0)
        self.assertGreater(cockpit_end, cockpit_start)
        cockpit = html[cockpit_start:cockpit_end]

        self.assertIn('<label for="operationalMissionSelect">', cockpit)
        self.assertIn('id="operationalRefresh"', cockpit)
        self.assertIn('id="operationalStatus"', cockpit)
        self.assertIn('role="status"', cockpit)
        self.assertIn('aria-live="polite"', cockpit)
        self.assertEqual(cockpit.count("aria-live="), 1)
        self.assertNotIn('tabindex="-1"', cockpit)

        for marker in (
            ".jv-button:focus-visible",
            ".jv-input:focus-visible, .jv-select:focus-visible",
            ".jv-cockpit.is-loading",
            ".jv-cockpit.is-error",
            ".jv-cockpit.is-blocked",
            ".is-empty",
            ".is-selected",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, components + patterns)

        self.assertIn("@media (prefers-reduced-motion: reduce)", components + patterns)
        self.assertIn('[data-theme="light"]', tokens)
        self.assertIn("--jv-color-bg-canvas", tokens)

        cockpit_css = components[components.index(".jv-cockpit-item"):]
        self.assertNotRegex(cockpit_css, r"#[0-9A-Fa-f]{3,8}\b")

    def test_absent_raw_export_is_not_reintroduced(self):
        self.assertFalse((ROOT / "design-system-export").exists())


if __name__ == "__main__":
    unittest.main()
