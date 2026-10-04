import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from tooling.install_obsidian_plugins import (
    InstallError,
    PLUGIN_ID,
    RELEASE_API_URL,
    install_claudian,
)


class FakeResponse:
    def __init__(self, body: bytes, url: str):
        self._body = body
        self._url = url
        self.headers = {"Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self._url

    def read(self, size=-1):
        return self._body if size < 0 else self._body[:size]


class FakeOpener:
    def __init__(self, release, assets, redirect_host="release-assets.githubusercontent.com"):
        self.release = release
        self.assets = assets
        self.redirect_host = redirect_host
        self.urls = []

    def __call__(self, request, timeout):
        url = request.full_url
        self.urls.append(url)
        if url == RELEASE_API_URL:
            body = json.dumps(self.release).encode("utf-8")
            return FakeResponse(body, url)
        if url in self.assets:
            final_url = url.replace("github.com", self.redirect_host, 1)
            return FakeResponse(self.assets[url], final_url)
        raise AssertionError(f"Unexpected download URL: {url}")


def make_release(manifest_id=PLUGIN_ID, asset_host="github.com"):
    manifest = json.dumps(
        {"id": manifest_id, "name": "Claudian", "version": "2.3.11"}
    ).encode("utf-8")
    assets = {}
    release_assets = []
    for name, content in (("main.js", b"new-plugin"), ("manifest.json", manifest),
                          ("styles.css", b".claudian{}")):
        url = f"https://{asset_host}/YishenTu/claudian/releases/download/v2.3.11/{name}"
        digest = hashlib.sha256(content).hexdigest()
        release_assets.append({
            "name": name,
            "browser_download_url": url,
            "digest": f"sha256:{digest}",
        })
        assets[url] = content
    release = {"draft": False, "prerelease": False, "assets": release_assets}
    return release, assets


class InstallClaudianTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.obsidian = self.root / ".obsidian"
        self.plugins = self.obsidian / "plugins"
        self.target = self.plugins / PLUGIN_ID
        self.obsidian.mkdir()

    def test_installs_canonical_id_and_preserves_user_state(self):
        self.target.mkdir(parents=True)
        data_path = self.target / "data.json"
        data_path.write_text('{"private":"leave unchanged"}', encoding="utf-8")
        data_before = data_path.read_bytes()
        app_path = self.obsidian / "app.json"
        app_path.write_text('{"safeMode": true}', encoding="utf-8")
        app_before = app_path.read_bytes()
        community_path = self.obsidian / "community-plugins.json"
        community_path.write_text('["copilot"]', encoding="utf-8")
        release, assets = make_release()

        version = install_claudian(self.root, opener=FakeOpener(release, assets))

        self.assertEqual(version, "2.3.11")
        self.assertEqual((self.target / "main.js").read_bytes(), b"new-plugin")
        self.assertEqual(json.loads((self.target / "manifest.json").read_text())["id"], PLUGIN_ID)
        self.assertEqual(data_path.read_bytes(), data_before)
        self.assertEqual(app_path.read_bytes(), app_before)
        self.assertEqual(json.loads(community_path.read_text()), ["copilot", PLUGIN_ID])

    def test_rejects_manifest_id_mismatch_before_writing_plugin_files(self):
        release, assets = make_release(manifest_id="claudian")
        with self.assertRaisesRegex(InstallError, "manifest must identify"):
            install_claudian(self.root, opener=FakeOpener(release, assets))
        self.assertFalse(self.target.exists())
        self.assertFalse((self.obsidian / "community-plugins.json").exists())

    def test_rejects_untrusted_asset_host_before_download(self):
        release, assets = make_release(asset_host="example.invalid")
        opener = FakeOpener(release, assets)
        with self.assertRaisesRegex(InstallError, "untrusted"):
            install_claudian(self.root, opener=opener)
        self.assertEqual(opener.urls, [RELEASE_API_URL])
        self.assertFalse(self.target.exists())

    def test_rejects_untrusted_redirect_before_writing_any_plugin_files(self):
        release, assets = make_release()
        opener = FakeOpener(release, assets, redirect_host="example.invalid")
        with self.assertRaisesRegex(InstallError, "redirected.*outside"):
            install_claudian(self.root, opener=opener)
        self.assertFalse(self.target.exists())
        self.assertFalse((self.obsidian / "community-plugins.json").exists())

    def test_rejects_release_asset_digest_mismatch_before_writing_any_files(self):
        release, assets = make_release()
        release["assets"][0]["digest"] = f"sha256:{'0' * 64}"
        with self.assertRaisesRegex(InstallError, "does not match"):
            install_claudian(self.root, opener=FakeOpener(release, assets))
        self.assertFalse(self.target.exists())
        self.assertFalse((self.obsidian / "community-plugins.json").exists())

    def test_invalid_community_plugin_state_fails_before_network_access(self):
        community_path = self.obsidian / "community-plugins.json"
        community_path.write_text("{invalid", encoding="utf-8")
        release, assets = make_release()
        opener = FakeOpener(release, assets)
        with self.assertRaisesRegex(InstallError, "unreadable"):
            install_claudian(self.root, opener=opener)
        self.assertEqual(opener.urls, [])
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
