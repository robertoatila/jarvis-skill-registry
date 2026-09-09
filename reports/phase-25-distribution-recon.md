# Phase 25 — Multi-Platform Distribution Reconnaissance Report

**Skill Registry Lifecycle Platform — Post-Core Distribution Layer**  
**Phase**: Phase 25 — Multi-Platform Distribution Recon  
**Gate**: `GATE_25_RECON_COMPLETE`  
**Timestamp (UTC)**: 2026-09-01T17:05:00Z  
**Status**: `PASS (15/15 Test Scenarios — 100%)`  
**Governance Invariant**: `GATES 0–24 SEALED & IMMUTABLE`  
**Mode**: `STRICT READ-ONLY RECONNAISSANCE` (Zero Target Mutation, Zero Source Mutation)

---

## 1. Executive Summary

Phase 25 establishes the **Multi-Platform Distribution Reconnaissance** baseline for the Skill Registry across **6 major AI execution runtimes**:

1. **Google Antigravity / Gemini CLI**
2. **OpenAI Codex**
3. **Claude Code (Anthropic)**
4. **ChatGPT (Custom GPTs / Actions / Apps SDK)**
5. **Cursor IDE (.cursorrules / .cursor/rules/*.mdc)**
6. **Generic Open Agent Runtime**

All evaluations were conducted under strict **Read-Only Inspection**, with zero modifications to source files, zero write actions on target platforms, and full adherence to the sovereign quarantine link (`gov-quarantine-link-v1`) and Merkle root immutability.

---

## 2. Multi-Platform Objective Reconnaissance Matrix (6 Targets)

| Target Platform | Discovery Mechanism | Format / Surface | Installation Mode | Script Execution Model | Metadata Support | Known Limitations | Adapter Binding | Verification Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Antigravity / Gemini** | `~/.gemini/config/skills`<br>`.agents/skills/` | `SKILL.md`<br>(Frontmatter + Body) | `LOCAL_COPY`<br>`LOCAL_SYMLINK` | `LOCAL_SHELL`<br>(PowerShell, Bash, Python) | YAML frontmatter (`name`, `description`) | Windows path separator escaping; large context consumption if references unbounded. | `adp-gemini-v1` | `VERIFIED_EMPIRICAL`<br>*(168 live skills in HD)* |
| **OpenAI Codex** | `~/.codex/skills`<br>`.codex/skills/`<br>`AGENTS.md` | `SKILL.md`<br>+ JSON Tool Specs | `LOCAL_COPY`<br>`LOCAL_SYMLINK` | `LOCAL_SHELL`<br>(Python, Bash, PowerShell) | YAML frontmatter + JSON argument schemas | Shell environment dependency across POSIX/Windows; format variation between prompt rules & skill RFCs. | `adp-codex-v1` | `VERIFIED_DOCS` |
| **Claude Code** | `.claude/skills/`<br>`CLAUDE.md`<br>`.claude/settings.json` | System prompt markdown<br>+ XML tag wrapping | `LOCAL_COPY`<br>`STATIC_PROMPT_EMBED`<br>`MCP_REGISTRATION` | `LOCAL_SHELL`<br>(Bash, sh, Python, Node) | `<skill_instruction>` root XML tags + prompt rules | Prefers XML tag encapsulation for semantic steering; requires explicit subagent hooks for background tasks. | `adp-claude-v1` | `VERIFIED_DOCS` |
| **ChatGPT** | `openapi.json`<br>`mcp-bridge`<br>Custom GPT instructions | OpenAPI 3.0/3.1 Tool Schema<br>+ Distilled Instructions | `REMOTE_ACTION_CONFIG`<br>`STATIC_PROMPT_EMBED` | `REMOTE_ACTION_ONLY`<br>(REST / MCP Bridge) | Parameter schemas & operation IDs | Zero arbitrary local OS script execution; 8,000 char prompt limit requires distillation; cloud upload requires API tokens. | `adp-chatgpt-v1` | `VERIFIED_DOCS`<br>*(Cloud push: UNVERIFIED)* |
| **Cursor IDE** | `.cursorrules`<br>`.cursor/rules/*.mdc`<br>`.cursor/skills/` | MDC Rules (`.mdc`)<br>+ Plain `.cursorrules` | `LOCAL_COPY`<br>`LOCAL_SYMLINK`<br>`MDC_RULE_EMBED` | `LOCAL_SHELL`<br>(Bash, PowerShell, Node) | MDC frontmatter (`description`, `globs`, `alwaysApply`) | Prefers modular MDC format with glob matching in modern versions; monolithic legacy `.cursorrules` limit. | `adp-cursor-v1` | `VERIFIED_DOCS` |
| **Generic Agents** | `agent-skills/<name>/`<br>`manifest.json` | Standard Markdown<br>+ Manifest Schema v1 | `LOCAL_COPY`<br>`MCP_REGISTRATION` | `DECLARED_RUNNER`<br>(Sandboxed tools) | Standard JSON schema tool specifications | Requires host runner implementing MCP or Open Agent runner interface. | `adp-generic-v1` | `VERIFIED_DOCS` |

---

## 3. Architecture & Contract Artifacts Delivered

- [platform-capabilities.schema.json](file:///E:/.skill-registry/schemas/platform-capabilities.schema.json) & [platform-capabilities.json](file:///E:/.skill-registry/schemas/platform-capabilities.json) *(6 platforms)*
- [adapter-contract-v1.schema.json](file:///E:/.skill-registry/schemas/adapter-contract-v1.schema.json) & [adapter-contract-v1.json](file:///E:/.skill-registry/schemas/adapter-contract-v1.json) *(6 adapters, including `adp-cursor-v1`)*
- [target-layouts.schema.json](file:///E:/.skill-registry/schemas/target-layouts.schema.json) & [target-layouts.json](file:///E:/.skill-registry/schemas/target-layouts.json) *(6 target layout specs)*
- [adapters/cursor/adapter.json](file:///E:/.skill-registry/adapters/cursor/adapter.json)
- [phase-25-distribution-recon.json](file:///E:/.skill-registry/reports/phase-25-distribution-recon.json)
- [phase-25-distribution-recon.md](file:///E:/.skill-registry/reports/phase-25-distribution-recon.md)

---

## 4. Test Suite Verification (15 / 15 PASS)

Verified via `tests/Invoke-DistributionReconTests.ps1` with 100% pass rate across all 6 platforms.
