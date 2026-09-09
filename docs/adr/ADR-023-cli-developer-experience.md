# ADR-023: Unified CLI Front-End & Developer Experience

## Status

ACCEPTED (Phase 21 / Gate 21 Certified)

## Context

Developers and operators interact with the registry across 20+ subsystems. Direct PowerShell module invocation requires memorizing dozens of cmdlets with long parameter lists. A unified, predictable CLI with consistent flag ergonomics is essential for operations.

## Decision

Establish `skillctl` (`tooling/skillctl.ps1`) as the single, authoritative front-end entrypoint:

1. Standardized syntax: `skillctl <domain> <command> [<target>] [-Json] [-DryRun] [-Force]`.
2. Covers all 23 real domains (`registry`, `source`, `discovery`, `structure`, `provenance`, `integrity`, `identity`, `capability`, `compatibility`, `security`, `quality`, `conflict`, `curation`, `materialize`, `profile`, `deploy`, `update`, `schedule`, `observe`, `admin`, `export`, `status`, `help`).
3. Dual-mode output: Human-readable structured ANSI console formatting by default, machine-readable JSON via `-Json`.
4. Consistent exit codes (0 = Success, 1 = Error / Diagnostic Failure).

## Alternatives Considered

- *Multiple standalone script entrypoints*: Rejected as unmaintainable and fragmented.

## Consequences

- **Positive**: Exceptional operator ergonomics, scriptability in CI/CD pipelines, instant diagnostic inspection.
- **Negative**: CLI routing layer must be kept synchronized with Core module capabilities.

## Security Implications

Enforces parameter validation and prevents raw unvalidated inputs from reaching core execution engines.

## Related Phases / Gates

- Phase 21: CLI Polish & Developer Experience (Gate 21)
