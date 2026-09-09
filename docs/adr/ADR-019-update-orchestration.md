# ADR-019: Update Orchestration & Supervised Promotion Queues

## Status

ACCEPTED (Phase 17 / Gate 17 Certified)

## Context

When multiple updates are staged across interdependent skills, applying them piecemeal can cause version incompatibilities and runtime failures.

## Decision

Implement Update Orchestration (`Invoke-RegistryUpdateOrchestration`):

1. Organizes updates into ordered, dependency-aware update queues (`index/update-queues.jsonl`).
2. Validates compatibility, security, and quality of the proposed update batch before execution.
3. Requires explicit supervisor confirmation for promotion (`Invoke-RegistryUpdatePromotion`).
4. Maintains full snapshot state for instant atomic rollback if post-update health checks fail.

## Alternatives Considered

- *Unsequenced direct update application*: Rejected due to high risk of dependency breakage.

## Consequences

- **Positive**: Coordinated multi-skill updates with complete rollback safety.
- **Negative**: Update workflow involves staging, queuing, and explicit promotion steps.

## Security Implications

Enforces separation of duties between update staging and production promotion.

## Related Phases / Gates

- Phase 17: Update Orchestration & Promotion (Gate 17)
