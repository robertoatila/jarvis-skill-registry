"""
verification.py // J.A.R.V.I.S. Verification & Evidence Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Implements:
- Section 12 Verification Protocol (9 check types)
- Strict state invariants:
  TASK EXECUTION COMPLETED ≠ TASK VERIFIED
  ALL TASKS EXECUTED ≠ MISSION SUCCESS
- Cryptographic provenance hashing for all evidence
"""

from __future__ import annotations
import os
import sys
import time
import json
import hashlib
import urllib.request
import ast
import py_compile
import subprocess
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import (
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationType,
    VerificationStatus,
    Mission,
    MissionStatus
)
from .dag import ExecutionDAG


REGISTRY_ROOT = Path("E:/.skill-registry").resolve()


@dataclass
class VerificationEvidence:
    evidence_id: str
    check_type: str
    target: str
    status: VerificationStatus
    duration_ms: float
    expected: Any = None
    actual: Any = None
    evidence_payload: Dict[str, Any] = field(default_factory=dict)
    provenance_hash: str = ""
    verified_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "check_type": self.check_type,
            "target": self.target,
            "expected": self.expected,
            "actual": self.actual,
            "status": self.status.value if isinstance(self.status, VerificationStatus) else str(self.status),
            "duration_ms": self.duration_ms,
            "evidence_payload": self.evidence_payload,
            "provenance_hash": self.provenance_hash,
            "verified_utc": self.verified_utc
        }


