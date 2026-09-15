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
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_hud_uses_design_system_assets_and_retractable_sidebar(self):
        html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "/assets/design-system/tokens.css",
            "/assets/design-system/components.css",
            "/assets/design-system/patterns.css",
            "id=\"jarvis-sidebar\"",
            "id=\"sidebar-toggle\"",
            "data-tab=\"overview\"",
            "data-tab=\"cockpit\"",
            "data-tab=\"cognitive\"",
            "data-tab=\"registry\"",
            "data-tab=\"agents\"",
            "data-tab=\"mission\"",
            "data-tab=\"logs\"",
            "data-tab=\"settings\"",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_sidebar_preference_is_persistent_and_keyboard_accessible(self):
        js = (ROOT / "ui" / "jarvis.js").read_text(encoding="utf-8")
        for marker in (
            "jarvis.sidebar.collapsed",
            "localStorage",
            "aria-expanded",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)

    def test_absent_raw_export_is_not_reintroduced(self):
        self.assertFalse((ROOT / "design-system-export").exists())


if __name__ == "__main__":
    unittest.main()
