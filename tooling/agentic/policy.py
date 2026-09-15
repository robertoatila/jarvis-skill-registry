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
import json
import tempfile
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
from .authorization import (
    AuthorizationDeniedError,
    AuthorizationGrant,
    AuthorizationGrantStore,
)


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
    action_context: Dict[str, Any] = field(default_factory=dict)
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
            "action_context": self.action_context,
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

    def __init__(self, config: Optional[JarvisRuntimeConfig] = None, *, operator_verifier=None):
        self.config = config or CONFIG
        self.root = self.config.registry_root.resolve()
        self._approvals: Dict[str, ApprovalRequest] = {}
<<<<<<< HEAD
        # The host supplies a trusted verifier; operator labels are not credentials.
        self._operator_verifier = operator_verifier
        self._approval_dir = self.config.state_dir / 'approvals'
        if self._approval_dir.exists():
            for path in self._approval_dir.glob('app-*.json'):
                try:
                    data = json.loads(path.read_text(encoding='utf-8'))
                    data.pop('schema_version', None)
                    data['risk_level'] = RiskLevel(data['risk_level'])
                    data['status'] = ApprovalStatus(data['status'])
                    req = ApprovalRequest(**data)
                    if re.fullmatch(r'app-[a-f0-9]{12}', req.approval_id):
                        self._approvals[req.approval_id] = req
                except (ValueError, TypeError, KeyError, OSError):
                    continue
=======
        self.authorization_store = AuthorizationGrantStore(config=self.config)
>>>>>>> 8f65117c4561b012121269e1afabe49cfe04c3a4

    def is_path_confined(self, target_path: str | Path) -> bool:
        """Verifies target path stays strictly within the repository workspace."""
        try:
            p = Path(target_path)
            if not p.is_absolute():
                p = (self.root / p).resolve()
            else:
                p = p.resolve()
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
        write_scopes: Optional[List[str]] = None,
        approval_id: Optional[str] = None,
        action_context: Optional[Dict[str, Any]] = None
    ) -> PolicyEvaluationResult:
        normalized_risk = RiskLevel.normalize(risk_level)
        action = {"local.write_text": "write", "local.read_file": "read"}.get(action.lower(), action.lower())
        write_actions = {"write", "edit", "create", "delete", "modify", "append", "truncate"}
        if action in write_actions and agent_profile.constraints.read_only:
            return PolicyEvaluationResult(PolicyDecision.DENY, normalized_risk, "Agent is constrained to read-only execution")
        if action in write_actions and (not resource or not write_scopes or agent_profile.constraints.read_only or normalized_risk == RiskLevel.R0_READ_ONLY):
            return PolicyEvaluationResult(PolicyDecision.DENY, normalized_risk, "Mutation requires a writable profile, declared target/scopes and non-read-only risk")

        if normalized_risk == RiskLevel.R5_DESTRUCTIVE:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                risk_level=normalized_risk,
                reason="R5 Destructive operations are strictly prohibited from autonomous execution"
            )

        if resource:
            if not self.is_path_confined(resource):
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    risk_level=normalized_risk,
                    reason=f"Path traversal detected or resource escapes workspace: '{resource}'"
                )

            write_actions = {"write", "edit", "create", "delete", "modify", "append", "truncate"}
            if action.lower() in write_actions:
                if agent_profile.constraints.read_only:
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.DENY,
                        risk_level=normalized_risk,
                        reason=f"Agent '{agent_profile.agent_id}' is constrained to read-only execution"
                    )

                if write_scopes:
                    matched = False
                    for scope in write_scopes:
                        scope_path = (self.root / scope).resolve()
                        resource_path = (self.root / resource).resolve()
                        if self.is_path_confined(scope_path) and resource_path.is_relative_to(scope_path):
                            matched = True
                            break
                    if not matched:
                        return PolicyEvaluationResult(
                            decision=PolicyDecision.DENY,
                            risk_level=normalized_risk,
                            reason=f"Resource '{resource}' not permitted by declared write_scopes: {write_scopes}"
                        )

        network_actions = {"network_call", "http_request", "api_query", "fetch", "git_fetch", "download"}
        if action.lower() in network_actions:
            if self.config.offline_only or not agent_profile.constraints.network_access:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    risk_level=normalized_risk,
                    reason=f"Agent '{agent_profile.agent_id}' network access is disabled by policy"
                )

        if tool_or_skill and agent_profile.allowed_tools:
            is_skill_auth = tool_or_skill in agent_profile.skills or tool_or_skill == "general"
            is_tool_auth = self.is_tool_allowed(tool_or_skill, agent_profile.allowed_tools) or self.is_tool_allowed(f"skills:{tool_or_skill}", agent_profile.allowed_tools)
            if not (is_skill_auth or is_tool_auth):
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    risk_level=normalized_risk,
                    reason=f"Tool/Skill '{tool_or_skill}' is not authorized for agent '{agent_profile.agent_id}'"
                )

        if normalized_risk == RiskLevel.R4_INFRA_MUTATION:
            if self.is_approval_authorized(approval_id, task_id, agent_profile.agent_id, action,
                                           tool_or_skill, resource, action_context or {}):
                # Exclusive marker makes consumption persistent and single-use across engines.
                self._approval_dir.mkdir(parents=True, exist_ok=True)
                try:
                    with (self._approval_dir / (approval_id + '.used')).open('x', encoding='utf-8') as stream:
                        stream.write(datetime.now(timezone.utc).isoformat())
                        stream.flush(); os.fsync(stream.fileno())
                except FileExistsError:
                    return PolicyEvaluationResult(PolicyDecision.DENY, normalized_risk, 'Approval already consumed')
                return PolicyEvaluationResult(PolicyDecision.ALLOW, normalized_risk, 'Authenticated single-use approval consumed', approval_id)
            req = self.create_approval_request(
                task_id=task_id,
                agent_profile=agent_profile.agent_id,
                action=action,
                tool_or_skill=tool_or_skill,
                resource=resource,
                risk_level=normalized_risk,
                justification=f"Autonomous action '{action}' on '{resource or tool_or_skill}' classified as R4",
                action_context=action_context
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
        justification: str,
        action_context: Optional[Dict[str, Any]] = None
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
            action_context=json.loads(json.dumps(action_context or {}, allow_nan=False)),
            status=ApprovalStatus.PENDING_ACK
        )
        self._approvals[app_id] = req
        self._save_approval(req)
        return req

    def get_approval_request(self, approval_id: str) -> Optional[ApprovalRequest]:
        return self._approvals.get(approval_id)

    def grant_approval(self, approval_id: str, operator_id: str, signature: str = "") -> bool:
        """Grant an approval request while strictly preventing autonomous self-approval."""
        req = self._approvals.get(approval_id)
        if not req or req.status != ApprovalStatus.PENDING_ACK:
            return False

        if req.is_expired():
            req.status = ApprovalStatus.EXPIRED
            self._save_approval(req)
            return False

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
            self._save_approval(req)
            return False

        if not operator_id.strip() or not signature or self._operator_verifier is None:
            return False
        payload = self.approval_payload(req, operator_id)
        try:
            if self._operator_verifier(operator_id, payload, signature) is not True:
                return False
        except Exception:
            return False
        req.status = ApprovalStatus.APPROVED
        req.approved_by = operator_id
        if signature:
            req.signature = signature
        req.decision_utc = datetime.now(timezone.utc).isoformat()
        self._save_approval(req)
        return True

