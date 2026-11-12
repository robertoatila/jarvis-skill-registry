"""Contract: the cockpit shell ships without numbers that look like live telemetry.

``ui/index.html`` used to pre-seed counters, benchmark figures and PASS lines
that stayed on screen whenever the local server did not answer, and
``ui/jarvis.js`` replaced missing server values with remembered defaults.  A
dynamic field now starts as a dash and is filled only from a server response.
Pure Python Standard Library // Zero PIP Dependencies
"""

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = (_REPO_ROOT / "ui" / "index.html").read_text(encoding="utf-8")
JARVIS_JS = (_REPO_ROOT / "ui" / "jarvis.js").read_text(encoding="utf-8")

# Fields that a script fills from an API response.
DYNAMIC_PLACEHOLDER_IDS = (
    "benchNavBadge",
    "benchMetricRatio",
    "benchMetricWave",
    "benchMetricHeadroom",
    "benchMetricRepos",
    "benchRowRatio",
    "benchRowWave",
    "benchRowRepos",
    "benchRowHeadroom",
    "benchBarJarvisLabel",
    "benchBarEagerLabel",
    "benchLatWave",
    "benchLatPolicy",
    "benchLatMerkle",
    "benchLatPlanning",
    "badgeTotalArsenalRepos",
    "badgeManagedSkillsCount",
    "countSquadAll",
    "countSquadHyperion",
    "countSquadNeuro",
    "countSquadAegis",
    "countSquadCyberspace",
    "countSquadTactical",
    "hudSuccessRate",
    "hudAvgDuration",
    "hudTotalSpans",
    "hudTotalTokens",
    "memCountBadge",
    "k100CounterBadge",
)

SEEDED_FIGURES = (
    "40.2x",
    "97.51",
    "125 µs",
    "125µs",
    "42.872",
    "42,872",
    "394 Skills",
    "394 skills",
    "906.660",
    "906,660",
    "22.544",
    "22.296",
    "90.1%",
    "VALIDADO (PASS)",
    "[PASS] ",
    "100.0%",
)


def _inner_text(element_id: str) -> str:
    match = re.search(r'<[a-zA-Z0-9]+\b[^>]*\bid="%s"[^>]*>(.*?)</' % re.escape(element_id), INDEX_HTML, re.DOTALL)
    if match is None:
        raise AssertionError(f'element id="{element_id}" not found in ui/index.html')
    return match.group(1).strip()


class TestCockpitShellHasNoSeededTelemetry(unittest.TestCase):
    def test_dynamic_fields_start_as_a_dash(self):
        for element_id in DYNAMIC_PLACEHOLDER_IDS:
            with self.subTest(element_id=element_id):
                self.assertEqual(_inner_text(element_id), "—")

    def test_shell_contains_no_remembered_benchmark_or_inventory_figures(self):
        for figure in SEEDED_FIGURES:
            with self.subTest(figure=figure):
                self.assertNotIn(figure, INDEX_HTML)

    def test_shell_contains_no_workstation_specific_addresses(self):
        # A personal tailnet hostname and drive letters were hard-coded here.
        self.assertNotRegex(INDEX_HTML, r"[A-Za-z0-9-]+\.ts\.net")
        self.assertNotIn("E:\\.skill-registry", INDEX_HTML)
        self.assertEqual(_inner_text("valOllamaLocal"), "LOCAL (OPCIONAL)")
        hidden = re.search(r'<input type="hidden" id="companionUrlInput" value="([^"]*)"', INDEX_HTML)
        self.assertIsNotNone(hidden)
        self.assertEqual(hidden.group(1), "")

    def test_shell_names_no_drive_letter_and_no_remembered_schedule(self):
        drive_lines = [n for n, line in enumerate(INDEX_HTML.splitlines(), 1) if re.search(r"\b[A-Za-z]:\\", line)]
        self.assertEqual(drive_lines, [])
        self.assertNotIn("20:00:00", INDEX_HTML)
        self.assertFalse("Patamar 100%" in INDEX_HTML)
        self.assertTrue(_inner_text("autonomousNextRun").endswith("—"))
        # The script still fills the schedule from the server's answer.
        self.assertIn("data.next_run", JARVIS_JS)

    def test_benchmark_console_is_not_pre_seeded_with_results(self):
        block = re.search(r'id="benchLiveTerminal">(.*?)</div>\s*<div class="benchmark-terminal-footer"', INDEX_HTML, re.DOTALL)
        self.assertIsNotNone(block)
        self.assertNotIn("ok-line", block.group(1))
        self.assertNotRegex(block.group(1), r"\d")


class TestCockpitScriptHasNoDefaultTelemetry(unittest.TestCase):
    def test_no_numeric_fallback_replaces_a_missing_server_value(self):
        forbidden = (
            "|| 100}%",
            "|| '40.2x'",
            "|| 97.51",
            "|| 2254",
            "|| 26549",
            "|| 392",
            ": '125 µs'",
            ": '100%'",
            "145 skills",
        )
        for snippet in forbidden:
            with self.subTest(snippet=snippet):
                self.assertNotIn(snippet, JARVIS_JS)

    def test_unknown_security_status_is_never_rendered_as_pass(self):
        self.assertNotIn("security_status || 'PASS'", JARVIS_JS)
        self.assertNotIn("isFlagged ? 'FLAGGED' : 'PASS'", JARVIS_JS)
        self.assertIn("'NÃO AUDITADA'", JARVIS_JS)

    def test_unreachable_server_does_not_render_sample_skills_or_a_simulated_proposal(self):
        self.assertNotIn("simulateAutonomousWorkflow", JARVIS_JS)
        body = re.search(r"function renderFallbackSkills\(\) \{(.*?)\n  \}", JARVIS_JS, re.DOTALL)
        self.assertIsNotNone(body)
        self.assertIn("allSkills = [];", body.group(1))
        self.assertNotIn("name:", body.group(1))

    def test_every_field_the_benchmark_binder_writes_exists_in_the_shell(self):
        body = re.search(r"async function loadBenchmarks\(\) \{(.*?)\n  \}\n", JARVIS_JS, re.DOTALL)
        self.assertIsNotNone(body)
        written = set(re.findall(r"set(?:Text|Width)\('([A-Za-z0-9]+)'", body.group(1)))
        self.assertGreaterEqual(len(written), 15)
        for element_id in sorted(written):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', INDEX_HTML)
        self.assertIn("describeBenchmarkReport", body.group(1))


if __name__ == "__main__":
    unittest.main()
