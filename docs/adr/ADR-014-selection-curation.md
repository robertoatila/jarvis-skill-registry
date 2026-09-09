# ADR-014: Canonical Selection & Curated Set Compilation

## Status

ACCEPTED (Phase 12 / Gate 12 Certified)

## Context

Deploying an entire catalog of 180+ skills simultaneously exhausts model context windows and introduces unnecessary noise. Operators need targeted, task-specific skill bundles (e.g. `coding-assistant`, `security-auditor`, `devops-engineer`).

## Decision

Implement Curated Sets (`Invoke-RegistryCurationCompile`) defined in `schemas/curated-set.schema.json` and indexed in `index/curated-sets.jsonl`. A Curated Set resolves:

1. Included skill selectors (by name, capability, or tag).
2. Resolved canonical leaders from identity clusters.
3. Excluded shadowed resources and security-gated items.
4. Total token budget calculation.

## Alternatives Considered

- *Ad-hoc skill selection on the command line*: Rejected due to lack of reproducibility and version control.

## Consequences

- **Positive**: Declarative, reproducible bundles; predictable token consumption.
- **Negative**: Curated sets must be compiled before deployment staging.

## Security Implications

Guarantees only vetted, non-conflicting skills enter production deployment staging.

## Related Phases / Gates

- Phase 12: Selection & Curating (Gate 12)
