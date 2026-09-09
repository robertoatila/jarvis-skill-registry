# ADR-013: Conflict Detection & Precedence Shadowing

## Status

ACCEPTED (Phase 11 / Gate 11 Certified)

## Context

When multiple skills define conflicting instructions (e.g. conflicting rules for code style), claim identical command namespaces, or duplicate tool signatures, agent behavior becomes non-deterministic.

## Decision

Implement Conflict Detection (`Invoke-RegistryConflictDetection`) that:

1. Identifies namespace collisions, capability clashes, and rule contradictions.
2. Applies deterministic precedence rules based on Source Trust Tier, Specificity, and Explicit Pinning.
3. Marks shadowed resources explicitly in `index/conflicts.jsonl` without silently omitting them.

## Alternatives Considered

- *Last-write-wins*: Rejected because random directory ordering could shadow trusted corporate skills with untrusted user skills.

## Consequences

- **Positive**: Complete transparency on why specific skills are active while others are shadowed.
- **Negative**: Requires conflict index resolution before bundle compilation.

## Security Implications

Prevents malicious skill shadowing where a low-trust skill overwrites core agent security policies.

## Related Phases / Gates

- Phase 11: Conflict Detection & Shadowing (Gate 11)
