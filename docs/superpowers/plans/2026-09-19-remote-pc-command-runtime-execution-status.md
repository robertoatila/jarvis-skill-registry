# Remote PC Command Runtime — Execution Status

**Branch:** `feat/remote-pc-command-runtime`  
**Pull request:** #53  
**Candidate SHA:** resolve from PR #53 immediately before validation; every report must record that exact SHA.  
**Status:** `KEEP_DRAFT / EXACT_HEAD_VALIDATION_REQUIRED`

## 2026-10-03 mainline migration

The remote runtime has been migrated onto a fresh branch, `feat/remote-runtime-mainline-20261003`, created from current `main@a332cbe5b697bad4c950bc0e1cb8a844250d27f6`. The source implementation came from PR #53 at `82f8c3d7924b818c1dd88ada2ac749045e2c2090`, but only the cohesive remote-runtime files were carried forward; unrelated historical changes were intentionally excluded.

This migration preserves the newer memory/privacy and truthful HUD work already merged to `main`. It also applies current-main integration changes for bounded planner context, non-persistent companion credentials, remote state ignore rules, and service-worker ownership. Historical #53 test results remain regression context only. **No fresh PASS is claimed for the migrated branch until the exact new head is executed on the required platforms and physical Windows + Galaxy acceptance is repeated.**

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

Additional hardening on the current branch:

- pairing offer/device registries are capacity-bounded; expired offers stop consuming pending capacity and revoked device records are pruned only when retention capacity is reached;
- sessions are capped per device and globally, closed sessions may be pruned for capacity, journals have both per-session and aggregate storage ceilings, and replay/request-result persistence has byte limits;
- durable command/task stores now cap pending work and prune only terminal completed/failed records; `UNKNOWN` outcomes are retained rather than silently discarded;
- the public client protocol now admits only request kinds the bridge actually implements;
- remote Git is restricted to read-only inspection and blocks helper/escape forms such as `--no-index`, `--ext-diff`, `--textconv`, `--output` and external pager options; `npx` is not an allowed remote executable;
- the desktop and Remote Companion service workers own separate cache families; the desktop worker no longer caches, rewrites, or deletes Remote Companion cache state;
- Remote Companion request bodies are rejected above 128 KiB before protocol dispatch.

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

## Vercel preview policy

The Vercel project serves the public landing site from `site/`, not the resident runtime under `ui/` or `tooling/`.

To avoid exhausting preview build quotas while hardening backend/runtime code, `site/vercel.json` now uses:

```json
"ignoreCommand": "git diff --quiet HEAD^ HEAD -- ."
```

Because the Vercel project root is `site/`, a commit with no changes under that root exits zero and is ignored by Vercel. Changes to the public landing site still trigger a preview. This only reduces static-site preview churn; Vercel remains non-authoritative for runtime/release validation.

The public landing copy was also corrected to describe **portable runtime evidence** and **direct Windows compatibility evidence**, rather than claiming active CI/jobs after GitHub Actions were removed.

## Evidence boundary

Historical validation results are useful for regression context but are **not merge authority** for the current PR head.

The canonical release evidence remains governed by `evidence/current.json`. The v0.2 release must stay `DIRECT_VALIDATION_REQUIRED / INCOMPLETE` until fresh direct reports are produced for the exact final source SHA.

GitHub Actions workflows were removed from `main` and this branch. Release authority is direct/local-first evidence bound to the exact source SHA.

## 2026-09-27 hardening and CI-policy follow-up

- manual command approvals use digest v3 and bind both direct script/npm artifacts and the resolved runtime executable identity before approval;
- the executable binding contains binary SHA-256 plus a non-reversible SHA-256 fingerprint of its canonical path, avoiding host-path disclosure;
- pending v1/v2 command records cannot execute; completed v1/v2 receipts remain readable/idempotent;
- autonomous command plans now include both artifact and executable bindings inside the approved `plan_digest`; executable swaps fail preflight before any plan effect;
- legacy Mobile Companion authentication no longer generates or accepts query-string tokens: generated links use `#token=...`, the browser keeps the token in `sessionStorage`, and request authorization uses headers/Bearer/cookie rather than URL query credentials;
- global event-storage accounting includes orphan `.jsonl` journals, so failed cleanup cannot evade the disk quota;
- replay-index capacity is measured from the complete serialized prospective request record, including ID/fingerprint/metadata overhead;
- durable host/device/session/command/task state rejects direct symlinked state paths; event journals reject symlink targets before append/replay;
- the legacy companion token is now 256-bit, atomically persisted, and refuses a symlink token file;
- Windows HKCU autostart derives and validates the canonical launcher/Python command before start/stop; tampered launcher content or redirected metadata fails closed;
- all five GitHub Actions workflow files were removed from both `main` and PR #53; pre-removal `main` is preserved at `backup/main-pre-no-actions-768e8be`;
- PR #53 was reconciled with the no-Actions `main` through an explicit merge commit, without force-push.

The candidate remains draft. These changes invalidate earlier exact-HEAD evidence and require a new direct battery.

## Required exact-HEAD software validation

Run on the final PR #53 checkout:

