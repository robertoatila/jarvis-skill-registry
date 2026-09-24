# Remote PC Command Runtime — Execution Status

**Branch:** `feat/remote-pc-command-runtime`  
**Pull request:** #53  
**Current HEAD:** `328f20b3a58c8af2d0af507040c146e5b5732e49`  
**Status:** `KEEP_DRAFT / EXACT_HEAD_VALIDATION_REQUIRED`

## Objective

Use the Windows PC as the resident J.A.R.V.I.S. execution host while a paired phone acts as a remote control. ChatGPT Desktop or a Codex Remote session must not be required to remain open.

## Implemented contracts

- versioned `/api/remote/v1` protocol and dedicated Remote Companion UI;
- per-device pairing, durable sessions, reconnect and revocation;
- exact command SHA-256 digest with explicit `approve_action`;
- exact task-plan SHA-256 digest with explicit `approve_plan`;
- digest material binds device, session and request ownership;
- persisted records are revalidated before execution;
- interrupted `RUNNING` work becomes `UNKNOWN` and is never silently replayed;
- repository-confined working directories and write paths;
- symlink/reparse-point checks for executable task paths;
- `shell=False` process execution;
- bounded argv, timeout and stdout/stderr receipts;
- output overflow and incomplete drain fail closed;
- two-pass bounded task planning: path selection, then selected-source planning;
- task-wide preflight before the first write or command;
- overwrite concurrency checks using observed SHA-256;
- Tailscale Serve HTTPS support with the JARVIS backend bound to loopback;
- adopt-only resident transport after explicit Serve provisioning;
- Windows current-user HKCU Run autostart;
- `remote-doctor`, pairing and device-revocation CLI paths;
- dedicated `/remote` PWA shell.

The runtime is an approval-bound development runner, not an operating-system sandbox. Approved scripts execute with the privileges of the Windows user. Direct-child termination does not guarantee process-tree rollback.

## Security and repository hygiene

PR #53 was re-scoped on 2026-09-24.

Removed from the merge candidate:

- local pairing/host state;
- generated staging distribution plans;
- unrelated imported skills;
- external-reference material unrelated to the remote runtime;
- raw local runtime reports and stale Windows acceptance reports;
- desktop-chat UI changes unrelated to the Remote Companion;
- the accidental `FALTA.MD` development transcript.

The pre-publish auditor now checks configured host-metadata patterns in addition to credentials, and verifies that remote runtime state files are covered by `.gitignore`. The auditor intentionally reports only what its deterministic patterns establish; it no longer claims universal "100% / zero leaks" assurance.

All removed material is preserved in:

`backup/pr53-pre-hygiene-8b8f8bf`

## 2026-09-24 follow-up hardening

- remembered pairing is session-only by default; persistent credential storage is explicit opt-in;
- one-time pairing offer/secret are accepted only from the URL fragment, never from query-string credentials;
- Remote Companion has a dedicated service worker scoped to `/remote/` and never serves cached `/api/*` state;
- remote API responses are `Cache-Control: no-store`;
- manual command subprocess environment removes likely credential and execution-control variables;
- remote sessions bound request IDs to deterministic request fingerprints and cap request/event storage;
- oversized write diffs fail closed instead of presenting a truncated approval view.

These changes require a fresh exact-HEAD validation run; earlier reports are historical only.

## Evidence boundary

Historical validation results are useful for regression context but are **not merge authority** for the current PR head.

The canonical release evidence remains governed by `evidence/current.json`. The v0.2 release must stay `DIRECT_VALIDATION_REQUIRED / INCOMPLETE` until fresh direct reports are produced for the exact final source SHA.

No GitHub Actions result is used as authoritative evidence.

## Required exact-HEAD software validation

Run on the final PR #53 checkout:

```powershell
python run_tests.py
python jarvis.py --doctor
python jarvis.py --test
node tests/remote_companion_node_test.js
python -m unittest tests.test_pre_publish_security_auditor -v
python tooling/audit_pre_publish_security.py
python tooling/validate_v020_plan4.py --gate portable-runtime
python tooling/validate_v020_plan4.py --gate legacy-governance
```

Where available, also run the browser/Chromium gate required by the current v0.2 evidence manifest.

Reports must record the exact tested commit SHA and must redact host-specific user paths and machine identifiers.

## Required physical Windows + phone acceptance

On the target Windows PC:

```powershell
python jarvis.py remote-doctor

# Only when the doctor reports Serve setup is required:
python jarvis.py remote-serve provision

python jarvis.py remote-serve status
python jarvis.py service install --transport tailscale-serve
python jarvis.py service start
python jarvis.py service status
python jarvis.py remote-pair --label "Galaxy"
```

Then, from the paired phone:

1. Open the Remote Companion over the verified HTTPS tailnet endpoint.
2. Reconnect to the same paired device/session flow.
3. Request the harmless command `python jarvis.py --doctor`.
4. Confirm that execution does not occur before the exact action digest is approved.
5. Approve the digest and inspect the returned `action_receipt`.
6. Submit a small reviewable natural-language repository task.
7. Confirm `task_requested -> task_plan_required -> approve_plan -> task_receipt`.
8. Verify no write or command occurs before exact plan approval.
9. Restart/reconnect and verify durable status behavior.
10. Revoke the device and confirm further authenticated remote requests are rejected.

Do not promote or merge #53 based only on unit/contract tests. The final physical journey must be exercised against the exact merge-candidate code.

## Current limitations

- Linux systemd-user and macOS LaunchAgent registration are not implemented here.
- Command execution is synchronous per request handler; stdout/stderr are returned as bounded receipts rather than live streaming.
- Remembered pairing is persistent and revocable; session-only pairing remains available.
- Natural-language tasks are deliberately bounded and approval-gated rather than unrestricted autonomous SWE execution.
- Planning uses the configured PC-side inference provider; selected source contents are disclosed to that provider within the documented bounds.
- A local/offline task planner remains follow-up work.

## Promotion rule

PR #53 remains draft until all of the following are true:

- repository hygiene is clean;
- focused remote tests pass;
- complete local/master battery passes;
- deterministic pre-publish audit passes;
- required v0.2 direct gates pass on the exact candidate SHA;
- physical Windows/Tailscale/phone pairing and approval flow passes;
- device revocation is verified;
- `evidence/current.json` is updated only from fresh, redacted, exact-SHA evidence.

Until then: **KEEP DRAFT**.
