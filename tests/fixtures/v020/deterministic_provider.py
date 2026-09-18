"""Deterministic provider fixture for v0.2.0 validation.

No network, credentials or provider SDKs are used. The fixture is a callable
registered directly at the inference boundary so tests can prove invocation,
failure classification, resource semantics and bounded fallback deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tooling.agentic.adapters.inference import (
    InferenceFailure,
    InferenceRequest,
    InferenceResult,
)
from tooling.agentic.models import FailureClass


class ProviderCase(str, Enum):
    SUCCESS = "SUCCESS"
    TRANSIENT = "TRANSIENT"
    POLICY = "POLICY"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    MALFORMED = "MALFORMED"
    OVERSIZED = "OVERSIZED"


@dataclass(frozen=True)
class ProviderInvocation:
    mission_id: str
    task_id: str
    agent_id: str
    session_id: str
    max_output_tokens: int


class DeterministicProvider:
    """Callable provider fixture with explicit, inspectable invocation evidence."""

    def __init__(
        self,
        case: ProviderCase | str,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        cost_usd: float | None = None,
        confidence: float = 0.95,
        evidence_refs: tuple[str, ...] = ("fixture-evidence",),
        text: str = "deterministic provider response",
    ):
        self.case = ProviderCase(case)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.cost_usd = cost_usd
        self.confidence = confidence
        self.evidence_refs = tuple(evidence_refs)
        self.text = text
        self.invocations: list[ProviderInvocation] = []

    @property
    def invocation_count(self) -> int:
        return len(self.invocations)

    def __call__(self, request: InferenceRequest):
        if not isinstance(request, InferenceRequest):
            raise TypeError("request must be InferenceRequest")

        self.invocations.append(
            ProviderInvocation(
                mission_id=request.mission_id,
                task_id=request.task_id,
                agent_id=request.agent_id,
                session_id=request.session_id,
                max_output_tokens=request.max_output_tokens,
            )
        )

        if self.case == ProviderCase.TRANSIENT:
            raise InferenceFailure(
                FailureClass.TRANSIENT,
                "DETERMINISTIC_TRANSIENT_FAILURE",
            )

        if self.case == ProviderCase.POLICY:
            raise InferenceFailure(
                FailureClass.POLICY,
                "DETERMINISTIC_POLICY_FAILURE",
            )

        if self.case == ProviderCase.MALFORMED:
            return {"malformed": True}

        if self.case == ProviderCase.OVERSIZED:
            return InferenceResult(
                text="x" * (request.max_output_tokens + 1),
                confidence=self.confidence,
                evidence_refs=self.evidence_refs,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                cost_usd=self.cost_usd,
            )

        if self.case == ProviderCase.LOW_CONFIDENCE:
            return InferenceResult(
                text=self.text,
                confidence=min(self.confidence, 0.20),
                evidence_refs=self.evidence_refs,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                cost_usd=self.cost_usd,
            )

        return InferenceResult(
            text=self.text,
            confidence=self.confidence,
            evidence_refs=self.evidence_refs,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            cost_usd=self.cost_usd,
        )
