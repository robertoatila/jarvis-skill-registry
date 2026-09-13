# Trust Boundaries — evidence and required authorization

Audit: 2026-09-12 at local baseline `23612c9`. This document replaces unsupported assertions that Git, SHA-256, stdio or local execution inherently authenticate an actor. Companion: [execution contract](../architecture/RUNTIME_EXECUTION_CONTRACT.md).

## 1. Mechanisms located and limits

| Classification | Path / symbol | Current behavior / consumers | Limitation |
| --- | --- | --- | --- |
| PARTIAL | tooling/agentic/policy.py: PolicyEngine.evaluate_policy | Runtime consults risk, path, profile and tool constraints | No full mission/agent/skill/tool/node/environment/risk intersection; action-name checks and prefix scope matching are incomplete |
| PARTIAL | policy.py: grant_approval/create_approval_request | Expiring in-memory request and operator string; runtime approval flags | Operator string is not authentication; optional signature not verified; boolean approval cannot prove payload-scoped grant |
| CONFLICTING | admission.py: AdmissionGate.evaluate_task | Scope/profile/budget checks, risk approval status | Approved flags and unknown estimates cannot prove effective permission; capability is not authority |
| PARTIAL | adapters/local.py: resolve_confined_path | Resolved-root confinement and protected paths for local actions | Other readers/verifiers need equivalent enforcement |
| PARTIAL | context_governor.py: read_with_receipt; runtime.py local read path | Rejects root escape and returns source receipts | Runtime takes this path instead of LocalActionAdapter; equivalent protected-file and size policy not established |
| PARTIAL | telemetry.py: redact_sensitive_credentials / Span.to_dict | Recursive key/regex redaction of serialized spans | Not a universal secret detector or boundary for state/artifact/learning writes |
| PARTIAL | models.py: Artifact.compute_hash; verification.py | Hashes content and verifies selected checks | Hash is neither signature nor proof of trusted producer; path-only artifacts accepted |
| CONFLICTING | federation.py: register_node/build_exchange_envelope | Accepts node object and labels SHA-256 digest a signature | No secret/private key involved; neither identity nor authenticity is proven |
| CONFLICTING | adapters/n8n.py: N8nAdapter.parse_inbound_trigger | HMAC checked only when signature supplied; fixed default secret | Unsigned triggers accepted; only payload is covered, not all envelope fields |
| MISSING | agentic paths searched for secret_ref/SecretsProvider | No shared enforced reference materialization contract located | Repo-wide provider existence outside inspected paths remains uncertain |

## 2. Boundary matrix

These are current evidence limits, not declarations of blanket trust. “Not established” means this audit has not proven it. All textual sources can contain secrets or instructions, including artifacts and tool output.

| Boundary | Authentication / authorization / validation / integrity today | Instructions / secrets / effects | Authority and required treatment |
| --- | --- | --- | --- |
| User input | Operator identity and grant binding not established end-to-end | Yes / yes / indirect | Requests scope, does not bypass higher policy |
| Repository content | Git content tracking is not actor authentication or runtime permission | Yes / yes / indirect | Data, inspect under bounded scopes |
| Skill metadata | Catalog/schema/hash mechanisms may identify bytes; execution trust chain not established here | Possible / possible / indirect | Candidate capability declaration, never permission |
| Skill instructions | Required reference files missing in inspected loop skill | Yes / possible / indirect | Selected guidance subordinate to authorization |
| Skill scripts | General OS confinement not proven by runtime policy regex | Yes / possible / direct | Executable only under explicit effective permission |
| Local tools | Local process does not prove safe behavior; command denylist only partial | Yes / yes / direct | Untrusted output, bounded invocation and effects |
| MCP servers | Stdio transport does not authenticate policy compliance; deployment not exercised | Yes / yes / direct | Explicit provider trust and tool-specific authorization needed |
| External APIs | Credentials may authenticate caller; content/result integrity and permissions are provider-specific | Yes / yes / direct | Data; unknown outcome needs inspection |
| n8n | Optional HMAC validation and known default secret are insufficient | Yes / yes / indirect/direct workflows | Block production trust until required full-envelope authentication and replay defense |
| Remote nodes | Declared trust tier and unkeyed digest only in inspected router | Yes / yes / direct | Untrusted worker until identity/grant/protocol proof |
| Artifacts | Optional producer/hash and legacy paths; no signed evidence guarantee | Yes / yes / passive until consumed | Data/proof candidate; integrity, freshness and provenance gates |
| Telemetry | Internal JSONL, redaction, no durable authenticated delivery guarantee | Yes / possible / no authorized execution | Observation/projection input, never command |
| Cognitive Vault | Human-readable projection; local storage not authentication | Yes / possible / indirect if consumed | Notes cannot expand runtime policy or become authoritative machine state |
| Secrets provider | Common scoped reference interface not located in agentic flow | Secrets by definition / materialization has effects | Trusted only for configured narrow boundary; do not infer an OS key vault |

## 3. Required permission and instruction contract

Effective permission must be the intersection of mission authorization, agent profile, skill policy, tool policy, verified node capability, environment policy and risk policy. Calculate at admission and re-enforce against the actual bound adapter and complete effect targets immediately before dispatch. A lower layer can reduce access, never expand it.

Priority: runtime policy > explicit mission authorization > agent contract > selected skill instructions > repository data > external data. This is a required invariant, not a claim that prompt injection is solved. Tool/API responses and remote metadata may contain hostile instructions. Text may inform a decision, never change its approval scope.

Current weaknesses include action aliases not recognized as writes, string-prefix scope matches, mutable approval flags and unverified operator identity. Fixing a single policy call cannot certify all direct adapter and verification-command paths. Approval must bind identity, action/payload, targets, risk, budget, expiry and operation identity; changes require a fresh decision. No self-increased privileges, removed gates, hidden telemetry, rewritten evidence, erased audits or unverified heuristic promotion.

## 4. Secret and artifact invariants

Desired reference contract: secret_ref, provider, scope, expires_at, allowed_consumers. Materialize only at the consumer boundary; record reference usage, not secret value. Do not claim secure deletion from Python memory. Redaction is defense in depth, not permission to persist arbitrary raw payloads.

Potential leak paths: TaskNode.action/execution_result, ExecutionAttempt references if misused as payload, subprocess output snippets, untyped verification payloads, state JSON, learning evidence, artifacts and Vault projections. A pre-publish scanner is not automatically executed before each runtime write. Testing with synthetic canary secrets across all sinks is still required.

Artifact reuse requires bytes/hash and size, producer/attempt provenance, environment and freshness. Content addressing may help identity but cannot authorize content or prove provenance. A repository commit is a version identifier, not user authentication. Current hash metadata remains mutable; no signed immutable ledger guarantee was located.

## 5. External and distributed prerequisites

Before trusting remote results: authenticated node identity and proof of key possession; scoped grants; protocol/runtime/schema compatibility and explicit feature negotiation; expected skill hashes; artifact checks; heartbeat/lease and clock assumptions; correlated task/attempt/effect IDs; replay protection; unknown-outcome reconciliation.

Do not mandate a new mTLS system without deployment evidence: choose a configured authenticated transport and signing/identity scheme when external execution is authorized. An unkeyed digest named signature_sha256 is not such a scheme.

Open gates: production n8n authentication, remote identity, complete permission intersection, uniform read/verification boundaries, secret-reference handling, artifact reuse integrity and authenticated evidence. No external service, credential, remote node or infrastructure mutation was exercised in this audit.
