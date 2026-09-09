---
name: codex-plugin-qa
description: "QA and verify OpenAI Codex plugins and agent hooks in strict isolation (isolated CODEX_HOME + local mock model). Prevents real ~/.codex pollution, asserts hook/started and hook/completed events, and validates TUI/app-server flows with cross-platform fallbacks. Triggers: codex qa, qa codex, codex-plugin-qa, test codex plugin, verify codex hook, codex app-server, isolated CODEX_HOME."
---

# Codex Plugin QA

QA and verify Codex plugins, extensions, and agent hooks in strict isolation.
We exercise the plugin in a REAL Codex instance while touching nothing in the user's setup:
an isolated `CODEX_HOME` + a local mock model provider means no real API calls and the user's
`~/.codex` is never read or written. Each helper script ships a `--self-test`
that asserts its scenario against the live machine, making the scripts both QA tools
and their own regression checks.

Verified against `codex-cli 0.140.0+` (node, jq, tmux, bun on macOS/Linux/WSL).
Confirm with `codex --version`; check flags with `codex <cmd> --help`.

## Golden rules (read before running anything)

- **QA ONLY the target plugin.** Everything that spawns codex must use an isolated
  `CODEX_HOME` and a LOCAL mock model provider. Never QA against the real `~/.codex`,
  and never hit a real model API during automated QA. Enforce:
  `export CODEX_HOME="$(mktemp -d)/codex"; mkdir -p "$CODEX_HOME"` FIRST (a set
  `CODEX_HOME` must already exist or codex hard-errors).
- **Prove the real home stayed clean.** Compute SHA-256 digests of
  `~/.codex/config.toml` before and after each run and assert it is unchanged.
- **The interactive `codex` is often an alias or shell function.**
  Scripts must bypass aliases and invoke the real binary directly.
- **The first-party way to prove a hook fired is the app-server** notification
  stream (`hook/started` / `hook/completed`), not log scraping.
- **Evidence is mandatory.** Capture JSON notifications or terminal output under
  `${EVIDENCE_DIR:-.evidence/codex-qa}/<YYYYMMDD>-<slug>/` (no evidence file == QA did not happen).

## Setup & Environment

```bash
# Configure plugin directory (default: current directory or packages/plugin)
export PLUGIN_DIR="${PLUGIN_DIR:-.}"
export EVIDENCE_DIR="${EVIDENCE_DIR:-.evidence/codex-qa}"

# Verify dependencies and isolation harness
bash scripts/lib/common.sh --self-check
```

**Docker is the recommended clean-room surface:**
Run inside a disposable container that has codex installed, leaving host `~/.codex` untouched.
On native Windows without Docker, use headless app-server pipe mode (see below).

## Cross-Platform Execution Matrix

| Surface | Mechanism | Fallback / Notes |
|---|---|---|
| Linux / macOS / WSL | `tmux` + `pty` live TUI smoke | `scripts/tui-smoke.sh --self-test` |
| Windows (Native PowerShell) | Headless `codex app-server` over stdio | Avoids pty dependency; captures raw JSON-RPC stream |
| CI / Automation | Mock model SSE + isolated `CODEX_HOME` | Non-interactive driver with exit-code assertions |

## Router: pick your case

| You need toâ€¦ | Run | Expected Proof |
|---|---|---|
| Prove a plugin hook fires in a LIVE Codex turn (first-party) | `scripts/app-server-drive.sh --plugin` | JSON assertions for `hook/started` & `hook/completed` |
| Prove the app-server driver itself works (no plugin, fast) | `scripts/app-server-drive.sh --self-test` | Mock assistant response received |
| Install the LOCAL build into an isolated home + assert landing | `scripts/install-verify.sh --self-test` | Plugin registered in isolated `config.toml` |
| Pin ONE component's hook logic deterministically | `scripts/hook-unit-probe.sh --self-test` | Deterministic stdout payload |
| Smoke the real TUI under tmux (boots, renders, survives) | `scripts/tui-smoke.sh --self-test` | Rendered pane capture / exit 0 |
| Watch runtime logs while QAing | `RUST_LOG=debug` / SQLite inspection | Live structured trace |

## Capturing Evidence

```bash
ev="${EVIDENCE_DIR}/$(date +%Y%m%d)-codex-qa-${SLUG:-run}"; mkdir -p "$ev"
bash scripts/app-server-drive.sh --plugin > "$ev/app-server-drive.json" 2>&1
bash scripts/install-verify.sh --self-test > "$ev/install-verify.txt" 2>&1
```