class VerificationEngine:
    """
    Executes and seals verification checks against 9 concrete types.
    Enforces fail-closed gates before any task or mission can be certified as VERIFIED/SUCCEEDED.
    """

    def __init__(self, registry_root: Optional[Path] = None):
        self.root = (registry_root or REGISTRY_ROOT).resolve()

    def verify_requirement(
        self,
        req: VerificationRequirement,
        base_dir: Optional[Path] = None
    ) -> VerificationEvidence:
        work_dir = base_dir or self.root
        start_time = time.perf_counter()
        ev_id = f"ev-{hashlib.sha256(f'{req.check_type}:{req.target}:{time.time()}'.encode('utf-8')).hexdigest()[:12]}"

        ctype = req.check_type.value if isinstance(req.check_type, VerificationType) else str(req.check_type)
        status = VerificationStatus.FAILED
        actual_val = None
        payload: Dict[str, Any] = {}

        try:
            if ctype == "file_exists":
                target_path = Path(req.target)
                if not target_path.is_absolute():
                    target_path = work_dir / target_path
                exists = target_path.exists()
                actual_val = exists
                if exists:
                    status = VerificationStatus.VERIFIED
                    h = hashlib.sha256(target_path.read_bytes()).hexdigest()
                    payload = {"size_bytes": target_path.stat().st_size, "sha256": h}
                else:
                    payload = {"error": f"File not found: {target_path}"}

            elif ctype == "artifact_hash_matches":
                target_path = Path(req.target)
                if not target_path.is_absolute():
                    target_path = work_dir / target_path
                if target_path.exists():
                    computed = hashlib.sha256(target_path.read_bytes()).hexdigest()
                    actual_val = computed
                    if req.expected and computed.lower() == str(req.expected).lower():
                        status = VerificationStatus.VERIFIED
                        payload = {"matched": True, "sha256": computed}
                    else:
                        payload = {"matched": False, "computed": computed, "expected": req.expected}
                else:
                    payload = {"error": f"Target file does not exist: {target_path}"}

            elif ctype == "command_exit_zero":
                cmd = req.target
                res = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(work_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                actual_val = res.returncode
                payload = {
                    "command": cmd,
                    "returncode": res.returncode,
                    "stdout_snippet": res.stdout[:500] if res.stdout else "",
                    "stderr_snippet": res.stderr[:500] if res.stderr else ""
                }
                if res.returncode == 0:
                    status = VerificationStatus.VERIFIED

            elif ctype == "test_passes":
                target_mod = req.target
                cmd = [sys.executable, "-m", "unittest", target_mod]
                res = subprocess.run(
                    cmd,
                    cwd=str(work_dir),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                actual_val = res.returncode
                payload = {
                    "runner": "unittest",
                    "target": target_mod,
                    "returncode": res.returncode,
                    "output": (res.stdout + res.stderr)[-500:]
                }
                if res.returncode == 0:
                    status = VerificationStatus.VERIFIED

            elif ctype == "schema_valid":
                target_json = Path(req.target)
                if not target_json.is_absolute():
                    target_json = work_dir / target_json
                if target_json.exists():
                    data = json.loads(target_json.read_text(encoding="utf-8"))
                    if not isinstance(req.expected, dict):
                        raise ValueError("schema_valid requires an explicit JSON Schema object")
                    try:
                        import jsonschema
                    except ImportError:
                        status = VerificationStatus.UNVERIFIED
                        payload = {"execution": "NOT_EXECUTED", "reason": "JSON Schema validator unavailable; JSON parsing is not schema validation"}
                    else:
                        jsonschema.validators.validator_for(req.expected).check_schema(req.expected)
                        jsonschema.validate(data, req.expected)
                        actual_val = True
                        status = VerificationStatus.VERIFIED
                        payload = {"valid": True, "validator": "jsonschema"}
                else:
                    payload = {"error": f"JSON file not found: {target_json}"}

            elif ctype == "http_health_check":
                url = req.target
                req_obj = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Verification/1.0"})
                with urllib.request.urlopen(req_obj, timeout=5) as response:
                    actual_val = response.status
                    if response.status == 200:
                        status = VerificationStatus.VERIFIED
                        payload = {"status_code": 200, "reason": response.reason}
                    else:
                        payload = {"status_code": response.status}

            elif ctype in ("lint_clean", "typecheck_clean"):
                status = VerificationStatus.UNVERIFIED
                payload = {"execution": "NOT_EXECUTED", "reason": f"No {ctype} tool adapter configured; AST/compilation cannot certify this check"}

            elif ctype == "no_regression":
                target_metric = (Path(work_dir) / req.target).resolve()
                if not req.target or not target_metric.is_relative_to(Path(work_dir).resolve()):
                    raise ValueError("Observed metric must be an explicit file under the verification root")
                observed = json.loads(target_metric.read_text(encoding="utf-8"))
                metric = observed["metric_value"]
                if isinstance(metric, bool) or not isinstance(metric, (int, float)) or not math.isfinite(metric):
                    raise ValueError("Observed metric must be a finite number")
                expected = req.expected
                if isinstance(expected, bool) or not isinstance(expected, (int, float)) or not math.isfinite(expected):
                    raise ValueError("Baseline must be a finite number")
                actual_val, expected_val = float(metric), float(expected)
                if actual_val >= expected_val:
                    status = VerificationStatus.VERIFIED
                    payload = {"no_regression": True, "current": actual_val, "baseline": expected_val}
                else:
                    payload = {"no_regression": False, "current": actual_val, "baseline": expected_val}

        except Exception as e:
            status = VerificationStatus.FAILED
            payload = {"error": str(e), "exception_type": type(e).__name__}

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        
        # Cryptographic provenance
        provenance_str = f"{ev_id}|{ctype}|{req.target}|{status.value}|{duration_ms}|{json.dumps(payload, sort_keys=True)}"
        prov_hash = hashlib.sha256(provenance_str.encode("utf-8")).hexdigest()

        evidence = VerificationEvidence(
            evidence_id=ev_id,
            check_type=ctype,
            target=req.target,
            status=status,
            duration_ms=duration_ms,
            expected=req.expected,
            actual=actual_val,
            evidence_payload=payload,
            provenance_hash=prov_hash
        )

        # Update requirement state
        req.status = status
        req.evidence = evidence.to_dict()
        return evidence

    def verify_task(self, task: TaskNode, base_dir: Optional[Path] = None) -> bool:
        """
        Enforces: TASK EXECUTION COMPLETED ≠ TASK VERIFIED
        A task is ONLY VERIFIED when all verification requirements evaluate to VERIFIED.
        """
        if task.status not in (TaskStatus.EXECUTED, TaskStatus.VERIFIED):
            return False
        if not task.verification_requirements:
            return False
        execution = task.execution_result or {}
        if execution.get("exit_code") != 0 or not execution.get("producer"):
            return False

        all_passed = True

        for req in task.verification_requirements:
            req.status = VerificationStatus.VERIFYING
            ev = self.verify_requirement(req, base_dir=base_dir)
            if ev.status != VerificationStatus.VERIFIED:
                all_passed = False

        if all_passed:
            task.status = TaskStatus.VERIFIED
            return True
        else:
            task.status = TaskStatus.FAILED
            return False

    def verify_mission(self, mission: Mission, dag: ExecutionDAG, base_dir: Optional[Path] = None) -> bool:
        """
        Enforces: ALL TASKS EXECUTED ≠ MISSION SUCCESS
        A mission is ONLY SUCCEEDED when every task is VERIFIED.
        """
        mission.status = MissionStatus.VERIFYING
        all_verified = True

        for task in dag.nodes.values():
            if task.status != TaskStatus.VERIFIED:
                # Attempt verification
                passed = self.verify_task(task, base_dir=base_dir)
                if not passed:
                    all_verified = False

            # Collect evidence into mission ledger
            for req in task.verification_requirements:
                if req.evidence:
                    mission.evidence_ledger.append(req.evidence)

        if all_verified and dag.is_complete():
            mission.status = MissionStatus.SUCCEEDED
            mission.completed_utc = datetime.now(timezone.utc).isoformat()
            return True
        else:
            mission.status = MissionStatus.FAILED
            return False
