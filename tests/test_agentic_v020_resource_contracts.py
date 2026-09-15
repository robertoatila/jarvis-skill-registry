"""v0.2.0 contracts for evidence-aware resource accounting."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

from tooling.agentic.budgets import BudgetLimits, BudgetTracker
from tooling.agentic.telemetry import TelemetryCollector


class TestV020ResourceContracts(unittest.TestCase):
    def _resource_usage(self):
        try:
            return importlib.import_module("tooling.agentic.resource_usage")
        except ModuleNotFoundError as exc:
            self.fail(f"resource measurement contract is missing: {exc}")

    def test_resource_measurement_contract_exposes_explicit_unknown(self):
        resource_usage = self._resource_usage()
        measurement = resource_usage.ResourceMeasurement.unknown("usd")
        self.assertEqual(measurement.status, resource_usage.MeasurementStatus.UNKNOWN)
        self.assertIsNone(measurement.value)
        self.assertEqual(measurement.unit, "usd")
        self.assertIsNone(measurement.method)

    def test_token_charge_does_not_infer_usd_cost(self):
        resource_usage = self._resource_usage()
        tracker = BudgetTracker(BudgetLimits(token_budget=10_000, cost_budget_usd=1.0))

        self.assertTrue(hasattr(tracker, "cost_measurement"), "BudgetTracker must expose cost_measurement")
        self.assertEqual(tracker.cost_measurement.status, resource_usage.MeasurementStatus.UNKNOWN)

        try:
            tracker.charge_tokens(1_000, method="provider_reported")
        except TypeError as exc:
            self.fail(f"charge_tokens must accept measurement method: {exc}")

        self.assertEqual(tracker.tokens_consumed, 1_000)
        self.assertEqual(tracker.token_measurement.status, resource_usage.MeasurementStatus.MEASURED)
        self.assertEqual(tracker.token_measurement.method, "provider_reported")
        self.assertEqual(tracker.cost_measurement.status, resource_usage.MeasurementStatus.UNKNOWN)
        self.assertIsNone(tracker.cost_measurement.value)

    def test_explicit_provider_cost_is_recorded_and_enforced(self):
        resource_usage = self._resource_usage()
        tracker = BudgetTracker(BudgetLimits(token_budget=10_000, cost_budget_usd=0.004))

        self.assertTrue(hasattr(tracker, "charge_cost_usd"), "BudgetTracker must expose charge_cost_usd")
        tracker.charge_cost_usd(0.0042, method="provider_reported")

        self.assertEqual(tracker.cost_measurement.status, resource_usage.MeasurementStatus.MEASURED)
        self.assertEqual(tracker.cost_measurement.value, 0.0042)
        self.assertEqual(tracker.cost_measurement.method, "provider_reported")
        self.assertEqual(tracker.status, "TRIPPED")
        allowed, reason = tracker.check_limits()
        self.assertFalse(allowed)
        self.assertIn("COST_BUDGET_EXCEEDED", reason or "")

    def test_empty_telemetry_is_no_data_not_perfect_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            collector = TelemetryCollector(ledger_file=Path(tmp) / "spans.jsonl")
            metrics = collector.get_metrics_summary()

        self.assertEqual(metrics.get("data_status"), "NO_DATA")
        self.assertIsNone(metrics.get("success_rate"))
        self.assertIsNone(metrics.get("total_tokens"))
        token_measurement = metrics.get("token_measurement")
        self.assertIsInstance(token_measurement, dict)
        self.assertEqual(token_measurement.get("status"), "UNKNOWN")
        self.assertIsNone(token_measurement.get("value"))

    def test_budget_serialization_preserves_measurement_status(self):
        resource_usage = self._resource_usage()
        tracker = BudgetTracker(BudgetLimits(token_budget=10_000, cost_budget_usd=1.0))
        tracker.charge_tokens(0, method="no_model_invocation")
        snapshot = tracker.to_dict()

        self.assertEqual(snapshot["token_measurement"]["status"], resource_usage.MeasurementStatus.MEASURED.value)
        self.assertEqual(snapshot["token_measurement"]["value"], 0)
        self.assertEqual(snapshot["token_measurement"]["method"], "no_model_invocation")
        self.assertEqual(snapshot["cost_measurement"]["status"], resource_usage.MeasurementStatus.UNKNOWN.value)
        self.assertIsNone(snapshot["cost_measurement"]["value"])


if __name__ == "__main__":
    unittest.main()