<<<<<<< HEAD
    @staticmethod
    def approval_payload(req: ApprovalRequest, operator_id: str) -> bytes:
        """Stable signed envelope. Runtime dispatch still requires separate binding."""
        return json.dumps({"approval_id": req.approval_id, "operator_id": operator_id,
                           "task_id": req.task_id, "agent_profile": req.agent_profile,
                           "action": req.action, "tool_or_skill": req.tool_or_skill,
                           "resource": req.resource, "risk_level": req.risk_level.value,
                           "context_hash": req.context_hash, "expires_utc": req.expires_utc,
                           "action_context": req.action_context},
                          sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def _save_approval(self, req):
        self._approval_dir.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=self._approval_dir, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(req.to_dict(), stream, allow_nan=False)
                stream.flush(); os.fsync(stream.fileno())
            Path(name).replace(self._approval_dir / (req.approval_id + '.json'))
        finally:
            Path(name).unlink(missing_ok=True)

    def is_approval_authorized(self, approval_id, task_id, agent_id, action, tool, resource, context):
        req = self._approvals.get(approval_id)
        action = {'local.write_text': 'write', 'local.read_file': 'read'}.get(action, action)
        if not req or req.risk_level != RiskLevel.R4_INFRA_MUTATION or req.status != ApprovalStatus.APPROVED or req.is_expired() or not self._operator_verifier:
            return False
        if (self._approval_dir / (req.approval_id + '.used')).exists():
            return False
        # Another host instance may have revoked or replaced this request.
        try:
            persisted = json.loads((self._approval_dir / (req.approval_id + '.json')).read_text(encoding='utf-8'))
            if persisted != req.to_dict():
                return False
        except (OSError, ValueError):
            return False
        if (req.task_id, req.agent_profile, req.action, req.tool_or_skill, req.resource, req.action_context) != (task_id, agent_id, action, tool, resource, context):
            return False
        try:
            return self._operator_verifier(req.approved_by, self.approval_payload(req, req.approved_by), req.signature) is True
        except Exception:
            return False
=======
    def issue_authorization_grant(
        self,
        approval_id: str,
        *,
        scopes: List[str],
        budget: Dict[str, Any]
    ) -> AuthorizationGrant:
        """Materialize approved authority as an immutable, durable execution grant."""
        req = self._approvals.get(approval_id)
        if req is None:
            raise AuthorizationDeniedError("APPROVAL_NOT_FOUND")
        if req.status != ApprovalStatus.APPROVED or not req.approved_by:
            raise AuthorizationDeniedError("APPROVAL_NOT_GRANTED")
        if req.is_expired():
            req.status = ApprovalStatus.EXPIRED
            raise AuthorizationDeniedError("APPROVAL_EXPIRED")

        grant = AuthorizationGrant.issue(
            task_id=req.task_id,
            subject=req.agent_profile,
            action=req.action,
            scopes=scopes,
            budget=budget,
            approved_by=req.approved_by,
            issued_utc=req.decision_utc or datetime.now(timezone.utc).isoformat(),
            expires_utc=req.expires_utc,
            registry_root=self.root,
        )
        self.authorization_store.save(grant)
        return grant

    def get_authorization_grant(self, grant_id: str) -> Optional[AuthorizationGrant]:
        return self.authorization_store.load(grant_id)
>>>>>>> 8f65117c4561b012121269e1afabe49cfe04c3a4

    def deny_approval(self, approval_id: str, operator_id: str, reason: str = "") -> bool:
        req = self._approvals.get(approval_id)
        if not req:
            return False
        req.status = ApprovalStatus.DENIED
        req.approved_by = operator_id
        req.decision_utc = datetime.now(timezone.utc).isoformat()
        self._save_approval(req)
        return True
