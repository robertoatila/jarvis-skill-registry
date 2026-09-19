# Remote PC Command Runtime — Execution Status

**Date:** 2026-09-19  
**Branch:** `feat/remote-pc-command-runtime`  
**Base:** `main` at `bf6836a0f29a640083e5a75c3b9109bf43cd41dc`

## Objective

Make the Windows PC the resident J.A.R.V.I.S. execution host while a paired phone acts as the remote control. The path must not require a Codex Remote session or ChatGPT Desktop to remain open.

## Implemented on this branch

- structured remote `command` protocol envelopes;
- exact action SHA-256 digest and explicit `approve_action` flow;
- durable pending/completed command state in `state/remote_commands.json`;
- repository-confined cwd;
- `subprocess.run(..., shell=False)` execution;
- bounded argv, timeout and stdout/stderr receipts;
- rejection of inline `python -c`, Node eval and PowerShell command wrappers;
- duplicate approval returns the completed receipt without repeating the mutable effect;
- restart during `RUNNING` degrades to `UNKNOWN` and is never silently replayed;
- Remote Companion command input and approval card;
- `action_receipt` rendering on the phone;
- resident host wiring through the existing `/api/remote/v1` session path;
- Windows per-user ONLOGON Scheduled Task service through:
  - `python jarvis.py service install`
  - `python jarvis.py service start`
  - `python jarvis.py service stop`
  - `python jarvis.py service status`
  - `python jarvis.py service uninstall`

## Tests added/extended

- `tests/test_agentic_remote_commands.py`
- `tests/test_agentic_remote_command_bridge.py`
- `tests/test_agentic_remote_protocol.py`
- `tests/test_agentic_remote_http.py`
- `tests/test_agentic_remote_service.py`
- `tests/remote_companion_node_test.js`

These contracts are present on the branch, but this status document does **not** claim they were executed successfully on a real Windows host yet.

## Required direct Windows evidence

After the branch is checked out on the target PC:

```powershell
python run_tests.py
node tests/remote_companion_node_test.js
python jarvis.py --doctor
python tooling/validate_v020_plan4.py --gate portable-runtime
python tooling/validate_v020_plan4.py --gate legacy-governance
```

Then verify the resident service path:

```powershell
python jarvis.py service install --transport tailscale
python jarvis.py service start
python jarvis.py service status
```

From the paired phone, request a harmless command first:

```text
python jarvis.py --doctor
```

Confirm the phone receives `approval_required`, the exact command digest is approved, and one `action_receipt` returns the PC-side exit code/output.

## Current limitations

- Real Windows execution evidence is still pending.
- Linux systemd-user and macOS LaunchAgent service registration are not implemented in this branch.
- The existing Tailscale transport still exposes private HTTP directly; Tailscale Serve/HTTPS hardening is a separate follow-up.
- The command request is synchronous per HTTP handler thread. The durable receipt survives client disconnect after completion, but live stdout streaming is not implemented yet.
- Natural-language autonomous development tasks still enter through the existing chat/runtime path. This branch provides the governed PC execution primitive needed for the later planner/tool loop; it does not claim that arbitrary natural language is already converted into command plans automatically.

## Promotion rule

Do not merge this branch based only on code presence. Require the focused remote contracts plus the two Windows v0.2 gates on the exact branch HEAD.
