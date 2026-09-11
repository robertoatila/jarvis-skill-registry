"""
models.py // J.A.R.V.I.S. Autonomous Agentic Data Models
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

from __future__ import annotations
import json
import math
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0.0"


def validate_schema_version(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("Serialized model must be an object")
    if data.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
        raise ValueError("Unsupported schema_version")


def _nonnegative(value: Any, name: str, *, integer: bool = False, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{name} is outside its allowed range")
    if integer and not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")


def _strings(value: Any, name: str) -> None:
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{name} must be a list of nonempty strings")


def _identifier(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def _artifacts(value: Any, name: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    for v in value:
        if isinstance(v, str):
            if not v.strip():
                raise ValueError(f"{name} string items must be nonempty")
        elif not isinstance(v, Artifact):
            raise ValueError(f"{name} items must be strings or Artifact instances")


class RiskLevel(str, Enum):
    R0_READ_ONLY = "R0"
    R1_LOCAL_WRITE = "R1"
    R2_REPO_MUTATION = "R2"
    R3_EXTERNAL_SIDE_EFFECT = "R3"
    R4_INFRA_MUTATION = "R4"
    R5_DESTRUCTIVE = "R5"

    @classmethod
    def normalize(cls, val: Any) -> RiskLevel:
        if isinstance(val, cls):
            return val
        s = str(val).upper().strip() if val is not None else "R0"
        legacy_map = {
            "UNKNOWN": cls.R0_READ_ONLY,
            "LOW": cls.R0_READ_ONLY,
            "MEDIUM": cls.R1_LOCAL_WRITE,
            "HIGH": cls.R2_REPO_MUTATION,
            "CRITICAL": cls.R4_INFRA_MUTATION,
            "R0": cls.R0_READ_ONLY,
            "R1": cls.R1_LOCAL_WRITE,
            "R2": cls.R2_REPO_MUTATION,
            "R3": cls.R3_EXTERNAL_SIDE_EFFECT,
            "R4": cls.R4_INFRA_MUTATION,
            "R5": cls.R5_DESTRUCTIVE,
        }
        return legacy_map.get(s, cls.R0_READ_ONLY)


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUESTED = "REQUESTED"
    PENDING_ACK = "PENDING_ACK"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    EXECUTED = "EXECUTED"


class ArtifactType(str, Enum):
    SOURCE_CODE = "source_code"
    CONFIG = "config"
    TEST_REPORT = "test_report"
    EVIDENCE = "evidence"
    METRIC = "metric"
    LOG = "log"
    BINARY = "binary"
    OTHER = "other"


@dataclass
class Artifact:
    artifact_id: str
    mission_id: str
    task_id: str
    producer: str
    artifact_type: ArtifactType | str = ArtifactType.OTHER
    path: str = ""
    size_bytes: int = 0
    sha256: str = ""
    environment: Dict[str, Any] = field(default_factory=dict)
    verification_state: str = "UNVERIFIED"
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_artifacts: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _identifier(self.artifact_id, "artifact_id")
        _identifier(self.mission_id, "mission_id")
        _identifier(self.task_id, "task_id")
        _identifier(self.producer, "producer")
        _nonnegative(self.size_bytes, "size_bytes", integer=True)
        if isinstance(self.artifact_type, str):
            try:
                self.artifact_type = ArtifactType(self.artifact_type)
            except ValueError:
                self.artifact_type = ArtifactType.OTHER

    def compute_hash(self, base_dir: Optional[Path] = None) -> str:
        if not self.path:
            return ""
        p = Path(self.path)
        if not p.is_absolute() and base_dir:
            p = base_dir / p
        if not p.exists() or not p.is_file():
            return ""
        hasher = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        self.sha256 = hasher.hexdigest()
        self.size_bytes = p.stat().st_size
        return self.sha256

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "artifact_id": self.artifact_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "producer": self.producer,
            "artifact_type": self.artifact_type.value if isinstance(self.artifact_type, ArtifactType) else str(self.artifact_type),
            "path": self.path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "environment": self.environment,
            "verification_state": self.verification_state,
            "created_utc": self.created_utc,
            "parent_artifacts": self.parent_artifacts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Artifact:
        validate_schema_version(data)
        atype = data.get("artifact_type", ArtifactType.OTHER)
        try:
            atype = ArtifactType(atype)
        except ValueError:
            atype = ArtifactType.OTHER
        return cls(
            artifact_id=data["artifact_id"],
            mission_id=data.get("mission_id", "mis-legacy"),
            task_id=data.get("task_id", "tsk-legacy"),
            producer=data.get("producer", "unknown"),
            artifact_type=atype,
            path=data.get("path", ""),
            size_bytes=data.get("size_bytes", 0),
            sha256=data.get("sha256", ""),
            environment=data.get("environment", {}),
            verification_state=data.get("verification_state", "UNVERIFIED"),
            created_utc=data.get("created_utc", datetime.now(timezone.utc).isoformat()),
            parent_artifacts=data.get("parent_artifacts", [])
        )


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class VerificationType(str, Enum):
    FILE_EXISTS = "file_exists"
    TEST_PASSES = "test_passes"
    COMMAND_EXIT_ZERO = "command_exit_zero"
    SCHEMA_VALID = "schema_valid"
    ARTIFACT_HASH_MATCHES = "artifact_hash_matches"
    HTTP_HEALTH_CHECK = "http_health_check"
    LINT_CLEAN = "lint_clean"
    TYPECHECK_CLEAN = "typecheck_clean"
    NO_REGRESSION = "no_regression"


class MissionStatus(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class VerificationRequirement:
    check_type: VerificationType | str
    target: str = ""
    expected: Any = None
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.check_type = VerificationType(self.check_type)
        self.status = VerificationStatus(self.status)
        if not isinstance(self.target, str) or not isinstance(self.evidence, dict):
            raise ValueError("Invalid verification target or evidence")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_type": str(self.check_type.value if isinstance(self.check_type, VerificationType) else self.check_type),
            "target": self.target,
            "expected": self.expected,
            "status": str(self.status.value if isinstance(self.status, VerificationStatus) else self.status),
            "evidence": self.evidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VerificationRequirement:
        validate_schema_version(data)
        ctype = data.get("check_type", VerificationType.FILE_EXISTS)
        try:
            ctype = VerificationType(ctype)
        except ValueError:
            pass
        status = data.get("status", VerificationStatus.UNVERIFIED)
        try:
            status = VerificationStatus(status)
        except ValueError:
            pass
        return cls(
            check_type=ctype,
            target=data.get("target", ""),
            expected=data.get("expected"),
            status=status,
            evidence=data.get("evidence", {})
        )


@dataclass
class TaskNode:
    task_id: str
    title: str
    description: str = ""
    agent_profile: str = "Quantum-AuditAgent"
    required_skills: List[str] = field(default_factory=list)
    read_scopes: List[str] = field(default_factory=list)
    write_scopes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    verification_requirements: List[VerificationRequirement] = field(default_factory=list)
    artifacts: List[Artifact | str] = field(default_factory=list)
    execution_result: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 60.0
    start_utc: Optional[str] = None
    end_utc: Optional[str] = None
    node_id: str = "local"
    risk_level: RiskLevel | str = "UNKNOWN"
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    estimated_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None

    @property
    def canonical_risk_level(self) -> RiskLevel:
        return RiskLevel.normalize(self.risk_level)

    def __post_init__(self) -> None:
        _identifier(self.task_id, "task_id")
        _identifier(self.title, "title")
        _identifier(self.agent_profile, "agent_profile")
        _identifier(self.node_id, "node_id")
        valid_risks = {"UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL", "R0", "R1", "R2", "R3", "R4", "R5"}
        if str(self.risk_level).upper() not in valid_risks and not isinstance(self.risk_level, RiskLevel):
            raise ValueError("Invalid task risk_level")
        if isinstance(self.approval_status, str):
            try:
                self.approval_status = ApprovalStatus(self.approval_status)
            except ValueError:
                self.approval_status = ApprovalStatus.NOT_REQUIRED
        elif not isinstance(self.approval_status, ApprovalStatus):
            self.approval_status = ApprovalStatus.NOT_REQUIRED

        if self.estimated_tokens is not None:
            _nonnegative(self.estimated_tokens, "estimated_tokens", integer=True)
        if self.estimated_cost_usd is not None:
            _nonnegative(self.estimated_cost_usd, "estimated_cost_usd")
        self.status = TaskStatus(self.status)
        for name in ("required_skills", "read_scopes", "write_scopes", "dependencies"):
            _strings(getattr(self, name), name)
        _artifacts(self.artifacts, "artifacts")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("Duplicate task dependencies")
        if not isinstance(self.verification_requirements, list) or any(
            not isinstance(v, VerificationRequirement) for v in self.verification_requirements
        ):
            raise ValueError("Invalid verification requirements")
        _nonnegative(self.retry_count, "retry_count", integer=True)
        _nonnegative(self.max_retries, "max_retries", integer=True)
        _nonnegative(self.timeout_seconds, "timeout_seconds", positive=True)
        if self.execution_result is not None and not isinstance(self.execution_result, dict):
            raise ValueError("execution_result must be an object or null")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "agent_profile": self.agent_profile,
            "required_skills": sorted(self.required_skills),
            "read_scopes": sorted(self.read_scopes),
            "write_scopes": sorted(self.write_scopes),
            "dependencies": sorted(self.dependencies),
            "status": str(self.status.value if isinstance(self.status, TaskStatus) else self.status),
            "verification_requirements": [v.to_dict() for v in self.verification_requirements],
            "artifacts": [a.to_dict() if isinstance(a, Artifact) else str(a) for a in self.artifacts],
            "execution_result": self.execution_result,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "start_utc": self.start_utc,
            "end_utc": self.end_utc,
            "node_id": self.node_id,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else str(self.risk_level),
            "approval_status": self.approval_status.value if isinstance(self.approval_status, ApprovalStatus) else str(self.approval_status),
            "estimated_tokens": self.estimated_tokens,
            "estimated_cost_usd": self.estimated_cost_usd
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskNode:
        validate_schema_version(data)
        for name in ("required_skills", "read_scopes", "write_scopes", "dependencies"):
            _strings(data.get(name, []), name)
        raw_artifacts = data.get("artifacts", [])
        if not isinstance(raw_artifacts, list):
            raise ValueError("artifacts must be an array")
        parsed_artifacts: List[Artifact | str] = []
        for a in raw_artifacts:
            if isinstance(a, dict) and "artifact_id" in a:
                parsed_artifacts.append(Artifact.from_dict(a))
            elif isinstance(a, str):
                parsed_artifacts.append(a)
            elif isinstance(a, Artifact):
                parsed_artifacts.append(a)
            else:
                raise ValueError("Artifact entry must be a string or Artifact object")
        if not isinstance(data.get("verification_requirements", []), list):
            raise ValueError("verification_requirements must be an array")
        vreqs = [
            VerificationRequirement.from_dict(v) if isinstance(v, dict) else v
            for v in data.get("verification_requirements", [])
        ]
        status = data.get("status", TaskStatus.PENDING)
        try:
            status = TaskStatus(status)
        except ValueError:
            pass
        app_status = data.get("approval_status", ApprovalStatus.NOT_REQUIRED)
        try:
            app_status = ApprovalStatus(app_status)
        except ValueError:
            app_status = ApprovalStatus.NOT_REQUIRED
        return cls(
            task_id=data["task_id"],
            title=data.get("title", data["task_id"]),
            description=data.get("description", ""),
            agent_profile=data.get("agent_profile", "Quantum-AuditAgent"),
            required_skills=list(data.get("required_skills", [])),
            read_scopes=list(data.get("read_scopes", [])),
            write_scopes=list(data.get("write_scopes", [])),
            dependencies=list(data.get("dependencies", [])),
            status=status,
            verification_requirements=vreqs,
            artifacts=parsed_artifacts,
            execution_result=data.get("execution_result"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 60.0),
            start_utc=data.get("start_utc"),
            end_utc=data.get("end_utc"),
            node_id=data.get("node_id", "local"),
            risk_level=data.get("risk_level", "UNKNOWN"),
            approval_status=app_status,
            estimated_tokens=data.get("estimated_tokens"),
            estimated_cost_usd=data.get("estimated_cost_usd")
        )


@dataclass
class MissionBudget:
    max_iterations: int = 20
    max_token_budget: int = 100_000
    max_runtime_seconds: float = 600.0
    max_tool_calls: int = 50
    max_retries: int = 5

    def __post_init__(self) -> None:
        for name in ("max_iterations", "max_token_budget", "max_tool_calls", "max_retries"):
            _nonnegative(getattr(self, name), name, integer=True, positive=name == "max_iterations")
        _nonnegative(self.max_runtime_seconds, "max_runtime_seconds", positive=True)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MissionBudget:
        validate_schema_version(data)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Mission:
    mission_id: str
    goal: str
    status: MissionStatus = MissionStatus.PENDING
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_utc: Optional[str] = None
    budget: MissionBudget = field(default_factory=MissionBudget)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_ledger: List[Dict[str, Any]] = field(default_factory=list)
    dag: Any = None

    def __post_init__(self) -> None:
        _identifier(self.mission_id, "mission_id")
        _identifier(self.goal, "goal")
        self.status = MissionStatus(self.status)
        if not isinstance(self.budget, MissionBudget) or not isinstance(self.metadata, dict):
            raise ValueError("Invalid mission budget or metadata")
        if not isinstance(self.evidence_ledger, list) or any(not isinstance(e, dict) for e in self.evidence_ledger):
            raise ValueError("evidence_ledger must be an array of objects")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "mission_id": self.mission_id,
            "goal": self.goal,
            "status": str(self.status.value if isinstance(self.status, MissionStatus) else self.status),
            "created_utc": self.created_utc,
            "completed_utc": self.completed_utc,
            "budget": self.budget.to_dict(),
            "metadata": self.metadata,
            "evidence_ledger": self.evidence_ledger,
            "dag": self.dag.to_dict() if self.dag is not None else {"schema_version": SCHEMA_VERSION, "nodes": [], "edges": []}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Mission:
        validate_schema_version(data)
        from .dag import ExecutionDAG
        status = data.get("status", MissionStatus.PENDING)
        try:
            status = MissionStatus(status)
        except ValueError:
            pass
        budget = MissionBudget.from_dict(data.get("budget", {}))
        return cls(
            mission_id=data["mission_id"],
            goal=data["goal"],
            status=status,
            created_utc=data.get("created_utc", datetime.now(timezone.utc).isoformat()),
            completed_utc=data.get("completed_utc"),
            budget=budget,
            metadata=data.get("metadata", {}),
            evidence_ledger=data.get("evidence_ledger", []),
            dag=ExecutionDAG.from_dict(data.get("dag", {"nodes": [], "edges": []}))
        )
