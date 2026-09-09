# ADR-008: Multi-Dimensional Identity & Deduplication Clustering

## Status

ACCEPTED (Phase 6 / Gate 6 Certified)

## Context

Multiple skill sources frequently provide identical, cloned, or slightly diverged copies of the same skill (e.g. `ai-engineer` across multiple agent directories). Loading duplicates wastes context window budgets and causes conflicting instructions.

## Decision

Implement multi-dimensional identity deduplication (`Invoke-RegistryIdentityDeduplication`) that:

1. Normalizes canonical names.
2. Evaluates content divergence using structural hashes.
3. Groups duplicate/divergent skills into identity clusters (`index/identity-clusters.jsonl`).
4. Selects a deterministic canonical leader based on provenance trust and versioning.

## Alternatives Considered

- *Strict filename-only uniqueness*: Rejected because different skills can share filenames while identical skills can have slight naming variations.

## Consequences

- **Positive**: Clean catalog, zero duplicate deployments, deterministic resolution of overlapping skills.
- **Negative**: Cluster calculation requires pairwise comparison across catalog candidates.

## Security Implications

Prevents shadow skills with identical names from hijacking canonical tools.

## Related Phases / Gates

- Phase 6: Identity & Deduplication (Gate 6)
