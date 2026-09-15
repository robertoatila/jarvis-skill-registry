"""v0.2.0 durable authorization grant contracts."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tooling.agentic.config import JarvisRuntimeConfig


class TestV020AuthorizationGrants(unittest.TestCase):
    def _auth(self):
        try:
            return importlib.import_module("tooling.agentic.authorization")
        except ModuleNotFoundError as exc:
            self.fail(f"authorization grant module is missing: {exc}")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = JarvisRuntimeConfig(registry_root=self.root)
        self.config.ensure_directories()
        self.now = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.tmp.cleanup()

    def _issue(self, **overrides):
        auth = self._auth()
        params = {
            "task_id": "tsk-001",
            "subject": "Quantum-ExecutorAgent",
            "action": "write",
            "scopes": ["workspace/config.json"],
            "budget": {"tokens": 1000, "cost_usd": 0.25},
            "approved_by": "HumanOperator",
            "issued_utc": self.now.isoformat(),
            "expires_utc": (self.now + timedelta(minutes=5)).isoformat(),
            "registry_root": self.root,
        }
        params.update(overrides)
        return auth.AuthorizationGrant.issue(**params)

    def test_runtime_config_has_authorizations_directory(self):
        self.assertTrue(hasattr(self.config, "authorizations_dir"))
        self.assertEqual(self.config.authorizations_dir, self.config.state_dir / "authorizations")
        self.assertTrue(self.config.authorizations_dir.is_dir())

    def test_canonical_digest_is_stable_across_mapping_key_order(self):
        auth = self._auth()
        left = {"b": 2, "a": {"y": 2, "x": 1}}
        right = {"a": {"x": 1, "y": 2}, "b": 2}
        self.assertEqual(auth.canonical_digest(left), auth.canonical_digest(right))
        self.assertRegex(auth.canonical_digest(left), r"^[0-9a-f]{64}$")

    def test_self_approval_is_rejected(self):
        auth = self._auth()
        with self.assertRaises(auth.AuthorizationDeniedError):
            self._issue(approved_by="Quantum-ExecutorAgent")
        with self.assertRaises(auth.AuthorizationDeniedError):
            self._issue(approved_by="agent:Quantum-ExecutorAgent")

    def test_exact_bound_context_verifies(self):
        grant = self._issue()
        decision = grant.verify(
            task_id="tsk-001",
            subject="Quantum-ExecutorAgent",
            action="write",
            scopes=["workspace/config.json"],
            budget={"tokens": 1000, "cost_usd": 0.25},
            registry_root=self.root,
            now_utc=self.now + timedelta(seconds=30),
        )
        self.assertTrue(decision.valid)
        self.assertEqual(decision.reason, "AUTHORIZED")

    def test_expired_and_revoked_grants_fail_closed(self):
        auth = self._auth()
        expired = self._issue(expires_utc=(self.now - timedelta(seconds=1)).isoformat())
        with self.assertRaises(auth.AuthorizationDeniedError):
            expired.verify(
                task_id="tsk-001", subject="Quantum-ExecutorAgent", action="write",
                scopes=["workspace/config.json"], budget={"tokens": 1000, "cost_usd": 0.25},
                registry_root=self.root, now_utc=self.now,
            )

        revoked = self._issue()
        revoked.revoke((self.now + timedelta(seconds=10)).isoformat())
        with self.assertRaises(auth.AuthorizationDeniedError):
            revoked.verify(
                task_id="tsk-001", subject="Quantum-ExecutorAgent", action="write",
                scopes=["workspace/config.json"], budget={"tokens": 1000, "cost_usd": 0.25},
                registry_root=self.root, now_utc=self.now + timedelta(seconds=20),
            )

    def test_task_subject_action_scope_and_budget_are_immutable_authority_context(self):
        auth = self._auth()
        grant = self._issue()
        cases = (
            {"task_id": "tsk-other"},
            {"subject": "Quantum-OtherAgent"},
            {"action": "delete"},
            {"scopes": ["workspace/other.json"]},
            {"scopes": ["workspace/../outside.json"]},
            {"budget": {"tokens": 1001, "cost_usd": 0.25}},
            {"budget": {"tokens": 1000, "cost_usd": 0.26}},
        )
        baseline = {
            "task_id": "tsk-001",
            "subject": "Quantum-ExecutorAgent",
            "action": "write",
            "scopes": ["workspace/config.json"],
            "budget": {"tokens": 1000, "cost_usd": 0.25},
            "registry_root": self.root,
            "now_utc": self.now + timedelta(seconds=30),
        }
        for patch in cases:
            with self.subTest(patch=patch):
                request = dict(baseline)
                request.update(patch)
                with self.assertRaises(auth.AuthorizationDeniedError):
                    grant.verify(**request)

    def test_malformed_digest_is_rejected(self):
        auth = self._auth()
        grant = self._issue()
        grant.scope_digest = "not-a-sha256"
        with self.assertRaises(auth.AuthorizationDeniedError):
            grant.verify(
                task_id="tsk-001", subject="Quantum-ExecutorAgent", action="write",
                scopes=["workspace/config.json"], budget={"tokens": 1000, "cost_usd": 0.25},
                registry_root=self.root, now_utc=self.now,
            )

    def test_grant_round_trip_persists_atomically(self):
        auth = self._auth()
        grant = self._issue()
        store = auth.AuthorizationGrantStore(config=self.config)
        path = store.save(grant)
        self.assertEqual(path.parent, self.config.authorizations_dir)
        self.assertTrue(path.is_file())
        self.assertFalse(path.with_suffix(path.suffix + ".tmp").exists())

        restored = store.load(grant.grant_id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.to_dict(), grant.to_dict())


if __name__ == "__main__":
    unittest.main()
