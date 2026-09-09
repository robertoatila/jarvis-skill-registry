# ADR-025: Real-Arsenal Production Hardening & Scale Validation

## Status

ACCEPTED (Phase 23 / Gate 23 Certified)

## Context

Up to Phase 22, the registry core was validated on synthetic fixtures (15 test skills). Proving production readiness required testing against the entire real disk corpus (168 skills across `~/.gemini/config/skills` and `~/.gemini/antigravity-ide/builtin/skills`, yielding 183 total catalog resources).

## Decision

Execute full-scale ingestion and scale validation (`Invoke-RegistryRealArsenalIngestion`):

1. Ingest all 168 real skills across user configuration and built-in roots.
2. Generate structural analyses, integrity manifests, capability profiles, compatibility evaluations (915 matrices across 5 adapters), and static security scans across all 183 resources.
3. Validate strict zero unattended promotion (`active_deployments_delta = 0`).
4. Validate that all real sources remain `UNTRUSTED`.
5. Verify complete ACID ledger consistency across 2,829 total index records.

## Alternatives Considered

- *Synthetic testing only*: Rejected because real skills have unique YAML anomalies, varying file layouts, and unexpected script constructs that synthetic tests do not reproduce.

## Consequences

- **Positive**: Empirical mathematical proof that the Registry Core handles real production scale without memory exhaustion, lock contention, or invariant breaches.
- **Negative**: Catalog ledgers now contain realistic multi-megabyte record sets.

## Security Implications

Confirmed that 0 real scripts were executed dynamically and 0 active deployments were altered.

## Related Phases / Gates

- Phase 23: Real-Arsenal Production Hardening (Gate 23)
