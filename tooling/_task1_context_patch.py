"""Temporary branch-only patch helper for Plan 2 Task 1.

Removed after the target production files are committed.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0 and new in text:
        return
    if count != 1:
        raise SystemExit(f"{path}: expected one patch target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Context Governor: explicit byte measurement and optional qualified token estimate.
replace_once(
    "tooling/agentic/context_governor.py",
    "from typing import List, Dict, Set, Optional, Tuple, Any",
    "from typing import List, Dict, Set, Optional, Tuple, Any, Callable",
)

start = "def compile_context(items: List[ContextItem], budget: int, *, now: float) -> Tuple[str, ContextReceipt]:\n"
end = "\n\nclass InferenceCache:"
target = ROOT / "tooling/agentic/context_governor.py"
text = target.read_text(encoding="utf-8")
if start in text:
    before, rest = text.split(start, 1)
    old_body, after = rest.split(end, 1)
    new_function = '''def compile_context(
    items: List[ContextItem],
    budget: int,
    *,
    now: float,
    token_estimator: Optional[Callable[[str], int]] = None,
    token_estimation_method: Optional[str] = None,
) -> Tuple[str, ContextReceipt]:
    """Compile context under a serialized UTF-8 byte budget.

    Bytes are measured directly. Token counts remain UNKNOWN unless the caller
    supplies both an estimator and an explicit methodology label.
    """
    if type(budget) is not int or budget <= 0:
        raise ValueError("INVALID_CONTEXT_BUDGET")
    if not isinstance(items, list) or any(not isinstance(item, ContextItem) for item in items):
        raise ValueError("INVALID_CONTEXT_ITEMS")
    if token_estimator is not None and not callable(token_estimator):
        raise ValueError("INVALID_TOKEN_ESTIMATOR")
    if token_estimator is not None and (
        not isinstance(token_estimation_method, str) or not token_estimation_method.strip()
    ):
        raise ValueError("TOKEN_ESTIMATION_METHOD_REQUIRED")
    if token_estimator is None and token_estimation_method is not None:
        raise ValueError("TOKEN_ESTIMATOR_REQUIRED")

    groups = {}
    for item in items:
        if item.valid_until is not None and item.valid_until <= now:
            if item.required:
                raise ValueError("STALE_REQUIRED_EVIDENCE")
            continue
        key = hashlib.sha256(item.content.encode("utf-8")).hexdigest()
        group = groups.setdefault(
            key,
            {"content": item.content, "sources": [], "required": False, "priority": item.priority},
        )
        group["sources"].append(item.source)
        group["required"] |= item.required
        group["priority"] = min(group["priority"], item.priority)

    ordered = sorted(
        groups.values(),
        key=lambda group: (not group["required"], group["priority"], sorted(group["sources"])),
    )
    payload, loaded = [], []
    for group in ordered:
        entry = {"content": group["content"], "sources": sorted(set(group["sources"]))}
        trial = json.dumps(payload + [entry], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(trial.encode("utf-8")) > budget:
            if group["required"]:
                raise ContextOverflowError("MANDATORY_CONTEXT_OVERFLOW")
            continue
        payload.append(entry)
        loaded.extend(entry["sources"])

    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    serialized_bytes = len(text.encode("utf-8"))
    if serialized_bytes > budget:
        raise ContextOverflowError("CONTEXT_ENVELOPE_OVERFLOW")

    token_estimate = None
    if token_estimator is not None:
        token_estimate = token_estimator(text)
        if type(token_estimate) is not int or token_estimate < 0:
            raise ValueError("INVALID_TOKEN_ESTIMATE")

    receipt = ContextReceipt(
        receipt_id=f"ctx-{uuid.uuid4().hex[:8]}",
        sources_considered=sorted({item.source for item in items}),
        sources_loaded=sorted(set(loaded)),
        selection_reason="MANDATORY_FIRST_BOUNDED_CONTEXT",
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        serialized_bytes=serialized_bytes,
        token_estimate=token_estimate,
        token_estimation_method=token_estimation_method,
        provenance={
            "byte_measurement_method": "serialized_utf8_bytes",
            "estimator": "serialized_utf8_bytes_upper_bound",
            "budget": budget,
            "budget_bytes": budget,
            "omitted_sources": sorted({item.source for item in items} - set(loaded)),
        },
    )
    return text, receipt
'''
    target.write_text(before + new_function + end + after, encoding="utf-8")
elif "token_estimation_method: Optional[str] = None" not in text:
    raise SystemExit("context_governor.py: compile_context patch target missing")

# Replace ContextReceipt contract as one bounded block.
target = ROOT / "tooling/agentic/context_governor.py"
text = target.read_text(encoding="utf-8")
receipt_start = "@dataclass\nclass ContextReceipt:"
receipt_end = "\n\nclass NoRepeatReadCache:"
if receipt_start in text:
    before, rest = text.split(receipt_start, 1)
    _, after = rest.split(receipt_end, 1)
    new_receipt = '''@dataclass
class ContextReceipt:
    """Audit receipt with measured bytes and optional qualified token estimate."""

    receipt_id: str
    mission_id: Optional[str] = None
    task_id: Optional[str] = None
    attempt_id: Optional[str] = None
    trace_id: Optional[str] = None
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sources_considered: List[str] = field(default_factory=list)
    sources_loaded: List[str] = field(default_factory=list)
    selection_reason: str = ""
    content_hash: str = ""
    serialized_bytes: int = 0
    token_estimate: Optional[int] = None
    token_estimation_method: Optional[str] = None
    # Deprecated compatibility projections. They never change units.
    bytes_loaded: int = 0
    estimated_tokens: Optional[int] = None
    cache_hit: bool = False
    is_measured_tokens: bool = False
    delivery_mode: str = "full"
    relevance: Optional[float] = None
    confidence: Optional[float] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    freshness_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("serialized_bytes", "bytes_loaded"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"INVALID_{name.upper()}")
        if self.serialized_bytes and self.bytes_loaded and self.serialized_bytes != self.bytes_loaded:
            raise ValueError("CONTEXT_BYTE_MEASUREMENT_MISMATCH")
        canonical_bytes = self.serialized_bytes or self.bytes_loaded
        self.serialized_bytes = canonical_bytes
        self.bytes_loaded = canonical_bytes

        supplied_estimate = self.token_estimate
        if supplied_estimate is None and self.estimated_tokens is not None:
            # Legacy unqualified values are not authoritative token estimates.
            if self.token_estimation_method:
                supplied_estimate = self.estimated_tokens
            else:
                self.estimated_tokens = None
        if supplied_estimate is not None:
            if type(supplied_estimate) is not int or supplied_estimate < 0:
                raise ValueError("INVALID_TOKEN_ESTIMATE")
            if not isinstance(self.token_estimation_method, str) or not self.token_estimation_method.strip():
                raise ValueError("TOKEN_ESTIMATION_METHOD_REQUIRED")
            if self.estimated_tokens is not None and self.estimated_tokens != supplied_estimate:
                raise ValueError("TOKEN_ESTIMATE_MISMATCH")
            self.token_estimate = supplied_estimate
            self.estimated_tokens = supplied_estimate
        elif self.token_estimation_method is not None:
            raise ValueError("TOKEN_ESTIMATE_REQUIRED")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "schema_version": self.schema_version,
            "mission_id": self.mission_id,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "trace_id": self.trace_id,
            "created_utc": self.created_utc,
            "sources_considered": sorted(self.sources_considered),
            "sources_loaded": sorted(self.sources_loaded),
            "selection_reason": self.selection_reason,
            "content_hash": self.content_hash,
            "serialized_bytes": self.serialized_bytes,
            "token_estimate": self.token_estimate,
            "token_estimation_method": self.token_estimation_method,
            "bytes_loaded": self.serialized_bytes,
            "estimated_tokens": self.token_estimate,
            "cache_hit": self.cache_hit,
            "is_measured_tokens": self.is_measured_tokens,
            "delivery_mode": self.delivery_mode,
            "relevance": self.relevance,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "freshness_utc": self.freshness_utc,
            "timestamp_utc": self.timestamp_utc,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextReceipt":
        method = data.get("token_estimation_method")
        token_estimate = data.get("token_estimate")
        if token_estimate is None and method:
            token_estimate = data.get("estimated_tokens")
        return cls(
            receipt_id=data["receipt_id"],
            mission_id=data.get("mission_id"),
            task_id=data.get("task_id"),
            attempt_id=data.get("attempt_id"),
            trace_id=data.get("trace_id"),
            created_utc=data.get("created_utc", data.get("timestamp_utc", "")),
            sources_considered=list(data.get("sources_considered", [])),
            sources_loaded=list(data.get("sources_loaded", [])),
            selection_reason=data.get("selection_reason", ""),
            content_hash=data.get("content_hash", ""),
            serialized_bytes=data.get("serialized_bytes", data.get("bytes_loaded", 0)),
            token_estimate=token_estimate,
            token_estimation_method=method,
            cache_hit=data.get("cache_hit", False),
            is_measured_tokens=data.get("is_measured_tokens", False),
            delivery_mode=data.get("delivery_mode", "full"),
            relevance=data.get("relevance"),
            confidence=data.get("confidence"),
            provenance=dict(data.get("provenance", {})),
            freshness_utc=data.get("freshness_utc", ""),
            timestamp_utc=data.get("timestamp_utc", ""),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )
'''
    target.write_text(before + new_receipt + receipt_end + after, encoding="utf-8")
elif "serialized_bytes: int = 0" not in text:
    raise SystemExit("context_governor.py: ContextReceipt patch target missing")

replace_once(
    "tooling/agentic/context_governor.py",
    '''            content_hash=current_hash,\n            bytes_loaded=len(content.encode("utf-8")),\n            estimated_tokens=max(1, len(content.encode("utf-8")) // 4),\n            cache_hit=cache_hit,''',
    '''            content_hash=current_hash,\n            serialized_bytes=len(content.encode("utf-8")),\n            token_estimate=None,\n            token_estimation_method=None,\n            cache_hit=cache_hit,''',
)

# Runtime: if tokens are unknown, preserve the caller-declared requirement.
replace_once(
    "tooling/agentic/runtime.py",
    "        route_requirements = replace(requirements, context_tokens=receipt.estimated_tokens + max_output_tokens)",
    '''        route_context_tokens = (\n            receipt.token_estimate\n            if receipt.token_estimate is not None\n            else requirements.context_tokens\n        )\n        route_requirements = replace(\n            requirements,\n            context_tokens=route_context_tokens + max_output_tokens,\n        )''',
)

# Benchmark: use the measured receipt field and publish the unit boundary explicitly.
replace_once(
    "benchmarks/context_budget_benchmark.py",
    "    admitted_bytes = len(compiled.encode(\"utf-8\"))",
    "    admitted_bytes = receipt.serialized_bytes",
)
replace_once(
    "benchmarks/context_budget_benchmark.py",
    '''        "estimator": receipt.provenance.get("estimator"),\n        "claim_boundary": "serialized UTF-8 bytes only; not provider token counts, quality, latency or cost",''',
    '''        "estimator": receipt.provenance.get("estimator"),\n        "byte_measurement_method": receipt.provenance.get("byte_measurement_method"),\n        "token_estimate": receipt.token_estimate,\n        "token_estimation_method": receipt.token_estimation_method,\n        "claim_boundary": "serialized UTF-8 bytes only; not provider token counts, quality, latency or cost",''',
)
replace_once(
    "benchmarks/context_budget_benchmark.py",
    '''    if admitted_bytes > BUDGET_BYTES:\n        print("ERROR: bounded context exceeded declared budget", file=sys.stderr)''',
    '''    if admitted_bytes != len(compiled.encode("utf-8")):\n        print("ERROR: receipt byte measurement diverged from serialized payload", file=sys.stderr)\n        return 1\n    if receipt.token_estimate is not None or receipt.token_estimation_method is not None:\n        print("ERROR: benchmark invented token estimates without an estimator", file=sys.stderr)\n        return 1\n    if admitted_bytes > BUDGET_BYTES:\n        print("ERROR: bounded context exceeded declared budget", file=sys.stderr)''',
)
