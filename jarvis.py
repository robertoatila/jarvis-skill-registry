#!/usr/bin/env python3
"""Zero-dependency launcher for the local J.A.R.V.I.S. runtime.

The launcher intentionally stays thin: it validates the checkout, delegates to
the established server or resident-host assembly and never hides runtime failures.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "tooling" / "jarvis_server.py"
TEST_RUNNER = ROOT / "run_tests.py"
UI_DIR = ROOT / "ui"


def build_server_command(port: int, remote: bool = False) -> list[str]:
    """Return the exact legacy command used to launch the local server."""
    cmd = [sys.executable, str(SERVER), "--port", str(port)]
    if remote:
        cmd.append("--remote")
    return cmd


def build_host_server_command(port: int, remote: bool = False) -> list[str]:
    """Return the resident-host command without changing the legacy path."""
    cmd = [sys.executable, "-m", "tooling.remote_host", "--port", str(port)]
    if remote:
        cmd.append("--remote")
    return cmd


def doctor(stream: TextIO = sys.stdout) -> int:
    """Validate the minimum local prerequisites without making network calls."""
    checks = [
        (sys.version_info >= (3, 10), f"Python >= 3.10 ({sys.version.split()[0]})"),
        (SERVER.is_file(), "tooling/jarvis_server.py"),
        (TEST_RUNNER.is_file(), "run_tests.py"),
        (UI_DIR.is_dir(), "ui/"),
        ((ROOT / ".env.example").is_file(), ".env.example"),
    ]

    stream.write("J.A.R.V.I.S. doctor\n")
    failed = False
    for ok, label in checks:
        stream.write(f"  {'PASS' if ok else 'FAIL'}  {label}\n")
        failed = failed or not ok

    if failed:
        stream.write("Doctor failed. Restore the missing checkout files before launching.\n")
        return 1

    stream.write("Doctor passed. The local runtime can be launched.\n")
    return 0


def _open_browser_later(url: str) -> None:
    def open_url() -> None:
        try:
            webbrowser.open(url)
        except Exception:
            # Browser opening is convenience only; the server remains authoritative.
            pass

    timer = threading.Timer(1.0, open_url)
    timer.daemon = True
    timer.start()


def serve(port: int, open_browser: bool = True, remote: bool = False) -> int:
    """Run the existing server in the foreground and propagate its exit code."""
    if doctor() != 0:
        return 1

    url = f"http://127.0.0.1:{port}"
    print(f"\nJ.A.R.V.I.S. local HUD: {url}")
    print("Press Ctrl+C to stop. Provider-backed inference still requires explicit configuration/authorization.\n")
    if open_browser:
        _open_browser_later(url)

    try:
        return subprocess.call(build_server_command(port, remote=remote), cwd=ROOT)
    except KeyboardInterrupt:
        return 130


def host(port: int, remote: bool = False) -> int:
    """Run the resident host assembly in the foreground without opening a browser."""
    if doctor() != 0:
        return 1
    print(f"\nJ.A.R.V.I.S. resident host: 127.0.0.1:{port}")
    print("Host state is persisted and checked for process liveness. Press Ctrl+C to stop.\n")
    try:
        return subprocess.call(build_host_server_command(port, remote=remote), cwd=ROOT)
    except KeyboardInterrupt:
        return 130


def server_self_test() -> int:
    """Run the server's built-in self-test without starting the HTTP service."""
    return subprocess.call([sys.executable, str(SERVER), "--test"], cwd=ROOT)


def full_test() -> int:
    """Run the repository's portable Python master battery."""
    return subprocess.call([sys.executable, str(TEST_RUNNER)], cwd=ROOT)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch or validate the local J.A.R.V.I.S. cognitive runtime."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("host",),
        help="Optional resident runtime command",
    )
    parser.add_argument("--port", type=int, default=8899, help="HUD port (default: 8899)")
    parser.add_argument("--remote", action="store_true", help="Enable remote mobile companion access over LAN/Wi-Fi with QR code and token auth")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the HUD in a browser")
    parser.add_argument("--doctor", action="store_true", help="Check local prerequisites and exit")
    parser.add_argument("--test", action="store_true", help="Run the server self-test and exit")
    parser.add_argument("--full-test", action="store_true", help="Run the full portable Python battery and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.port < 1 or args.port > 65535:
        print("Port must be between 1 and 65535.", file=sys.stderr)
        return 2
    if args.doctor:
        return doctor()
    if args.test:
        return server_self_test()
    if args.full_test:
        return full_test()
    if args.command == "host":
        return host(args.port, remote=args.remote)
    return serve(args.port, open_browser=not args.no_browser, remote=args.remote)


if __name__ == "__main__":
    raise SystemExit(main())
