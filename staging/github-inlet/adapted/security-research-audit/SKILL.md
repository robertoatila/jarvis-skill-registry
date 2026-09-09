---
name: security-research-audit
description: "Audit and research security vulnerabilities, CVEs, and dependency risks across project components in strict read-only mode. Identifies exposed secrets, insecure configurations, and vulnerable third-party dependencies with actionable remediation evidence. Triggers: security research, vulnerability audit, cve audit, security audit, dependency scan, audit security."
---

# Security Research Audit

Perform structured, non-destructive security research and dependency vulnerability audits
across project repositories, components, and libraries.
This workflow operates in strict read-only mode: automated exploit execution against live systems
is strictly prohibited.

## Golden rules

- **Read-Only / Non-Destructive Inspection**: Scan code, manifests, and configs for vulnerabilities. Never execute live attack payloads or unauthorized pen-testing.
- **Evidence is Mandatory**: Store vulnerability reports, dependency trees, and CVE citations under `${EVIDENCE_DIR:-.evidence/security-audit}/<slug>/`.
- **Zero Host Pollution**: Never install unverified global binaries or third-party scanner packages outside isolated project sandboxes.
- **Actionable Remediation**: Every identified CVE or risk must specify: Affected Component, Severity (CVSS), Vector, and Remediated Version.

## Execution Router

| Audit Target | Tool / Command | Output Artifact |
|---|---|---|
| Node / JavaScript Dependencies | `npm audit --json` or `pnpm audit` | `npm-audit-findings.json` |
| Python Dependencies | `pip-audit --format json` | `python-audit-findings.json` |
| Rust / Cargo Dependencies | `cargo audit --json` | `cargo-audit-findings.json` |
| Secrets & API Keys | Git history & regex pattern scan | `secrets-scan-report.md` |
| Code & Configuration Risks | Static analysis / SAST rules | `sast-vulnerability-matrix.md` |

## Remediation Checklist

1. Verify false-positive status against upstream CVE advisories.
2. Formulate minimal non-breaking dependency upgrades.
3. Validate build and test suites after version patching.