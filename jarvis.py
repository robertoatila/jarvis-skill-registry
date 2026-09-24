#!/usr/bin/env python3
"""Zero-dependency launcher for the local J.A.R.V.I.S. runtime.

The launcher intentionally stays thin: it validates the checkout, delegates to
the established server or resident-host assembly and never hides runtime failures.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
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


def build_host_server_command(
    port: int,
    remote: bool = False,
    transport: str | None = None,
) -> list[str]:
    """Return the resident-host command without changing the legacy path."""
    cmd = [sys.executable, "-m", "tooling.remote_host", "--port", str(port)]
    if transport:
        cmd.extend(["--transport", transport])
    elif remote:
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


def host(
    port: int,
    remote: bool = False,
    transport: str | None = None,
) -> int:
    """Run the resident host assembly in the foreground without opening a browser."""
    if doctor() != 0:
        return 1
    mode = transport or ("lan" if remote else "local")
    print(f"\nJ.A.R.V.I.S. resident PC host: port {port} // transport={mode}")
    print("Host state is persisted and checked for process liveness. Press Ctrl+C to stop.\n")
    try:
        return subprocess.call(
            build_host_server_command(port, remote=remote, transport=transport),
            cwd=ROOT,
        )
    except KeyboardInterrupt:
        return 130


def service(action: str, *, port: int, transport: str) -> int:
    """Manage the per-user resident host autostart service."""
    from tooling.remote_service import RemoteServiceError, manage_windows_service

    if action == "install" and transport == "tailscale-serve":
        from tooling.remote_transport import TransportState
        from tooling.remote_transport_tailscale_serve import TailscaleServeRemoteTransport

        serve_status = TailscaleServeRemoteTransport(
            backend_port=port,
            adopt_only=True,
        ).start()
        if serve_status.state is not TransportState.ACTIVE:
            print(
                "J.A.R.V.I.S. service error: Tailscale Serve is not provisioned for "
                f"http://127.0.0.1:{port}. Run 'python jarvis.py remote-serve provision' "
                "from an elevated Windows terminal first.",
                file=sys.stderr,
            )
            return 1

    try:
        result = manage_windows_service(
            action,
            registry_root=ROOT,
            state_dir=ROOT / "state",
            port=port,
            transport=transport,
        )
    except RemoteServiceError as exc:
        print(f"J.A.R.V.I.S. service error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def remote_doctor_command(*, port: int) -> int:
    """Check whether this PC is ready for persistent phone-controlled JARVIS access."""
    from tooling.remote_doctor import remote_doctor

    result = remote_doctor(
        ROOT,
        ROOT / "state",
        port=port,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "READY" else 1


def _windows_admin_state() -> bool | None:
    """Return Windows elevation state; None means this is not Windows."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def remote_serve(action: str, *, port: int) -> int:
    """Provision or verify the HTTPS Tailscale Serve mapping used by JARVIS."""
    from tooling.remote_transport import TransportState
    from tooling.remote_transport_tailscale_serve import TailscaleServeRemoteTransport

    if action not in {"provision", "status"}:
        print("remote-serve requires provision or status", file=sys.stderr)
        return 2

    if action == "provision" and _windows_admin_state() is False:
        print(
            "J.A.R.V.I.S. Serve provisioning requires a Windows Admin terminal. "
            "Reopen PowerShell/Terminal as Administrator and run this command again.",
            file=sys.stderr,
        )
        return 1

    transport = TailscaleServeRemoteTransport(
        backend_port=port,
        adopt_only=(action == "status"),
    )
    status = transport.start()
    payload = status.to_dict()
    payload["backend_target"] = transport.target
    payload["mode"] = "provision" if action == "provision" else "adopt-only-status"
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if status.state is TransportState.ACTIVE:
        return 0
    if action == "provision":
        print(
            "Tailscale Serve provisioning did not become active. On Windows, run this "
            "command from an Admin terminal and follow any Tailscale HTTPS consent URL.",
            file=sys.stderr,
        )
    return 1


