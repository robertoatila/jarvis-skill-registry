"""Contract: the public site shows only commands and figures this checkout has.

The page used to advertise a skill count the repository does not contain, a
repository count from an untracked database, and a "live simulator" replaying
output of commands that do not exist.  It now replays recorded output of real
commands, and the one figure it states is measured.
Pure Python Standard Library // Zero PIP Dependencies
"""

import re
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling import audit_documentation_claims as claims

SITE_HTML = (_REPO_ROOT / "site" / "index.html").read_text(encoding="utf-8")


def _demo_commands():
    block = re.search(r"const simData = \{(.*?)\n    \};", SITE_HTML, re.DOTALL)
    if block is None:
        raise AssertionError("simData block not found in site/index.html")
    return re.findall(r'^\s*cmd: "((?:[^"\\]|\\.)*)",\s*$', block.group(1), re.MULTILINE)


class TestSiteDemoCommandsExist(unittest.TestCase):
    def test_every_replayed_command_can_be_run_from_a_checkout(self):
        commands = _demo_commands()
        self.assertGreaterEqual(len(commands), 5)
        launcher = (_REPO_ROOT / "jarvis.py").read_text(encoding="utf-8")
        server = (_REPO_ROOT / "tooling" / "jarvis_server.py").read_text(encoding="utf-8")
        for command in commands:
            command = command.replace('\\"', '"')
            with self.subTest(command=command):
                words = command.split()
                if words[0] == "python":
                    script = _REPO_ROOT / words[1]
                    self.assertTrue(script.is_file(), f"{words[1]} does not exist")
                    if words[1] == "jarvis.py":
                        for flag in (w for w in words[2:] if w.startswith("--")):
                            self.assertIn(f'"{flag}"', launcher)
                elif words[0] == "curl":
                    route = re.search(r"https?://[^/]+(/[^?\"]*)", command)
                    self.assertIsNotNone(route)
                    self.assertIn(f'"{route.group(1)}"', server)
                else:
                    self.fail(f"unexpected demo command: {command}")

    def test_the_section_says_the_output_is_recorded(self):
        section = re.search(r'<section id="simulator">(.*?)</section>', SITE_HTML, re.DOTALL)
        self.assertIsNotNone(section)
        self.assertIn("recorded", section.group(1).lower())
        self.assertFalse("Test it live" in section.group(1))
        self.assertFalse("ENGINE READY" in section.group(1))


class TestSiteFigures(unittest.TestCase):
    def test_skill_count_is_the_measured_one(self):
        report = claims.audit_repository(_REPO_ROOT)
        self.assertIn("site/index.html", report["skill_count_surfaces"])
        site_violations = [v for v in report["violations"] if v["path"] == "site/index.html"]
        self.assertEqual(site_violations, [])
        measured = report["measured_canonical_skills"]
        self.assertIn(f'<div class="metric-val">{measured}</div>', SITE_HTML)

    def test_auditor_reports_a_stale_site_count(self):
        stale = SITE_HTML.replace('<div class="metric-val">', '<div class="metric-val">9', 1)
        folded = re.sub(r"(<div class=\"metric-val\">[^<]*</div>)\s*\n\s*", r"\1 ", stale)
        found = claims.audit_skill_counts("site/index.html", folded, claims.count_canonical_skills(_REPO_ROOT))
        self.assertEqual([v.code for v in found], ["SKILL_COUNT_STALE"])

    def test_no_untracked_inventory_or_workstation_facts(self):
        for needle in ("42,872", "42k", "5,870", "HD D:", "Drive E:", "125 µs"):
            with self.subTest(needle=needle):
                self.assertFalse(needle in SITE_HTML)


class TestSiteGeneratorIsInert(unittest.TestCase):
    def test_importing_the_generator_writes_nothing(self):
        import importlib.util

        target = _REPO_ROOT / "site" / "index.html"
        before = target.read_bytes()
        spec = importlib.util.spec_from_file_location("_build_site_probe", _REPO_ROOT / "tooling" / "build_site.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(target.read_bytes(), before)
        # Without --force a differing page is left alone and the exit code says so.
        self.assertEqual(module.main([]), 0 if before.decode("utf-8") == module.html_content else 1)
        self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
