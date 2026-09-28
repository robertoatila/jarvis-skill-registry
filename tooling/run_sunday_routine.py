#!/usr/bin/env python3
"""
run_sunday_routine.py // J.A.R.V.I.S. Sunday Master Routine Python Wrapper
Pure Python 3 Standard Library runner for the sovereign Sunday pipeline.
Allows direct execution from the Remote Companion, mobile phone, or local CLI.
"""

from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

REGISTRY_ROOT = Path(__file__).resolve().parent.parent
MASTER_PS1 = REGISTRY_ROOT / "tooling" / "Invoke-SundayMasterAutonomousRoutine.ps1"


def main() -> int:
    print("=" * 65)
    print("  J.A.R.V.I.S. // DISPARO DA ESTEIRA DOMINICAL VIA PYTHON")
    print(f"  Diretorio: {REGISTRY_ROOT}")
    print(f"  Script:    {MASTER_PS1}")
    print("=" * 65)

    if not MASTER_PS1.exists():
        print(f"[ERRO] Script nao encontrado: {MASTER_PS1}", file=sys.stderr)
        return 1

    powershell_cmd = "powershell.exe" if os.name == "nt" else "pwsh"
    cmd = [
        powershell_cmd,
        "-ExecutionPolicy", "Bypass",
        "-NoProfile",
        "-File", str(MASTER_PS1),
    ]

    try:
        proc = subprocess.run(cmd, cwd=REGISTRY_ROOT)
        return proc.returncode
    except Exception as exc:
        print(f"[ERRO EXECUCAO] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
