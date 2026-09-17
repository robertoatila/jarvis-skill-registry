#!/usr/bin/env python3
"""Acceptance contract for the first external skill contribution walkthrough."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WALKTHROUGH = ROOT / "docs" / "contributing" / "FIRST_EXTERNAL_SKILL.md"


class FirstExternalSkillWalkthroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WALKTHROUGH.read_text(encoding="utf-8")

    def test_starts_from_clean_fork_and_creates_parseable_example_skill(self):
        text = self.text
        self.assertIn("git clone", text)
        self.assertIn("git remote add upstream", text)
        self.assertIn("git checkout -b", text)
        self.assertIn("skills/text-stats/SKILL.md", text)

        start = text.index("<!-- example-skill:start -->")
        end = text.index("<!-- example-skill:end -->")
        skill = text[start:end]
        self.assertRegex(skill, r"(?m)^---\s*$")
        self.assertRegex(skill, r"(?m)^name:\s*text-stats\s*$")
        self.assertRegex(skill, r"(?m)^description:\s*.+$")
        self.assertRegex(skill, r"(?m)^tags:\s*\[.+\]\s*$")
        self.assertGreaterEqual(skill.count("---"), 2)
        self.assertIn("No network access", skill)
        self.assertNotRegex(skill, r"(?i)(api[_ -]?key|password|bearer\s+[A-Za-z0-9])")

    def test_documents_provenance_license_validation_and_failure_handling(self):
        lower = self.text.lower()
        self.assertIn("provenance", lower)
        self.assertIn("license", lower)
        self.assertIn("third-party", lower)
        self.assertIn("python jarvis.py --doctor", self.text)
        self.assertIn("python jarvis.py --full-test", self.text)
        self.assertIn("python benchmarks/context_budget_benchmark.py", self.text)
        self.assertIn("python tooling/audit_pre_publish_security.py", self.text)
        self.assertIn("do not bypass", lower)
        self.assertIn("read the first failing test", lower)

    def test_pr_evidence_is_small_explicit_and_reproducible(self):
        text = self.text
        for heading in (
            "Problem",
            "Change",
            "Evidence",
            "Boundary",
            "Risk",
        ):
            self.assertIn(f"**{heading}**", text)
        self.assertIn("exact commit SHA", text)
        self.assertIn("exact commands", text)
        self.assertIn("one skill", text.lower())
        self.assertIn("do not include credentials", text.lower())


if __name__ == "__main__":
    unittest.main()
