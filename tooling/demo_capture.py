#!/usr/bin/env python3
"""Generate truthful, machine-readable evidence for the public 90-second demo.

The capture path is intentionally deterministic and provider-free. It exercises
real J.A.R.V.I.S. routing, context admission, adapter invocation and independent
verification using a local fixture backend. No provider/network credential is
required and no private chain-of-thought is emitted.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.context_budget_benchmark import evaluate_fixture, load_fixture
from tooling.agentic.adapters.inference import InferenceResult
from tooling.agentic.adapters.local import LocalAction, LocalAdapterType
from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.context_governor import ContextItem
from tooling.agentic.dag import ExecutionDAG
from tooling.agentic.model_router import InferencePolicy, InferenceRequirements, ModelCandidate
from tooling.agentic.models import (
    Mission,
    RiskLevel,
    TaskNode,
    VerificationRequirement,
    VerificationType,
)
from tooling.agentic.planner_resolver import AutonomousSkillResolver
from tooling.agentic.runtime import JarvisAgenticRuntime

DEMO_ID = "jarvis-public-demo-90s-v1"
CLAIM_BOUNDARY = (
    "real local runtime receipts with deterministic fixture backend; "
    "no live provider, browser-rendering, quality, or dollar-savings claim"
)
EVIDENCE_REF = "benchmark:repository-context-admission-v2"


def resolve_commit_sha() -> str:
    github_sha = os.environ.get("GITHUB_SHA", "").strip()
    if len(github_sha) == 40 and all(ch in "0123456789abcdefABCDEF" for ch in github_sha):
        return github_sha.lower()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"
    value = completed.stdout.strip()
    return value or "UNKNOWN"


def run_doctor() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "jarvis.py"), "--doctor"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
    return {
        "command": "python jarvis.py --doctor",
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "exit_code": completed.returncode,
        "output": output,
    }


def resolve_skill() -> dict[str, Any]:
    config = JarvisRuntimeConfig(registry_root=ROOT, security_mode="FAIL_CLOSED")
    resolver = AutonomousSkillResolver(config=config)
    winner, receipt = resolver.resolve_with_decision_receipt(
        "systematic-code-debugging",
        target_platform="linux",
    )
    encoded = receipt.to_dict()
    if not winner:
        raise RuntimeError("demo skill resolution produced no catalog-backed winner")
    if encoded.get("selected_candidate") != winner:
        raise RuntimeError("demo skill receipt does not match selected skill")
    return {
        "requested_capability": "systematic-code-debugging",
        "selected_skill": winner,
        "receipt": encoded,
    }


def run_context_benchmark(commit_sha: str) -> dict[str, Any]:
    result = evaluate_fixture(load_fixture(), commit_sha=commit_sha)
    if result.get("status") != "PASS":
        raise RuntimeError(f"context benchmark failed: {result.get('failure_reason')}")
    return result


def run_verified_inference(selected_skill: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="jarvis-demo-inference-") as directory:
        root = Path(directory)
        config = JarvisRuntimeConfig(registry_root=root, security_mode="FAIL_CLOSED")
        runtime = JarvisAgenticRuntime(config=config)
        runtime.inference_backends.register(
            ModelCandidate(
                "demo-local-fixture",
                "deterministic-fixture",
                8000,
                0.0,
                0.95,
                is_local=True,
            ),
            lambda request: InferenceResult(
                text=(
                    "Required benchmark evidence is admitted within the configured "
                    "context budget; omitted sources remain explicit in the receipt."
                ),
                confidence=0.96,
                evidence_refs=(EVIDENCE_REF,),
                prompt_tokens=24,
                completion_tokens=17,
                cost_usd=None,
            ),
        )
        task = TaskNode(
            "tsk-demo-inference",
            "Summarize the bounded context benchmark using only explicit evidence",
            required_skills=[selected_skill],
            risk_level=RiskLevel.R0_READ_ONLY,
        )
        result = runtime.execute_inference(
            task,
            mission_id="mis-demo-inference",
            agent_id="agent-demo-local",
            session_id="session-demo-public",
            items=[
                ContextItem(
                    "Repository context benchmark passed its byte-budget invariants.",
                    EVIDENCE_REF,
                    priority=0,
                    required=True,
                    valid_until=9_999_999_999,
                ),
                ContextItem(
                    "Optional expansion exists but is not required for this conclusion. " * 20,
                    "fixture:optional-expansion",
                    priority=9,
                    required=False,
                    valid_until=9_999_999_999,
                ),
            ],
            policy=InferencePolicy(local_only=True, network_allowed=False),
            requirements=InferenceRequirements(context_tokens=1000),
            verifier=lambda candidate: candidate.evidence_refs == (EVIDENCE_REF,),
            confidence_threshold=0.80,
            max_attempts=1,
            max_output_tokens=512,
            max_cost_usd=0.0,
        )
        if result.get("status") != "SUCCESS":
            raise RuntimeError(f"demo inference did not verify: {result}")
        attempt = result["trace"]["attempts"][-1]
        execution = attempt.get("execution_receipt")
        verification = attempt.get("verification_receipt")
        if not execution or not execution.get("invocation_occurred"):
            raise RuntimeError("demo inference lacks a positive execution receipt")
        if not verification or verification.get("verification_state") != "VERIFIED":
            raise RuntimeError("demo inference lacks an independent VERIFIED receipt")
        return result


def run_local_execution(selected_skill: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="jarvis-demo-exec-") as directory:
        root = Path(directory)
        (root / "fixture.txt").write_text(
            "public deterministic fixture\nverified evidence\n",
            encoding="utf-8",
        )
        runtime = JarvisAgenticRuntime(
            config=JarvisRuntimeConfig(registry_root=root, security_mode="FAIL_CLOSED")
        )
        action = LocalAction(
            adapter=LocalAdapterType.READ_FILE,
            path="fixture.txt",
        )
        task = TaskNode(
            task_id="tsk-demo-local-read",
            title="Read deterministic public fixture",
            agent_profile="Quantum-ExecutorAgent",
            required_skills=[selected_skill],
            action=action.to_dict(),
            risk_level=RiskLevel.R0_READ_ONLY,
            read_scopes=["fixture.txt"],
            verification_requirements=[
                VerificationRequirement(
                    check_type=VerificationType.FILE_EXISTS,
                    target="fixture.txt",
                )
            ],
        )
        dag = ExecutionDAG()
        dag.add_node(task)
        mission = Mission(
            mission_id="mis-demo-local-read",
            goal="Read and independently verify a public deterministic fixture",
            dag=dag,
        )
        result = runtime.execute_goal(mission)
        if result.get("status") != "SUCCESS":
            raise RuntimeError(f"demo local execution failed: {result}")
        execution_receipts = mission.metadata.get("execution_receipts", [])
        verification_receipts = mission.metadata.get("verification_receipts", [])
        if len(execution_receipts) != 1 or len(verification_receipts) != 1:
            raise RuntimeError("demo local execution receipt correlation is incomplete")
        if verification_receipts[0].get("verification_state") != "VERIFIED":
            raise RuntimeError("demo local execution is not VERIFIED")
        return {
            "result": result,
            "execution_receipt": execution_receipts[0],
            "verification_receipt": verification_receipts[0],
        }


def build_demo_evidence(*, commit_sha: str | None = None) -> dict[str, Any]:
    exact_commit = commit_sha or resolve_commit_sha()
    doctor = run_doctor()
    if doctor["status"] != "PASS":
        raise RuntimeError("public doctor command failed")

    skill = resolve_skill()
    benchmark = run_context_benchmark(exact_commit)
    inference = run_verified_inference(skill["selected_skill"])
    local_execution = run_local_execution(skill["selected_skill"])

    routing = inference["trace"]["routing"]
    attempt = inference["trace"]["attempts"][-1]
    context = inference["trace"]["context"]
    evidence = {
        "schema_version": 1,
        "demo": DEMO_ID,
        "status": "PASS",
        "commit_sha": exact_commit,
        "claim_boundary": CLAIM_BOUNDARY,
        "provider_key_required": False,
        "live_provider_used": False,
        "doctor": doctor,
        "skill": skill,
        "context_benchmark": benchmark,
        "inference": {
            "status": inference["status"],
            "reason": inference["trace"]["reason"],
            "text": inference["text"],
            "context": context,
            "routing": routing,
            "governor": attempt["governor"],
            "execution_receipt": attempt["execution_receipt"],
            "verification_receipt": attempt["verification_receipt"],
        },
        "local_execution": local_execution,
    }

    if routing.get("selected_candidate") != "demo-local-fixture":
        raise RuntimeError("demo model routing selected an unexpected backend")
    if attempt["verification_receipt"].get("verification_state") != "VERIFIED":
        raise RuntimeError("demo inference verification invariant failed")
    if benchmark.get("token_estimate") is not None:
        raise RuntimeError("demo benchmark must not invent token counts")
    return evidence


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _summary(payload: dict[str, Any]) -> str:
    benchmark = payload["context_benchmark"]
    inference = payload["inference"]
    local = payload["local_execution"]
    return "\n".join([
        "J.A.R.V.I.S. PUBLIC DEMO EVIDENCE",
        f"commit: {payload['commit_sha']}",
        f"doctor: {payload['doctor']['status']}",
        f"skill: {payload['skill']['selected_skill']}",
        (
            "context: "
            f"{benchmark['naive_serialized_bytes']} B naive -> "
            f"{benchmark['bounded_serialized_bytes']} B admitted / "
            f"{benchmark['budget_bytes']} B budget"
        ),
        f"model/backend: {inference['routing']['selected_candidate']}",
        f"governor: {inference['governor']['action']}",
        (
            "inference verification: "
            f"{inference['verification_receipt']['verification_state']}"
        ),
        (
            "local adapter: "
            f"{local['execution_receipt']['adapter']} / "
            f"{local['verification_receipt']['verification_state']}"
        ),
        "provider key required: false",
        "claim boundary: " + payload["claim_boundary"],
    ]) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate evidence for the truthful J.A.R.V.I.S. 90-second demo."
    )
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = build_demo_evidence()
    except Exception as exc:
        print(f"DEMO_CAPTURE_FAIL: {exc}", file=sys.stderr)
        return 1

    rendered = _summary(payload)
    print(rendered, end="")
    if args.json_output is not None:
        _write_json(args.json_output, payload)
    if args.text_output is not None:
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
