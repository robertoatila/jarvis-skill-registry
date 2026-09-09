# Extending the Skill Registry — Provider & Adapter Developer Guide

**Version:** 1.0.0 (Phase 24 Edition)

---

## 1. Adding a New Target Provider Adapter

To add support for a new AI provider runtime (e.g. `LLAMA_INDEX`, `LANGCHAIN`, `MISTRAL`):

### Step 1: Register Provider Specification

Create a new provider descriptor in `schemas/provider.schema.json` and register the provider in `index/providers.jsonl`.

### Step 2: Implement Adapter Directory

Create a new adapter subfolder under `adapters/<provider-name>/` containing:

- `adapter.json`: Configuration defining supported entrypoint filenames, frontmatter dialect, and tool calling conventions.
- `transform.ps1`: Deterministic transformation function converting generic skill files into target-specific formats.

### Step 3: Register in Compatibility Engine

Add the provider key to the compatibility evaluator in `tooling/RegistryCore.psm1` (`Invoke-RegistryCompatibilityEvaluation`).

---

## 2. Adding New Static Security Rules

To add a new static security pattern (e.g. detection of specific malicious packages or obfuscation techniques):

1. Open `tooling/RegistryCore.psm1`.
2. Locate the static pattern rules table in `Invoke-RegistryStaticSecurityScan`.
3. Add the regex rule, threat category, severity level, and remediation guidance.
4. Update `schemas/security-report.schema.json` if a new threat category enum is introduced.
