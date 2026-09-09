# ADR-007: Provenance Tracking & Cryptographic Integrity Chain

## Status

ACCEPTED (Phase 5 / Gate 5 Certified)

## Context

In multi-agent environments, skills can be modified, patched, or tampered with. The registry must track origin lineage (repository, commit, path) and guarantee file-level cryptographic integrity.

## Decision

1. Record immutable provenance records (`index/provenance.jsonl`) with revision details and SHA-256 preimages.
2. Compute Merkle content manifests (`index/integrity-manifests.jsonl`) storing SHA-256 digests for every file in the skill tree.
3. Validate integrity upon every inspection, materialization, and deployment.

## Alternatives Considered

- *Single directory timestamp checking*: Rejected because timestamps are easily forged or modified.

## Consequences

- **Positive**: Instant tamper detection; bit-flip attacks are immediately detected and rejected.
- **Negative**: Hashing large file trees incurs computational overhead during initial ingestion (mitigated by index caching).

## Security Implications

Prevents upstream supply-chain tampering and man-in-the-middle payload alterations.

## Related Phases / Gates

- Phase 5: Provenance & Integrity (Gate 5)
