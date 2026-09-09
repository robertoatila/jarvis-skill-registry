# 🛡️ Security Policy & Sovereign Security Protocol v13 (SSP-v13)

The **Skill Registry & J.A.R.V.I.S. Ecosystem** strictly enforces the **Sovereign Security Protocol v13 (SSP-v13)** across all canonical skills, quantum agent dispatchers, and multi-platform adapters.

---

## 1. Supported Versions

| Protocol Version | Architecture Version | Status | Security Maintenance |
| :--- | :--- | :--- | :--- |
| **SSP-v13 (13.0.x)** | **v1.2.x** | :white_check_mark: **CURRENT & SEALED** | Active Fail-Closed Defense |
| SSP-v12 | v1.1.x | :white_check_mark: Maintained | Patch & Migration Support |
| < SSP-v12 | < v1.0 | :x: Deprecated | End of Life |

---

## 2. The 13 Invariant Security Laws (SSP-v13)

Every tool, agent, pull request, and distributed package is governed by the 13 Invariant Security Laws defined in [`governance/sovereign-security-protocol-v13.json`](governance/sovereign-security-protocol-v13.json):

1. **SSP13-01 // Zero-Secret Leakage Pre-Publish Barrier**: Deterministic regex and entropy scanning against active API tokens (`sk-...`, `gsk_...`, `AIza...`, `ghp_...`, RSA/EC private keys). Release blocked if unmasked secrets are detected.
2. **SSP13-02 // Cryptographic Merkle Root Integrity**: Every canonical skill must verify against `c6d7e89f256c6baa76fc3083e567b525695296ecbc8a2599dcd1bdfdd8918901` (`urn:skill-registry:merkle-tree:v1`). Zero unverified binary blobs allowed.
3. **SSP13-03 // Fail-Closed Quarantine Barrier & Custody Ledger**: Unverified skills or candidate tools are held in `governance/quarantine-link.json`. Pentest or audit tools (e.g. `payloadsallthethings`) require explicit waiver `WAIVER-2026-SEC-010`.
4. **SSP13-04 // Token Budget Compounding Defense**: SKILL.md frontmatters must be concise ($\le 15$ words) with zero embedded shell scripts or bloat, keeping token consumption under 25% of total budget.
5. **SSP13-05 // Local-First Sovereign Isolation**: Telemetry, vector databases, and keys operate locally on the host; no remote exfiltration without explicit user authentication.
6. **SSP13-06 // System Path Anonymization & Redaction**: Host-specific personal paths (`C:\Users\...`) are redacted to `$REGISTRY_ROOT` in public manifests and reports.
7. **SSP13-07 // Role-Based Agent Isolation & Mutation Consent**: Quantum Agents execute in read-only forensic mode; any mutating filesystem modification strictly mandates the affirmative `-Approved` flag.
8. **SSP13-08 // Multi-Platform Dependency Pinning**: Pinned cryptographic digests across all 870 platform pins (Gemini, Claude, Codex, ChatGPT, Cursor, Generic).
9. **SSP13-09 // Universal Accessibility & Cognitive Ergonomics**: WCAG 2.1 AA compliance: high contrast (>4.5:1), semantic ARIA landmarks, focus rings (`:focus-visible`), and complete keyboard navigability.
10. **SSP13-10 // Deterministic Pre-Publish Audit Gate**: Automated pre-publish auditor (`python tooling/audit_pre_publish_security.py`) must return `Exit 0` before any public branch push.
11. **SSP13-11 // Responsible Vulnerability Disclosure**: Coordinated private disclosure channel without public 0-day exposure.
12. **SSP13-12 // Immutable Quantum Ledger**: Append-only telemetry and mission audits logged to `state/quantum-agent-ledger.jsonl`.
13. **SSP13-13 // Fail-Safe Rollback & Recovery Checkpoints**: Instant transactional reversion via `state/recovery-checkpoint.json` upon any integrity breach.

---

## 3. Reporting a Vulnerability

If you discover a potential vulnerability, bypass of the quarantine barrier, Merkle collision, or credential leak:

1. **DO NOT file a public GitHub issue.**
2. Report the vulnerability privately via **GitHub Private Vulnerability Reporting** (Security Advisory) or email the security custodian directly.
3. Include:
   - Reproduction steps and minimal testcase.
   - Affected skills, adapter layers, or platform targets.
   - Cryptographic hashes of affected artifacts.
4. Maintainers acknowledge receipt within **24 hours** and provide a coordinated remediation release within **72 hours**.

---

## 4. Pre-Publish Verification Command

Before submitting a Pull Request or synchronizing releases, run the sovereign security auditor:

```bash
# Run pre-publish security audit (must exit 0)
python tooling/audit_pre_publish_security.py

# Verify Merkle Root and Platform CI
pwsh -File ./tooling/Bootstrap.ps1
```
