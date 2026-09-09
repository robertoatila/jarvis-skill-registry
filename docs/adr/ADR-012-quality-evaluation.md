# ADR-012: Multi-Dimensional Quality & Utility Assessment

## Status

ACCEPTED (Phase 10 / Gate 10 Certified)

## Context

A skill may be safe from malware but poorly documented, missing examples, bloated in token size, or structurally brittle. Evaluating quality objectively requires standardized scoring dimensions.

## Decision

Implement `Invoke-RegistryQualityAssessment` using 5 weighted metrics:

1. **Completeness** (frontmatter, description, parameters, return types).
2. **Maintainability** (modularity, script structure, clean code).
3. **Documentation Quality** (usage examples, clear prompt instructions).
4. **Token Efficiency** (conciseness, context window footprint).
5. **Operational Reliability** (error handling, deterministic behaviors).

Records results in `index/quality-evaluations.jsonl`.

## Alternatives Considered

- *Single binary pass/fail score*: Rejected because nuanced curation requires multi-attribute ranking.

## Consequences

- **Positive**: Enables automated curation of highest-quality skills; transparent scorecards for developers.
- **Negative**: Adds heuristic scoring computation to the ingestion pipeline.

## Security Implications

Ensures high-utility skills with well-defined parameter bounds are prioritized over ambiguous prompt snippets.

## Related Phases / Gates

- Phase 10: Quality & Utility Evaluation (Gate 10)
