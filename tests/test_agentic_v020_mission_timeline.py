"""v0.2.0 Plan 3 Task 2 contracts for pure mission timeline projection."""

from __future__ import annotations

import json
import unittest

from tooling.agentic.observability import (
    MissionTimeline,
    TimelineEvent,
    TimelineProjectionError,
    project_mission_timeline,
)


MISSION_ID = "mis-timeline"
TASK_ID = "tsk-timeline"
ATTEMPT_ID = "att-timeline"
TRACE_ID = "trc-timeline"


def _receipt(
    receipt_id: str,
    created_utc: str = "2026-09-17T23:45:00+00:00",
    *,
    mission_id: str = MISSION_ID,
    task_id: str | None = TASK_ID,
    attempt_id: str | None = ATTEMPT_ID,
    trace_id: str | None = TRACE_ID,
    **extra,
):
    value = {
        "schema_version": "1.0.0",
        "receipt_id": receipt_id,
        "mission_id": mission_id,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "trace_id": trace_id,
        "created_utc": created_utc,
    }
    value.update(extra)
    return value


class TestMissionTimelineProjection(unittest.TestCase):
    def test_orders_by_timestamp_then_receipt_id_stably(self):
        receipts = [
            _receipt(
                "rcp-b",
                "2026-09-17T23:45:01+00:00",
                sources_loaded=["b"],
                serialized_bytes=20,
            ),
            _receipt(
                "rcp-z",
                "2026-09-17T23:45:00+00:00",
                decision_type="tool_routing",
                selected_candidate="local.read_file",
            ),
            _receipt(
                "rcp-a",
                "2026-09-17T23:45:01+00:00",
                sources_loaded=["a"],
                serialized_bytes=10,
            ),
        ]

        timeline = project_mission_timeline(MISSION_ID, receipts)

        self.assertIsInstance(timeline, MissionTimeline)
        self.assertTrue(all(isinstance(event, TimelineEvent) for event in timeline.events))
        self.assertEqual(
            [event.receipt_id for event in timeline.events],
            ["rcp-z", "rcp-a", "rcp-b"],
        )

    def test_projects_only_structured_state_for_all_supported_event_families(self):
        secret_reasoning = "private hidden reasoning must never be projected"
        receipts = [
            _receipt(
                "rcp-admission",
                admission_decision="ADMITTED",
                admitted=True,
                rejection_reasons=[],
                risk_level="R0",
            ),
            _receipt(
                "rcp-context",
                sources_loaded=["AGENTS.md"],
                sources_considered=["AGENTS.md", "README.md"],
                serialized_bytes=512,
                token_estimate=None,
                selection_reason="MANDATORY_FIRST_BOUNDED_CONTEXT",
                chain_of_thought=secret_reasoning,
            ),
            _receipt(
                "rcp-decision",
                decision_type="model_routing",
                candidates=["local-a", "cloud-b"],
                rejected_candidates={"cloud-b": "LOCAL_ONLY"},
                selected_candidate="local-a",
                selection_reason="POLICY_ELIGIBLE",
                prompt=secret_reasoning,
            ),
            _receipt(
                "rcp-execution",
                adapter="inference:local-a",
                invocation_occurred=True,
                execution_state="FINISHED",
                output_reference="sha256:abc",
                raw_output=secret_reasoning,
            ),
            _receipt(
                "rcp-effect",
                side_effect_id="se-001",
                side_effect_type="LOCAL_WRITE",
                target="fixture.txt",
                observed_change="file size: 10 bytes",
                idempotency="RETRY_SAFE",
                text=secret_reasoning,
            ),
            _receipt(
                "rcp-recovery",
                recovery_state="RECONCILIATION_PENDING",
                failure_class="CONFLICT",
                retryable=False,
            ),
            _receipt(
                "rcp-verification",
                execution_receipt_id="rcp-execution",
                verification_state="VERIFIED",
                evidence_ids=["ev-001"],
                metadata={"private_reasoning": secret_reasoning},
            ),
            _receipt(
                "rcp-memory",
                query="bounded runtime",
                tier_filter=["semantic"],
                matched_items=["mem-001"],
                excluded_conflicts=[],
                decay_scores={"mem-001": 0.92},
                total_tokens_estimated=12,
            ),
            _receipt(
                "rcp-governor",
                governor_action="CONTINUE",
                reason_code="EVIDENCE_AND_CONFIDENCE_SUFFICIENT",
                observation={
                    "authority_valid": True,
                    "evidence_sufficient": True,
                    "confidence": 0.96,
                },
                chain_of_thought=secret_reasoning,
            ),
            _receipt(
                "rcp-unknown",
                arbitrary_payload="not a structured timeline event",
            ),
        ]

        timeline = project_mission_timeline(MISSION_ID, receipts)

        self.assertEqual(
            [event.event_type for event in timeline.events],
            [
                "ADMISSION",
                "CONTEXT",
                "DECISION",
                "EXECUTION",
                "EFFECT",
                "RECOVERY",
                "VERIFICATION",
                "MEMORY",
                "GOVERNOR",
            ],
        )
        serialized = json.dumps(
            [event.data for event in timeline.events],
            sort_keys=True,
        )
        self.assertNotIn(secret_reasoning, serialized)
        for forbidden in ("chain_of_thought", "reasoning", "prompt", "raw_output", "text"):
            self.assertNotIn(f'"{forbidden}"', serialized)

    def test_resource_summary_aggregates_measured_values_and_preserves_unknown(self):
        receipts = [
            _receipt(
                "rcp-exec-1",
                adapter="inference:local",
                invocation_occurred=True,
                execution_state="FINISHED",
                resource_usage={
                    "tokens": {
                        "status": "MEASURED",
                        "value": 41,
                        "unit": "tokens",
                        "method": "provider_reported",
                    },
                    "cost_usd": {
                        "status": "UNKNOWN",
                        "value": None,
                        "unit": "USD",
                        "method": None,
                    },
                    "latency_ms": {
                        "status": "MEASURED",
                        "value": 12.5,
                        "unit": "ms",
                        "method": "monotonic_clock",
                    },
                },
            ),
            _receipt(
                "rcp-exec-2",
                "2026-09-17T23:45:01+00:00",
                attempt_id="att-timeline-2",
                trace_id="trc-timeline-2",
                adapter="inference:local",
                invocation_occurred=True,
                execution_state="FINISHED",
                resource_usage={
                    "tokens": {
                        "status": "MEASURED",
                        "value": 9,
                        "unit": "tokens",
                        "method": "provider_reported",
                    },
                    "cost_usd": {
                        "status": "UNKNOWN",
                        "value": None,
                        "unit": "USD",
                        "method": None,
                    },
                    "latency_ms": {
                        "status": "MEASURED",
                        "value": 7.5,
                        "unit": "ms",
                        "method": "monotonic_clock",
                    },
                },
            ),
        ]

        timeline = project_mission_timeline(MISSION_ID, receipts)

        self.assertEqual(timeline.resource_summary["attempt_count"], 2)
        self.assertEqual(
            timeline.resource_summary["tokens"],
            {"status": "MEASURED", "value": 50.0, "unit": "tokens"},
        )
        self.assertEqual(
            timeline.resource_summary["latency_ms"],
            {"status": "MEASURED", "value": 20.0, "unit": "ms"},
        )
        self.assertEqual(
            timeline.resource_summary["cost_usd"],
            {"status": "UNKNOWN", "value": None, "unit": "USD"},
        )
        self.assertIn("resources.cost_usd", timeline.unknown_fields)
        self.assertNotIn("resources.tokens", timeline.unknown_fields)

    def test_verification_summary_and_empty_no_data_semantics_are_truthful(self):
        receipts = [
            _receipt(
                "rcp-exec-1",
                adapter="local.read_file",
                invocation_occurred=True,
                execution_state="FINISHED",
            ),
            _receipt(
                "rcp-ver-1",
                execution_receipt_id="rcp-exec-1",
                verification_state="VERIFIED",
                evidence_ids=["ev-1"],
            ),
            _receipt(
                "rcp-exec-2",
                "2026-09-17T23:45:01+00:00",
                attempt_id="att-2",
                trace_id="trc-2",
                adapter="local.read_file",
                invocation_occurred=True,
                execution_state="FINISHED",
            ),
            _receipt(
                "rcp-ver-2",
                "2026-09-17T23:45:01+00:00",
                attempt_id="att-2",
                trace_id="trc-2",
                execution_receipt_id="rcp-exec-2",
                verification_state="REJECTED",
                evidence_ids=["ev-2"],
            ),
        ]

        timeline = project_mission_timeline(MISSION_ID, receipts)
        self.assertEqual(timeline.verification_summary["count"], 2)
        self.assertEqual(timeline.verification_summary["by_state"]["VERIFIED"], 1)
        self.assertEqual(timeline.verification_summary["by_state"]["REJECTED"], 1)
        self.assertEqual(timeline.verification_summary["verification_rate"], 0.5)
        self.assertEqual(
            timeline.verification_summary["verification_rate_status"],
            "MEASURED",
        )

        empty = project_mission_timeline(MISSION_ID, [])
        self.assertEqual(empty.resource_summary["attempt_count"], 0)
        for metric, unit in (
            ("tokens", "tokens"),
            ("cost_usd", "USD"),
            ("latency_ms", "ms"),
        ):
            self.assertEqual(
                empty.resource_summary[metric],
                {"status": "UNKNOWN", "value": None, "unit": unit},
            )
        self.assertEqual(empty.verification_summary["count"], 0)
        self.assertIsNone(empty.verification_summary["verification_rate"])
        self.assertEqual(
            empty.verification_summary["verification_rate_status"],
            "NO_DATA",
        )
        self.assertIn("verification.rate", empty.unknown_fields)

    def test_cross_mission_and_invalid_timestamps_fail_closed(self):
        with self.assertRaises(TimelineProjectionError):
            project_mission_timeline(
                MISSION_ID,
                [
                    _receipt(
                        "rcp-other",
                        mission_id="mis-other",
                        sources_loaded=["x"],
                        serialized_bytes=1,
                    )
                ],
            )

        with self.assertRaises(TimelineProjectionError):
            project_mission_timeline(
                MISSION_ID,
                [
                    _receipt(
                        "rcp-bad-time",
                        created_utc="not-a-timestamp",
                        sources_loaded=["x"],
                        serialized_bytes=1,
                    )
                ],
            )


if __name__ == "__main__":
    unittest.main()
