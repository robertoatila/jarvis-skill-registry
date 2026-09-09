# ADR-005: Discovery Model & Non-Mutating Frontmatter Parsing

## Status

ACCEPTED (Phase 3 / Gate 3 Certified)

## Context

Skill manifests (`SKILL.md`) contain YAML frontmatter defining name, description, capabilities, and dependencies. Parsing must be robust against formatting anomalies and malformed YAML without mutating source files or invoking external interpreters.

## Decision

Implement a pure-PowerShell AST/Regex parser in `RegistryCore.psm1` (`Invoke-RegistryDiscovery`) that extracts frontmatter, computes content digests, and registers candidates into `index/resources.jsonl` and `index/discoveries.jsonl` in read-only mode.

## Alternatives Considered

- *External Python PyYAML wrapper*: Rejected to prevent spawning child processes during discovery.
- *Strict fail on any YAML error*: Rejected in favor of capturing `MALFORMED` state in structural analysis.

## Consequences

- **Positive**: Zero external dependencies; safe read-only parsing of hundreds of skills in seconds.
- **Negative**: Advanced nested YAML constructs are simplified to normalized string maps.

## Security Implications

Completely immune to YAML deserialization exploits.

## Related Phases / Gates

- Phase 3: Discovery Layer (Gate 3)
