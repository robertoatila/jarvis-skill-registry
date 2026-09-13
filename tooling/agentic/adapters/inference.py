"""Provider-neutral, explicitly registered inference boundary.

Adapters are trusted application code, not repository instructions. They must
honor max_output_tokens, keep no session history, and perform no tool effects.
Provider-specific transport and credentials belong inside the adapter.
"""
from dataclasses import dataclass
from threading import RLock
from copy import deepcopy
import uuid
from typing import Callable, Optional

from ..model_router import ModelCandidate, InferencePolicy
from ..models import FailureClass


class InferenceFailure(RuntimeError):
    def __init__(self, failure_class: FailureClass, reason: str):
        super().__init__(reason)
        self.failure_class = FailureClass(failure_class)


@dataclass(frozen=True)
class InferenceRequest:
    mission_id: str
    task_id: str
    agent_id: str
    session_id: str
    context: str
    policy: InferencePolicy
    max_output_tokens: int


@dataclass(frozen=True)
class InferenceResult:
    text: str
    confidence: Optional[float] = None
    evidence_refs: tuple[str, ...] = ()
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class InferenceBackends:
    def __init__(self):
        self._entries = {}
        self._lock = RLock()

    def register(self, manifest: ModelCandidate, invoke: Callable[[InferenceRequest], InferenceResult]):
        if not callable(invoke):
            raise ValueError("INVALID_BACKEND")
        manifest.__post_init__()
        with self._lock:
            self._entries[manifest.model_id] = (deepcopy(manifest), invoke, RLock(), uuid.uuid4().hex)

    def snapshot(self):
        with self._lock:
            return {key: (deepcopy(entry[0]), entry[1], entry[2], entry[3]) for key, entry in self._entries.items()}

    @staticmethod
    def invoke(entry, request):
        # Serialize a shared backend; private request state remains call-local.
        with entry[2]:
            return entry[1](request)
