# ADR-003: Metadata-First Architecture & Structured Ledgers

## Status

ACCEPTED (Phase 1 / Gate 1 Certified)

## Context

Traditional skill management directly mounted filesystem directories, making discovery unversioned and prone to runtime mutation. A robust catalog requires decoupled metadata indexes.

## Decision

Adopt a **Metadata-First Architecture** utilizing append-only JSONL ledgers located in `index/*.jsonl` with JSON Schema Draft 2020-12 contracts. All catalog queries operate against indexed metadata rather than live disk scans.

## Alternatives Considered

- *Direct filesystem traversal on every request*: Rejected due to high latency and lack of immutability.
- *Relational database (SQLite/PostgreSQL)*: Rejected to maintain zero external binary dependencies on Windows PowerShell.

## Consequences

- **Positive**: Blazing fast queries, complete audit trail, reproducible state, transparent text inspection.
- **Negative**: Requires transactional consistency between ledger writes and index files.

## Security Implications

Prevents time-of-check to time-of-use (TOCTOU) exploits on live skill directories.

## Reversibility

Ledger structure is versioned via `schema_version`.

## Related Phases / Gates

- Phase 1: Foundation (Gate 1)
