# ADR-011: Static Security Audit & Threat Modeling

## Status

ACCEPTED (Phase 9 / Gate 9 Certified)

## Context

Untrusted third-party skills may contain malicious code execution, prompt injections, network exfiltration attempts, destructive disk operations, or reverse shell patterns.

## Decision

Implement a multi-tier Static Security Engine (`Invoke-RegistryStaticSecurityScan`) in `RegistryCore.psm1` that:

1. Performs pure static regex and AST analysis across all skill files (Markdown, Python, PowerShell, JS/TS, Shell).
2. Detects threat categories: `COMMAND_INJECTION`, `NETWORK_EXFILTRATION`, `PROMPT_INJECTION`, `CREDENTIAL_ACCESS`, `DESTRUCTIVE_FILESYSTEM`, `UNSAFE_DESERIALIZATION`.
3. Stratifies findings into severity tiers: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `CLEAN`.
4. Enforces **Zero Dynamic Execution** during analysis — never running untrusted scripts.
5. Records immutable audit reports in `index/security-reports.jsonl`.

## Alternatives Considered

- *Dynamic execution inside Docker sandbox*: Rejected for static inspection phase to eliminate container escape risks and performance bottlenecks.
- *LLM-based security review*: Rejected as core gating mechanism due to hallucination risks and non-deterministic scores.

## Consequences

- **Positive**: Blazing fast, deterministic, zero dynamic execution risk, verifiable findings.
- **Negative**: Pure static analysis has potential false positives on legitimate system admin scripts.

## Security Implications

Critical layer of defense; blocks high-risk payloads from entering curation and deployment pipelines.

## Related Phases / Gates

- Phase 9: Static Security Audit (Gate 9)
