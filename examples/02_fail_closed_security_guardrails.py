"""
examples/02_fail_closed_security_guardrails.py
==============================================
J.A.R.V.I.S. Autonomous Agentic Runtime // Protocol v2.0
Zero PIP Dependencies // Pure Python 3.12 Standard Library

This example demonstrates:
  1. The R0-R5 Risk Taxonomy and automated task classification.
  2. Workspace path confinement (fail-closed directory isolation).
  3. Fail-closed blocking of R5_DESTRUCTIVE actions.
  4. Non-self-approval enforcement for R4_INFRA_MUTATION tasks.
  5. The fundamental invariant: Task Execution != Task Verification.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.models import RiskLevel, ApprovalStatus
from tooling.agentic.profiles import AgentProfile, AgentConstraints
from tooling.agentic.policy import PolicyEngine, PolicyDecision


def main():
    print("=" * 70)
    print("  J.A.R.V.I.S. // EXAMPLE 02: FAIL-CLOSED SECURITY GUARDRAILS")
    print("=" * 70)

    # 1. Initialize Sovereign Fail-Closed Policy Engine
    config = JarvisRuntimeConfig(registry_root=_REPO_ROOT, security_mode="FAIL_CLOSED")
    policy_engine = PolicyEngine(config=config)
    print(f"[+] Policy Engine initialized at: {policy_engine.root}")
    print(f"    - Security Mode: FAIL_CLOSED (Enforcing 14 Invariant Laws)")

    # 2. Risk Taxonomy Overview
    print("\n[*] Section 1: R0-R5 Risk Taxonomy")
    for level in RiskLevel:
        print(f"    - {level.name:24} ({level.value}): Description={level.name.split('_', 1)[-1]}")

    # 3. Section 2: Workspace Boundary Enforcement (Path Confinement)
    print("\n[*] Section 2: Workspace Boundary Enforcement")
    safe_path = _REPO_ROOT / "state" / "test.json"
    unsafe_path = Path("C:/Windows/System32/drivers/etc/hosts")

    is_safe = policy_engine.is_path_confined(safe_path)
    is_unsafe = policy_engine.is_path_confined(unsafe_path)
    print(f"    - Inside Workspace Path  : '{safe_path.name}' -> Allowed: {is_safe}")
    print(f"    - Outside Workspace Path : '{unsafe_path}' -> Allowed: {is_unsafe}")
    assert is_safe is True, "Safe path should be allowed"
    assert is_unsafe is False, "Unsafe path must be blocked fail-closed"
    print("    >>> Path confinement verified: Directory traversal blocked fail-closed.")

    # 4. Section 3: R5_DESTRUCTIVE Execution Blocking (Fail-Closed)
    print("\n[*] Section 3: Destructive Action Interception (R5_DESTRUCTIVE)")
    agent = AgentProfile(
        agent_id="Quantum-ExecutorAgent",
        name="Executor Agent",
        domain="System Execution",
        skills=["systematic-code-debugging"],
        allowed_tools=["*"],
        constraints=AgentConstraints(read_only=False, network_access=True)
    )

    eval_r5 = policy_engine.evaluate_policy(
        agent_profile=agent,
        action="purge_system_files",
        tool_or_skill="system-purge",
        resource=str(_REPO_ROOT / "state"),
        risk_level=RiskLevel.R5_DESTRUCTIVE,
        task_id="tsk-malicious-01"
    )
    print(f"    - Task ID         : tsk-malicious-01")
    print(f"    - Risk Level      : {eval_r5.risk_level.value}")
    print(f"    - Policy Decision : {eval_r5.decision.value}")
    print(f"    - Reason          : {eval_r5.reason}")
    assert eval_r5.decision == PolicyDecision.DENY, "R5 destructive operation must be DENIED!"
    print("    >>> R5 task blocked: Invariant 1 strictly enforced (Exit code 126 fail-closed).")

    # 5. Section 4: Non-Self-Approval Enforcement for R4 Mutations
    print("\n[*] Section 4: Non-Self-Approval Enforcement (R4_INFRA_MUTATION)")
    eval_r4 = policy_engine.evaluate_policy(
        agent_profile=agent,
        action="deploy_infrastructure",
        tool_or_skill="terraform-apply",
        resource=str(_REPO_ROOT / "config"),
        risk_level=RiskLevel.R4_INFRA_MUTATION,
        task_id="tsk-infra-01"
    )
    print(f"    - Task ID         : tsk-infra-01")
    print(f"    - Policy Decision : {eval_r4.decision.value}")
    print(f"    - Reason          : {eval_r4.reason}")
    print(f"    - Approval Ticket : {eval_r4.approval_id}")
    assert eval_r4.decision == PolicyDecision.REQUIRE_APPROVAL, "R4 must require approval"

    # Agent attempts to self-approve
    approval_id = eval_r4.approval_id
    self_approved = policy_engine.grant_approval(
        approval_id=approval_id,
        operator_id="Quantum-ExecutorAgent"  # The agent itself!
    )
    req = policy_engine.get_approval_request(approval_id)
    print(f"    - Agent Self-Approval Attempt : Granted={self_approved} | Status={req.status.value}")
    assert self_approved is False, "Agent must never be permitted to approve itself!"
    assert req.status == ApprovalStatus.DENIED, "Status must be DENIED on self-approval attempt"

    # Human operator signs off
    human_approved = policy_engine.grant_approval(
        approval_id=approval_id,
        operator_id="HUMAN_SOVEREIGN_OPERATOR"
    )
    print(f"    - Human Operator Sign-Off     : Granted={human_approved} | Status={req.status.value}")
    print(f"    - Approved By                 : {req.approved_by}")
    print(f"    - Decision Timestamp          : {req.decision_utc}")
    assert human_approved is True, "Human operator approval should succeed"
    print("    >>> Anti-self-approval verified: R4 actions strictly require independent operator sign-off.")

    print("\n" + "=" * 70)
    print(">>> SUCCESS: All Fail-Closed Security Guardrails Verified Deterministically!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
