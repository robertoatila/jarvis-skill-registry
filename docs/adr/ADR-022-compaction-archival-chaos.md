# ADR-022: Ledger Compaction, Archival & Chaos Resilience

## Status

ACCEPTED (Phase 20 / Gate 20 Certified)

## Context

High-volume append-only ledgers grow over time. Ingesting, updating, and auditing hundreds of skills creates large JSONL files. To prevent unbounded disk growth while preserving cryptographic audit history, old superseded ledger records must be safely compacted and archived.

## Decision

Implement Compaction, Archival & Chaos Resilience (`Invoke-RegistryCompaction`, `Restore-RegistryFromArchive`, `Invoke-RegistryChaosTest`):

1. Reads retention policies (`schemas/compaction-retention.schema.json`).
2. Deduplicates superseded tombstones and intermediate audit states into compressed archives (`archives/`).
3. Updates `index/archives.jsonl` with archive Merkle proofs.
4. Validates resilience through automated chaos testing (injected corruptions, killed transactions, truncated logs).

## Alternatives Considered

- *In-place destructive deletion without archives*: Rejected because auditability and cryptographic history would be permanently lost.

## Consequences

- **Positive**: Controlled disk footprint; verifiable archival; proven resilience against bit-rot and corruption.
- **Negative**: Compaction is a heavyweight I/O operation requiring exclusive lock acquisition.

## Security Implications

Preserves mathematical integrity proof across historical archives.

## Related Phases / Gates

- Phase 20: Compaction & Chaos Resilience (Gate 20)
