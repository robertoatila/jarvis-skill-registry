# ADR-006: Structural Analysis & Packaging Archetypes

## Status

ACCEPTED (Phase 4 / Gate 4 Certified)

## Context

Skills vary from simple single-markdown files to composite multi-script directories containing Python, PowerShell, shell scripts, and auxiliary assets. Downstream execution needs an exact structural classification and risk tiering.

## Decision

Implement `Invoke-RegistryStructuralAnalysis` to classify skills into standardized layout types (`SINGLE_FILE`, `STANDARD_SKILL_DIR`, `EXTENDED_PACKAGE`, `MALFORMED_STRUCTURE`), identify entrypoints, inspect script runtimes, and assign structural risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

## Alternatives Considered

- *Treating all skills as opaque directories*: Rejected because single-document prompts require different handling than executable tools.

## Consequences

- **Positive**: Accurate downstream sandboxing and adapter selection based on verified layout.
- **Negative**: Adds structural analysis step to the ingestion lifecycle.

## Security Implications

Flags dangerous file extensions (`.exe`, `.dll`, `.bat`, `.vbs`, `.pif`) during static layout inspection.

## Related Phases / Gates

- Phase 4: Structural Analysis (Gate 4)
