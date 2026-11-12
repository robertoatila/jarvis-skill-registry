"""Contract: locations outside the checkout are resolved in one place.

``tooling/agentic/config.py`` owns every path that is not inside the registry;
no tooling module builds a ``Path`` from a drive-letter literal of its own.
Pure Python Standard Library // Zero PIP Dependencies
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic import config

DRIVE_LITERAL = re.compile(r"^[A-Za-z]:[\\/]")

# The only place allowed to name a drive: the documented legacy default.
ALLOWED_DRIVE_LITERALS = {
    ("tooling/agentic/config.py", config.LEGACY_WINDOWS_ARSENAL_HOME),
}


class TestExternalArsenalResolution(unittest.TestCase):
    def test_environment_variable_wins_on_every_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {config.ARSENAL_HOME_ENV: tmp}
            for windows in (True, False):
                with self.subTest(windows=windows):
                    self.assertEqual(config.external_arsenal_home(env, windows=windows), Path(tmp))
                    self.assertEqual(
                        config.external_arsenal_db_path(env, windows=windows),
                        Path(tmp) / "data" / "arsenal_library.sqlite",
                    )
                    self.assertEqual(
                        config.external_rf_model_path(env, windows=windows),
                        Path(tmp) / "models" / "random_forest_model.json",
                    )

    def test_blank_value_is_treated_as_unset(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                self.assertEqual(
                    config.external_arsenal_home({config.ARSENAL_HOME_ENV: value}, windows=False),
                    Path.home() / config.DEFAULT_POSIX_ARSENAL_DIRNAME,
                )

    def test_defaults_keep_the_legacy_location_only_on_windows(self):
        self.assertEqual(
            config.external_arsenal_home({}, windows=True), Path(config.LEGACY_WINDOWS_ARSENAL_HOME)
        )
        posix_default = config.external_arsenal_home({}, windows=False)
        self.assertEqual(posix_default, Path.home() / ".jarvis-arsenal")
        self.assertNotIn("jarvis-arsenal/data", posix_default.as_posix())

    def test_mirror_is_written_only_when_named_or_already_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "not-created"
            self.assertTrue(config.external_arsenal_mirror_enabled({config.ARSENAL_HOME_ENV: str(missing)}))
            self.assertFalse(missing.exists(), "resolving a location must not create it")
        # No setting and no existing directory: nothing may be written.
        with tempfile.TemporaryDirectory() as fake_home:
            with mock.patch.dict(os.environ, {"HOME": fake_home, "USERPROFILE": fake_home}):
                self.assertEqual(Path.home(), Path(fake_home))
                self.assertFalse(config.external_arsenal_mirror_enabled({}, windows=False))
                (Path(fake_home) / config.DEFAULT_POSIX_ARSENAL_DIRNAME).mkdir()
                self.assertTrue(config.external_arsenal_mirror_enabled({}, windows=False))

    def test_gemini_root_honours_the_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(config.gemini_root({config.GEMINI_ROOT_ENV: tmp}), Path(tmp))
        self.assertEqual(config.gemini_root({}), Path.home() / ".gemini")


class TestNoModuleCarriesItsOwnDrivePath(unittest.TestCase):
    def test_no_path_is_built_from_a_drive_letter_literal(self):
        offenders = []
        for path in sorted((_REPO_ROOT / "tooling").rglob("*.py")):
            relative = path.relative_to(_REPO_ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                literals = []
                if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in {
                    "Path",
                    "PureWindowsPath",
                    "WindowsPath",
                }:
                    literals = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    literals = [node.value.value]
                for literal in literals:
                    if DRIVE_LITERAL.match(literal) and (relative, literal) not in ALLOWED_DRIVE_LITERALS:
                        offenders.append(f"{relative}:{node.lineno}: {literal}")
        self.assertEqual(offenders, [])

    def test_consumers_resolve_the_same_external_database(self):
        code = (
            "import sys, json; sys.path.insert(0, sys.argv[1]);"
            "from tooling.agentic import omni_recall; from tooling import repo_to_skill, jarvis_mcp_server;"
            "print('RESULT=' + json.dumps([str(omni_recall.DB_PATH_PRIMARY), str(repo_to_skill.D_DB_PATH),"
            " str(jarvis_mcp_server.D_DB_FILE), str(omni_recall.REGISTRY_ROOT), str(jarvis_mcp_server.GEMINI_ROOT)]))"
        )
        with tempfile.TemporaryDirectory() as tmp:
            arsenal = Path(tmp) / "arsenal"
            gemini = Path(tmp) / "gemini"
            env = dict(os.environ)
            env.pop("JARVIS_REGISTRY_ROOT", None)
            env[config.ARSENAL_HOME_ENV] = str(arsenal)
            env[config.GEMINI_ROOT_ENV] = str(gemini)
            completed = subprocess.run(
                [sys.executable, "-c", code, str(_REPO_ROOT)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr[-600:])
            line = next(l for l in completed.stdout.splitlines() if l.startswith("RESULT="))
            primary, repo_db, mcp_db, registry_root, gemini_root = json.loads(line[len("RESULT="):])
            expected = str(arsenal / "data" / "arsenal_library.sqlite")
            self.assertEqual({primary, repo_db, mcp_db}, {expected})
            self.assertEqual(Path(registry_root), _REPO_ROOT.resolve())
            self.assertEqual(Path(gemini_root), gemini.resolve())
            self.assertFalse(arsenal.exists(), "importing consumers must not create the external location")


class TestAgentPromptsAndLauncher(unittest.TestCase):
    """Agent prompts and the desktop launcher carry no workstation facts."""

    def test_agent_prompts_name_no_drive_letter(self):
        offenders = []
        for path in sorted((_REPO_ROOT / "agents").glob("*.md")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"\b[A-Za-z]:\\", line):
                    offenders.append(f"{path.name}:{number}")
        self.assertEqual(offenders, [])

    def test_generator_still_reproduces_the_tracked_agents(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_build_ultimate_arsenal_probe", _REPO_ROOT / "tooling" / "build_ultimate_arsenal.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertGreater(len(module.SOVEREIGN_AGENTS), 0)
        for agent in module.SOVEREIGN_AGENTS:
            tools_yaml = "\n".join(f"  - {tool}" for tool in agent["tools"])
            expected = (
                f"---\nname: {agent['name']}\ndescription: \"{agent['description']}\"\ntools:\n{tools_yaml}\n"
                f"mainAgent: true\nsubagent: true\ncommandExecutionPolicy: auto\n---\n\n{agent['body'].strip()}\n"
            )
            tracked = (_REPO_ROOT / "agents" / f"{agent['name']}.md").read_bytes().decode("utf-8").replace("\r\n", "\n")
            with self.subTest(agent=agent["name"]):
                self.assertEqual(tracked, expected)

    def test_desktop_panel_measures_instead_of_remembering(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_jarvis_desktop_probe", _REPO_ROOT / "tooling" / "jarvis_desktop.py")
        desktop = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(desktop)
        source = (_REPO_ROOT / "tooling" / "jarvis_desktop.py").read_text(encoding="utf-8")
        self.assertNotIn("144 ATIVAS", source)
        self.assertNotIn("2.168", source)

        with tempfile.TemporaryDirectory() as tmp:
            for name in ("a", "b", "c"):
                (Path(tmp) / "skills" / name).mkdir(parents=True)
                (Path(tmp) / "skills" / name / "SKILL.md").write_text("x", encoding="utf-8")
            (Path(tmp) / "skills" / "empty").mkdir()
            # Port 9 (discard) is not served: the panel must say so, not guess.
            offline = dict(desktop.measure_panel_stats(Path(tmp), url="http://127.0.0.1:9", timeout=0.5))
            self.assertEqual(offline["ARSENAL DE SKILLS"], "3 NO DISCO")
            self.assertEqual(offline["REPOSITÓRIOS GITHUB"], "N/D (SERVIDOR OFFLINE)")

            class _Response:
                def __init__(self, payload):
                    self._payload = payload

                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

                def read(self):
                    return json.dumps(self._payload).encode("utf-8")

            for payload, expected in (
                ({"total_tools": 74653, "catalog_available": True}, "74.653 INDEXADOS"),
                ({"total_tools": 0, "catalog_available": False}, "CATÁLOGO AUSENTE"),
                ({"status": "SQLITE_READY"}, "N/D"),
            ):
                with self.subTest(payload=payload):
                    with mock.patch.object(desktop.urllib.request, "urlopen", return_value=_Response(payload)):
                        online = dict(desktop.measure_panel_stats(Path(tmp)))
                    self.assertEqual(online["REPOSITÓRIOS GITHUB"], expected)


if __name__ == "__main__":
    unittest.main()
