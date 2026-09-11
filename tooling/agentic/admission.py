"""
admission.py // J.A.R.V.I.S. Formal Task Admission Gate Engine
Pure Python 3.12 Standard Library (Zero External PIP Dependencies)

Implements Phase 18 (Admission Protocol) of the Autonomous Architecture Plan:
- Pre-flight admission gate before task scheduling or mutation dispatch
- Hard authority, privacy, scope, capability, and budget headroom evaluation
- Rejects invented capabilities or unverified prerequisites immediately (fail-closed)
"""

from __future__ import annotations
import os
import re
import posixpath
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime, timezone

from .models import (
    TaskNode,
    TaskStatus,
    RiskLevel,
    ApprovalStatus,
    SCHEMA_VERSION,
    _identifier
)
from .profiles import AgentProfile, AgentProfileRegistry
from .policy import PolicyEngine, PolicyDecision

PROTECTED_PATHS = {
    ".git",
    ".gitignore",
    "config/api_keys.json",
    "state/authoritative"
}


class AdmissionDecision(str, Enum):
    ADMITTED = "ADMITTED"
    BLOCKED = "BLOCKED"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class AdmissionResult:
    decision: AdmissionDecision
    task_id: str
    agent_id: str
    admitted: bool
    rejection_reasons: List[str] = field(default_factory=list)
    evaluated_constraints: Dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "admitted": self.admitted,
            "rejection_reasons": self.rejection_reasons,
            "evaluated_constraints": self.evaluated_constraints,
            "timestamp_utc": self.timestamp_utc
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AdmissionResult:
        dec = data.get("decision", "BLOCKED")
        try:
            dec = AdmissionDecision(dec)
        except ValueError:
            dec = AdmissionDecision.BLOCKED
        return cls(
            decision=dec,
            task_id=data.get("task_id", ""),
            agent_id=data.get("agent_id", ""),
            admitted=data.get("admitted", False),
            rejection_reasons=list(data.get("rejection_reasons", [])),
            evaluated_constraints=dict(data.get("evaluated_constraints", {})),
            timestamp_utc=data.get("timestamp_utc", ""),
            schema_version=data.get("schema_version", SCHEMA_VERSION)
        )


class AdmissionGate:
    """
    Sovereign Task Admission Gate.
    Verifies all hard constraints (authority, scopes, capabilities, budgets, dependencies)
    BEFORE tasks can enter the scheduling queue or execute.
    """

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        agent_registry: Optional[AgentProfileRegistry] = None
    ):
        self.policy = policy_engine or PolicyEngine()
        self.agents = agent_registry or AgentProfileRegistry()

    def evaluate_task(
        self,
        task: TaskNode,
        agent_profile: Optional[AgentProfile] = None,
        remaining_budget: Optional[Dict[str, Any]] = None,
        completed_task_ids: Optional[Set[str]] = None
    ) -> AdmissionResult:
        rejections: List[str] = []
        constraints_log: Dict[str, Any] = {}

        # 1. Dependency Satisfaction Check
        completed = completed_task_ids or set()
        missing_deps = [dep for dep in task.dependencies if dep not in completed]
        if missing_deps:
            rejections.append(f"Prerequisite dependencies unsatisfied: {', '.join(missing_deps)}")
            constraints_log["dependencies_satisfied"] = False
        else:
            constraints_log["dependencies_satisfied"] = True

        # 2. Agent Profile & Capability Resolution
        prof = agent_profile or self.agents.get(task.agent_profile)
        if not prof:
            res_agent = self.agents.resolve_agent(required_skills=task.required_skills)
            prof = res_agent.get("selected_agent")

        if not prof:
            rejections.append(f"No agent profile found or capable for task '{task.task_id}'")
            constraints_log["agent_capable"] = False
            agent_id = "UNKNOWN"
        else:
            agent_id = prof.agent_id
            req_skills = set(task.required_skills)
            agent_all_caps = set(prof.skills) | set(prof.capabilities)
            has_wildcard = "*" in agent_all_caps or "general-execution" in agent_all_caps
            missing_skills = req_skills - agent_all_caps
            if missing_skills and not has_wildcard:
                rejections.append(f"Agent '{agent_id}' lacks required capabilities: {', '.join(sorted(missing_skills))}")
                constraints_log["agent_capable"] = False
            else:
                constraints_log["agent_capable"] = True

        # 3. Sandbox & Authority Constraints
        if prof and task.write_scopes and prof.constraints.read_only:
            rejections.append(f"Task requires write scopes but agent '{prof.agent_id}' is read-only")
            constraints_log["write_authority_permitted"] = False
        else:
            constraints_log["write_authority_permitted"] = True

        # 4. Scope Confinement & Protected Paths Sanitization
        scope_violation = False
        for s in list(task.read_scopes) + list(task.write_scopes):
            clean = s.replace("\\", "/").strip().lstrip("/")
            if ".." in clean.split("/"):
                rejections.append(f"Scope traversal prohibited: '{s}'")
                scope_violation = True
                break
            for prot in PROTECTED_PATHS:
                if clean == prot or clean.startswith(f"{prot}/"):
                    rejections.append(f"Access to protected target prohibited: '{s}'")
                    scope_violation = True
                    break
            if scope_violation:
                break
        constraints_log["scopes_confined"] = not scope_violation

        # 5. Budget Headroom Check
        if remaining_budget:
            rem_tokens = remaining_budget.get("tokens")
            if rem_tokens is not None and task.estimated_tokens is not None:
                if task.estimated_tokens > rem_tokens:
                    rejections.append(f"Insufficient token budget: task requires {task.estimated_tokens}, remaining {rem_tokens}")
                    constraints_log["budget_headroom"] = False
                else:
                    constraints_log["budget_headroom"] = True

            rem_cost = remaining_budget.get("cost_usd")
            if rem_cost is not None and task.estimated_cost_usd is not None:
                if task.estimated_cost_usd > rem_cost:
                    rejections.append(f"Insufficient cost budget: task requires ${task.estimated_cost_usd:.4f}, remaining ${rem_cost:.4f}")
                    constraints_log["cost_headroom"] = False
                else:
                    constraints_log["cost_headroom"] = True
        else:
            constraints_log["budget_headroom"] = True

        # 6. Risk / Approval Decision
        canonical_risk = task.canonical_risk_level
        constraints_log["canonical_risk"] = canonical_risk.value

        if rejections:
            return AdmissionResult(
                decision=AdmissionDecision.BLOCKED,
                task_id=task.task_id,
                agent_id=agent_id,
                admitted=False,
                rejection_reasons=rejections,
                evaluated_constraints=constraints_log
            )

        if canonical_risk in (RiskLevel.R4_INFRA_MUTATION, RiskLevel.R5_DESTRUCTIVE):
            if task.approval_status != ApprovalStatus.APPROVED:
                return AdmissionResult(
                    decision=AdmissionDecision.REQUIRE_APPROVAL,
                    task_id=task.task_id,
                    agent_id=agent_id,
                    admitted=False,
                    rejection_reasons=[f"Task risk level {canonical_risk.value} requires human operator approval"],
                    evaluated_constraints=constraints_log
                )

        return AdmissionResult(
            decision=AdmissionDecision.ADMITTED,
            task_id=task.task_id,
            agent_id=agent_id,
            admitted=True,
            rejection_reasons=[],
            evaluated_constraints=constraints_log
        )
