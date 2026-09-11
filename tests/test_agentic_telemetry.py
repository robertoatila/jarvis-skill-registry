"""
test_agentic_telemetry.py // Unit and Integration Tests for Phase 06 (Agent Telemetry)
Pure Python 3.12 Standard Library (Zero PIP Dependencies)
"""

import unittest
import tempfile
import time
from pathlib import Path

from tooling.agentic.telemetry import (
    Span,
    TokenUsage,
    TelemetryCollector
)


class TestAgentTelemetry(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ledger_file = Path(self.tmp_dir.name) / "test_spans.jsonl"
        self.collector = TelemetryCollector(ledger_file=self.ledger_file)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_span_lifecycle_and_duration(self):
        span = self.collector.start_span(
            mission_id="MIS-001",
            task_id="task_audit",
            agent_id="Quantum-AuditAgent",
            skill_id="security-research-audit"
        )
        self.assertEqual(span.status, "RUNNING")
        self.assertTrue(span.span_id.startswith("span-"))

        time.sleep(0.01)  # small delta
        finished = self.collector.finish_span(
            span_id=span.span_id,
            status="SUCCESS",
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            tool_calls_count=2,
            evidence_summary={"cve_count": 0}
        )
        self.assertIsNotNone(finished)
        self.assertEqual(finished.status, "SUCCESS")
        self.assertGreaterEqual(finished.duration_ms, 5)
        self.assertEqual(finished.token_usage.total_tokens, 150)
        self.assertEqual(finished.tool_calls_count, 2)

    def test_ledger_persistence(self):
        span = self.collector.start_span("MIS-002", "task_02", "Quantum-ReconAgent")
        self.collector.finish_span(span.span_id, "SUCCESS")

        self.assertTrue(self.ledger_file.exists())
        lines = self.ledger_file.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)

        recent = self.collector.get_recent_spans(limit=10)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["task_id"], "task_02")

    def test_metrics_aggregation(self):
        # 1. Success span for AuditAgent
        s1 = self.collector.start_span("M1", "T1", "Quantum-AuditAgent", "security-research-audit")
        self.collector.finish_span(s1.span_id, "SUCCESS", token_usage=TokenUsage(total_tokens=200))

        # 2. Fail span for AuditAgent
        s2 = self.collector.start_span("M1", "T2", "Quantum-AuditAgent", "security-research-audit")
        self.collector.finish_span(s2.span_id, "FAIL", error_message="AST syntax violation")

        # 3. Success span for ReconAgent
        s3 = self.collector.start_span("M1", "T3", "Quantum-ReconAgent", "blackbird-osint-recon")
        self.collector.finish_span(s3.span_id, "SUCCESS", token_usage=TokenUsage(total_tokens=300))

        metrics = self.collector.get_metrics_summary()
        self.assertEqual(metrics["total_spans"], 3)
        self.assertAlmostEqual(metrics["success_rate"], 66.67, places=1)
        self.assertEqual(metrics["total_tokens"], 500)

        # By-agent breakdown
        audit_stats = metrics["by_agent"]["Quantum-AuditAgent"]
        self.assertEqual(audit_stats["total"], 2)
        self.assertEqual(audit_stats["success"], 1)

        recon_stats = metrics["by_agent"]["Quantum-ReconAgent"]
        self.assertEqual(recon_stats["total"], 1)
        self.assertEqual(recon_stats["success"], 1)


if __name__ == "__main__":
    unittest.main()
