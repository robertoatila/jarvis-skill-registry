# ADR-002: Sovereign Quarantine Precedence

## Status

ACCEPTED (Phase 1 / Gate 1 Certified)

## Context

Malicious or malformed skills may exist in user directories or external repos. An explicit mechanism was required to prevent any scanned, discovered, or promoted artifact from resolving if it matches quarantined hashes or directory paths.

## Decision

Implement `gov-quarantine-link-v1` as a sovereign, immutable anchor containing:

1. 118 cryptographic SHA-256 tombstone hashes.
2. 8 explicitly blocked container subtrees.
3. Fail-closed precedence in every discovery, analysis, curation, and deployment function.

## Alternatives Considered

- *Dynamic blacklist in memory*: Rejected because in-memory state does not survive reboots.
- *Soft quarantine with override switch*: Rejected to prevent unauthorized runtime bypassing.

## Consequences

- **Positive**: Absolute mathematical guarantee that quarantined content cannot be ingested or executed.
- **Negative**: Hardened against manual tampering; unblocking requires intentional governance transaction.

## Security Implications

Guarantees containment of all known compromised skills.

## Reversibility

Requires updating governance anchor with supervisor consensus.

## Related Phases / Gates

- Phase 1: Foundation & Quarantine Linking (Gate 1)
