"""
budgets.py // J.A.R.V.I.S. Runtime Budgets & Circuit Breaker Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces Section 13 (Autonomous Execution Safety) & Section 9 (Concurrency Bounds):
- Hard deterministic limits on Tokens, Wall Clock Runtime, Tool Calls, Iterations, and Cost
- 80% Early warning threshold before hard exhaustion
- Fail-closed CircuitBreakerTrippedError prevents runaway autonomous loops
"""

from __future__ import annotations
import math
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple

from .resource_usage import MeasurementStatus, ResourceMeasurement


class CircuitBreakerTrippedError(RuntimeError):
    """Raised immediately when a declared safety budget is breached."""
    def __init__(self, reason: str, budget_summary: Dict[str, Any]):
        super().__init__(f"Circuit breaker tripped: {reason}")
        self.reason = reason
        self.budget_summary = budget_summary


@dataclass
class BudgetLimits:
    token_budget: int = 100_000
    runtime_budget_seconds: float = 300.0
    max_tool_calls: int = 50
    max_iterations: int = 10
    cost_budget_usd: float = 5.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BudgetTracker:
    """
    Monitors and enforces resource allowances during mission and goal execution.
    Resource evidence is tracked independently by unit: tokens never imply USD.
    """

    def __init__(
        self,
        limits: Optional[BudgetLimits] = None,
        budget_id: Optional[str] = None
    ):
        self.budget_id = budget_id or f"bdg-{uuid.uuid4().hex[:10]}"
        self.limits = limits or BudgetLimits()
        self.tokens_consumed = 0
        self.seconds_elapsed = 0.0
        self.tool_calls_count = 0
        self.iterations_completed = 0
        # Compatibility accumulator for callers that still subtract a numeric
        # headroom. Serialized evidence uses cost_measurement and reports None
        # until an actual or estimated cost is explicitly supplied.
        self.cost_consumed_usd = 0.0
        self.token_measurement = ResourceMeasurement.unknown("tokens")
        self.cost_measurement = ResourceMeasurement.unknown("usd")
        self._start_perf = time.perf_counter()
        self.status = "HEALTHY"
        self.breach_reason: Optional[str] = None

    def _sync_elapsed_time(self) -> None:
        self.seconds_elapsed = round(time.perf_counter() - self._start_perf, 3)

    def charge_tokens(
        self,
        count: int,
        method: str = "runtime_counted",
        status: MeasurementStatus = MeasurementStatus.MEASURED
    ) -> None:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("INVALID_TOKEN_MEASUREMENT")
        status = MeasurementStatus(status)
        if status not in (MeasurementStatus.MEASURED, MeasurementStatus.ESTIMATED):
            raise ValueError("TOKEN_CHARGE_REQUIRES_AVAILABLE_MEASUREMENT")
        self.tokens_consumed += count
        if status == MeasurementStatus.MEASURED:
            self.token_measurement = ResourceMeasurement.measured(
                self.tokens_consumed, "tokens", method
            )
        else:
            self.token_measurement = ResourceMeasurement.estimated(
                self.tokens_consumed, "tokens", method
            )
        # Deliberately no token -> USD conversion. Cost stays UNKNOWN until
        # charge_cost_usd() receives independent evidence.
        self._evaluate_status()

    def charge_cost_usd(
        self,
        amount: float,
        method: str,
        status: MeasurementStatus = MeasurementStatus.MEASURED
    ) -> None:
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ValueError("INVALID_COST_MEASUREMENT")
        amount = float(amount)
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("INVALID_COST_MEASUREMENT")
        status = MeasurementStatus(status)
        if status not in (MeasurementStatus.MEASURED, MeasurementStatus.ESTIMATED):
            raise ValueError("COST_CHARGE_REQUIRES_AVAILABLE_MEASUREMENT")
        self.cost_consumed_usd = round(self.cost_consumed_usd + amount, 10)
        if status == MeasurementStatus.MEASURED:
            self.cost_measurement = ResourceMeasurement.measured(
                self.cost_consumed_usd, "usd", method
            )
        else:
            self.cost_measurement = ResourceMeasurement.estimated(
                self.cost_consumed_usd, "usd", method
            )
        self._evaluate_status()

    def charge_tool_call(self, count: int = 1) -> None:
        self.tool_calls_count += max(0, count)
        self._evaluate_status()

    def charge_iteration(self, count: int = 1) -> None:
        self.iterations_completed += max(0, count)
        self._evaluate_status()

    def _evaluate_status(self) -> None:
        self._sync_elapsed_time()

        # Check for exhaustion breaches
        if self.tokens_consumed > self.limits.token_budget:
            self.status = "TRIPPED"
            self.breach_reason = f"TOKEN_BUDGET_EXCEEDED ({self.tokens_consumed} > {self.limits.token_budget})"
            return

        if self.seconds_elapsed > self.limits.runtime_budget_seconds:
            self.status = "TRIPPED"
            self.breach_reason = f"RUNTIME_BUDGET_EXCEEDED ({self.seconds_elapsed}s > {self.limits.runtime_budget_seconds}s)"
            return

        if self.tool_calls_count > self.limits.max_tool_calls:
            self.status = "TRIPPED"
            self.breach_reason = f"TOOL_CALL_BUDGET_EXCEEDED ({self.tool_calls_count} > {self.limits.max_tool_calls})"
            return

        if self.iterations_completed > self.limits.max_iterations:
            self.status = "TRIPPED"
            self.breach_reason = f"ITERATION_BUDGET_EXCEEDED ({self.iterations_completed} > {self.limits.max_iterations})"
            return

        if (
            self.cost_measurement.status in (MeasurementStatus.MEASURED, MeasurementStatus.ESTIMATED)
            and self.cost_consumed_usd > self.limits.cost_budget_usd
        ):
            self.status = "TRIPPED"
            self.breach_reason = f"COST_BUDGET_EXCEEDED (${self.cost_consumed_usd} > ${self.limits.cost_budget_usd})"
            return

        # Check for 80% warning threshold. Unknown cost is not converted to zero
        # evidence; it is simply omitted from ratio evaluation.
        ratios = [
            self.tokens_consumed / self.limits.token_budget if self.limits.token_budget else 0,
            self.seconds_elapsed / self.limits.runtime_budget_seconds if self.limits.runtime_budget_seconds else 0,
            self.tool_calls_count / self.limits.max_tool_calls if self.limits.max_tool_calls else 0,
            self.iterations_completed / self.limits.max_iterations if self.limits.max_iterations else 0,
        ]
        if (
            self.cost_measurement.status in (MeasurementStatus.MEASURED, MeasurementStatus.ESTIMATED)
            and self.limits.cost_budget_usd
        ):
            ratios.append(self.cost_consumed_usd / self.limits.cost_budget_usd)

        if any(r >= 0.80 for r in ratios):
            self.status = "WARNING_80_PERCENT"
        else:
            self.status = "HEALTHY"
            self.breach_reason = None

    def check_limits(self) -> Tuple[bool, Optional[str]]:
        """Returns (is_allowed, error_reason_if_tripped)."""
        self._evaluate_status()
        if self.status == "TRIPPED":
            return False, self.breach_reason
        return True, None

    def assert_within_limits(self) -> None:
        """Throws CircuitBreakerTrippedError if budget is exhausted."""
        allowed, reason = self.check_limits()
        if not allowed:
            raise CircuitBreakerTrippedError(reason or "Budget exhausted", self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        self._sync_elapsed_time()
        return {
            "budget_id": self.budget_id,
            "token_budget": self.limits.token_budget,
            "tokens_consumed": self.tokens_consumed,
            "token_measurement": self.token_measurement.to_dict(),
            "runtime_budget_seconds": self.limits.runtime_budget_seconds,
            "seconds_elapsed": self.seconds_elapsed,
            "max_tool_calls": self.limits.max_tool_calls,
            "tool_calls_count": self.tool_calls_count,
            "max_iterations": self.limits.max_iterations,
            "iterations_completed": self.iterations_completed,
            "cost_budget_usd": self.limits.cost_budget_usd,
            "cost_consumed_usd": self.cost_measurement.value,
            "cost_measurement": self.cost_measurement.to_dict(),
            "status": self.status,
            "breach_reason": self.breach_reason
        }
