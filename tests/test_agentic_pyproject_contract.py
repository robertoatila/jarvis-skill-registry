"""Contract: ``pyproject.toml`` configures optional developer tooling only.

The runtime is started with ``python jarvis.py`` on the standard library.  The
file must not turn the repository into an installable package or introduce a
dependency, and its lint exclusions must point at things that exist.
Pure Python Standard Library // Zero PIP Dependencies
"""

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = _REPO_ROOT / "pyproject.toml"

try:  # Python 3.11+
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10
    tomllib = None


class TestPyprojectIsToolingOnly(unittest.TestCase):
    def setUp(self):
        self.text = PYPROJECT.read_text(encoding="utf-8")

    def test_declares_no_package_build_or_dependency(self):
        tables = set(re.findall(r"^\[([^\]]+)\]\s*$", self.text, re.MULTILINE))
        self.assertTrue(tables, "pyproject.toml declares no table")
        for table in tables:
            with self.subTest(table=table):
                self.assertTrue(table == "tool.ruff" or table.startswith("tool.ruff."), table)
        self.assertNotRegex(self.text, r"(?m)^\s*(dependencies|requires|optional-dependencies)\s*=")

    @unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
    def test_parses_and_targets_the_lowest_supported_interpreter(self):
        data = tomllib.loads(self.text)
        self.assertEqual(set(data), {"tool"})
        self.assertEqual(set(data["tool"]), {"ruff"})
        ruff = data["tool"]["ruff"]
        self.assertEqual(ruff["target-version"], "py310")
        selected = ruff["lint"]["select"]
        self.assertEqual(len(selected), len(set(selected)))
        for rule in ("E9", "F63", "F7", "F82"):
            self.assertIn(rule, selected)

    @unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
    def test_every_exclusion_exists_and_the_fixture_is_still_invalid(self):
        data = tomllib.loads(self.text)
        excluded = data["tool"]["ruff"]["extend-exclude"]
        for entry in excluded:
            with self.subTest(entry=entry):
                self.assertTrue((_REPO_ROOT / entry).exists(), f"excluded path does not exist: {entry}")
        fixture = _REPO_ROOT / "staging" / "orchestration" / "broken-syntax-tool" / "implementation.py"
        self.assertIn("staging/orchestration/broken-syntax-tool", excluded)
        with self.assertRaises(SyntaxError):
            compile(fixture.read_text(encoding="utf-8"), str(fixture), "exec")

    def test_launcher_and_battery_do_not_depend_on_the_linter(self):
        for name in ("jarvis.py", "run_tests.py"):
            with self.subTest(name=name):
                source = (_REPO_ROOT / name).read_text(encoding="utf-8")
                self.assertNotRegex(source, r"\bruff\b")


if __name__ == "__main__":
    unittest.main()
