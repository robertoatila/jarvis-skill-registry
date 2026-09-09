# Skill Registry — Security Architecture & Threat Model

**Standard:** Zero Dynamic Execution during Inspection / Fail-Closed Sovereignty  
**Version:** 1.0.0 (Phase 24 Edition)

---

## 1. Core Security Guarantees vs Assumptions vs Test Evidence

| Security Dimension | Security Guarantee | Operational Assumption | Empirical Test Evidence |
| :--- | :--- | :--- | :--- |
| **Zero Dynamic Execution** | No untrusted script (Python, PowerShell, Bash, JS) is executed during discovery, analysis, security audit, or quality evaluation. | Host PowerShell runtime does not execute string evaluations on untrusted inputs. | Verified across all 183 catalog resources (Tests 18 & 20 in Phase 23 test harness). |
| **Quarantine Sovereignty** | `gov-quarantine-link-v1` (118 tombstone hashes, 8 blocked subtrees) is checked with fail-closed precedence before any operation. | Cryptographic hash algorithm (SHA-256) is collision-resistant. | Verified fail-closed behavior on corrupted and tombstoned fixtures (Tests 13 & 25). |
| **Zero Unattended Promotion** | Discovery, indexing, updates, and drift monitoring never promote resources to `ACTIVE` deployments (`auto_promote = false`). | Operator approval is required to execute `Invoke-RegistryDeployment`. | `active_deployments_delta = 0` verified across batch real-arsenal ingestion (Test 24). |
| **Source Immutability** | Original skill files on disk are opened with read-only sharing (`FileAccess.Read`, `FileShare.Read`). | Operating system enforces read-only file locks. | 0 source file mutations verified across all 168 real skills on disk. |
| **Append-Only Integrity** | Ledgers are written exclusively via journaled ACID append operations with Merkle root checks. | Underlying filesystem supports atomic append semantics. | Verified via crash recovery and chaos tests (Phase 20 / Phase 23). |

---

## 2. Threat Modeling & Attack Vectors Mitigated

### Threat 1: Prompt Injection via Skill Descriptions

- **Vector**: Attacker writes adversarial prompt instructions into YAML frontmatter description fields to hijack agent planning.
- **Mitigation**: Pure static parsing; semantic normalization; frontmatter is isolated from agent instruction system prompts until explicitly adapted and curated.

### Threat 2: Command Injection & Reverse Shells

- **Vector**: Skill includes helper scripts (`run.py`, `tool.ps1`, `script.sh`) containing subprocess calls, network sockets, or curl/wget downloaders.
- **Mitigation**: Static Security Engine AST/Regex scanning flags `COMMAND_INJECTION` and `NETWORK_EXFILTRATION` with `CRITICAL`/`HIGH` risk ratings, blocking automatic inclusion in default curated sets.

### Threat 3: Time-of-Check to Time-of-Use (TOCTOU) Supply Chain Tampering

- **Vector**: Upstream files are altered on disk after initial security audit.
- **Mitigation**: Content integrity manifest stores SHA-256 hashes of every individual file. Materialization and deployment re-verify file hashes against `integrity-manifests.jsonl`.

### Threat 4: Rogue Skill Shadowing & Namespace Hijacking

- **Vector**: A low-trust skill declares an identical name to a core security tool to override safety policies.
- **Mitigation**: Conflict Detection Engine identifies namespace collisions and enforces trust-tier precedence rules (`SYSTEM_CORE` > `ORGANIZATION_INTERNAL` > `COMMUNITY_VERIFIED` > `UNTRUSTED`).

---

## 3. Sandboxing & Runtime Execution Profiles

All deployments must bind to one of four standardized execution containment profiles:

1. `STRICT_SANDBOX`: Zero network, read-only temporary workspace, memory and CPU ceilings.
2. `OFFLINE_DEVELOPER`: Project-scoped filesystem, no outbound network.
3. `NETWORK_RESTRICTED`: Whitelisted endpoint access, scoped filesystem.
4. `PROVIDER_NATIVE`: Target AI provider sandbox containment.
