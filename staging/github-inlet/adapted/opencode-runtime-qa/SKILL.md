---
name: opencode-runtime-qa
description: "QA and verify OpenCode runtime configurations, plugin hooks, tool definitions, and session state in strict isolation. Prevents workspace pollution and verifies deterministic agent turns. Triggers: opencode qa, qa opencode, opencode-runtime-qa, test opencode plugin, verify opencode."
---

# OpenCode Runtime QA

Execute automated and live QA verification for OpenCode runtime integrations, custom tools,
agent configuration manifests, and session turn handling.
Exercises plugin capabilities inside an isolated runtime sandbox, ensuring zero drift
on user configuration directories.

## Golden rules

- **Strict Sandbox Isolation**: All execution must target isolated sandbox homes (`OPENCODE_SANDBOX_DIR="$(mktemp -d)"`).
- **No Production API Contamination**: Use local mock model endpoints or deterministic mock turns for automated assertions.
- **Evidence Collection**: Record all JSON-RPC turn streams and state transitions under `${EVIDENCE_DIR:-.evidence/opencode-qa}/`.
- **Cross-Platform Compatibility**: Scripts must execute on Linux, macOS, WSL, and Windows PowerShell without unhandled exit errors.

## Verification Router

| Verification Scope | Command | Expected Evidence |
|---|---|---|
| Plugin Manifest & Schema | `node scripts/qa/validate-manifest.mjs` | Schema validation PASS |
| Isolated Tool Call Execution | `node scripts/qa/test-tool-dispatch.mjs` | Return value schema matched |
| Session Start & Hook Lifecycle | `node scripts/qa/session-hook-probe.mjs` | `hook/completed` events logged |
| Error State & Recovery | `node scripts/qa/chaos-turn-test.mjs` | Graceful error response (no crash) |