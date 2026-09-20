# Remote PC Command Runtime — Execution Status

**Date:** 2026-09-19  
**Branch:** `feat/remote-pc-command-runtime`  
**Base:** `main` at `bf6836a0f29a640083e5a75c3b9109bf43cd41dc`  

**Contract update:** 2026-09-20. The canonical
[remote task contract](../../architecture/REMOTE_TASK_CONTRACT.md) now defines
the three modes, wire exchange, digest serialization, approval ownership,
failure/restart states, bounded receipts and final acceptance boundary.

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
- explicit one-time `python jarvis.py remote-serve provision` path for Windows Admin context;
- resident `tailscale-serve` transport is adopt-only and never mutates Serve configuration;
- `service install --transport tailscale-serve` refuses installation until the exact HTTPS mapping is verified;
- `remote-doctor` distinguishes `NOT_READY`, `SETUP_REQUIRED` and `READY`, with the next setup command;
- local PC CLI for `remote-pair` and `remote-devices list/revoke`;
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
- Windows current-user HKCU `Run` autostart management through:
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
- `tests/test_agentic_remote_task_lifecycle.py`
- `tests/test_agentic_remote_task_bridge.py`
- `tests/test_agentic_remote_doctor.py`
- `tests/test_agentic_remote_host.py`
- `tests/remote_companion_node_test.js`

The 2026-09-20 validation below records local contract evidence. It does **not**
complete the physical Windows acceptance gates or the real paired-phone journey.

### 2026-09-20 contract validation

Scope: working tree based on `bdd432d7066c721afa6d19d860ead71614f1016f`, with
documentation and test-only changes. Production runtime code is unchanged.
Python 3.12.10 on Windows; no resident service installation, Serve provisioning,
real device pairing or v0.2 gate promotion was performed.

- `python -m unittest discover -s tests -p test_agentic_remote_task*.py -v`:
  **PASS**, 17 tests. Includes digest material, ownership, pending-plan restart,
  terminal idempotency, interrupted-task refusal, partial failure and new-file collision.
- `node tests/remote_companion_node_test.js`: **PASS**.
- `python jarvis.py --doctor`: **PASS**.
- `python benchmarks/context_budget_benchmark.py`: **PASS**; serialized-byte
  admission fixture only, not a provider-quality/token/cost measurement.
- `pwsh -NoProfile -File tooling/Bootstrap.ps1`: **PASS**, 85 schemas and 9 modules.
- `python jarvis.py --full-test`: **PASS** after fixture corrections,
  648 tests / 102 suites, 0 failures, 0 errors (66.331 seconds).
- `python tooling/audit_pre_publish_security.py`: **PASS** (exit 0).

The first full battery reported 643/647 passing tests. Four existing fixtures
were corrected: a literal backslash-n in a generated Python script, unescaped
Windows path comparison, stale service-worker cache version, and dependence on
real process elevation in the mocked provisioning test. No execution permission
or production guard was changed.

## Required direct Windows evidence

### Direct run on 2026-09-20, commit `36e94c1`

The exact tested commit was `36e94c16503a90c80439991ae4b750f6e7c5c47c`
on Windows 11 / Python 3.12.10. The subsequent evidence-only commit does not
change production code; these results remain scoped to the tested SHA.

| Check | Result | Direct evidence |
| --- | --- | --- |
| `portable-runtime` | **PASS**, 4/4 commands, including 648/648 tests | [Gate report](../../../reports/remote-windows-36e94c1/portable-runtime-windows.json) |
| Quickstart | **PASS**, real loopback HUD HTTP 200 | [Startup report](../../../reports/remote-windows-36e94c1/quickstart-windows.json) |
| `legacy-governance` | **FAIL**, guard refused to overwrite existing `E:\.skill-registry`; legacy suites did not execute | [Gate report](../../../reports/remote-windows-36e94c1/legacy-governance-windows.json) |

The read-only `python jarvis.py remote-doctor` returned `NOT_READY`: Tailscale
CLI/node/DNS unavailable, resident host offline, autostart not installed, and
planner provider/model/token configuration absent in this checkout. No existing
legacy checkout was modified, and no Tailscale provisioning or device pairing
was attempted. Published reports redact host-specific personal paths.

**Final physical-Windows acceptance is still pending.** Portable local execution
now has direct passing evidence for the SHA above. Legacy governance requires a
safe runner with a free compatibility path (or a separately verified matching
legacy checkout), and the real phone/HTTPS/resident/planner journey remains
unverified. Do not merge or promote the global v0.2 evidence status from this
partial gate result. The commands below remain the full acceptance checklist.

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

# If SETUP_REQUIRED, run once in Windows Admin terminal:
python jarvis.py remote-serve provision

python jarvis.py remote-serve status
python jarvis.py service install --transport tailscale-serve
python jarvis.py service start
python jarvis.py service status
python jarvis.py remote-pair --label "Galaxy"
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
- Tailscale Serve HTTPS is implemented as the preferred remote transport, with the backend loopback-only and a dedicated `/remote` PWA shell; provisioning is deliberately a separate explicit Admin-terminal setup step, while the resident service is adopt-only. Direct Windows evidence is still pending.
- The command request is synchronous per HTTP handler thread. The durable receipt survives client disconnect after completion, but live stdout streaming is not implemented yet.
- Remembered phone pairing is persistent and revocable; session-only pairing remains selectable.
- Natural-language software tasks are now converted into bounded write/command plans, but this is intentionally not an unrestricted self-directed SWE agent: the plan is limited to the selected context, full-file writes and the constrained command policy, and each exact plan still requires explicit approval.
- Planning currently uses the configured PC-side inference provider; selected source contents are disclosed to that provider within the documented bounds. A local/offline planner backend is still a follow-up.

## Promotion rule

Do not merge this branch based only on code presence. Require the focused remote contracts plus the two Windows v0.2 gates on the exact branch HEAD.
