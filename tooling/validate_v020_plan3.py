#!/usr/bin/env python3
"""Direct Plan 3 validation gate for JARVIS v0.2.0.

This runner intentionally does not depend on GitHub Actions. It executes the
canonical Task 8 command matrix in order and writes one machine-readable report.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports" / "v020-plan3-validation.json"
OUTPUT_TAIL_LIMIT = 6000

_REDACTION_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "sk-[REDACTED]"),
    (re.compile(r"\bgsk_[A-Za-z0-9_-]{12,}\b"), "gsk_[REDACTED]"),
    (re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"), "AIza[REDACTED]"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_output(value: str) -> str:
    text = value or ""
    for pattern, replacement in _REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def build_commands(root: Path = ROOT) -> list[dict[str, object]]:
    py = sys.executable
    return [
        {
            "name": "observability-contracts",
            "argv": [py, "-m", "unittest", "tests.test_agentic_v020_observability", "-v"],
        },
        {
            "name": "mission-timeline-contracts",
            "argv": [py, "-m", "unittest", "tests.test_agentic_v020_mission_timeline", "-v"],
        },
        {
            "name": "server-observability-contracts",
            "argv": [py, "-m", "unittest", "tests.test_agentic_v020_server_observability", "-v"],
        },
        {
            "name": "hud-runtime-integration",
            "argv": [py, "-m", "unittest", "tests.test_agentic_v020_hud_runtime_integration", "-v"],
        },
        {
            "name": "chat-session-node",
            "argv": ["node", "--test", "tests/test_chat_session.cjs"],
        },
        {
            "name": "runtime-observability-node",
            "argv": ["node", "--test", "tests/test_runtime_observability.cjs"],
        },
        {
            "name": "operational-cockpit-node",
            "argv": ["node", "--test", "tests/test_operational_cockpit.cjs"],
        },
        {
            "name": "repository-test-battery",
            "argv": [py, "run_tests.py"],
        },
        {
            "name": "doctor",
            "argv": [py, "jarvis.py", "--doctor"],
        },
        {
            "name": "jarvis-test",
            "argv": [py, "jarvis.py", "--test"],
        },
        {
            "name": "context-budget-benchmark",
            "argv": [py, "benchmarks/context_budget_benchmark.py"],
        },
        {
            "name": "pre-publish-audit",
            "argv": [py, "tooling/audit_pre_publish_security.py"],
        },
    ]


def _tool_available(argv: Sequence[str]) -> bool:
    executable = argv[0]
    if Path(executable).is_absolute():
        return Path(executable).exists()
    return shutil.which(executable) is not None


def _default_runner(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def run_validation(
    root: Path = ROOT,
    *,
    commands: Iterable[dict[str, object]] | None = None,
    runner: Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]] = _default_runner,
) -> dict[str, object]:
    root = Path(root).resolve()
    matrix = list(commands if commands is not None else build_commands(root))
    started = _utc_now()
    results: list[dict[str, object]] = []

    for spec in matrix:
        name = str(spec["name"])
        argv = [str(item) for item in spec["argv"]]
        started_monotonic = time.monotonic()

        if not _tool_available(argv):
            results.append({
                "name": name,
                "argv": argv,
                "status": "FAIL",
                "exit_code": None,
                "duration_ms": 0,
                "output_tail": f"Required executable unavailable: {argv[0]}",
            })
            continue

        try:
            completed = runner(argv, root)
            raw_output = completed.stdout or ""
            elapsed_ms = int((time.monotonic() - started_monotonic) * 1000)
            results.append({
                "name": name,
                "argv": argv,
                "status": "PASS" if completed.returncode == 0 else "FAIL",
                "exit_code": completed.returncode,
                "duration_ms": elapsed_ms,
                "output_tail": redact_output(raw_output[-OUTPUT_TAIL_LIMIT:]),
            })
        except Exception as exc:  # gate must record runner failures, not hide them
            elapsed_ms = int((time.monotonic() - started_monotonic) * 1000)
            results.append({
                "name": name,
                "argv": argv,
                "status": "FAIL",
                "exit_code": None,
                "duration_ms": elapsed_ms,
                "output_tail": f"{type(exc).__name__}: {exc}",
            })

    overall = "PASS" if results and all(item["status"] == "PASS" for item in results) else "FAIL"
    return {
        "schema_version": "1.0.0",
        "gate": "jarvis-v0.2.0-plan3-direct-validation",
        "status": overall,
        "started_utc": started,
        "finished_utc": _utc_now(),
        "cwd": str(root),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "github_actions_used": False,
        "command_count": len(results),
        "passed": sum(item["status"] == "PASS" for item in results),
        "failed": sum(item["status"] == "FAIL" for item in results),
        "results": results,
    }


def write_report(report: dict[str, object], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the JARVIS v0.2.0 Plan 3 validation matrix directly.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="JSON report path (default: reports/v020-plan3-validation.json)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_validation(ROOT)
    write_report(report, args.report)
    print(json.dumps({
        "status": report["status"],
        "passed": report["passed"],
        "failed": report["failed"],
        "command_count": report["command_count"],
        "report": str(args.report),
    }, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
