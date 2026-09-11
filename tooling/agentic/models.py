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
        if s not in legacy_map:
            raise ValueError(f"Unrecognized risk level: '{val}'. Fail-closed policy requires explicit risk classification.")
        return legacy_map[s]


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


class ExecutionState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class VerificationState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    STALE = "STALE"


class RecoveryState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    RETRY_PENDING = "RETRY_PENDING"
    RECONCILIATION_PENDING = "RECONCILIATION_PENDING"
    COMPENSATION_PENDING = "COMPENSATION_PENDING"
    RECOVERY_PENDING = "RECOVERY_PENDING"
    RECOVERED = "RECOVERED"
    UNRECOVERABLE = "UNRECOVERABLE"


class MissionOutcome(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    PARTIALLY_SUCCEEDED = "PARTIALLY_SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ABORTED_BY_POLICY = "ABORTED_BY_POLICY"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"


class FailureClass(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    VALIDATION = "VALIDATION"
    POLICY = "POLICY"
    AUTHORIZATION = "AUTHORIZATION"
    CONFLICT = "CONFLICT"
    TIMEOUT = "TIMEOUT"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    MALFORMED_RESULT = "MALFORMED_RESULT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    COMPATIBILITY = "COMPATIBILITY"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class FailureAttribution(str, Enum):
    PLANNER = "PLANNER"
    RESOLVER = "RESOLVER"
    AGENT = "AGENT"
    SKILL = "SKILL"
    TOOL = "TOOL"
    NODE = "NODE"
    DEPENDENCY = "DEPENDENCY"
    ENVIRONMENT = "ENVIRONMENT"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    POLICY = "POLICY"
    UNKNOWN = "UNKNOWN"


class SideEffectType(str, Enum):
    PURE = "PURE"
    READ_ONLY = "READ_ONLY"
    LOCAL_WRITE = "LOCAL_WRITE"
    REPOSITORY_WRITE = "REPOSITORY_WRITE"
    EXTERNAL_WRITE = "EXTERNAL_WRITE"
    INFRASTRUCTURE_MUTATION = "INFRASTRUCTURE_MUTATION"
    DESTRUCTIVE = "DESTRUCTIVE"


class IdempotencySemantics(str, Enum):
    IDEMPOTENT = "IDEMPOTENT"
    RETRY_SAFE = "RETRY_SAFE"
    IDEMPOTENCY_KEY_REQUIRED = "IDEMPOTENCY_KEY_REQUIRED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    COMPENSATION_REQUIRED = "COMPENSATION_REQUIRED"
    UNSAFE_TO_RETRY = "UNSAFE_TO_RETRY"


@dataclass
class SideEffectRecord:
    side_effect_id: str
    side_effect_type: SideEffectType | str = SideEffectType.PURE
    target: str = ""
    expected_change: str = ""
    observed_change: Optional[str] = None
    idempotency: IdempotencySemantics | str = IdempotencySemantics.UNSAFE_TO_RETRY
    rollback_target: Optional[str] = None
    compensation_action: Optional[str] = None
    verification_requirement_id: Optional[str] = None
    provenance_hash: str = ""

    def __post_init__(self) -> None:
        _identifier(self.side_effect_id, "side_effect_id")
        if isinstance(self.side_effect_type, str):
            try:
                self.side_effect_type = SideEffectType(self.side_effect_type)
            except ValueError:
                raise ValueError(f"Invalid side_effect_type: '{self.side_effect_type}'")
        elif not isinstance(self.side_effect_type, SideEffectType):
            raise ValueError(f"Invalid side_effect_type: '{self.side_effect_type}'")

        if isinstance(self.idempotency, str):
            try:
                self.idempotency = IdempotencySemantics(self.idempotency)
            except ValueError:
                raise ValueError(f"Invalid idempotency semantics: '{self.idempotency}'")
        elif not isinstance(self.idempotency, IdempotencySemantics):
            raise ValueError(f"Invalid idempotency semantics: '{self.idempotency}'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "side_effect_id": self.side_effect_id,
            "side_effect_type": self.side_effect_type.value if isinstance(self.side_effect_type, SideEffectType) else str(self.side_effect_type),
            "target": self.target,
            "expected_change": self.expected_change,
            "observed_change": self.observed_change,
            "idempotency": self.idempotency.value if isinstance(self.idempotency, IdempotencySemantics) else str(self.idempotency),
            "rollback_target": self.rollback_target,
            "compensation_action": self.compensation_action,
            "verification_requirement_id": self.verification_requirement_id,
            "provenance_hash": self.provenance_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SideEffectRecord:
        validate_schema_version(data)
        return cls(
            side_effect_id=data["side_effect_id"],
            side_effect_type=data.get("side_effect_type", SideEffectType.PURE),
            target=data.get("target", ""),
            expected_change=data.get("expected_change", ""),
            observed_change=data.get("observed_change"),
            idempotency=data.get("idempotency", IdempotencySemantics.UNSAFE_TO_RETRY),
            rollback_target=data.get("rollback_target"),
            compensation_action=data.get("compensation_action"),
            verification_requirement_id=data.get("verification_requirement_id"),
            provenance_hash=data.get("provenance_hash", "")
        )


@dataclass
class ExecutionAttempt:
    attempt_id: str
    mission_id: str
    task_id: str
    attempt_number: int = 1
    agent_id: str = "Quantum-AuditAgent"
    skill_id: str = ""
    tool_id: str = ""
    node_id: str = "local"
    started_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_utc: Optional[str] = None
    input_reference: str = ""
    output_reference: str = ""
    idempotency_key: str = ""
    execution_state: ExecutionState = ExecutionState.PENDING
    verification_state: VerificationState = VerificationState.UNVERIFIED
    recovery_state: RecoveryState = RecoveryState.NOT_REQUIRED
    outcome: MissionOutcome = MissionOutcome.OUTCOME_UNKNOWN
    failure_class: Optional[FailureClass | str] = None
    failure_attribution: Optional[FailureAttribution | str] = None
    retryable: bool = False
    side_effects: List[SideEffectRecord] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    budget_consumed: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    parent_trace_id: str = ""
    environment_fingerprint: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _identifier(self.attempt_id, "attempt_id")
        _identifier(self.mission_id, "mission_id")
        _identifier(self.task_id, "task_id")
        _nonnegative(self.attempt_number, "attempt_number", integer=True, positive=True)
        if isinstance(self.execution_state, str):
            try:
                self.execution_state = ExecutionState(self.execution_state)
            except ValueError:
                raise ValueError(f"Invalid execution_state: '{self.execution_state}'")
        elif not isinstance(self.execution_state, ExecutionState):
            raise ValueError(f"Invalid execution_state: '{self.execution_state}'")

        if isinstance(self.verification_state, str):
            try:
                self.verification_state = VerificationState(self.verification_state)
            except ValueError:
                raise ValueError(f"Invalid verification_state: '{self.verification_state}'")
        elif not isinstance(self.verification_state, VerificationState):
            raise ValueError(f"Invalid verification_state: '{self.verification_state}'")

        if isinstance(self.recovery_state, str):
            try:
                self.recovery_state = RecoveryState(self.recovery_state)
            except ValueError:
                raise ValueError(f"Invalid recovery_state: '{self.recovery_state}'")
        elif not isinstance(self.recovery_state, RecoveryState):
            raise ValueError(f"Invalid recovery_state: '{self.recovery_state}'")

        if isinstance(self.outcome, str):
            try:
                self.outcome = MissionOutcome(self.outcome)
            except ValueError:
                raise ValueError(f"Invalid outcome: '{self.outcome}'")
        elif not isinstance(self.outcome, MissionOutcome):
            raise ValueError(f"Invalid outcome: '{self.outcome}'")

        if self.failure_class is not None:
            if isinstance(self.failure_class, str):
                try:
                    self.failure_class = FailureClass(self.failure_class)
                except ValueError:
                    raise ValueError(f"Invalid failure_class: '{self.failure_class}'")
            elif not isinstance(self.failure_class, FailureClass):
                raise ValueError(f"Invalid failure_class: '{self.failure_class}'")

        if self.failure_attribution is not None:
            if isinstance(self.failure_attribution, str):
                try:
                    self.failure_attribution = FailureAttribution(self.failure_attribution)
                except ValueError:
                    raise ValueError(f"Invalid failure_attribution: '{self.failure_attribution}'")
            elif not isinstance(self.failure_attribution, FailureAttribution):
                raise ValueError(f"Invalid failure_attribution: '{self.failure_attribution}'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "attempt_id": self.attempt_id,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "attempt_number": self.attempt_number,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "tool_id": self.tool_id,
            "node_id": self.node_id,
            "started_utc": self.started_utc,
            "completed_utc": self.completed_utc,
            "input_reference": self.input_reference,
            "output_reference": self.output_reference,
            "idempotency_key": self.idempotency_key,
            "execution_state": self.execution_state.value if isinstance(self.execution_state, ExecutionState) else str(self.execution_state),
            "verification_state": self.verification_state.value if isinstance(self.verification_state, VerificationState) else str(self.verification_state),
            "recovery_state": self.recovery_state.value if isinstance(self.recovery_state, RecoveryState) else str(self.recovery_state),
            "outcome": self.outcome.value if isinstance(self.outcome, MissionOutcome) else str(self.outcome),
            "failure_class": self.failure_class.value if isinstance(self.failure_class, FailureClass) else (str(self.failure_class) if self.failure_class else None),
            "failure_attribution": self.failure_attribution.value if isinstance(self.failure_attribution, FailureAttribution) else (str(self.failure_attribution) if self.failure_attribution else None),
            "retryable": self.retryable,
            "side_effects": [s.to_dict() if isinstance(s, SideEffectRecord) else s for s in self.side_effects],
            "artifacts": self.artifacts,
            "budget_consumed": self.budget_consumed,
            "trace_id": self.trace_id,
            "parent_trace_id": self.parent_trace_id,
            "environment_fingerprint": self.environment_fingerprint
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionAttempt:
        validate_schema_version(data)
        side_effects = [
            SideEffectRecord.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("side_effects", [])
        ]
        env_fp = dict(data.get("environment_fingerprint", {}))
        if "mission_id" not in data or "task_id" not in data:
            env_fp["_migration_provenance"] = "LEGACY_SYNTHESIZED_IDENTIFIERS"

        return cls(
            attempt_id=data["attempt_id"],
            mission_id=data.get("mission_id", "mis-legacy"),
            task_id=data.get("task_id", "tsk-legacy"),
            attempt_number=data.get("attempt_number", 1),
            agent_id=data.get("agent_id", "Quantum-AuditAgent"),
            skill_id=data.get("skill_id", ""),
            tool_id=data.get("tool_id", ""),
            node_id=data.get("node_id", "local"),
            started_utc=data.get("started_utc", datetime.now(timezone.utc).isoformat()),
            completed_utc=data.get("completed_utc"),
            input_reference=data.get("input_reference", ""),
            output_reference=data.get("output_reference", ""),
            idempotency_key=data.get("idempotency_key", ""),
            execution_state=data.get("execution_state", ExecutionState.PENDING),
            verification_state=data.get("verification_state", VerificationState.UNVERIFIED),
            recovery_state=data.get("recovery_state", RecoveryState.NOT_REQUIRED),
            outcome=data.get("outcome", MissionOutcome.OUTCOME_UNKNOWN),
            failure_class=data.get("failure_class"),
            failure_attribution=data.get("failure_attribution"),
            retryable=data.get("retryable", False),
            side_effects=side_effects,
            artifacts=data.get("artifacts", []),
            budget_consumed=data.get("budget_consumed", {}),
            trace_id=data.get("trace_id", ""),
            parent_trace_id=data.get("parent_trace_id", ""),
            environment_fingerprint=env_fp
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
    REJECTED = "REJECTED"
    STALE = "STALE"


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
    action: Optional[Dict[str, Any]] = None
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
    attempts: List[ExecutionAttempt] = field(default_factory=list)

    @property
    def canonical_risk_level(self) -> RiskLevel:
        return RiskLevel.normalize(self.risk_level)

    def record_attempt(self, attempt: ExecutionAttempt) -> None:
        if not isinstance(attempt, ExecutionAttempt):
            raise ValueError("attempt must be an ExecutionAttempt instance")
        self.attempts.append(attempt)
        self.retry_count = max(self.retry_count, len(self.attempts) - 1)

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
        if not isinstance(self.attempts, list) or any(
            not isinstance(a, ExecutionAttempt) for a in self.attempts
        ):
            raise ValueError("Invalid execution attempts")
        _nonnegative(self.retry_count, "retry_count", integer=True)
        _nonnegative(self.max_retries, "max_retries", integer=True)
        _nonnegative(self.timeout_seconds, "timeout_seconds", positive=True)
        if self.execution_result is not None and not isinstance(self.execution_result, dict):
            raise ValueError("execution_result must be an object or null")
        if self.action is not None and not isinstance(self.action, dict):
            raise ValueError("action must be a dictionary or null")

    def to_dict(self) -> Dict[str, Any]:
        d = {
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
        if self.action is not None:
            d["action"] = self.action
        if self.attempts:
            d["attempts"] = [a.to_dict() if isinstance(a, ExecutionAttempt) else a for a in self.attempts]
        return d

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
        parsed_attempts: List[ExecutionAttempt] = []
        for att in data.get("attempts", []):
            if isinstance(att, dict) and "attempt_id" in att:
                parsed_attempts.append(ExecutionAttempt.from_dict(att))
            elif isinstance(att, ExecutionAttempt):
                parsed_attempts.append(att)
            else:
                raise ValueError("Attempt entry must be an ExecutionAttempt object")
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
            action=data.get("action"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 60.0),
            start_utc=data.get("start_utc"),
            end_utc=data.get("end_utc"),
            node_id=data.get("node_id", "local"),
            risk_level=data.get("risk_level", "UNKNOWN"),
            approval_status=app_status,
            estimated_tokens=data.get("estimated_tokens"),
            estimated_cost_usd=data.get("estimated_cost_usd"),
            attempts=parsed_attempts
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
