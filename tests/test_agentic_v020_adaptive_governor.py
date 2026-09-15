"""v0.2.0 deterministic adaptive Cognitive Governor contracts."""

from __future__ import annotations

import unittest

import tooling.agentic.cognitive_governor as governor_module
from tooling.agentic.models import RecoveryState, RiskLevel


class TestV020AdaptiveGovernor(unittest.TestCase):
    def _types(self):
        self.assertTrue(hasattr(governor_module, "GovernorAction"))
        self.assertTrue(hasattr(governor_module, "GovernorObservation"))
        return governor_module.GovernorAction, governor_module.GovernorObservation

    def _observation(self, **overrides):
        _, GovernorObservation = self._types()
        values = {
            "authority_valid": True,
            "risk_level": RiskLevel.R0_READ_ONLY,
            "confidence": 0.9,
            "evidence_sufficient": True,
            "context_exhausted": False,
            "eligible_alternatives": 0,
            "attempts": 1,
            "repeats": 0,
            "remaining_tokens": 100,
            "remaining_cost_usd": 1.0,
            "recovery_state": RecoveryState.NOT_REQUIRED,
        }
        values.update(overrides)
        return GovernorObservation(**values)

    def test_declares_exact_public_actions(self):
        GovernorAction, _ = self._types()
        self.assertEqual(
            [action.value for action in GovernorAction],
            [
                "CONTINUE",
                "EXPAND_CONTEXT",
                "ESCALATE_CAPABILITY",
                "REPLAN",
                "STOP",
                "REQUIRE_HUMAN",
            ],
        )

    def test_invalid_authority_high_risk_and_unsafe_recovery_precede_optimization(self):
        GovernorAction, _ = self._types()
        governor = governor_module.CognitiveGovernor()

        self.assertEqual(
            governor.decide("mis-authority", self._observation(authority_valid=False)),
            GovernorAction.REQUIRE_HUMAN,
        )
        self.assertEqual(
            governor.decide("mis-risk", self._observation(risk_level=RiskLevel.R5_DESTRUCTIVE)),
            GovernorAction.REQUIRE_HUMAN,
        )
        self.assertEqual(
            governor.decide(
                "mis-reconcile",
                self._observation(recovery_state=RecoveryState.RECONCILIATION_PENDING),
            ),
            GovernorAction.REQUIRE_HUMAN,
        )
        self.assertEqual(
            governor.decide(
                "mis-unrecoverable",
                self._observation(recovery_state=RecoveryState.UNRECOVERABLE),
            ),
            GovernorAction.STOP,
        )

    def test_hard_budget_boundary_stops_but_unknown_resource_values_do_not_become_zero(self):
        GovernorAction, _ = self._types()
        governor = governor_module.CognitiveGovernor()

        self.assertEqual(
            governor.decide("mis-token-zero", self._observation(remaining_tokens=0)),
            GovernorAction.STOP,
        )
        self.assertEqual(
            governor.decide("mis-cost-zero", self._observation(remaining_cost_usd=0.0)),
            GovernorAction.STOP,
        )
        self.assertEqual(
            governor.decide(
                "mis-unknown-budget",
                self._observation(remaining_tokens=None, remaining_cost_usd=None),
            ),
            GovernorAction.CONTINUE,
        )

    def test_insufficient_evidence_expands_context_before_capability_escalation(self):
        GovernorAction, _ = self._types()
        governor = governor_module.CognitiveGovernor()

        observation = self._observation(
            confidence=0.2,
            evidence_sufficient=False,
            context_exhausted=False,
            eligible_alternatives=3,
        )
        self.assertEqual(
            governor.decide("mis-expand", observation),
            GovernorAction.EXPAND_CONTEXT,
        )

    def test_context_exhaustion_allows_capability_escalation_only_after_context_path_is_closed(self):
        GovernorAction, _ = self._types()
        governor = governor_module.CognitiveGovernor()

        observation = self._observation(
            confidence=0.2,
            evidence_sufficient=False,
            context_exhausted=True,
            eligible_alternatives=1,
        )
        self.assertEqual(
            governor.decide("mis-escalate", observation),
            GovernorAction.ESCALATE_CAPABILITY,
        )

    def test_confidence_threshold_equality_is_not_treated_as_low_confidence(self):
        GovernorAction, _ = self._types()
        governor = governor_module.CognitiveGovernor(confidence_threshold=0.8)

        at_boundary = self._observation(confidence=0.8, evidence_sufficient=True)
        below_boundary = self._observation(confidence=0.799, evidence_sufficient=True)
        self.assertEqual(governor.decide("mis-boundary", at_boundary), GovernorAction.CONTINUE)
        self.assertEqual(
            governor.decide("mis-below", below_boundary),
            GovernorAction.EXPAND_CONTEXT,
        )

    def test_repeat_loop_replans_without_cross_mission_state_leak(self):
        GovernorAction, _ = self._types()
        governor = governor_module.CognitiveGovernor(max_consecutive_repeats=3)

        looping = self._observation(repeats=3)
        clean = self._observation(repeats=0)
        self.assertEqual(governor.decide("mis-looping", looping), GovernorAction.REPLAN)
        self.assertEqual(governor.decide("mis-clean", clean), GovernorAction.CONTINUE)
        self.assertEqual(governor.decide("mis-looping", looping), GovernorAction.REPLAN)
        self.assertEqual(governor.decide("mis-clean", clean), GovernorAction.CONTINUE)

    def test_default_safe_path_continues(self):
        GovernorAction, _ = self._types()
        governor = governor_module.CognitiveGovernor()
        self.assertEqual(
            governor.decide("mis-continue", self._observation()),
            GovernorAction.CONTINUE,
        )


if __name__ == "__main__":
    unittest.main()
