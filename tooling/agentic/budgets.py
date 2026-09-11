"""
budgets.py // J.A.R.V.I.S. Runtime Budgets & Circuit Breaker Engine
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
Enforces Section 13 (Autonomous Execution Safety) & Section 9 (Concurrency Bounds):
- Hard deterministic limits on Tokens, Wall Clock Runtime, Tool Calls, Iterations, and Cost
- 80% Early warning threshold before hard exhaustion
- Fail-closed CircuitBreakerTrippedError prevents runaway autonomous loops
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple


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
    Acts as an infallible circuit breaker against infinite loops or resource drain.
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
        self.cost_consumed_usd = 0.0
        self._start_perf = time.perf_counter()
        self.status = "HEALTHY"
        self.breach_reason: Optional[str] = None

    def _sync_elapsed_time(self) -> None:
        self.seconds_elapsed = round(time.perf_counter() - self._start_perf, 3)

    def charge_tokens(self, count: int) -> None:
        self.tokens_consumed += max(0, count)
        # Cost estimate: ~$0.002 per 1k tokens standard baseline
        self.cost_consumed_usd = round(self.tokens_consumed * 0.000002, 4)
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

        if self.cost_consumed_usd > self.limits.cost_budget_usd:
            self.status = "TRIPPED"
            self.breach_reason = f"COST_BUDGET_EXCEEDED (${self.cost_consumed_usd} > ${self.limits.cost_budget_usd})"
            return

        # Check for 80% warning threshold
        ratios = [
            self.tokens_consumed / self.limits.token_budget if self.limits.token_budget else 0,
            self.seconds_elapsed / self.limits.runtime_budget_seconds if self.limits.runtime_budget_seconds else 0,
            self.tool_calls_count / self.limits.max_tool_calls if self.limits.max_tool_calls else 0,
            self.iterations_completed / self.limits.max_iterations if self.limits.max_iterations else 0,
            self.cost_consumed_usd / self.limits.cost_budget_usd if self.limits.cost_budget_usd else 0
        ]

        if any(r >= 0.80 for r in ratios):
            self.status = "WARNING_80_PERCENT"
        else:
            self.status = "HEALTHY"

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
            "runtime_budget_seconds": self.limits.runtime_budget_seconds,
            "seconds_elapsed": self.seconds_elapsed,
            "max_tool_calls": self.limits.max_tool_calls,
            "tool_calls_count": self.tool_calls_count,
            "max_iterations": self.limits.max_iterations,
            "iterations_completed": self.iterations_completed,
            "cost_budget_usd": self.limits.cost_budget_usd,
            "cost_consumed_usd": self.cost_consumed_usd,
            "status": self.status,
            "breach_reason": self.breach_reason
        }
