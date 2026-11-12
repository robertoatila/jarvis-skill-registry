"""Contract: recorded release checksums are reproducible from the repository.

``releases/*/checksums.sha256`` was recorded over the bytes of a working tree.
For most v1.x artifacts those bytes had CRLF line endings, while Git stores the
files with LF.  ``.gitattributes`` pins the line ending of exactly those files
so the recorded checksum can be reproduced on any platform; this test proves
each pin against the recorded value and keeps the file from growing a global
rule that would silently change other hash-verified content.
Pure Python Standard Library // Zero PIP Dependencies
"""

import fnmatch
import hashlib
import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
ATTRIBUTES = _REPO_ROOT / ".gitattributes"

CHECKSUM_LINE = re.compile(r"^([0-9a-fA-F]{64})\s+\*?(.+)$")


def _rules():
    rules = []
    for raw in ATTRIBUTES.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pattern, *attributes = line.split()
        rules.append((pattern, attributes))
    return rules


def _declared_eol(relative: str):
    """Line ending the last matching rule pins for ``relative`` (or None)."""
    declared = None
    for pattern, attributes in _rules():
        if "/" in pattern:
            matched = fnmatch.fnmatchcase(relative, pattern.replace("**/", "*"))
        else:
            matched = fnmatch.fnmatchcase(relative.rsplit("/", 1)[-1], pattern)
        if not matched:
            continue
        for attribute in attributes:
            if attribute.startswith("eol="):
                declared = attribute[len("eol="):]
            elif attribute in ("binary", "-text"):
                declared = None
    return declared


def _bytes_as_checked_out(relative: str) -> bytes:
    """Bytes Git writes for ``relative`` under the declared attributes."""
    data = (_REPO_ROOT / relative).read_bytes()
    eol = _declared_eol(relative)
    if eol is None:
        return data
    normalized = data.replace(b"\r\n", b"\n")
    return normalized.replace(b"\n", b"\r\n") if eol == "crlf" else normalized


def _recorded(release: str):
    entries = []
    folder = _REPO_ROOT / "releases" / release
    for line in (folder / "checksums.sha256").read_text(encoding="utf-8-sig").splitlines():
        match = CHECKSUM_LINE.match(line.strip())
        if not match:
            continue
        name = match.group(2).strip().replace("\\", "/")
        for candidate in (name, f"releases/{release}/{name}"):
            if (_REPO_ROOT / candidate).is_file():
                entries.append((candidate, match.group(1).lower()))
                break
    return entries


class TestGitAttributesStayNarrow(unittest.TestCase):
    def test_no_global_text_rule(self):
        for pattern, attributes in _rules():
            with self.subTest(pattern=pattern):
                if pattern in ("*", "**", "*.*"):
                    self.fail("a global rule would change how hash-verified files are checked out")
                if not any(a.startswith("eol=") for a in attributes):
                    self.assertEqual(attributes, ["binary"], f"{pattern}: only binary or an eol pin is allowed")

    def test_every_eol_pin_names_existing_files(self):
        tracked = [p.relative_to(_REPO_ROOT).as_posix() for p in _REPO_ROOT.rglob("*") if p.is_file() and ".git/" not in p.as_posix()]
        for pattern, attributes in _rules():
            if not any(a.startswith("eol=") for a in attributes):
                continue
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    any(fnmatch.fnmatchcase(path, pattern.replace("**/", "*")) for path in tracked),
                    f"pattern matches no file: {pattern}",
                )

    def test_large_binary_types_are_declared_binary(self):
        declared = {pattern for pattern, attributes in _rules() if attributes == ["binary"]}
        for pattern in ("*.mp4", "*.jpg", "*.png", "*.pdf", "*.sqlite"):
            self.assertIn(pattern, declared)


class TestRecordedChecksumsAreReproducible(unittest.TestCase):
    def test_v110_bundle_reproduces_completely(self):
        entries = _recorded("v1.1.0")
        self.assertEqual(len(entries), 7)
        for relative, recorded in entries:
            with self.subTest(relative=relative):
                self.assertEqual(_declared_eol(relative), "crlf")
                self.assertEqual(hashlib.sha256(_bytes_as_checked_out(relative)).hexdigest(), recorded)

    def test_every_pinned_file_reproduces_its_recorded_checksum(self):
        checked = 0
        for release in ("v1.0.0", "v1.1.0", "v2.0.0"):
            for relative, recorded in _recorded(release):
                if _declared_eol(relative) is None:
                    continue
                checked += 1
                with self.subTest(release=release, relative=relative):
                    self.assertEqual(hashlib.sha256(_bytes_as_checked_out(relative)).hexdigest(), recorded)
        self.assertGreaterEqual(checked, 20)

    def test_a_pin_is_needed_only_where_the_line_ending_decides_the_checksum(self):
        """No pinned file would also verify with the other line ending."""
        for release in ("v1.0.0", "v1.1.0", "v2.0.0"):
            for relative, recorded in _recorded(release):
                eol = _declared_eol(relative)
                if eol is None:
                    continue
                lf = (_REPO_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
                other = lf if eol == "crlf" else lf.replace(b"\n", b"\r\n")
                with self.subTest(relative=relative):
                    self.assertNotEqual(hashlib.sha256(other).hexdigest(), recorded)


if __name__ == "__main__":
    unittest.main()
