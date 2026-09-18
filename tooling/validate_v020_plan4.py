#!/usr/bin/env python3
"""Direct v0.2.0 Plan 4 evidence gates.

The gates are responsibility-scoped and intentionally independent from GitHub
Actions. Each invocation produces a machine-readable report tied to the current
platform and exact command matrix.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.validate_v020_plan3 import redact_output


OUTPUT_TAIL_LIMIT = 6000


def platform_key() -> str:
    value = platform.system().casefold()
    if value == "windows":
        return "windows"
    if value == "darwin":
        return "macos"
    if value == "linux":
        return "linux"
    return value or "unknown"


def _python(*args: str) -> list[str]:
    return [sys.executable, *args]


def build_gate_commands(gate: str, *, current_platform: str | None = None) -> list[list[str]]:
    current_platform = current_platform or platform_key()
    gates: dict[str, list[list[str]]] = {
        "contracts": [
            _python(
                "-m", "unittest",
                "tests.test_agentic_v020_observability",
                "tests.test_agentic_v020_mission_timeline",
                "tests.test_agentic_v020_server_observability",
                "tests.test_agentic_design_system_contract",
                "-v",
            ),
        ],
        "integration": [
            _python(
                "-m", "unittest",
                "tests.test_agentic_v020_deterministic_provider",
                "tests.test_agentic_v020_hud_runtime_integration",
                "-v",
            ),
            ["node", "--test", "tests/test_chat_session.cjs"],
            ["node", "--test", "tests/test_runtime_observability.cjs"],
            ["node", "--test", "tests/test_operational_cockpit.cjs"],
        ],
        "recovery": [
            _python(
                "tooling/run_v020_recovery_gate.py",
                "--output",
                "reports/v020-recovery-gate.json",
            ),
            _python("-m", "unittest", "tests.test_agentic_v020_recovery_gate", "-v"),
        ],
        "browser-ui": [
            ["npm", "run", "test:browser"],
        ],
        "benchmarks-claims": [
            _python("-m", "unittest", "tests.test_agentic_v020_claim_audit", "-v"),
            _python("benchmarks/context_budget_benchmark.py"),
            _python(
                "benchmarks/repository_context_benchmark.py",
                "--output",
                "reports/v020-repository-context.json",
            ),
            _python(
                "tooling/audit_documentation_claims.py",
                "--output",
                "reports/v020-claim-audit.json",
            ),
        ],
        "portable-runtime": [
            _python("run_tests.py"),
            _python("jarvis.py", "--doctor"),
            _python("jarvis.py", "--test"),
            _python(
                "tooling/quickstart_verifier.py",
                "--json-output",
                f"reports/quickstart-{current_platform}.json",
            ),
        ],
        "legacy-governance": [
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", "tooling/run_v020_legacy_governance_gate.ps1",
            ],
        ],
    }
    if gate not in gates:
        raise ValueError(f"UNKNOWN_GATE:{gate}")
    return [list(command) for command in gates[gate]]


def supported_platforms(gate: str) -> tuple[str, ...]:
    if gate == "legacy-governance":
        return ("windows",)
    if gate == "portable-runtime":
        return ("windows", "linux", "macos")
    return ("windows", "linux", "macos")


def _tool_available(command: Sequence[str]) -> bool:
    executable = command[0]
    if Path(executable).is_absolute():
        return Path(executable).exists()
    return shutil.which(executable) is not None


def _run(
    command: Sequence[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_gate(
    gate: str,
    *,
    root: Path = ROOT,
    current_platform: str | None = None,
    runner: Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]] = _run,
) -> dict[str, object]:
    root = Path(root).resolve()
    current_platform = current_platform or platform_key()
    allowed = supported_platforms(gate)
    started = datetime.now(timezone.utc).isoformat()

    if current_platform not in allowed:
        return {
            "schema_version": "1.0.0",
            "plan": "v0.2.0-plan4",
            "gate": gate,
            "status": "FAIL",
            "failure_reason": "UNSUPPORTED_PLATFORM",
            "platform": current_platform,
            "supported_platforms": list(allowed),
            "github_actions_used": False,
            "started_utc": started,
            "finished_utc": datetime.now(timezone.utc).isoformat(),
            "results": [],
        }

    commands = build_gate_commands(gate, current_platform=current_platform)
    results: list[dict[str, object]] = []

    for command in commands:
        tick = time.monotonic()
        if not _tool_available(command):
            results.append({
                "argv": command,
                "status": "FAIL",
                "exit_code": None,
                "duration_ms": 0,
                "output_tail": f"Required executable unavailable: {command[0]}",
            })
            continue

        try:
            completed = runner(command, root)
            duration_ms = int((time.monotonic() - tick) * 1000)
            output = redact_output(completed.stdout or "")
            results.append({
                "argv": command,
                "status": "PASS" if completed.returncode == 0 else "FAIL",
                "exit_code": completed.returncode,
                "duration_ms": duration_ms,
                "output_tail": output[-OUTPUT_TAIL_LIMIT:],
            })
        except Exception as exc:
            duration_ms = int((time.monotonic() - tick) * 1000)
            results.append({
                "argv": command,
                "status": "FAIL",
                "exit_code": None,
                "duration_ms": duration_ms,
                "output_tail": f"{type(exc).__name__}: {exc}",
            })

    passed = sum(item["status"] == "PASS" for item in results)
    failed = sum(item["status"] == "FAIL" for item in results)
    return {
        "schema_version": "1.0.0",
        "plan": "v0.2.0-plan4",
        "gate": gate,
        "status": "PASS" if results and failed == 0 else "FAIL",
        "failure_reason": None,
        "platform": current_platform,
        "supported_platforms": list(allowed),
        "github_actions_used": False,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "command_count": len(results),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def default_report_path(gate: str, current_platform: str) -> Path:
    return ROOT / "reports" / f"v020-plan4-{gate}-{current_platform}.json"


def write_report(path: Path, report: dict[str, object]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Run one direct JARVIS v0.2.0 Plan 4 evidence gate.",
    )
    value.add_argument(
        "--gate",
        required=True,
        choices=(
            "contracts",
            "integration",
            "recovery",
            "browser-ui",
            "benchmarks-claims",
            "portable-runtime",
            "legacy-governance",
        ),
    )
    value.add_argument("--report", type=Path)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    current_platform = platform_key()
    report = run_gate(args.gate, current_platform=current_platform)
    report_path = args.report or default_report_path(args.gate, current_platform)
    write_report(report_path, report)
    print(json.dumps({
        "gate": args.gate,
        "status": report["status"],
        "platform": current_platform,
        "report": str(report_path),
    }, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
