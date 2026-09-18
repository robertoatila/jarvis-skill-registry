#!/usr/bin/env python3
"""Canonical v0.2.0 restart/recovery evidence gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from tooling.agentic.adapters.local import LocalAction, LocalAdapterType
from tooling.agentic.authorization import AuthorizationGrant
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.models import (
    ApprovalStatus,
    ExecutionAttempt,
    ExecutionState,
    IdempotencySemantics,
    Mission,
    MissionOutcome,
    MissionStatus,
    RecoveryState,
    RiskLevel,
    SideEffectRecord,
    SideEffectType,
    TaskNode,
    TaskStatus,
    VerificationRequirement,
    VerificationState,
    VerificationType,
)
from tooling.agentic.runtime import JarvisAgenticRuntime


MISSION_ID = "mis-v020-recovery-gate"
TASK_ID = "tsk-v020-recovery-gate"
TARGET = "recovery-gate-effect.txt"
ORIGINAL_CONTENT = "effect-already-observed"
DUPLICATE_CONTENT = "duplicate-effect-must-not-run"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_interrupted_mission(root: Path) -> tuple[JarvisAgenticRuntime, Mission]:
    runtime = JarvisAgenticRuntime(registry_root=root)
    target = root / TARGET
    target.write_text(ORIGINAL_CONTENT, encoding="utf-8")

    action = LocalAction(
        adapter=LocalAdapterType.WRITE_TEXT,
        path=TARGET,
        content=DUPLICATE_CONTENT,
    ).to_dict()

    task = TaskNode(
        task_id=TASK_ID,
        title="Canonical interrupted mutable effect",
        agent_profile="Quantum-ExecutorAgent",
        required_skills=["general"],
        action=action,
        risk_level=RiskLevel.R4_INFRA_MUTATION,
        approval_status=ApprovalStatus.APPROVED,
        write_scopes=[TARGET],
        status=TaskStatus.RUNNING,
        verification_requirements=[
            VerificationRequirement(
                check_type=VerificationType.FILE_EXISTS,
                target=TARGET,
            )
        ],
    )
    task.record_attempt(
        ExecutionAttempt(
            attempt_id="att-v020-recovery-interrupted",
            mission_id=MISSION_ID,
            task_id=TASK_ID,
            attempt_number=1,
            agent_id="Quantum-ExecutorAgent",
            tool_id="local.write_text",
            execution_state=ExecutionState.RUNNING,
            verification_state=VerificationState.UNVERIFIED,
            recovery_state=RecoveryState.NOT_REQUIRED,
            outcome=MissionOutcome.OUTCOME_UNKNOWN,
            side_effects=[
                SideEffectRecord(
                    side_effect_id="effect-v020-recovery-gate",
                    side_effect_type=SideEffectType.LOCAL_WRITE,
                    target=TARGET,
                    observed_change="mutable dispatch observed before interruption",
                    idempotency=IdempotencySemantics.RECONCILIATION_REQUIRED,
                    provenance_hash="a" * 64,
                )
            ],
            trace_id="trace-v020-recovery-gate",
        )
    )

    dag = ExecutionDAG()
    dag.add_node(task)
    mission = Mission(
        mission_id=MISSION_ID,
        goal="Prove restart does not duplicate ambiguous mutable effects",
        dag=dag,
        status=MissionStatus.RUNNING,
    )

    now = datetime.now(timezone.utc)
    grant = AuthorizationGrant.issue(
        task_id=TASK_ID,
        subject="Quantum-ExecutorAgent",
        action=action["adapter"],
        scopes=[TARGET],
        budget={},
        approved_by="operator:v020-recovery-gate",
        issued_utc=(now - timedelta(minutes=1)).isoformat(),
        expires_utc=(now + timedelta(hours=1)).isoformat(),
        registry_root=root,
    )
    runtime.policy.authorization_store.save(grant)
    task.action["authorization_grant_id"] = grant.grant_id
    runtime.state_store.save_mission(mission)
    return runtime, mission


def run_recovery_gate(root: Path) -> dict[str, object]:
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    runtime, mission = _build_interrupted_mission(root)
    mission_path = runtime.state_store.get_mission_path(mission.mission_id)
    target = root / TARGET

    before_effect_sha256 = _sha256(target)
    before_mission_sha256 = _sha256(mission_path)

    restarted = JarvisAgenticRuntime(registry_root=root)
    try:
        result = restarted.resume_mission(MISSION_ID)
        runtime_error = None
    except Exception as exc:
        result = {}
        runtime_error = f"{type(exc).__name__}: {exc}"

    after_effect_sha256 = _sha256(target)
    after_mission_sha256 = _sha256(mission_path)
    restored = restarted.state_store.load_mission(MISSION_ID)
    restored_task = restored.dag.nodes[TASK_ID] if restored is not None else None
    first_attempt = restored_task.attempts[0] if restored_task and restored_task.attempts else None

    blocked_tasks = result.get("blocked_tasks", []) if isinstance(result, dict) else []
    blocked_reason = (
        blocked_tasks[0].get("reason")
        if blocked_tasks and isinstance(blocked_tasks[0], dict)
        else None
    )
    checks = {
        "runtime_completed_without_error": runtime_error is None,
        "resume_blocked": result.get("status") == "BLOCKED",
        "zero_waves_executed": result.get("waves_executed") == 0,
        "reconciliation_required": (
            isinstance(blocked_reason, str)
            and "RECONCILIATION_REQUIRED" in blocked_reason
        ),
        "effect_unchanged": before_effect_sha256 == after_effect_sha256,
        "mission_state_unchanged": before_mission_sha256 == after_mission_sha256,
        "duplicate_content_absent": target.read_text(encoding="utf-8") == ORIGINAL_CONTENT,
        "outcome_remains_unknown": (
            first_attempt is not None
            and first_attempt.outcome == MissionOutcome.OUTCOME_UNKNOWN
        ),
    }
    passed = all(checks.values())

    return {
        "schema_version": "1.0.0",
        "gate": "v020-restart-recovery",
        "status": "PASS" if passed else "FAIL",
        "mission_id": MISSION_ID,
        "task_id": TASK_ID,
        "effect_target": TARGET,
        "before_effect_sha256": before_effect_sha256,
        "after_effect_sha256": after_effect_sha256,
        "before_mission_sha256": before_mission_sha256,
        "after_mission_sha256": after_mission_sha256,
        "waves_executed": result.get("waves_executed"),
        "blocked_reason": blocked_reason,
        "attempt_outcome": (
            first_attempt.outcome.value if first_attempt is not None else None
        ),
        "runtime_error": runtime_error,
        "checks": checks,
    }


def _write_output(path: Path, evidence: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the canonical v0.2.0 restart/recovery gate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON evidence output path.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="jarvis-v020-recovery-") as directory:
        evidence = run_recovery_gate(Path(directory))

    if args.output is not None:
        _write_output(args.output, evidence)

    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
