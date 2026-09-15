"""Evidence-aware resource measurement primitives for J.A.R.V.I.S. v0.2.0."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Optional


class MeasurementStatus(str, Enum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class ResourceMeasurement:
    value: Optional[float]
    unit: str
    status: MeasurementStatus
    method: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("INVALID_MEASUREMENT_UNIT")
        if not isinstance(self.status, MeasurementStatus):
            object.__setattr__(self, "status", MeasurementStatus(self.status))
        if self.status in (MeasurementStatus.UNKNOWN, MeasurementStatus.NOT_APPLICABLE):
            if self.value is not None:
                raise ValueError("UNAVAILABLE_MEASUREMENT_MUST_NOT_HAVE_VALUE")
            return
        if self.value is None or isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("AVAILABLE_MEASUREMENT_REQUIRES_NUMERIC_VALUE")
        numeric = float(self.value)
        if not math.isfinite(numeric) or numeric < 0:
            raise ValueError("INVALID_MEASUREMENT_VALUE")
        if not isinstance(self.method, str) or not self.method.strip():
            raise ValueError("AVAILABLE_MEASUREMENT_REQUIRES_METHOD")

    @classmethod
    def unknown(cls, unit: str) -> "ResourceMeasurement":
        return cls(value=None, unit=unit, status=MeasurementStatus.UNKNOWN)

    @classmethod
    def not_applicable(cls, unit: str, method: Optional[str] = None) -> "ResourceMeasurement":
        return cls(value=None, unit=unit, status=MeasurementStatus.NOT_APPLICABLE, method=method)

    @classmethod
    def measured(cls, value: float, unit: str, method: str) -> "ResourceMeasurement":
        return cls(value=value, unit=unit, status=MeasurementStatus.MEASURED, method=method)

    @classmethod
    def estimated(cls, value: float, unit: str, method: str) -> "ResourceMeasurement":
        return cls(value=value, unit=unit, status=MeasurementStatus.ESTIMATED, method=method)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data