```powershell
python run_tests.py
python jarvis.py --doctor
python jarvis.py --test
node tests/remote_companion_node_test.js
python -m unittest tests.test_pre_publish_security_auditor -v
python -m unittest tests.test_agentic_remote_state_limits -v
python -m unittest tests.test_agentic_remote_commands -v
python -m unittest tests.test_agentic_remote_tasks -v
python -m unittest tests.test_agentic_remote_service -v
python -m unittest tests.test_remote_companion -v
python tooling/audit_pre_publish_security.py
python tooling/validate_v020_plan4.py --gate portable-runtime
python tooling/validate_v020_plan4.py --gate legacy-governance
```

Where available, also run the browser/Chromium gate required by the current v0.2 evidence manifest.

Reports must record the exact tested commit SHA and must redact host-specific user paths and machine identifiers.

## Physical acceptance progress — 2026-09-27

Partial physical evidence has now been exercised on the target Windows PC and a paired Galaxy phone over Tailscale Serve:

- Windows resident host reported ONLINE on port 8899 after the native Windows PID-liveness fix;
- Tailscale node and HTTPS Serve path were reachable from the phone;
- one-time Galaxy pairing completed successfully;
- a manual remote `python jarvis.py --doctor` request reached `APPROVAL_REQUIRED` before execution;
- the phone displayed the exact action digest plus script artifact SHA-256 and runtime executable SHA-256/path fingerprint before approval;
- no command execution was observed before approval;
- after approval, the request produced `approval_submitted` followed by `PASS // exit=0` and the expected doctor output;
- Windows command execution was repeated after the no-console-window fix and still returned `PASS // exit=0`.
- browser refresh preserved the paired session; no prior action was replayed automatically, and a newly requested doctor command received a distinct action digest and completed `PASS // exit=0` after fresh approval.
- resident-host restart persistence passed: after stop/start, the paired phone resumed, no prior action replayed automatically, and a fresh doctor request received a new action digest and completed `PASS // exit=0` after approval.

Physical revocation testing then exposed a real cross-process consistency defect: the CLI persisted a device as `REVOKED`, while the already-running host retained an older in-memory `ACTIVE` registry and still accepted command requests. The registry has now been changed to serialize access across processes and reload durable device state before authentication/authorization/mutation. Regression coverage now revokes through a second registry instance, matching the CLI-versus-resident-host topology. **Revocation physical retest PASSED on the corrected head:** the CLI persisted `REVOKED`, the resident host stopped accepting the prior credential, the phone surfaced the revoked state, and the UI returned to `PAIR DEVICE` without allowing command execution.

Galaxy revocation physical retest passed after the cross-process registry fix. The old device credential was invalidated immediately and the Remote Companion returned to pairing state.

## Autonomous planner readiness — 2026-09-27

The Windows host initially reported `task_planner=WARN` because `JARVIS_CHAT_ALLOW_CLOUD`, `JARVIS_CHAT_PROVIDERS` and the server-owned `JARVIS_CHAT_TOKEN` were absent from the user environment. The local ignored provider configuration already contained a preferred provider, model and credential; no credential value was read into output, copied into the phone, or added to Git.

The operator-scoped environment was configured for the already selected `groq` provider only. Cloud authorization was enabled, the chat grant was generated with the operating-system cryptographic random generator, and its value was not printed or committed. The resident host was restarted from a process carrying those variables. Direct Windows `remote-doctor` evidence then reported `task_planner=PASS`, `cloud_enabled=true`, `chat_token_present=true`, `allowed_providers=["groq"]`, a configured model and provider credential, and the host ONLINE. The doctor reports presence only; no live provider request has yet been made. This evidence is scoped to source `9c562219cd1f3853632d166ab85017d361d39f6e`.

Before requesting a plan, the paired-device owner must accept that the natural-language goal and planner-selected repository text are sent to Groq. The planner is bounded to at most eight files, 32 KiB per file and 64 KiB total selected source; `.env`, `config`, `state`, backups and `.git` are excluded. Provider credentials remain on the PC. No write or command may execute until the phone approves the exact `plan_digest`.

The Galaxy credential used for the revocation acceptance remains `REVOKED`; the companion returned to `PAIR DEVICE`. Pair a fresh device before the physical task test. Then submit a harmless, narrowly scoped repository goal, confirm the full plan and exact digest on the phone, and approve it explicitly. The real provider response and the `task_requested -> task_plan_required -> approve_plan -> task_receipt` journey remain unverified.

Focused software evidence against the runtime source at `96ba3325c8edc064ce41bbb20e950701b6c8686c`, with the test-only fixture correction in this change: five focused Python suites ran 57 tests successfully with one Windows symlink privilege skip; `node tests/remote_companion_node_test.js` passed. The first Python run exposed a fixture error: its failure-path plan invoked `fail.py` without selecting that script. The fixture now selects the script, preserving the production rule that a task plan may execute only an inspected or newly written entrypoint. The rerun passed. This is focused evidence, not the full exact-head software battery required for promotion.

This is **partial physical acceptance only**. The branch must remain draft until reconnect/restart durability, selective device revocation, autonomous task plan approval, the exact-head software battery, and fresh redacted evidence are completed. The final evidence bundle must independently record the exact tested source SHA; do not promote this narrative note to release authority by itself.

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
- Persisted host liveness still relies primarily on PID probing; PID reuse could produce a transient false `ONLINE` projection. A future hardening should bind liveness to an in-memory instance nonce/identity probe without recursing through `/host`.

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
