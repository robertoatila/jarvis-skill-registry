"""Contract: large optional artifacts are inventoried and restored fail-closed.

Covers ``tooling/large_artifacts.py`` and ``config/large-artifacts.json``.
Downloads are exercised against a loopback HTTP server started by the test.
Pure Python Standard Library // Zero PIP Dependencies
"""

import hashlib
import io
import json
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling import large_artifacts as la

GOOD = b"catalog-bytes\n" * 300
MEDIA = bytes(range(256)) * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _Handler(BaseHTTPRequestHandler):
    payloads = {}
    requested = []

    def do_GET(self):  # noqa: N802
        type(self).requested.append(self.path)
        body = type(self).payloads.get(self.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class LargeArtifactsCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "config").mkdir()
        self.entries = [
            {"path": "cache/catalog.json", "kind": "live", "bytes": len(GOOD), "sha256": _sha(GOOD), "purpose": "cache"},
            {"path": "docs/assets/clip.mp4", "kind": "static", "bytes": len(MEDIA), "sha256": _sha(MEDIA), "purpose": "media"},
        ]
        self._write_manifest(self.entries)

    def _write_manifest(self, entries):
        (self.root / la.MANIFEST_RELATIVE).write_text(
            json.dumps({"schema_version": la.SCHEMA_VERSION, "artifacts": entries}), encoding="utf-8"
        )

    def _place(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def _serve(self, payloads):
        _Handler.payloads = payloads
        _Handler.requested = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_address[1]}/assets"


class TestStatus(LargeArtifactsCase):
    def test_absent_artifacts_are_optional(self):
        report = la.build_status(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["present"], 0)
        self.assertEqual(sorted(report["absent"]), ["cache/catalog.json", "docs/assets/clip.mp4"])

    def test_changed_live_cache_is_not_corruption_but_changed_static_is(self):
        self._place("cache/catalog.json", GOOD + b"rewritten by a sync\n")
        self._place("docs/assets/clip.mp4", MEDIA)
        report = la.build_status(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["changed_live"], ["cache/catalog.json"])
        self.assertEqual(report["corrupt_static"], [])

        self._place("docs/assets/clip.mp4", MEDIA[:-1] + b"\x00")
        report = la.build_status(self.root)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["corrupt_static"], ["docs/assets/clip.mp4"])

    def test_record_updates_only_what_changed(self):
        self._place("cache/catalog.json", GOOD + b"more\n")
        outcome = la.record(self.root)
        self.assertEqual(outcome["updated"], ["cache/catalog.json"])
        manifest = la.load_manifest(self.root)
        self.assertEqual(manifest["artifacts"][0]["sha256"], _sha(GOOD + b"more\n"))
        self.assertEqual(manifest["artifacts"][1]["sha256"], _sha(MEDIA))
        self.assertEqual(la.record(self.root)["updated"], [])

    def test_manifest_entries_cannot_point_outside_the_repository(self):
        for bad in ("../outside.bin", "/etc/passwd", "a/../../b", "C:/Windows/x", "sub\\file", ""):
            with self.subTest(path=bad):
                self._write_manifest([dict(self.entries[0], path=bad)])
                with self.assertRaises(la.ArtifactError):
                    la.load_manifest(self.root)

    def test_malformed_entries_are_refused(self):
        for patch in ({"kind": "other"}, {"bytes": -1}, {"bytes": True}, {"sha256": "ABC"}, {"sha256": "z" * 64}, {"purpose": " "}):
            with self.subTest(patch=patch):
                self._write_manifest([dict(self.entries[0], **patch)])
                with self.assertRaises(la.ArtifactError):
                    la.load_manifest(self.root)
        self._write_manifest([self.entries[0], dict(self.entries[0])])
        with self.assertRaises(la.ArtifactError):
            la.load_manifest(self.root)


