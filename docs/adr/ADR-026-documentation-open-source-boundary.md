# ADR-026: Documentation Quality, Architectural Truth & Open-Source Boundary

## Status

ACCEPTED (Phase 24 / Gate 24 Implementation)

## Context

Preparing a critical infrastructure project for future open-source release requires clear, truthful documentation grounded strictly in existing code rather than aspirational features. Private environment details, user paths, and quarantined payloads must never be leaked.

## Decision

1. Establish a strict Architectural Truth Matrix classifying all capabilities as `IMPLEMENTED`, `TESTED`, `PARTIALLY_IMPLEMENTED`, `DOCUMENTED_ONLY`, `PLANNED`, or `UNVERIFIED`.
2. Produce comprehensive architectural handbooks, 33 schema specifications, CLI manuals, security/governance guides, and operational playbooks.
3. Establish clear data classification boundaries (`PUBLIC_SAFE`, `PERSONAL_LOCAL`, `ENVIRONMENT_SPECIFIC`, `SECRET`, `QUARANTINED`, `NOT_FOR_DISTRIBUTION`).
4. Validate documentation integrity with an automated 15-scenario test suite (`Invoke-DocumentationIntegrityTests.ps1`).

## Alternatives Considered

- *Marketing-style documentation with unverified claims*: Strongly rejected to uphold security and engineering integrity.

## Consequences

- **Positive**: Complete onboarding clarity, high auditability, safe future public release readiness.
- **Negative**: Requires maintaining extensive documentation and tests.

## Security Implications

Ensures no credentials, local private paths, or quarantined exploits are published.

## Related Phases / Gates

- Phase 24: Documentation, Architecture Handbook & Open-Source Packaging
