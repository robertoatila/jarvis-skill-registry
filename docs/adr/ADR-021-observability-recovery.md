# ADR-021: Operational Observability & Recovery Engine

## Status

ACCEPTED (Phase 19 / Gate 19 Certified)

## Context

Operators need deep diagnostic visibility into registry health, ledger performance, lock state, transaction history, and Merkle consistency proofs. In case of unexpected system crashes or power outages, the registry must recover cleanly.

## Decision

1. Implement Observability Engine (`Get-RegistryTelemetry`, `Get-RegistryTimeline`) recording snapshots in `index/observability-snapshots.jsonl`.
2. Implement Recovery Engine (`Invoke-RegistryCrashRecovery`, `Invoke-RegistryRollback`):
   - Scans `transactions/journal.jsonl` for dangling transactions.
   - Clears abandoned locks in `state/locks/`.
   - Reconciles partially written ledgers to the last known healthy transaction.

## Alternatives Considered

- *Manual file inspection and manual lock removal*: Rejected as error-prone during operational outages.

## Consequences

- **Positive**: Complete operational telemetry and automated crash recovery in sub-second time.
- **Negative**: Adds journal verification overhead on startup.

## Security Implications

Prevents deadlocks and guarantees consistency of append-only ledgers across process crashes.

## Related Phases / Gates

- Phase 19: Operational Observability & Recovery (Gate 19)
