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
- Tailscale Serve HTTPS transport with JARVIS bound only to `127.0.0.1`;
- dedicated `/remote` mobile/PWA shell rather than exposing the desktop HUD remotely;
- reverse-proxy-aware request validation that still requires per-device proof on remote APIs;
- optional persistent phone pairing for Chrome-Remote-like reopen/reconnect behavior;
- read-only remote readiness doctor through `python jarvis.py remote-doctor`;
- retry of unavailable remote transport after Windows logon/Tailscale startup races;
- natural-language remote `task` + digest-bound `approve_plan` protocol;
- two-pass planner: path-only selection followed by bounded selected-source planning;
- exact persisted task plans in `state/remote_tasks.json`;
- autonomous `write_text` actions bound to inspected before-SHA and existing LocalActionAdapter confinement;
- autonomous command actions executed through RemoteCommandController after one exact plan approval;
- task-wide preflight for write hashes plus command cwd/executable before the first effect;
- bounded public plan projection to the phone (paths/purposes/hashes/commands, not full replacement contents);
- task receipts with per-action evidence and no automatic replay after UNKNOWN restart outcome;
- stricter autonomous command policy than manual command mode;
- `remote-doctor` planner-readiness diagnostics without token/provider-key disclosure;
- planner-only 128 KiB inference budget while ordinary chat keeps its existing 16 KB boundary;
- planner source bounds: 32 KiB/file, 64 KiB total selected source, 120 KiB serialized prompt cap;
- bounded unified diff previews shown on the phone before exact plan approval;
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
- `tests/test_agentic_remote_tasks.py`
- `tests/test_agentic_remote_task_bridge.py`
- `tests/test_agentic_remote_doctor.py`
- `tests/test_agentic_remote_host.py`
- `tests/remote_companion_node_test.js`

These contracts are present on the branch. Current JavaScript sources have been parsed successfully during implementation, but this status document does **not** claim the Python/Node battery or Windows gates passed on the physical Windows host yet.

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
python jarvis.py remote-doctor
python jarvis.py service install --transport tailscale-serve
python jarvis.py service start
python jarvis.py service status
```

From the paired phone, request a harmless command first:

```text
python jarvis.py --doctor
```

Confirm the phone receives `approval_required`, the exact command digest is approved, and one `action_receipt` returns the PC-side exit code/output.

Then test the natural-language path with a small, reviewable repository task. Confirm: `task_requested` -> `task_plan_required` -> exact `plan_digest` approval -> `task_receipt`, and verify no repository mutation occurs before plan approval.

## Current limitations

- Real Windows execution evidence is still pending.
- Linux systemd-user and macOS LaunchAgent service registration are not implemented in this branch.
- Tailscale Serve HTTPS is implemented as the preferred remote transport, with the backend loopback-only and a dedicated `/remote` PWA shell; direct Windows evidence is still pending.
- The command request is synchronous per HTTP handler thread. The durable receipt survives client disconnect after completion, but live stdout streaming is not implemented yet.
- Remembered phone pairing is persistent and revocable; session-only pairing remains selectable.
- Natural-language software tasks are now converted into bounded write/command plans, but this is intentionally not an unrestricted self-directed SWE agent: the plan is limited to the selected context, full-file writes and the constrained command policy, and each exact plan still requires explicit approval.
- Planning currently uses the configured PC-side inference provider; selected source contents are disclosed to that provider within the documented bounds. A local/offline planner backend is still a follow-up.

## Promotion rule

Do not merge this branch based only on code presence. Require the focused remote contracts plus the two Windows v0.2 gates on the exact branch HEAD.
