# ADR-018: Upstream Drift Monitoring & Non-Disruptive Detection

## Status

ACCEPTED (Phase 16 / Gate 16 Certified)

## Context

Upstream repositories and user skill directories change over time (new commits, modified documentation, updated scripts). The registry must detect drift without automatically overwriting active production deployments.

## Decision

Implement Upstream Drift Detection (`Invoke-RegistryDriftDetection` / `Invoke-RegistryUpdateScan`) that:

1. Compares live source hashes against indexed provenance and integrity manifests.
2. Identifies drift types: `CONTENT_DRIFT`, `METADATA_DRIFT`, `UPSTREAM_VERSION_BUMP`, `ORPHANED_RESOURCE`.
3. Records detected updates in `index/updates.jsonl` in `STAGED` state without mutating live deployments.

## Alternatives Considered

- *Auto-rebase on detection*: Rejected because untested upstream changes could introduce breaking agent prompt regressions.

## Consequences

- **Positive**: Proactive visibility into upstream improvements and security patches without risk to active workloads.
- **Negative**: Operator must review and promote staged updates.

## Security Implications

Prevents upstream compromise from immediately propagating to production agent instances.

## Related Phases / Gates

- Phase 16: Automated Updates & Drift (Gate 16)
