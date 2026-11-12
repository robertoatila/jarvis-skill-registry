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


def _string_list(text: str, key: str):
    """Read ``key = [ "a", "b" ]`` without a TOML parser (Python 3.10 has none)."""
    match = re.search(r"(?ms)^%s\s*=\s*\[(.*?)^\]" % re.escape(key), text)
    if match is None:
        raise AssertionError(f"{key} list not found in pyproject.toml")
    body = "\n".join(line.split("#", 1)[0] for line in match.group(1).splitlines())
    return re.findall(r'"([^"]*)"', body)


def _string_value(text: str, key: str) -> str:
    match = re.search(r'(?m)^%s\s*=\s*"([^"]*)"' % re.escape(key), text)
    if match is None:
        raise AssertionError(f"{key} not found in pyproject.toml")
    return match.group(1)


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

    def test_parses_and_targets_the_lowest_supported_interpreter(self):
        self.assertEqual(_string_value(self.text, "target-version"), "py310")
        selected = _string_list(self.text, "select")
        self.assertEqual(len(selected), len(set(selected)))
        for rule in ("E9", "F63", "F7", "F82", "F401", "F841"):
            self.assertIn(rule, selected)
        if tomllib is not None:  # cross-check the hand reader against a real parser
            data = tomllib.loads(self.text)
            self.assertEqual(set(data), {"tool"})
            self.assertEqual(set(data["tool"]), {"ruff"})
            self.assertEqual(data["tool"]["ruff"]["target-version"], "py310")
            self.assertEqual(data["tool"]["ruff"]["lint"]["select"], selected)
            self.assertEqual(data["tool"]["ruff"]["extend-exclude"], _string_list(self.text, "extend-exclude"))

    def test_every_exclusion_exists_and_the_fixture_is_still_invalid(self):
        excluded = _string_list(self.text, "extend-exclude")
        for entry in excluded:
            with self.subTest(entry=entry):
                self.assertTrue((_REPO_ROOT / entry).exists(), f"excluded path does not exist: {entry}")
        fixture = _REPO_ROOT / "staging" / "orchestration" / "broken-syntax-tool" / "implementation.py"
        self.assertIn("staging/orchestration/broken-syntax-tool", excluded)
        with self.assertRaises(SyntaxError):
            compile(fixture.read_text(encoding="utf-8"), str(fixture), "exec")

    def test_source_banners_do_not_pin_an_interpreter_version(self):
        # The supported range is stated once, in QUICKSTART.md.
        offenders = []
        for folder in ("tooling", "tests", "examples", "benchmarks"):
            for path in sorted((_REPO_ROOT / folder).rglob("*.py")):
                head = path.read_text(encoding="utf-8-sig", errors="replace")[:600]
                if re.search(r"Pure Python 3\.\d+(?![\d+])", head):  # "3.10+" states a range
                    offenders.append(path.relative_to(_REPO_ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_launcher_and_battery_do_not_depend_on_the_linter(self):
        for name in ("jarvis.py", "run_tests.py"):
            with self.subTest(name=name):
                source = (_REPO_ROOT / name).read_text(encoding="utf-8")
                self.assertNotRegex(source, r"\bruff\b")


if __name__ == "__main__":
    unittest.main()
