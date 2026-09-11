"""
test_agentic_budgets.py // Unit tests for Runtime Budgets & Circuit Breakers (Phase 22)
"""

import unittest
from tooling.agentic.budgets import (
    BudgetTracker,
    BudgetLimits,
    CircuitBreakerTrippedError
)


class TestRuntimeBudgets(unittest.TestCase):

    def test_01_healthy_initial_state(self):
        limits = BudgetLimits(token_budget=10_000, runtime_budget_seconds=60.0, max_tool_calls=10)
        tracker = BudgetTracker(limits=limits)
        self.assertEqual(tracker.status, "HEALTHY")
        allowed, reason = tracker.check_limits()
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_02_warning_at_80_percent(self):
        limits = BudgetLimits(token_budget=1_000, runtime_budget_seconds=60.0, max_tool_calls=10)
        tracker = BudgetTracker(limits=limits)
        
        # Charge 850 tokens (85%)
        tracker.charge_tokens(850)
        self.assertEqual(tracker.status, "WARNING_80_PERCENT")
        allowed, _ = tracker.check_limits()
        self.assertTrue(allowed, "Warning state still allows execution before hard limit")

    def test_03_token_exhaustion_trips_circuit_breaker(self):
        limits = BudgetLimits(token_budget=1_000, runtime_budget_seconds=60.0, max_tool_calls=10)
        tracker = BudgetTracker(limits=limits)

        # Charge 1050 tokens (105%)
        tracker.charge_tokens(1050)
        self.assertEqual(tracker.status, "TRIPPED")
        allowed, reason = tracker.check_limits()
        self.assertFalse(allowed)
        self.assertIn("TOKEN_BUDGET_EXCEEDED", reason)

        with self.assertRaises(CircuitBreakerTrippedError):
            tracker.assert_within_limits()

    def test_04_tool_calls_exhaustion_trips_circuit_breaker(self):
        limits = BudgetLimits(token_budget=10_000, runtime_budget_seconds=60.0, max_tool_calls=5)
        tracker = BudgetTracker(limits=limits)

        # Charge 6 tool calls
        for _ in range(6):
            tracker.charge_tool_call(1)

        self.assertEqual(tracker.status, "TRIPPED")
        allowed, reason = tracker.check_limits()
        self.assertFalse(allowed)
        self.assertIn("TOOL_CALL_BUDGET_EXCEEDED", reason)

    def test_05_iteration_budget_trips_circuit_breaker(self):
        limits = BudgetLimits(token_budget=10_000, max_iterations=3)
        tracker = BudgetTracker(limits=limits)

        for _ in range(4):
            tracker.charge_iteration(1)

        self.assertEqual(tracker.status, "TRIPPED")
        with self.assertRaises(CircuitBreakerTrippedError):
            tracker.assert_within_limits()


if __name__ == "__main__":
    unittest.main()
