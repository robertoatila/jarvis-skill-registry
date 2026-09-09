# Skill Registry — Open-Source Boundary & Data Classification Policy

**Standard:** Privacy-by-Design / Zero Leakage Boundary  
**Version:** 1.0.0 (Phase 24 Edition)

---

## 1. Data Classification Matrix

Every file and directory in the Skill Registry repository is classified under one of six strict data tiers:

| Data Tier | Description | Examples | Redistribution Rule |
| :--- | :--- | :--- | :--- |
| **`PUBLIC_SAFE`** | Core codebase, schemas, adapters, documentation, and synthetic examples. | `tooling/*.psm1`, `schemas/*.json`, `docs/*.md`, `CONTRIBUTING.md` | **SAFE FOR OPEN-SOURCE DISTRIBUTION** |
| **`PERSONAL_LOCAL`** | User-specific paths, local environment settings, machine-specific configs. | `config/registry.json` containing local drive letters, local paths | **REDACT / TEMPLATIZE BEFORE DISTRIBUTION** |
| **`ENVIRONMENT_SPECIFIC`** | Runtime transaction journals, live index ledgers with local paths. | `index/*.jsonl`, `transactions/*.jsonl`, `audit/*.jsonl` | **DO NOT DISTRIBUTE (INITIALIZE FRESH ON INSTALL)** |
| **`SECRET`** | API keys, tokens, credentials, private SSH keys. | Any `.env` file, credential store, auth tokens | **STRICTLY FORBIDDEN / NEVER COMMIT OR DISTRIBUTE** |
| **`QUARANTINED`** | Malicious payloads, quarantined malware samples, exploit test files. | Actual files matching quarantine tombstones | **ISOLATE IN AIR-GAPPED QUARANTINE / NEVER DISTRIBUTE** |
| **`NOT_FOR_DISTRIBUTION`** | User's actual personal skill directories and private corporate prompt files. | `C:\Users\...\.gemini\config\skills\` | **STRICTLY PRIVATE TO USER HOST** |

---

## 2. Redistribution Checklist

Before publishing this repository to a public Git repository or remote registry:

1. Verify that `index/*.jsonl` contains zero local hardcoded absolute user paths.
2. Confirm that `governance/quarantine-link.json` contains only cryptographic SHA-256 hashes, not malicious file payloads.
3. Ensure all examples in `docs/examples/` use synthetic paths (`file:///workspace/skills/example-skill`).
4. Run `Invoke-DocumentationIntegrityTests.ps1` to ensure 0 secret leaks or private paths exist in documentation.
