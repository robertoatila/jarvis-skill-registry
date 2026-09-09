# ADR-020: Scheduled Reconciliation & Autonomous Drift Verification

## Status

ACCEPTED (Phase 18 / Gate 18 Certified)

## Context

Long-running registry instances require periodic drift verification, health monitoring, and garbage collection without human intervention, while maintaining zero unattended promotion.

## Decision

Implement a Scheduled Reconciliation Engine (`Invoke-RegistryScheduledReconciliation`):

1. Reads declarative schedules from `schemas/reconciliation-schedule.schema.json` and `index/schedules.jsonl`.
2. Executes non-disruptive drift scans, index health audits, and quarantine link checks on defined intervals (e.g. `HOURLY`, `DAILY`).
3. Emits reconciliation audit reports without altering active deployments.

## Alternatives Considered

- *External Windows Task Scheduler tasks only*: Rejected to maintain portable core orchestration within RegistryCore.

## Consequences

- **Positive**: Continuous background health verification and drift alerting.
- **Negative**: Background scheduled runs consume minor I/O cycles during scanning.

## Security Implications

Detects unauthorized out-of-band disk modifications within the scheduled polling window.

## Related Phases / Gates

- Phase 18: Scheduled Reconciliation (Gate 18)
