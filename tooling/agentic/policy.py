"""
policy.py // J.A.R.V.I.S. Policy & Authorization Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces:
- Section 3 & 5 Sovereign Risk Governance (R0 to R5)
- Boundary Scopes (Read / Write / Network / Command)
- Approval Gate Lifecycle with Strict Anti-Self-Approval Invariant
"""

from __future__ import annotations
import os
import re
import fnmatch
import time
import uuid
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone, timedelta

from .models import (
    RiskLevel,
    ApprovalStatus,
    SCHEMA_VERSION,
    _identifier,
    _nonnegative
)
from .profiles import AgentProfile
from .config import CONFIG, JarvisRuntimeConfig


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class ApprovalRequest:
    approval_id: str
    task_id: str
    agent_profile: str
    action: str
    tool_or_skill: str
    resource: str
    risk_level: RiskLevel
    justification: str
    context_hash: str = ""
    signature: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING_ACK
    requested_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_utc: str = field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(seconds=300)).isoformat())
    approved_by: Optional[str] = None
    decision_utc: Optional[str] = None

    def is_expired(self) -> bool:
        try:
            exp = datetime.fromisoformat(self.expires_utc)
            return datetime.now(timezone.utc) > exp
        except Exception:
            return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "approval_id": self.approval_id,
            "task_id": self.task_id,
            "agent_profile": self.agent_profile,
            "action": self.action,
            "tool_or_skill": self.tool_or_skill,
            "resource": self.resource,
            "risk_level": self.risk_level.value,
            "justification": self.justification,
            "context_hash": self.context_hash,
            "signature": self.signature,
            "status": self.status.value,
            "requested_utc": self.requested_utc,
            "expires_utc": self.expires_utc,
            "approved_by": self.approved_by,
            "decision_utc": self.decision_utc
        }


@dataclass
class PolicyEvaluationResult:
    decision: PolicyDecision
    risk_level: RiskLevel
    reason: str
    approval_id: Optional[str] = None
    evaluated_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "approval_id": self.approval_id,
            "evaluated_utc": self.evaluated_utc
        }


