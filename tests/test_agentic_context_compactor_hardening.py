"""Regression contracts for fail-closed context compaction."""

import unittest

from tooling.agentic.context_governor import ContextCompactor


class TestContextCompactorHardening(unittest.TestCase):
    def test_authority_constraints_and_scopes_survive_all_compaction_stages(self):
        record = {
            "task_id": "task-context-hardening",
            "agent_id": "agent-test",
            "status": "EXECUTED",
            "verification_state": "UNVERIFIED",
            "unresolved_uncertainties": ["result still requires independent verification"],
            "decision_records": [{"decision": "do-not-escalate"}],
            "authority": {"operator": "operator:test", "level": "bounded"},
            "constraints": ["local-only", "no-unverified-promotion"],
            "pending_verification": ["artifact-hash"],
            "read_scopes": ["src"],
            "write_scopes": ["reports"],
            "stdout_snippet": "large execution output",
            "input_reference": "artifact://task-context-hardening",
            "provenance_hash": "abc123",
        }

        protected = (
            "authority",
            "constraints",
            "pending_verification",
            "read_scopes",
            "write_scopes",
        )
        for stage in ("STRUCTURED_ATTEMPT", "SUMMARY", "REFERENCE"):
            compacted = ContextCompactor.compact(record, stage)
            for key in protected:
                self.assertEqual(compacted[key], record[key], f"{key} lost at {stage}")

    def test_compaction_returns_detached_protected_metadata(self):
        record = {
            "authority": {"roles": ["operator"]},
            "constraints": ["fail-closed"],
            "pending_verification": ["receipt"],
            "read_scopes": ["src"],
            "write_scopes": ["reports"],
        }
        compacted = ContextCompactor.compact(record, "SUMMARY")
        compacted["authority"]["roles"].append("mutated")
        compacted["constraints"].append("mutated")
        self.assertEqual(record["authority"], {"roles": ["operator"]})
        self.assertEqual(record["constraints"], ["fail-closed"])


if __name__ == "__main__":
    unittest.main()
