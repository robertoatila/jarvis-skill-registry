# ADR-016: Runtime Execution Profiles & Sandboxing Policy

## Status

ACCEPTED (Phase 14 / Gate 14 Certified)

## Context

Deploying skills without explicit containment policies allows tools to execute network requests, access sensitive filesystems, or consume unbounded CPU/RAM.

## Decision

Establish standardized Execution Profiles (`profiles/*.json` and `index/execution-profiles.jsonl`):

1. `STRICT_SANDBOX`: Zero network, read-only temporary workspace, CPU/memory limits.
2. `OFFLINE_DEVELOPER`: Local filesystem access within project boundaries, zero outbound network.
3. `NETWORK_RESTRICTED`: Whitelisted domain access, scoped filesystem.
4. `PROVIDER_NATIVE`: Provider default containment with audit logging.

Every deployment must bind to an explicit execution profile.

## Alternatives Considered

- *Unconstrained native execution*: Rejected due to high risk of data exfiltration and accidental damage.

## Consequences

- **Positive**: Clear security boundary; enforceable containment contracts per skill deployment.
- **Negative**: Network-dependent skills fail when mistakenly bound to offline profiles.

## Security Implications

Restricts blast radius of any compromised or vulnerable skill tool.

## Related Phases / Gates

- Phase 14: Execution Profiles & Sandbox (Gate 14)
