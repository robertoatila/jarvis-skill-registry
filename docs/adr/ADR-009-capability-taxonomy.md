# ADR-009: Canonical Capability Taxonomy & Semantic Normalization

## Status

ACCEPTED (Phase 7 / Gate 7 Certified)

## Context

Skill authors describe capabilities using disparate keywords (e.g. `code-gen`, `coding`, `generate-code`, `code_generation`). Without semantic normalization, automated capability routing and conflict detection cannot function reliably.

## Decision

Establish a closed, standardized Capability Taxonomy in `schemas/capability.schema.json` and `index/capabilities.jsonl`. Extract declared and inferred capabilities into standardized Capability Profiles (`index/capability-profiles.jsonl`), mapping synonyms to canonical terms (e.g. `code-generation`, `prompt-engineering`, `ast-transform`, `agent-orchestration`).

## Alternatives Considered

- *Unconstrained free-text tags*: Rejected due to inability to perform deterministic capability matching.
- *External LLM embedding classification*: Rejected to keep core indexing deterministic and zero-cost offline.

## Consequences

- **Positive**: High-precision discovery queries, clear capability density metrics, deterministic conflict detection.
- **Negative**: New domain capabilities must be added to the canonical taxonomy schema.

## Security Implications

Prevents capability obfuscation where malicious tools mask risky features behind generic descriptions.

## Related Phases / Gates

- Phase 7: Capabilities & Semantics (Gate 7)
