#!/usr/bin/env python3
"""Install the optional Claudian Obsidian plugin without changing vault safety settings."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable


REGISTRY_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_REPOSITORY = "YishenTu/claudian"
PLUGIN_ID = "realclaudian"
PLUGIN_NAME = "Claudian"
RELEASE_API_URL = f"https://api.github.com/repos/{PLUGIN_REPOSITORY}/releases/latest"
REQUIRED_ASSETS = ("main.js", "manifest.json")
OPTIONAL_ASSETS = ("styles.css",)
MAX_RELEASE_METADATA_BYTES = 2 * 1024 * 1024
MAX_PLUGIN_ASSET_BYTES = 32 * 1024 * 1024
ALLOWED_ASSET_HOSTS = {
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}
Opener = Callable[..., object]


class InstallError(RuntimeError):
    """A safe, actionable plugin installation failure."""


def _read_response(
    url: str,
    *,
    opener: Opener,
    max_bytes: int,
    allowed_initial_hosts: set[str],
    allowed_final_hosts: set[str],
) -> bytes:
    parsed_url = urllib.parse.urlparse(url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in allowed_initial_hosts
        or parsed_url.username
        or parsed_url.password
    ):
        raise InstallError("Refusing a download URL outside the HTTPS GitHub allowlist.")

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "JARVIS-Obsidian-Plugin-Installer",
        },
    )
    try:
        response = opener(request, timeout=30)
        with response:
            final_url = urllib.parse.urlparse(response.geturl())
            if final_url.scheme != "https" or final_url.hostname not in allowed_final_hosts:
                raise InstallError("GitHub redirected the download outside the HTTPS allowlist.")
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise InstallError("The remote file exceeds the configured size limit.")
            body = response.read(max_bytes + 1)
    except InstallError:
        raise
    except (OSError, urllib.error.URLError, ValueError) as exc:
        raise InstallError(f"Could not download the official Claudian release: {exc}") from exc

    if len(body) > max_bytes:
        raise InstallError("The remote file exceeds the configured size limit.")
    return body


def _fetch_release_assets(*, opener: Opener) -> dict[str, bytes]:
    metadata_bytes = _read_response(
        RELEASE_API_URL,
        opener=opener,
        max_bytes=MAX_RELEASE_METADATA_BYTES,
        allowed_initial_hosts={"api.github.com"},
        allowed_final_hosts={"api.github.com"},
    )
    try:
        release = json.loads(metadata_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallError("GitHub returned invalid release metadata.") from exc

    if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
        raise InstallError("GitHub did not return a stable Claudian release.")

    declared_assets = release.get("assets")
    if not isinstance(declared_assets, list):
        raise InstallError("The Claudian release does not contain a valid asset list.")

    by_name: dict[str, tuple[str, str]] = {}
    for asset in declared_assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        download_url = asset.get("browser_download_url")
        if name in REQUIRED_ASSETS + OPTIONAL_ASSETS and isinstance(download_url, str):
            if name in by_name:
                raise InstallError(f"The release contains duplicate {name} assets.")
            declared_digest = asset.get("digest")
            if (
                not isinstance(declared_digest, str)
                or not declared_digest.startswith("sha256:")
                or len(declared_digest) != 71
            ):
                raise InstallError(f"The release does not provide a valid SHA-256 digest for {name}.")
            try:
                expected_digest = declared_digest[7:].lower()
                if any(char not in "0123456789abcdef" for char in expected_digest):
                    raise ValueError("digest contains non-hexadecimal characters")
                bytes.fromhex(expected_digest)
            except ValueError as exc:
                raise InstallError(f"The release provides an invalid SHA-256 digest for {name}.") from exc
            asset_url = urllib.parse.urlparse(download_url)
            expected_prefix = f"/{PLUGIN_REPOSITORY}/releases/download/"
            if (
                asset_url.scheme != "https"
                or asset_url.hostname != "github.com"
                or not asset_url.path.startswith(expected_prefix)
                or asset_url.username
                or asset_url.password
            ):
                raise InstallError(f"The release contains an untrusted {name} asset URL.")
            by_name[name] = (download_url, expected_digest)

    missing = [name for name in REQUIRED_ASSETS if name not in by_name]
    if missing:
        raise InstallError(f"The Claudian release is missing required assets: {', '.join(missing)}.")

    result: dict[str, bytes] = {}
    for name, (url, expected_digest) in by_name.items():
        content = _read_response(
            url,
            opener=opener,
            max_bytes=MAX_PLUGIN_ASSET_BYTES,
            allowed_initial_hosts={"github.com"},
            allowed_final_hosts=ALLOWED_ASSET_HOSTS,
        )
        if hashlib.sha256(content).hexdigest() != expected_digest:
            raise InstallError(f"The downloaded {name} does not match GitHub's SHA-256 digest.")
        result[name] = content

    try:
        manifest = json.loads(result["manifest.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallError("The downloaded plugin manifest is invalid JSON.") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("id") != PLUGIN_ID
        or manifest.get("name") != PLUGIN_NAME
        or not isinstance(manifest.get("version"), str)
        or not manifest["version"].strip()
    ):
        raise InstallError(
            f"The downloaded manifest must identify {PLUGIN_NAME} as {PLUGIN_ID!r}."
        )
    return result


def _read_enabled_plugins(path: Path) -> list[str]:
    if not path.exists():
        return []
    if path.is_symlink():
        raise InstallError("Refusing to replace a linked community-plugins.json file.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallError("community-plugins.json is unreadable; it was left unchanged.") from exc
    if not isinstance(data, list) or any(not isinstance(item, str) for item in data):
        raise InstallError("community-plugins.json must contain a JSON array of plugin IDs.")
    return data


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except OSError as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise InstallError(f"Could not safely write {path.name}.") from exc


def install_claudian(vault_root: Path, *, opener: Opener | None = None) -> str:
    """Install only official Claudian release files and enable its canonical plugin ID."""
    root = Path(vault_root).expanduser().resolve()
    obsidian_dir = root / ".obsidian"
    plugins_dir = obsidian_dir / "plugins"
    target_dir = plugins_dir / PLUGIN_ID
    community_plugins_path = obsidian_dir / "community-plugins.json"

    if obsidian_dir.is_symlink() or plugins_dir.is_symlink() or target_dir.is_symlink():
        raise InstallError("Refusing to install through a linked Obsidian plugin directory.")
    if target_dir.exists() and not target_dir.is_dir():
        raise InstallError("The Claudian plugin target exists but is not a directory.")
    if community_plugins_path.is_symlink():
        raise InstallError("Refusing to replace a linked community-plugins.json file.")

    enabled_plugins = _read_enabled_plugins(community_plugins_path)
    open_url = opener or urllib.request.urlopen
    assets = _fetch_release_assets(opener=open_url)

    obsidian_dir.mkdir(parents=True, exist_ok=True)
    plugins_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    previous_assets: dict[str, bytes | None] = {}
    written_assets: list[str] = []
    try:
        for name, content in assets.items():
            destination = target_dir / name
            if destination.is_symlink():
                raise InstallError(f"Refusing to replace linked plugin asset {name}.")
            previous_assets[name] = destination.read_bytes() if destination.exists() else None
            _atomic_write(destination, content)
            written_assets.append(name)
    except Exception:
        for name in reversed(written_assets):
            destination = target_dir / name
            previous = previous_assets[name]
            if previous is None:
                destination.unlink(missing_ok=True)
            else:
                _atomic_write(destination, previous)
        raise

    if PLUGIN_ID not in enabled_plugins:
        enabled_plugins.append(PLUGIN_ID)
        encoded = (json.dumps(enabled_plugins, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        _atomic_write(community_plugins_path, encoded)

    manifest = json.loads(assets["manifest.json"].decode("utf-8"))
    return manifest["version"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the official Claudian Obsidian plugin without changing safe mode."
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=REGISTRY_ROOT,
        help="Vault root directory (defaults to this repository).",
    )
    args = parser.parse_args(argv)
    try:
        version = install_claudian(args.vault)
    except InstallError as exc:
        print(f"[ERROR] {exc}")
        return 1
    print(f"[OK] {PLUGIN_NAME} {version} installed and enabled as {PLUGIN_ID}.")
    print("Obsidian safe mode and existing plugin data were left unchanged; reload Obsidian to use it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
