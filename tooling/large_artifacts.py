#!/usr/bin/env python3
"""Inventory, verify and restore the large optional artifacts of the registry.

Three tracked files account for most of the repository size.  None of them is
needed to start the runtime or to pass ``python jarvis.py --full-test``; the
manifest ``config/large-artifacts.json`` records what each one is, its size and
the sha256 of the recorded snapshot.

Commands::

    python tooling/large_artifacts.py status          # what is present / absent / changed
    python tooling/large_artifacts.py verify          # exit 1 if a static artifact is corrupt
    python tooling/large_artifacts.py record          # re-record size and sha256 of present files
    python tooling/large_artifacts.py fetch --base-url https://host/path

Scope and limits (stated so the tool is not overread):

- ``fetch`` has no default source.  Nothing in this repository publishes these
  files anywhere; an operator must name a location (``--base-url`` or
  ``JARVIS_LARGE_ARTIFACTS_BASE_URL``).  Without one the command refuses.
- A download is accepted only if its size and sha256 equal the manifest; the
  file is written next to its destination and moved into place only after the
  check, so a failed or tampered download never replaces anything.
- ``live`` artifacts are caches the runtime rewrites.  A different hash there
  means "changed since the snapshot was recorded", not corruption.
- This tool does not remove anything from Git and does not rewrite history.

Pure Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_RELATIVE = "config/large-artifacts.json"
BASE_URL_ENV = "JARVIS_LARGE_ARTIFACTS_BASE_URL"
SCHEMA_VERSION = "1.0.0"
KINDS = ("static", "live")
CHUNK = 1024 * 1024
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

STATE_MATCH = "PRESENT_MATCH"
STATE_CHANGED = "PRESENT_CHANGED"
STATE_ABSENT = "ABSENT"


class ArtifactError(Exception):
    """A manifest entry, a source or a download cannot be trusted."""


def _confined(root: Path, relative: str) -> Path:
    """Return ``root / relative`` or raise when it would leave ``root``."""
    if not isinstance(relative, str) or not relative.strip():
        raise ArtifactError("artifact path is empty")
    if "\\" in relative or "\x00" in relative:
        raise ArtifactError(f"artifact path must use forward slashes: {relative!r}")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or (pure.parts and ":" in pure.parts[0]):
        raise ArtifactError(f"artifact path must stay inside the repository: {relative!r}")
    target = (root / Path(*pure.parts)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ArtifactError(f"artifact path escapes the repository: {relative!r}") from exc
    return target


def load_manifest(root: Path = REPO_ROOT) -> Dict[str, Any]:
    path = root / MANIFEST_RELATIVE
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArtifactError(f"manifest not found: {MANIFEST_RELATIVE}") from exc
    except (OSError, ValueError) as exc:
        raise ArtifactError(f"manifest cannot be read: {exc}") from exc
    validate_manifest(manifest, root)
    return manifest


def validate_manifest(manifest: Any, root: Path = REPO_ROOT) -> None:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise ArtifactError(f"manifest schema_version must be {SCHEMA_VERSION}")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ArtifactError("manifest lists no artifacts")
    seen = set()
    for entry in artifacts:
        if not isinstance(entry, dict):
            raise ArtifactError("artifact entry must be an object")
        relative = entry.get("path")
        _confined(root, relative)
        if relative in seen:
            raise ArtifactError(f"duplicate artifact path: {relative}")
        seen.add(relative)
        if entry.get("kind") not in KINDS:
            raise ArtifactError(f"{relative}: kind must be one of {KINDS}")
        size = entry.get("bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ArtifactError(f"{relative}: bytes must be a non-negative integer")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ArtifactError(f"{relative}: sha256 must be 64 lowercase hex characters")
        if not isinstance(entry.get("purpose"), str) or not entry["purpose"].strip():
            raise ArtifactError(f"{relative}: purpose is required")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(entry: Dict[str, Any], root: Path = REPO_ROOT) -> Dict[str, Any]:
    target = _confined(root, entry["path"])
    result = {
        "path": entry["path"],
        "kind": entry["kind"],
        "recorded_bytes": entry["bytes"],
        "recorded_sha256": entry["sha256"],
    }
    if not target.is_file():
        result.update(state=STATE_ABSENT, actual_bytes=None, actual_sha256=None)
        return result
    actual_bytes = target.stat().st_size
    actual_sha256 = sha256_file(target)
    matches = actual_bytes == entry["bytes"] and actual_sha256 == entry["sha256"]
    result.update(
        state=STATE_MATCH if matches else STATE_CHANGED,
        actual_bytes=actual_bytes,
        actual_sha256=actual_sha256,
    )
    return result


def build_status(root: Path = REPO_ROOT, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    manifest = manifest if manifest is not None else load_manifest(root)
    items = [inspect(entry, root) for entry in manifest["artifacts"]]
    # Only a static artifact with different bytes is corruption.  A live cache
    # that differs was rewritten by the runtime; an absent file is optional.
    corrupt = [i["path"] for i in items if i["state"] == STATE_CHANGED and i["kind"] == "static"]
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest": MANIFEST_RELATIVE,
        "artifacts": items,
        "present": sum(1 for i in items if i["state"] != STATE_ABSENT),
        "absent": [i["path"] for i in items if i["state"] == STATE_ABSENT],
        "changed_live": [i["path"] for i in items if i["state"] == STATE_CHANGED and i["kind"] == "live"],
        "corrupt_static": corrupt,
        "status": "FAIL" if corrupt else "PASS",
    }


def record(root: Path = REPO_ROOT, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Re-record size and sha256 of every artifact that is present."""
    manifest = load_manifest(root)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated: List[str] = []
    for entry in manifest["artifacts"]:
        target = _confined(root, entry["path"])
        if not target.is_file():
            continue
        size, digest = target.stat().st_size, sha256_file(target)
        if size != entry["bytes"] or digest != entry["sha256"]:
            entry["bytes"], entry["sha256"], entry["recorded_utc"] = size, digest, stamp
            updated.append(entry["path"])
    if updated:
        _atomic_write_text(root / MANIFEST_RELATIVE, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return {"updated": updated}


def _atomic_write_text(path: Path, text: str) -> None:
    handle, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def validate_base_url(base_url: Optional[str]) -> str:
    value = (base_url or "").strip()
    if not value:
        raise ArtifactError(
            "no source configured: pass --base-url or set "
            f"{BASE_URL_ENV}. This repository does not publish these files anywhere by itself."
        )
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme == "https" and parsed.hostname:
        pass
    elif parsed.scheme == "http" and (parsed.hostname or "") in LOOPBACK_HOSTS:
        pass  # plain HTTP only to this machine
    else:
        raise ArtifactError("source must be an https:// URL (plain http:// is accepted only for loopback)")
    if parsed.username or parsed.password:
        raise ArtifactError("source URL must not embed credentials")
    if parsed.query or parsed.fragment:
        raise ArtifactError("source URL must not carry a query string or fragment")
    return value.rstrip("/")


class _NoRedirectToOtherScheme(urllib.request.HTTPRedirectHandler):
    """Follow redirects only to https (or loopback http), never to other schemes."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401, PLR0913
        parsed = urllib.parse.urlsplit(newurl)
        allowed = parsed.scheme == "https" or (
            parsed.scheme == "http" and (parsed.hostname or "") in LOOPBACK_HOSTS
        )
        if not allowed:
            raise ArtifactError(f"refusing redirect to {parsed.scheme}://{parsed.hostname}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_one(
    entry: Dict[str, Any],
    base_url: str,
    root: Path = REPO_ROOT,
    *,
    force: bool = False,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """Download one artifact; keep it only when size and sha256 match."""
    target = _confined(root, entry["path"])
    if target.exists() and not force:
        return {"path": entry["path"], "result": "SKIPPED_EXISTS"}
    url = f"{base_url}/{urllib.parse.quote(PurePosixPath(entry['path']).name)}"
    opener = urllib.request.build_opener(_NoRedirectToOtherScheme())
    request = urllib.request.Request(url, headers={"User-Agent": "jarvis-large-artifacts/1"})
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".download", dir=str(target.parent))
    digest = hashlib.sha256()
    received = 0
    try:
        with os.fdopen(handle, "wb") as stream:
            try:
                with opener.open(request, timeout=timeout) as response:
                    while True:
                        block = response.read(CHUNK)
                        if not block:
                            break
                        received += len(block)
                        if received > entry["bytes"]:
                            raise ArtifactError(
                                f"{entry['path']}: source sent more than the recorded {entry['bytes']} bytes"
                            )
                        digest.update(block)
                        stream.write(block)
            except urllib.error.URLError as exc:
                raise ArtifactError(f"{entry['path']}: download failed: {exc}") from exc
        if received != entry["bytes"]:
            raise ArtifactError(f"{entry['path']}: received {received} bytes, manifest records {entry['bytes']}")
        if digest.hexdigest() != entry["sha256"]:
            raise ArtifactError(f"{entry['path']}: sha256 mismatch; the download was discarded")
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return {"path": entry["path"], "result": "FETCHED", "bytes": received}


def fetch(
    base_url: Optional[str],
    root: Path = REPO_ROOT,
    *,
    only: Optional[Iterable[str]] = None,
    force: bool = False,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    source = validate_base_url(base_url if base_url is not None else os.environ.get(BASE_URL_ENV))
    manifest = load_manifest(root)
    wanted = set(only or [])
    known = {entry["path"] for entry in manifest["artifacts"]}
    unknown = sorted(wanted - known)
    if unknown:
        raise ArtifactError(f"not in the manifest: {', '.join(unknown)}")
    results, failures = [], []
    for entry in manifest["artifacts"]:
        if wanted and entry["path"] not in wanted:
            continue
        try:
            results.append(fetch_one(entry, source, root, force=force, timeout=timeout))
        except ArtifactError as exc:
            failures.append(str(exc))
            results.append({"path": entry["path"], "result": "FAILED", "error": str(exc)})
    return {"results": results, "failures": failures, "status": "FAIL" if failures else "PASS"}


def _human(size: Optional[int]) -> str:
    return "-" if size is None else f"{size / (1024 * 1024):.1f} MiB"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", nargs="?", default="status", choices=("status", "verify", "record", "fetch"))
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root (default: this checkout)")
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    parser.add_argument("--require-all", action="store_true", help="verify: also fail when an artifact is absent")
    parser.add_argument("--base-url", default=None, help=f"fetch: source location (or {BASE_URL_ENV})")
    parser.add_argument("--only", action="append", default=[], help="fetch: artifact path (repeatable)")
    parser.add_argument("--force", action="store_true", help="fetch: replace a file that already exists")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command in ("status", "verify"):
            report = build_status(root)
            failed = report["status"] == "FAIL" or (
                args.command == "verify" and args.require_all and bool(report["absent"])
            )
            if args.json:
                print(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                for item in report["artifacts"]:
                    note = ""
                    if item["state"] == STATE_CHANGED:
                        note = "  (rewritten since the snapshot)" if item["kind"] == "live" else "  (CORRUPT)"
                    print(
                        f"{item['state']:16} {item['kind']:6} {_human(item['recorded_bytes']):>10}  {item['path']}{note}"
                    )
                print(f"STATUS: {'FAIL' if failed else 'PASS'}")
            return 1 if failed else 0
        if args.command == "record":
            outcome = record(root)
            print(json.dumps(outcome, indent=2, ensure_ascii=False) if args.json else f"updated: {outcome['updated'] or 'nothing'}")
            return 0
        outcome = fetch(args.base_url, root, only=args.only, force=args.force)
        if args.json:
            print(json.dumps(outcome, indent=2, ensure_ascii=False))
        else:
            for item in outcome["results"]:
                print(f"{item['result']:15} {item['path']}" + (f"  {item['error']}" if item.get("error") else ""))
            print(f"STATUS: {outcome['status']}")
        return 1 if outcome["failures"] else 0
    except ArtifactError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
