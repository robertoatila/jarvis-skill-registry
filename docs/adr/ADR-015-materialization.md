# ADR-015: Deterministic Provider Adaptation & Materialization

## Status

ACCEPTED (Phase 13 / Gate 13 Certified)

## Context

Raw skill markdown and scripts cannot always be consumed directly by target runtimes without formatting adjustments (e.g. converting YAML frontmatter to Claude system instructions or Codex tool schema descriptors). Modifying raw source files violates the immutability invariant.

## Decision

Implement an isolated Materialization Pipeline (`Invoke-RegistryMaterialization`) that:

1. Leaves source files 100% untouched.
2. Generates provider-adapted bundles in an intermediate staging area (`staging/<deployment-id>/`).
3. Emits cryptographic Materialization Manifests (`index/materializations.jsonl`) recording source hashes, applied adaptation transforms, and output file digests.

## Alternatives Considered

- *In-place source transformation*: Rejected as catastrophic for source integrity and version control.
- *On-the-fly streaming adaptation*: Rejected because materialized files must be pre-audited and verified before deployment.

## Consequences

- **Positive**: Complete preservation of source files; deterministic, verifiable staged output.
- **Negative**: Requires disk space in `staging/` for materialized bundles.

## Security Implications

Allows sandboxed inspection of adapted artifacts prior to active mounting.

## Related Phases / Gates

- Phase 13: Adaptation & Materialization (Gate 13)
