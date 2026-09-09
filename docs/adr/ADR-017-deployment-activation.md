# ADR-017: Atomic Deployment, Live Wiring & Zero Unattended Promotion

## Status

ACCEPTED (Phase 15 / Gate 15 Certified)

## Context

Mounting skills into live agent directories (e.g. `~/.gemini/config/skills` or `.agents/skills`) can cause runtime partial states if interrupted. Furthermore, automated scripts must never promote unverified skills into `ACTIVE` deployments without human supervisor authorization.

## Decision

1. Implement Atomic Deployment (`Invoke-RegistryDeployment`) using staging symlinks or atomic directory swaps.
2. Execute post-mount health probes before declaring deployment `ACTIVE`.
3. Record deployment records in `index/deployments.jsonl`.
4. Enforce **Zero Unattended Promotion** invariant: Automated discovery, analysis, updates, and indexing operations are strictly forbidden from altering active deployments (`auto_promote = false`).

## Alternatives Considered

- *Direct in-place copy*: Rejected because power failures or crashes produce corrupt, half-copied skills.
- *Autonomous auto-promotion*: Rejected to prevent autonomous agent self-escalation.

## Consequences

- **Positive**: Zero downtime deployment, instant rollback capability, guaranteed human-in-the-loop control.
- **Negative**: Requires staging directory space and atomic file system operations.

## Security Implications

Prevents supply chain attacks from silently deploying malicious updates into active agent workspaces.

## Related Phases / Gates

- Phase 15: Activation & Safe Deployment (Gate 15)
