"""Contract: junction detection does not depend on the interpreter version.

``Path.is_junction()`` is Python 3.12+.  The runtime used to guard the call
with ``hasattr``, which on Windows with Python 3.10/3.11 skipped the check and
let a directory junction pass a "no linked paths" confinement rule.
Pure Python Standard Library // Zero PIP Dependencies
"""

import ast
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic import path_links
from tooling.agentic.composite import ProgressiveDisclosureReader
from tooling.agentic.path_links import IO_REPARSE_TAG_MOUNT_POINT, is_junction, is_link

IO_REPARSE_TAG_SYMLINK = 0xA000000C
IO_REPARSE_TAG_CLOUD = 0x9000001A  # a OneDrive placeholder: a reparse point, not a link


def _lstat_with_tag(tag):
    def fake_lstat(path):
        return types.SimpleNamespace(st_mode=0o040755, st_file_attributes=0x410, st_reparse_tag=tag)

    return fake_lstat


class TestIsJunction(unittest.TestCase):
    def test_reads_the_reparse_tag_like_the_312_implementation(self):
        with mock.patch.object(path_links.os, "lstat", _lstat_with_tag(IO_REPARSE_TAG_MOUNT_POINT)):
            self.assertTrue(is_junction("C:/registry/skills/linked"))
        for tag in (0, IO_REPARSE_TAG_SYMLINK, IO_REPARSE_TAG_CLOUD):
            with self.subTest(tag=hex(tag)):
                with mock.patch.object(path_links.os, "lstat", _lstat_with_tag(tag)):
                    self.assertFalse(is_junction("C:/registry/skills/plain"))

    def test_value_matches_the_platform_constant_when_it_exists(self):
        import stat

        self.assertEqual(getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", IO_REPARSE_TAG_MOUNT_POINT), IO_REPARSE_TAG_MOUNT_POINT)

    def test_never_raises_and_is_false_for_ordinary_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(is_junction(tmp))
            self.assertFalse(is_junction(Path(tmp) / "missing"))
        self.assertFalse(is_junction("bad\x00path"))
        self.assertFalse(is_junction(None))
        with mock.patch.object(path_links.os, "lstat", side_effect=PermissionError("denied")):
            self.assertFalse(is_junction("anything"))

    def test_agrees_with_the_standard_library_where_it_exists(self):
        # os.path.isjunction is Python 3.12+; on older interpreters only our
        # own answer is asserted (no skip: the battery verdict must not depend
        # on the interpreter version).
        reference = getattr(os.path, "isjunction", None)
        with tempfile.TemporaryDirectory() as tmp:
            for candidate in (Path(tmp), Path(tmp) / "missing", Path(__file__)):
                answer = is_junction(candidate)
                self.assertIs(answer, False)
                if reference is not None:
                    self.assertEqual(answer, reference(candidate))

    def test_is_link_covers_symlinks_and_junctions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            link = Path(tmp) / "link"
            self.assertFalse(is_link(target))
            try:
                link.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                link = None  # symbolic links need a privilege on some Windows hosts
            if link is not None:
                self.assertTrue(is_link(link))
        with mock.patch.object(path_links.os, "lstat", _lstat_with_tag(IO_REPARSE_TAG_MOUNT_POINT)), \
                mock.patch.object(path_links.os.path, "islink", return_value=False):
            self.assertTrue(is_link("C:/registry/skills/linked"))


class TestConfinementRefusesJunctionsOnEveryVersion(unittest.TestCase):
    def test_skill_reader_refuses_a_junction_without_path_is_junction(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            (skills / "demo").mkdir(parents=True)
            (skills / "demo" / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            self.assertEqual(ProgressiveDisclosureReader._skill_path("demo", skills), skills.resolve() / "demo")

            real_lstat = os.lstat

            def junction_lstat(path, *args, **kwargs):
                if Path(path).name == "demo":
                    return types.SimpleNamespace(st_mode=0o040755, st_reparse_tag=IO_REPARSE_TAG_MOUNT_POINT)
                return real_lstat(path, *args, **kwargs)

            # The reader must refuse it from the reparse tag alone, whether or
            # not this interpreter has Path.is_junction (3.12+).
            with mock.patch.object(path_links.os, "lstat", junction_lstat):
                with self.assertRaises(ValueError):
                    ProgressiveDisclosureReader._skill_path("demo", skills)

    def test_runtime_no_longer_uses_the_version_dependent_guard(self):
        offenders = []
        for path in sorted((_REPO_ROOT / "tooling").rglob("*.py")):
            relative = path.relative_to(_REPO_ROOT).as_posix()
            if relative == "tooling/validate_repository_contracts.py":
                continue  # the validator names the pattern in order to detect it
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "is_junction":
                    offenders.append(f"{relative}:{node.lineno}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
