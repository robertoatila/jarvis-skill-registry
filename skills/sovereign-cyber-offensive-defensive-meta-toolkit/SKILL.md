---
name: sovereign-cyber-offensive-defensive-meta-toolkit
description: Executes SSP-v13.4 red/blue team security audits, OWASP pentesting, and fail-closed hardening.
---

# Sovereign Cyber Offensive & Defensive Meta-Toolkit (SSP-v13.4)

## Overview
Comprehensive offensive (Red Team) and defensive (Blue Team) cybersecurity runbook aligned with the **Sovereign Security Protocol v13.4 (SSP-v13.4)**. Use this skill whenever auditing codebases, APIs, authentication flows, or system boundaries.

## 1. Offensive Reconnaissance & Vulnerability Discovery (Red Team)
- **Injection Surfaces**: Audit all SQL queries, shell executions (`subprocess`, PowerShell), template engines, and NoSQL filters for unparameterized inputs.
- **Broken Access Control (BOLA/IDOR)**: Verify every resource read/write checks the authenticated principal's ownership/role rather than trusting client-supplied IDs.
- **Authentication & Session Flaws**: Inspect JWT signature validation (`alg: none` prevention), OAuth2 state/PKCE parameters, cookie flags (`HttpOnly`, `Secure`, `SameSite`), and rate limiting.
- **XSS & Client-Side Hardening**: Scan for unsafe `innerHTML`, `dangerouslySetInnerHTML`, `eval()`, unvalidated `postMessage`, and missing `Content-Security-Policy` / `Permissions-Policy` headers.

## 2. Defensive Hardening & Fail-Closed Governance (Blue Team)
- **Fail-Closed Default**: Missing credentials, expired tokens, or unreachable policy stores MUST deny access immediately—never degrade to permissive mode.
- **Secret Hygiene**: Ensure API keys, tokens (`config/api_keys.json`, `.env`), and private keys are strictly excluded from git commits and error logs.
- **Executable Verification**:
  ```powershell
  python jarvis.py --doctor
  python tooling/audit_documentation_claims.py
  ```