class PolicyEngine:
    """
    Sovereign Authorization & Policy Engine.
    Evaluates: EvaluatePolicy(Agent, Action, Tool, Resource, Mission, RiskLevel)
    """

    def __init__(self, config: Optional[JarvisRuntimeConfig] = None):
        self.config = config or CONFIG
        self.root = self.config.registry_root.resolve()
        self._approvals: Dict[str, ApprovalRequest] = {}

    def is_path_confined(self, target_path: str | Path) -> bool:
        """Verifies target path stays strictly within the repository workspace."""
        try:
            p = Path(target_path)
            if not p.is_absolute():
                p = (self.root / p).resolve()
            else:
                p = p.resolve()
            # Enforce confinement under self.root
            common = os.path.commonpath([str(self.root), str(p)])
            return common == str(self.root)
        except Exception:
            return False

    def is_tool_allowed(self, tool_name: str, allowed_patterns: List[str]) -> bool:
        """Checks tool against wildcard permitted patterns."""
        for pat in allowed_patterns:
            if fnmatch.fnmatch(tool_name, pat):
                return True
        return False

    def evaluate_policy(
        self,
        agent_profile: AgentProfile,
        action: str,
        tool_or_skill: str,
        resource: str = "",
        risk_level: RiskLevel | str = RiskLevel.R0_READ_ONLY,
        task_id: str = "tsk-auto",
        read_scopes: Optional[List[str]] = None,
        write_scopes: Optional[List[str]] = None
    ) -> PolicyEvaluationResult:
        normalized_risk = RiskLevel.normalize(risk_level)

        # Invariant 1: R5 Destructive actions are strictly blocked from autonomous execution
        if normalized_risk == RiskLevel.R5_DESTRUCTIVE:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                risk_level=normalized_risk,
                reason="R5 Destructive operations are strictly prohibited from autonomous execution"
            )

        # Invariant 2: Filesystem scope and confinement validation
        if resource:
            if not self.is_path_confined(resource):
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    risk_level=normalized_risk,
                    reason=f"Path traversal detected or resource escapes workspace: '{resource}'"
                )

            # Check read-only agent constraints on mutation actions
            write_actions = {"write", "edit", "create", "delete", "modify", "append", "truncate"}
            if action.lower() in write_actions:
                if agent_profile.constraints.read_only:
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.DENY,
                        risk_level=normalized_risk,
                        reason=f"Agent '{agent_profile.agent_id}' is constrained to read-only execution"
                    )

                # If write scopes are defined, enforce confinement to declared write scopes
                if write_scopes:
                    matched = False
                    for scope in write_scopes:
                        scope_clean = scope.rstrip("/\\")
                        if resource.startswith(scope_clean) or resource.startswith(f"{scope_clean}/") or resource.startswith(f"{scope_clean}\\"):
                            matched = True
                            break
                    if not matched:
                        return PolicyEvaluationResult(
                            decision=PolicyDecision.DENY,
                            risk_level=normalized_risk,
                            reason=f"Resource '{resource}' not permitted by declared write_scopes: {write_scopes}"
                        )

        # Invariant 3: Network egress validation
        network_actions = {"network_call", "http_request", "api_query", "fetch", "git_fetch", "download"}
        if action.lower() in network_actions:
            if not agent_profile.constraints.network_access:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    risk_level=normalized_risk,
                    reason=f"Agent '{agent_profile.agent_id}' network access is disabled by policy"
                )

        # Invariant 4: Tool allowance validation
        if tool_or_skill and agent_profile.allowed_tools:
            is_skill_auth = tool_or_skill in agent_profile.skills or tool_or_skill == "general"
            is_tool_auth = self.is_tool_allowed(tool_or_skill, agent_profile.allowed_tools) or self.is_tool_allowed(f"skills:{tool_or_skill}", agent_profile.allowed_tools)
            if not (is_skill_auth or is_tool_auth):
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    risk_level=normalized_risk,
                    reason=f"Tool/Skill '{tool_or_skill}' is not authorized for agent '{agent_profile.agent_id}'"
                )

        # Invariant 5: R4 Infrastructure/Security Mutation requires approval gate
        if normalized_risk == RiskLevel.R4_INFRA_MUTATION:
            req = self.create_approval_request(
                task_id=task_id,
                agent_profile=agent_profile.agent_id,
                action=action,
                tool_or_skill=tool_or_skill,
                resource=resource,
                risk_level=normalized_risk,
                justification=f"Autonomous action '{action}' on '{resource or tool_or_skill}' classified as R4"
            )
            return PolicyEvaluationResult(
                decision=PolicyDecision.REQUIRE_APPROVAL,
                risk_level=normalized_risk,
                reason="Action classified as R4 Infrastructure Mutation requires explicit operator approval",
                approval_id=req.approval_id
            )

        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            risk_level=normalized_risk,
            reason="Action authorized under sovereign security policy"
        )

    def create_approval_request(
        self,
        task_id: str,
        agent_profile: str,
        action: str,
        tool_or_skill: str,
        resource: str,
        risk_level: RiskLevel,
        justification: str
    ) -> ApprovalRequest:
        app_id = f"app-{uuid.uuid4().hex[:12]}"
        rl_val = risk_level.value if isinstance(risk_level, RiskLevel) else str(risk_level)
        ctx_raw = f"{task_id}:{agent_profile}:{action}:{tool_or_skill}:{resource}:{rl_val}"
        ctx_hash = hashlib.sha256(ctx_raw.encode("utf-8")).hexdigest()
        req = ApprovalRequest(
            approval_id=app_id,
            task_id=task_id,
            agent_profile=agent_profile,
            action=action,
            tool_or_skill=tool_or_skill,
            resource=resource,
            risk_level=risk_level,
            justification=justification,
            context_hash=ctx_hash,
            status=ApprovalStatus.PENDING_ACK
        )
        self._approvals[app_id] = req
        return req

    def get_approval_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        return self._approvals.get(approval_id)

    def grant_approval(self, approval_id: str, operator_id: str, signature: str = "") -> bool:
        """
        Grants approval for a pending R4 request.
        ENFORCES ANTI-SELF-APPROVAL: An autonomous agent can never grant its own approval.
        """
        req = self._approvals.get(approval_id)
        if not req:
            return False

        if req.is_expired():
            req.status = ApprovalStatus.EXPIRED
            return False

        # Strict Anti-Self-Approval Enforcement
        normalized_operator = operator_id.lower().strip()
        if (
            normalized_operator == req.agent_profile.lower().strip()
            or normalized_operator.startswith("agent:")
            or normalized_operator.startswith("quantum-")
            or normalized_operator.startswith("runtime:")
            or "autonomous" in normalized_operator
        ):
            req.status = ApprovalStatus.DENIED
            req.decision_utc = datetime.now(timezone.utc).isoformat()
            return False

        req.status = ApprovalStatus.APPROVED
        req.approved_by = operator_id
        if signature:
            req.signature = signature
        req.decision_utc = datetime.now(timezone.utc).isoformat()
        return True

    def deny_approval(self, approval_id: str, operator_id: str, reason: str = "") -> bool:
        req = self._approvals.get(approval_id)
        if not req:
            return False
        req.status = ApprovalStatus.DENIED
        req.approved_by = operator_id
        req.decision_utc = datetime.now(timezone.utc).isoformat()
        return True
