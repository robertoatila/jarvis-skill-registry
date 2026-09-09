# ADR-001: Governance & Fail-Closed Precedence

## Status

ACCEPTED (Phase 0 / Gate 0 Certified)

## Context

The Skill Registry manages agent capabilities, tools, and extensions across multiple AI providers. In previous ad-hoc setups, skills were discovered and executed with implicit trust, risking prompt injection, unauthorized privilege escalation, and unintended tool execution.

## Decision

Establish an immutable fail-closed governance model where:

1. All unknown or unverified resources are strictly quarantined.
2. Any missing cryptographic anchor, corrupted index record, or invalid schema halts execution immediately.
3. Every state change requires explicit transaction logging and cryptographic auditability.

## Alternatives Considered

- *Fail-open with warnings*: Rejected because AI agents would proceed on corrupted metadata.
- *Advisory logging only*: Rejected due to high risk of tool injection.

## Consequences

- **Positive**: Complete defense against untrusted tool execution; predictable system state.
- **Negative**: Strict configuration requirements; corrupted ledgers require operator recovery.

## Security Implications

Prevents silent downgrade attacks and unauthorized capability execution.

## Reversibility

Irreversible by design without breaking the security invariant chain.

## Related Phases / Gates

- Phase 0: Bootstrap & Evidence Verification (Gate 0)