def remote_pair(*, port: int, label: str = "Remote device") -> int:
    """Create a one-time pairing offer through the already-running local host."""
    normalized_label = str(label or "Remote device").strip() or "Remote device"
    body = json.dumps(
        {"label_hint": normalized_label},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/remote/v1/pairing/offers",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            offer = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"J.A.R.V.I.S. pairing error: {exc}", file=sys.stderr)
        return 1
    if not isinstance(offer, dict):
        print("J.A.R.V.I.S. pairing error: malformed host response", file=sys.stderr)
        return 1
    offer_id = offer.get("offer_id")
    pairing_secret = offer.get("pairing_secret")
    if not isinstance(offer_id, str) or not isinstance(pairing_secret, str):
        print("J.A.R.V.I.S. pairing error: host did not return a valid offer", file=sys.stderr)
        return 1

    endpoint = offer.get("pairing_endpoint")
    base = f"http://127.0.0.1:{port}"
    if isinstance(endpoint, str) and endpoint.strip():
        try:
            parsed = urllib.parse.urlsplit(endpoint.strip())
            if (
                parsed.scheme in {"http", "https"}
                and parsed.hostname
                and not parsed.username
                and not parsed.password
                and parsed.path in {"", "/"}
                and not parsed.query
                and not parsed.fragment
            ):
                base = f"{parsed.scheme}://{parsed.netloc}"
        except ValueError:
            pass
    query = urllib.parse.urlencode({"remote": "1"})
    fragment = urllib.parse.urlencode(
        {
            "offer": offer_id,
            "pairing_secret": pairing_secret,
        }
    )
    result = {
        "offer_id": offer_id,
        "expires_at": offer.get("expires_at"),
        "pairing_endpoint": offer.get("pairing_endpoint"),
        "pairing_url": f"{base}/remote?{query}#{fragment}",
        "label_hint": normalized_label,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def remote_devices(action: str, *, device_id: str | None = None) -> int:
    """List or selectively revoke paired Remote Companion devices."""
    from tooling.remote_devices import RemoteDeviceError, RemoteDeviceRegistry

    registry = RemoteDeviceRegistry(ROOT / "state")
    if action == "list":
        payload = [
            RemoteDeviceRegistry.as_dict(device)
            for device in registry.list_devices()
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if action == "revoke":
        normalized = str(device_id or "").strip()
        if not normalized:
            print("remote-devices revoke requires --device-id", file=sys.stderr)
            return 2
        try:
            device = registry.revoke(normalized)
        except RemoteDeviceError as exc:
            print(f"J.A.R.V.I.S. device error: {exc}", file=sys.stderr)
            return 1
        print(
            json.dumps(
                RemoteDeviceRegistry.as_dict(device),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print("remote-devices requires list or revoke", file=sys.stderr)
    return 2


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
        choices=("host", "service", "remote-doctor", "remote-serve", "remote-pair", "remote-devices"),
        help="Optional resident runtime command",
    )
    parser.add_argument(
        "service_action",
        nargs="?",
        choices=("install", "start", "stop", "status", "uninstall", "provision", "list", "revoke"),
        help="Action used with the service command",
    )
    parser.add_argument("--port", type=int, default=8899, help="HUD port (default: 8899)")
    parser.add_argument("--remote", action="store_true", help="Enable remote mobile companion access over LAN/Wi-Fi with QR code and token auth")
    parser.add_argument(
        "--transport",
        choices=("local", "lan", "tailscale", "tailscale-serve"),
        default=None,
        help="Resident-host transport. Prefer tailscale-serve for HTTPS phone access from another network.",
    )
    parser.add_argument("--label", default="Remote device", help="Device label hint for remote-pair")
    parser.add_argument("--device-id", default=None, help="Device identifier for remote-devices revoke")
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
    if args.command == "remote-doctor":
        return remote_doctor_command(port=args.port)
    if args.command == "remote-serve":
        if args.service_action not in {"provision", "status"}:
            print("remote-serve requires provision or status", file=sys.stderr)
            return 2
        return remote_serve(args.service_action, port=args.port)
    if args.command == "remote-pair":
        return remote_pair(port=args.port, label=args.label)
    if args.command == "remote-devices":
        if args.service_action not in {"list", "revoke"}:
            print("remote-devices requires list or revoke", file=sys.stderr)
            return 2
        return remote_devices(args.service_action, device_id=args.device_id)
    if args.command == "service":
        if not args.service_action:
            print("service requires one of: install, start, stop, status, uninstall", file=sys.stderr)
            return 2
        transport = args.transport or ("lan" if args.remote else "local")
        return service(args.service_action, port=args.port, transport=transport)
    if args.command == "host":
        return host(args.port, remote=args.remote, transport=args.transport)
    if args.transport is not None:
        print("--transport is valid only with host or service", file=sys.stderr)
        return 2
    return serve(args.port, open_browser=not args.no_browser, remote=args.remote)


if __name__ == "__main__":
    raise SystemExit(main())
