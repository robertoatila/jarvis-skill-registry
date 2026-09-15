"""Correlated execution receipt primitives for J.A.R.V.I.S. v0.2.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .models import SCHEMA_VERSION, _identifier
from .resource_usage import ResourceMeasurement


@dataclass
class ExecutionReceipt:
    receipt_id: str
    mission_id: str
    task_id: str
    attempt_id: str
    trace_id: str
    adapter: str
    invocation_occurred: bool
    execution_state: str
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    output_reference: Optional[str] = None
    resource_usage: Dict[str, ResourceMeasurement | Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "mission_id", "task_id", "attempt_id", "trace_id", "adapter", "execution_state", "created_utc"):
            _identifier(getattr(self, name), name)
        if type(self.invocation_occurred) is not bool:
            raise ValueError("invocation_occurred must be a boolean")
        if not isinstance(self.resource_usage, dict) or not isinstance(self.metadata, dict):
            raise ValueError("resource_usage and metadata must be objects")
        for key, measurement in self.resource_usage.items():
            _identifier(key, "resource_usage key")
            if not isinstance(measurement, (ResourceMeasurement, dict)):
                raise ValueError("resource_usage values must be ResourceMeasurement or serialized measurement objects")

    def to_dict(self) -> Dict[str, Any]:
        usage: Dict[str, Any] = {}
        for key in sorted(self.resource_usage):
            value = self.resource_usage[key]
            usage[key] = value.to_dict() if isinstance(value, ResourceMeasurement) else dict(value)
        return {
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "trace_id": self.trace_id,
            "created_utc": self.created_utc,
            "adapter": self.adapter,
            "invocation_occurred": self.invocation_occurred,
            "execution_state": self.execution_state,
            "output_reference": self.output_reference,
            "resource_usage": usage,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionReceipt":
        return cls(
            receipt_id=data["receipt_id"],
            mission_id=data["mission_id"],
            task_id=data["task_id"],
            attempt_id=data["attempt_id"],
            trace_id=data["trace_id"],
            created_utc=data["created_utc"],
            adapter=data["adapter"],
            invocation_occurred=data["invocation_occurred"],
            execution_state=data["execution_state"],
            output_reference=data.get("output_reference"),
            resource_usage=dict(data.get("resource_usage", {})),
            metadata=dict(data.get("metadata", {})),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )
