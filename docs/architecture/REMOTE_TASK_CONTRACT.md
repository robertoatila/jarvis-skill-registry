# Remote autonomous task contract

Status: implemented branch contract for PR #53, `feat/remote-pc-command-runtime`.
Final validation on the physical Windows PC remains **PENDING**. This document
does not authorize merge or promote the v0.2 evidence status.

The PC owns planning, credentials, repository access, execution and durable
state. The paired phone submits a goal, reviews a plan and approves its exact
digest. See the [operational runbook](../REMOTE_SECOND_BRAIN.md) for setup and
the [execution ledger](../superpowers/plans/2026-09-19-remote-pc-command-runtime-execution-status.md)
for validation scope.

## Three independent modes

| Mode | Request | Authority | Evidence |
| --- | --- | --- | --- |
| Chat | `message`, `payload.text` | PC-side inference authorization; text is never execution consent | Chat response, not a command receipt |
| Manual command | `command`, structured `argv`, `cwd`, `timeout_seconds` | `approve_action` with exact `action_id` and `action_digest` | `action_receipt` |
| Autonomous task | `task`, `payload.goal` | `approve_plan` with exact `task_id` and `plan_digest` | `task_plan_required`, then `task_receipt` |

An unavailable task planner returns `REMOTE_TASK_PLANNER_UNAVAILABLE`; there is
no fallback to chat or manual execution. Approval of a command is not approval
of a task. Reachability through Tailscale/loopback is not device authentication.

## Wire exchange

All requests use `protocol: "jarvis-remote/1"`, `session_id`, `device_id`, a
non-empty `request_id`, `kind` and object `payload`. The HTTP boundary authenticates
the paired device and the bridge checks ownership of an open session. Identifiers
are bounded to 256 characters; encoded client payloads to 64 KiB.

Example goal request (identifiers are illustrative):

```json
{
  "protocol": "jarvis-remote/1",
  "session_id": "session-1",
  "device_id": "phone-1",
  "request_id": "request-task-1",
  "kind": "task",
  "payload": {"goal": "Update the small example and run its focused verification"}
}
```

The synchronous response is `PLAN_APPROVAL_REQUIRED` with `task_id`,
`plan_digest` and `event_seq`. Fetch/replay the session events for the reviewable
plan. Event order on success is:

```text
task_requested -> task_plan_required
  -> task_plan_approval_submitted -> task_receipt
```

`task_plan_required.payload` contains `request_id`, `task_id`, `plan_digest`,
`plan` and `requested_event_seq`. To approve, send a new request ID with
`kind: "approve_plan"` and payload containing only the returned `task_id` and
`plan_digest`. Do not reconstruct a digest from the public preview. The
`task_plan_approval_submitted` event records an attempt, not successful approval
or execution. A rejected attempt produces an error, not a successful receipt.

The bridge remembers handled request IDs per session. Use a fresh request ID
for a new goal or approval attempt. Duplicate terminal approvals return the
stored result; they do not run the actions again. `cancel_request` and
`resume_mission` are recognized protocol names but this bridge does not implement
them; neither is a task cancellation/recovery API.

## Planning limits and disclosure

Planning performs two inference calls: select paths from the bounded inventory,
then produce a normalized plan from selected source. It does not execute planned
writes or commands. It does persist session events and the pending plan on the PC.

| Bound | Value |
| --- | --- |
| Goal | 6,000 characters |
| Path inventory sent to planner | Up to 240 paths |
| Selected files | Up to 8 |
| Source bytes | 32 KiB/file, 64 KiB combined |
| Serialized prompt | 120 KiB per pass |
| Planner inference envelope | 128 KiB; ordinary chat retains its separate budget |
| Actions | 1–10, ordered |
| Summary / action purpose | 2,000 / 1,000 characters |
| Replacement content | 1 MiB UTF-8 per write |
| Diff preview | First 6,000 characters, plus truncation marker |

Oversized selected source/prompt is rejected rather than silently truncated.
The inventory itself is a limited selection, not a claim of whole-repository
analysis. The source pass discloses selected contents to the configured PC-side
provider. Provider keys remain on the PC. Protected paths are excluded, but this
path filter is not a general secret detector for arbitrary source files.

The public plan contains `goal`, `summary`, `selected_files`, and ordered
`actions`. A write exposes `index`, `type`, `path`, `purpose`, UTF-8 `bytes`,
`content_sha256`, nullable `expected_before_sha256`, `diff_preview` and
`diff_preview_truncated`. A command exposes `index`, `type`, `purpose`, exact
`argv`, `cwd` and `timeout_seconds`. Full replacement contents and the complete
observed-hash map remain in PC-side state. A preview may disclose source snippets;
a truncated preview is not a complete diff. Review the full PC-side plan before
approving when the preview is insufficient.

## Digest and approval authority

`plan_digest` is lowercase SHA-256 of UTF-8 JSON for this object:

```text
{session_id, device_id, request_id, plan}
```

Serialization uses `ensure_ascii=False`, `sort_keys=True`,
`separators=(",", ":")`, `allow_nan=False`. `request_id` here is the original
task request, not the approval request. `plan` contains `goal`, `summary`,
`selected_files`, `observed_hashes` and normalized ordered `actions`, including
full replacement contents and diff metadata. `task_id`, timestamps, status and
receipts are outside this hash. IDs have the form `rtask-` plus 24 lowercase hex
characters; digests contain 64 lowercase hex characters.

The controller checks task existence, session/device ownership and exact digest
before execution. A changed plan requires a newly prepared plan and explicit
approval. The phone does not supply executable actions in an approval. Persisted
state is host-owned trusted data; this digest is not a signature against a
compromised PC or a general filesystem integrity mechanism.

## Execution and fail-closed transitions

| Durable status | Meaning and next transition |
| --- | --- |
| `PENDING` | Exact plan saved; no planned effects. Valid approval plus preflight moves to `RUNNING` |
| `RUNNING` | Saved before first action; sequential execution in progress |
| `COMPLETED` | Every returned action receipt is `PASS`; terminal and replay-safe |
| `FAILED` | First failed/error action stops the sequence; terminal and replay-safe |
| `UNKNOWN` | Host loaded a previously `RUNNING` task; never replay automatically |

Before the first effect, preflight checks every write target's expected hash
(or absence for a new file), confined paths, and every command's cwd/executable
availability. It does not hash-pin executables, all script dependencies or every
read-only selected file. A preflight rejection leaves the task `PENDING` and
executes nothing; it is not a `FAILED` execution receipt.

Existing write targets must have been inspected in this plan. Each path may be
written once. `LocalActionAdapter` supplies confinement, reparse checks,
optimistic concurrency, verified backups of overwrites and atomic file replacement.
Commands reuse `RemoteCommandController` with `shell=False`, bounded arguments,
repository-confined cwd and 1–900 second timeout (default 120). The approved
plan authorizes its ordered commands internally; no second manual approval is
required for each command.

Autonomous command validation is narrower than manual mode: Git subcommands
are limited to `status`, `diff`, `log`, `show`, `grep`, `ls-files`, `rev-parse`;
`npx` is rejected; npm accepts `test`/`run` and rejects explicit
`deploy`/`publish`/`release` tokens; Python `-m` accepts `unittest`/`compileall`;
direct Python/Node/PowerShell scripts must use repository-relative paths.
Shared validation rejects the explicit inline-code wrappers it recognizes.
These are command-policy checks, **not an OS sandbox**: approved scripts and
their dependencies run with the PC user's permissions and can have other effects.
Do not describe the command ceiling as proof that arbitrary script behavior is safe.

There is no automatic replan, retry loop, rollback of earlier successful actions,
commit, push or merge in this task flow. After failure, inspect receipts and
physical state before submitting a new goal. After `UNKNOWN`, effects may already
exist; never infer that no receipt means no execution. Use one resident controller
per state directory; cross-process exactly-once execution is not claimed.

## Receipt semantics

`task_receipt.payload` correlates `request_id`, `task_id`, `plan_digest`,
`approval_event_seq` and `receipt`. The nested receipt contains `schema_version: 1`,
`task_id`, `plan_digest`, terminal `status`, `summary`, `actions_total`,
`actions_executed`, nullable `failure_reason`, `receipts` and `finished_at`.

Each action receipt includes a one-based `index`, `type`, `purpose` and `status`.
Writes report path, exit code, resulting SHA-256, bytes transferred and error.
Commands include command-controller evidence, exit code, stdout/stderr and
truncation metadata. Task receipts further cap each output stream to 8,192
characters with `stdout_task_receipt_truncated` / `stderr_task_receipt_truncated`
when applicable. An exception may supply only action identity, `ERROR` and error
text. `actions_executed` counts receipts, including a failed attempt; it does not
count successful effects. Unstarted actions have no receipt.

`COMPLETED` establishes reported execution success, not independent verification
or mission outcome. A plan must include appropriate verification commands, and
their output must support the intended claim. Live stdout/stderr streaming and
durable incremental task receipts are not implemented; final receipts are stored
at completion. Reconnecting clients replay session events, not commands.

## Executable evidence and final acceptance

Contract sources: [`remote_protocol.py`](../../tooling/remote_protocol.py),
[`remote_tasks.py`](../../tooling/remote_tasks.py),
[`remote_runtime_bridge.py`](../../tooling/remote_runtime_bridge.py),
[`remote_commands.py`](../../tooling/remote_commands.py).
Tests: [`task planner/controller`](../../tests/test_agentic_remote_tasks.py),
[`task lifecycle`](../../tests/test_agentic_remote_task_lifecycle.py),
[`task bridge`](../../tests/test_agentic_remote_task_bridge.py),
[`mobile client`](../../tests/remote_companion_node_test.js).

Final Windows acceptance remains pending on the exact candidate HEAD: focused
Python/Node contracts, `portable-runtime` and `legacy-governance` direct gates,
and a real paired-phone journey through HTTPS, resident autostart, plan review,
explicit approval, receipts, reconnection and revocation. Record SHA, commands,
exit codes and direct reports. Unit fixtures on Windows do not complete this gate.
Keep PR #53 draft and do not merge on documentation or fixture success alone.
