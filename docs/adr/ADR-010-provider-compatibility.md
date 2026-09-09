# ADR-010: Multi-Provider Compatibility Evaluation

## Status

ACCEPTED (Phase 8 / Gate 8 Certified)

## Context

Different AI agent runtimes support distinct manifest formats, tool calling models, and prompt structures:

- **GEMINI**: YAML frontmatter, Google Markdown, System Prompts.
- **CLAUDE**: CLAUDE.md guidelines, tool use hooks, XML tags.
- **CODEX**: OpenAI tool definitions, strict JSON schemas.
- **OPENAI**: Functions/Tools standard specifications.
- **GENERIC_AGENT**: Generic prompt standards.

Deploying an incompatible skill to a provider leads to runtime failure or degraded reasoning.

## Decision

Implement a Provider Compatibility Engine (`Invoke-RegistryCompatibilityEvaluation`) that evaluates each skill against 5 provider adapters (`GEMINI`, `CLAUDE`, `CODEX`, `OPENAI`, `GENERIC_AGENT`), generating a Compatibility Matrix (`index/compatibility.jsonl`) with exact compatibility scores (`COMPATIBLE`, `NEEDS_ADAPTATION`, `INCOMPATIBLE`).

## Alternatives Considered

- *Single runtime target*: Rejected because multi-agent ecosystems require heterogeneous provider support.
- *Runtime failure fallback*: Rejected as unsafe in production agent loops.

## Consequences

- **Positive**: Proactive detection of incompatible skills before deployment; clear adaptation requirements.
- **Negative**: Adds adapter evaluation logic to the lifecycle pipeline.

## Security Implications

Prevents syntax corruption and parameter misinterpretation across agent runtimes.

## Related Phases / Gates

- Phase 8: Provider Compatibility (Gate 8)