class TestFetch(LargeArtifactsCase):
    def test_no_source_means_no_download(self):
        with self.assertRaises(la.ArtifactError) as raised:
            la.fetch("", self.root)
        self.assertIn("no source configured", str(raised.exception))

    def test_source_must_be_https_or_loopback_and_carry_no_secret(self):
        for bad in (
            "http://example.com/assets",
            "ftp://example.com/assets",
            "file:///tmp/assets",
            "https://user:secret@example.com/assets",
            "https://example.com/assets?token=abc",
            "https://example.com/assets#frag",
            "example.com/assets",
        ):
            with self.subTest(url=bad):
                with self.assertRaises(la.ArtifactError):
                    la.validate_base_url(bad)
        self.assertEqual(la.validate_base_url("https://example.com/assets/"), "https://example.com/assets")
        self.assertEqual(la.validate_base_url("http://127.0.0.1:9/a"), "http://127.0.0.1:9/a")

    def test_matching_download_is_installed(self):
        base = self._serve({"/assets/catalog.json": GOOD, "/assets/clip.mp4": MEDIA})
        outcome = la.fetch(base, self.root)
        self.assertEqual(outcome["status"], "PASS")
        self.assertEqual([r["result"] for r in outcome["results"]], ["FETCHED", "FETCHED"])
        self.assertEqual((self.root / "cache/catalog.json").read_bytes(), GOOD)
        self.assertEqual((self.root / "docs/assets/clip.mp4").read_bytes(), MEDIA)
        self.assertEqual(la.build_status(self.root)["present"], 2)
        self.assertEqual(list((self.root / "cache").glob("*.download")), [])

    def test_tampered_short_or_oversized_download_is_discarded(self):
        cases = {
            "tampered": GOOD[:-1] + b"X",
            "short": GOOD[:-10],
            "oversized": GOOD + b"extra",
        }
        for name, body in cases.items():
            with self.subTest(case=name):
                base = self._serve({"/assets/catalog.json": body})
                outcome = la.fetch(base, self.root, only=["cache/catalog.json"])
                self.assertEqual(outcome["status"], "FAIL")
                self.assertEqual(outcome["results"][0]["result"], "FAILED")
                self.assertFalse((self.root / "cache/catalog.json").exists())
                self.assertEqual(list((self.root / "cache").glob("*")), [])

    def test_failed_download_never_replaces_an_existing_file(self):
        existing = self._place("cache/catalog.json", b"local copy\n")
        base = self._serve({"/assets/catalog.json": GOOD[:-1] + b"X"})
        skipped = la.fetch(base, self.root, only=["cache/catalog.json"])
        self.assertEqual(skipped["results"][0]["result"], "SKIPPED_EXISTS")
        self.assertEqual(_Handler.requested, [])
        forced = la.fetch(base, self.root, only=["cache/catalog.json"], force=True)
        self.assertEqual(forced["status"], "FAIL")
        self.assertEqual(existing.read_bytes(), b"local copy\n")

    def test_missing_remote_file_and_unknown_selection_are_reported(self):
        base = self._serve({})
        outcome = la.fetch(base, self.root, only=["docs/assets/clip.mp4"])
        self.assertEqual(outcome["status"], "FAIL")
        with self.assertRaises(la.ArtifactError):
            la.fetch(base, self.root, only=["not/in/manifest.bin"])

    def test_redirect_to_a_plain_http_host_is_refused(self):
        handler = la._NoRedirectToOtherScheme()
        with self.assertRaises(la.ArtifactError):
            handler.redirect_request(None, None, 302, "Found", {}, "http://example.com/clip.mp4")
        with self.assertRaises(la.ArtifactError):
            handler.redirect_request(None, None, 302, "Found", {}, "file:///etc/passwd")


class TestCommandLine(LargeArtifactsCase):
    def _run(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = la.main(["--root", str(self.root), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self._run("status")[0], 0)
        self.assertEqual(self._run("verify")[0], 0)
        self.assertEqual(self._run("verify", "--require-all")[0], 1)
        code, _, err = self._run("fetch")
        self.assertEqual(code, 2)
        self.assertIn("no source configured", err)
        self._place("docs/assets/clip.mp4", b"corrupt")
        code, out, _ = self._run("verify")
        self.assertEqual(code, 1)
        self.assertIn("CORRUPT", out)
        code, out, _ = self._run("status", "--json")
        self.assertEqual(json.loads(out)["corrupt_static"], ["docs/assets/clip.mp4"])


class TestRepositoryManifest(unittest.TestCase):
    def test_tracked_manifest_is_valid_and_names_documented_artifacts(self):
        manifest = la.load_manifest(_REPO_ROOT)
        paths = [entry["path"] for entry in manifest["artifacts"]]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertIn("cache/starred_catalog.json", paths)
        for entry in manifest["artifacts"]:
            with self.subTest(path=entry["path"]):
                self.assertGreater(entry["bytes"], 10 * 1024 * 1024, "the manifest is for large artifacts only")

    def test_present_static_artifacts_match_and_absence_is_tolerated(self):
        # Live caches may legitimately differ after a sync; only static content is asserted.
        report = la.build_status(_REPO_ROOT)
        self.assertEqual(report["corrupt_static"], [])
        self.assertEqual(report["status"], "PASS")


class TestServerWithoutCatalog(unittest.TestCase):
    """The local server answers honestly when the catalog file is absent."""

    def test_arsenal_payloads_say_the_catalog_is_missing(self):
        from unittest import mock

        from tooling import jarvis_server

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "starred_catalog.json"
            absent_db = Path(tmp) / "absent.sqlite"
            with mock.patch.object(jarvis_server, "STARRED_CATALOG_PATH", missing), \
                    mock.patch.object(jarvis_server, "ARSENAL_DB_PATH", absent_db), \
                    mock.patch.object(jarvis_server, "D_ARSENAL_DB_PATH", absent_db), \
                    mock.patch.object(jarvis_server, "STARRED_CACHE", [{"name": "stale/entry"}]), \
                    redirect_stderr(io.StringIO()) as warning:
                jarvis_server.load_starred_catalog()
                self.assertEqual(jarvis_server.STARRED_CACHE, [])
                stats = jarvis_server._build_arsenal_stats_payload()
                search = jarvis_server._search_arsenal_tools("agent", "ALL", 5)
            self.assertIn("large_artifacts.py", warning.getvalue())
        self.assertEqual(stats["status"], "MEMORY_FALLBACK")
        self.assertIs(stats["catalog_available"], False)
        self.assertEqual(stats["total_tools"], 0)
        self.assertIs(search["catalog_available"], False)
        self.assertEqual(search["tools"], [])


if __name__ == "__main__":
    unittest.main()
