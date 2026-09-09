# ADR-004: Explicit Source Registry & Boundary Isolation

## Status

ACCEPTED (Phase 2 / Gate 2 Certified)

## Context

Skills can originate from local directories, git repositories, or vendor packages. Without formal boundaries, paths outside authorized roots could be scanned or ingested.

## Decision

Create an explicit Source Registry (`index/sources.jsonl`) requiring every source to declare its `source_type`, `origin_uri`, `trust_level`, and `policy`. Sources default to `trust_level: UNTRUSTED` and cannot be promoted without human operator consensus.

## Alternatives Considered

- *Implicit wildcard scanning*: Rejected as dangerous.
- *Single-root model*: Rejected due to inability to support multi-provider environments.

## Consequences

- **Positive**: Strict containment; clear trust boundaries per directory.
- **Negative**: New skill repositories must be explicitly registered before discovery.

## Security Implications

Prevents arbitrary directory traversal and rogue source inclusion.

## Related Phases / Gates

- Phase 2: Source Registry (Gate 2)
