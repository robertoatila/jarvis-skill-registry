"""
profiles.py // J.A.R.V.I.S. Agent Profiles & Resolution Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Maintains 100% Backward Compatibility with QuantumAgentEngine
"""

from __future__ import annotations
import json
import fnmatch
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from .models import SCHEMA_VERSION, validate_schema_version, _identifier, _strings, _nonnegative
from .dag import save_json_atomic


@dataclass
class AgentConstraints:
    read_only: bool = False
    network_access: bool = True
    sandbox_profile: str = "strict-sandbox"

    def __post_init__(self) -> None:
        if type(self.read_only) is not bool or type(self.network_access) is not bool:
            raise ValueError("Agent read/network constraints must be booleans")
        _identifier(self.sandbox_profile, "sandbox_profile")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "read_only": self.read_only,
            "network_access": self.network_access,
            "sandbox_profile": self.sandbox_profile
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentConstraints:
        return cls(
            read_only=data.get("read_only", False),
            network_access=data.get("network_access", True),
            sandbox_profile=data.get("sandbox_profile", "strict-sandbox")
        )


@dataclass
class AgentBudgetLimits:
    max_tokens_per_task: int = 16_000
    max_runtime_seconds: float = 120.0
    max_tool_calls: int = 20

    def __post_init__(self) -> None:
        _nonnegative(self.max_tokens_per_task, "max_tokens_per_task", integer=True)
        _nonnegative(self.max_tool_calls, "max_tool_calls", integer=True)
        _nonnegative(self.max_runtime_seconds, "max_runtime_seconds", positive=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_tokens_per_task": self.max_tokens_per_task,
            "max_runtime_seconds": self.max_runtime_seconds,
            "max_tool_calls": self.max_tool_calls
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentBudgetLimits:
        return cls(
            max_tokens_per_task=data.get("max_tokens_per_task", 16_000),
            max_runtime_seconds=data.get("max_runtime_seconds", 120.0),
            max_tool_calls=data.get("max_tool_calls", 20)
        )


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    domain: str
    capabilities: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=lambda: ["mcp:*", "local_cli:*"])
    constraints: AgentConstraints = field(default_factory=AgentConstraints)
    budget_limits: AgentBudgetLimits = field(default_factory=AgentBudgetLimits)
    status: str = "ONLINE_READY"
    badge: str = "SOBERANO"
    capacity: int = 1
    model: Optional[str] = None

    def __post_init__(self) -> None:
        for name in ("agent_id", "name", "domain"):
            _identifier(getattr(self, name), name)
        for name in ("capabilities", "skills", "allowed_tools"):
            _strings(getattr(self, name), name)
        self.constraints.__post_init__()
        self.budget_limits.__post_init__()
        _nonnegative(self.capacity, "capacity", integer=True, positive=True)
        if self.status not in {"ONLINE_READY", "BUSY", "ENGAGED", "STANDBY", "OFFLINE", "DISABLED"}:
            raise ValueError("Unknown agent status")
        if self.model is not None:
            _identifier(self.model, "model")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "agent_id": self.agent_id,
            "name": self.name,
            "domain": self.domain,
            "status": self.status,
            "capabilities": sorted(self.capabilities),
            "skills": sorted(self.skills),
            "allowed_tools": sorted(self.allowed_tools),
            "constraints": self.constraints.to_dict(),
            "budget_limits": self.budget_limits.to_dict(),
            "badge": self.badge,
            "capacity": self.capacity,
            "model": self.model
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentProfile:
        validate_schema_version(data)
        for name in ("capabilities", "skills", "allowed_tools"):
            _strings(data.get(name, []), name)
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            domain=data.get("domain", "General Agent"),
            capabilities=list(data.get("capabilities", [])),
            skills=list(data.get("skills", [])),
            allowed_tools=list(data.get("allowed_tools", ["mcp:*", "local_cli:*"])),
            constraints=AgentConstraints.from_dict(data.get("constraints", {})),
            budget_limits=AgentBudgetLimits.from_dict(data.get("budget_limits", {})),
            status=data.get("status", "ONLINE_READY"),
            badge=data.get("badge", "SOBERANO"),
            capacity=data.get("capacity", 1),
            model=data.get("model")
        )


class AgentProfileRegistry:
    """
    Registry for managing and resolving agent profiles.
    Pre-populated with canonical Quantum Agents from QuantumAgentEngine.
    """

    def __init__(self):
        self._profiles: Dict[str, AgentProfile] = {}
        self._load_quantum_defaults()

    def _load_quantum_defaults(self) -> None:
        """Loads canonical 4 Quantum Agents to preserve 100% backward compatibility."""
        self.register(AgentProfile(
            agent_id="Quantum-AuditAgent",
            name="Agente Quântico de Auditoria & Hardening",
            domain="Cybersecurity & Sovereign Governance",
            capabilities=["security-audit", "code-review", "integrity-verification", "fail-closed-governance"],
            skills=["security-research-audit", "comprehensive-code-review", "bash-defensive-patterns", "broken-authentication", "blackbird-osint-recon"],
            badge="AUDITORIA",
            constraints=AgentConstraints(read_only=True, network_access=False, sandbox_profile="strict-sandbox")
        ))
        self.register(AgentProfile(
            agent_id="Quantum-ReconAgent",
            name="Agente Quântico de Radar & OSINT",
            domain="GitHub Starred Radar & Discovery",
            capabilities=["osint-recon", "repo-mining", "radar-search", "catalog-intelligence"],
            skills=["deep-technical-research", "blackbird-osint-recon", "free-ai-apis-router", "api-fuzzing-bug-bounty"],
            badge="RECONHECIMENTO",
            constraints=AgentConstraints(read_only=True, network_access=True, sandbox_profile="network-restricted")
        ))
        self.register(AgentProfile(
            agent_id="Quantum-SynthesisAgent",
            name="Agente Quântico de Síntese & IA",
            domain="Neural Bridge & Model Routing",
            capabilities=["ai-routing", "prompt-compilation", "neural-synthesis", "multi-provider"],
            skills=["ai-engineer", "dspy-declarative-prompt-compilation", "vllm-high-throughput-serving", "openrouter-ai-sdk", "free-ai-apis-router"],
            badge="MULTI-PROVEDOR",
            constraints=AgentConstraints(read_only=False, network_access=True, sandbox_profile="provider-native")
        ))
        self.register(AgentProfile(
            agent_id="Quantum-VisualizerAgent",
            name="Agente Quântico de UI/UX & Acessibilidade",
            domain="Accessible UI & Deck.gl Visualizer",
            capabilities=["frontend-engineering", "wcag-audit", "accessibility-compliance", "data-visualization"],
            skills=["frontend-ui-engineering", "frontend-design-engineering", "deckgl-geospatial-visualization", "shadcn"],
            badge="ACESSIBILIDADE",
            constraints=AgentConstraints(read_only=False, network_access=False, sandbox_profile="offline-developer")
        ))

    def register(self, profile: AgentProfile) -> None:
        profile.__post_init__()
        self._profiles[profile.agent_id] = profile

    def save(self, file_path: str | Path) -> None:
        save_json_atomic(file_path, {"schema_version": SCHEMA_VERSION,
                                    "profiles": [p.to_dict() for p in self.list_profiles()]})

    @classmethod
    def load(cls, file_path: str | Path) -> AgentProfileRegistry:
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        validate_schema_version(data)
        if not isinstance(data.get("profiles"), list):
            raise ValueError("Profile snapshot must contain profiles array")
        profiles = [AgentProfile.from_dict(p) for p in data["profiles"]]
        if len({p.agent_id for p in profiles}) != len(profiles):
            raise ValueError("Duplicate profile identifiers")
        registry = cls()
        for profile in profiles:
            registry.register(profile)
        return registry

    def get(self, agent_id: str) -> Optional[AgentProfile]:
        return self._profiles.get(agent_id)

    def list_profiles(self) -> List[AgentProfile]:
        return [self._profiles[k] for k in sorted(self._profiles.keys())]

    def resolve_agent(
        self,
        required_capabilities: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None,
        constraints_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deterministic Agent Resolution.
        Returns:
            {
                "selected_agent": AgentProfile or None,
                "score": float,
                "reason": str,
                "candidates_evaluated": [ { "agent_id": str, "score": float, "accepted": bool, "reason": str } ]
            }
        """
        req_caps = set(required_capabilities or [])
        req_skills = set(required_skills or [])
        c_filter = constraints_filter or {}

        evaluated: List[Dict[str, Any]] = []

        for agent_id in sorted(self._profiles.keys()):
            prof = self._profiles[agent_id]
            prof.__post_init__()

            reason = None
            if prof.status != "ONLINE_READY":
                reason = "Agent is not online and ready"
            elif not req_caps.issubset(prof.capabilities) or not req_skills.issubset(prof.skills):
                reason = "Missing required capabilities or skills"
            elif c_filter.get("requires_write") and prof.constraints.read_only:
                reason = "Task requires write access but agent is read-only"
            elif c_filter.get("requires_network") and not prof.constraints.network_access:
                reason = "Task requires network but agent is offline"
            elif c_filter.get("active_tasks", {}).get(agent_id, 0) >= prof.capacity:
                reason = "Agent capacity exhausted"
            elif any(not any(fnmatch.fnmatchcase(tool, pattern) for pattern in prof.allowed_tools)
                     for tool in c_filter.get("required_tools", [])):
                reason = "Required tool is not allowed by agent profile"
            else:
                for requested, maximum in (("estimated_tokens", prof.budget_limits.max_tokens_per_task),
                                           ("timeout_seconds", prof.budget_limits.max_runtime_seconds),
                                           ("tool_calls", prof.budget_limits.max_tool_calls)):
                    if requested in c_filter:
                        _nonnegative(c_filter[requested], requested)
                        if c_filter[requested] > maximum:
                            reason = f"Agent budget insufficient: {requested}"
                            break
            if reason:
                evaluated.append({"agent_id": agent_id, "score": None, "accepted": False,
                                  "reason": reason, "missing_caps": sorted(req_caps - set(prof.capabilities)),
                                  "missing_skills": sorted(req_skills - set(prof.skills))})
                continue

            # 1. Constraint filters
            if c_filter.get("read_only") and not prof.constraints.read_only:
                evaluated.append({
                    "agent_id": agent_id,
                    "score": 0.0,
                    "accepted": False,
                    "reason": "Rejected: Task requires read-only agent but profile is read-write"
                })
                continue

            if c_filter.get("require_offline") and prof.constraints.network_access:
                evaluated.append({
                    "agent_id": agent_id,
                    "score": 0.0,
                    "accepted": False,
                    "reason": "Rejected: Task requires offline isolation but profile has network access"
                })
                continue

            # 2. Score calculation
            cap_overlap = len(req_caps.intersection(prof.capabilities))
            skill_overlap = len(req_skills.intersection(prof.skills))

            # Base score: match ratio
            total_reqs = (len(req_caps) + len(req_skills)) or 1
            score = ((cap_overlap * 2.0) + (skill_overlap * 1.0)) / (total_reqs * 2.0)

            evaluated.append({
                "agent_id": agent_id,
                "score": round(score, 4),
                "accepted": True,
                "matched_caps": sorted(list(req_caps.intersection(prof.capabilities))),
                "matched_skills": sorted(list(req_skills.intersection(prof.skills))),
                "reason": f"Matched {cap_overlap} capabilities and {skill_overlap} skills"
            })

        # Filter accepted and sort deterministically by score (desc), then agent_id (asc)
        valid_candidates = [c for c in evaluated if c["accepted"]]
        valid_candidates.sort(key=lambda x: (-x["score"], x["agent_id"]))

        if not valid_candidates:
            return {
                "selected_agent": None,
                "score": 0.0,
                "reason": "No agent profile matched the required constraints and capabilities.",
                "candidates_evaluated": evaluated
            }

        best = valid_candidates[0]
        selected_profile = self.get(best["agent_id"])

        return {
            "selected_agent": selected_profile,
            "score": best["score"],
            "reason": f"Selected best matching profile '{best['agent_id']}' with score {best['score']}",
            "candidates_evaluated": evaluated
        }
