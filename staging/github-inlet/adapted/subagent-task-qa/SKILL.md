---
name: subagent-task-qa
description: "QA and verify sub-agent task engines, DAG orchestration, and multi-agent coordination in strict isolation with deterministic evidence tracking. Rejects path traversal and stray evidence roots, preserves user sandbox integrity, and validates terminal task states. Triggers: subagent qa, qa subagent, subagent-task-qa, task dag qa, verify agent task, multi-agent e2e, agent evidence path."
---

# Subagent Task QA

QA and verify sub-agent task adapters, execution engines, and task DAGs by driving
the REAL agent runner binary under strict sandbox isolation.
Unit tests alone do not count as live QA: mock tests verify syntax, but live drivers
provide deterministic proof of orchestration, child process isolation, and terminal state recovery.

## Golden rules

- **Evidence lives at exactly one path.** Every artifact goes under
  `${EVIDENCE_DIR:-.evidence/subagent-qa}/<slug>/`. Use the canonical path resolver:
  reject traversal (`..`), path separators, absolute paths, and stray roots.
- **The real agent dir stays untouched.** The live drivers build their own
  isolated `${TASK_AGENT_SANDBOX_DIR}` and deliberately IGNORE user-global agent directories.
  Report the driver's changed-path fields and the isolated sandbox path.
- **No binary means SKIP, not silence.** When the target runner binary is absent,
  the live drivers report `SKIP` or `FAIL` in their final JSON rather than silently
  degrading to the real home directory. A `SKIP` is not a pass â€” document it explicitly.
- **The captured JSON is the evidence.** No evidence file on disk means the QA did not
  happen, blocking promotion, commit, and push.

## Resolve the evidence directory first

```bash
# Define task agent binary (default: task-runner or senpi)
export TASK_AGENT_BIN="${TASK_AGENT_BIN:-task-runner}"
export EVIDENCE_DIR="${EVIDENCE_DIR:-.evidence/subagent-qa}"

ev="$(node scripts/resolve-evidence-dir.mjs \
  --repo-root "$(git rev-parse --show-toplevel)" --slug <YYYYMMDD>-<short-slug>)"
mkdir -p "$ev"
```

A slug must be ONE relative segment of lowercase letters, digits, and hyphens (e.g., `20260902-task-dag-contract`).
Separators, `.` / `..`, traversal, absolute paths, and non-git roots are rejected with exit code 1.

## Router: pick your case

| You changedâ€¦ | Run | Proves |
|---|---|---|
| Any adapter code, as fast precondition | `node scripts/qa/drive.mjs --self-test` | Driver and isolation harness itself works |
| Adapter wiring reaching a live session | `node scripts/qa/drive.mjs` | Live run with plugin loaded, sandbox isolated, no host drift |
| Task lifecycle (single + batch) | `node scripts/qa/task-e2e.mjs` | Live task start, stream, and terminal states |
| Multi-agent team delivery & recovery | `node scripts/qa/team-e2e.mjs` | Message delivery, shutdown, and exactly-once recovery |
| Task RPC driver scripts | `node scripts/qa/task-rpc-e2e.mjs --self-test` | RPC protocol surface contract |
| Skill delivery into a child task | `node scripts/qa/task-load-skills-e2e.mjs` | Skills reach the child process correctly |
| Continuation behavior | `node scripts/qa/probe-continuation.mjs` | Multi-turn continuations execute reliably |
| DAG state machine / runners | `npm test -- --testPathPattern=task-dag` | State machine invariants and chaos tests |

## Writing the Evidence Report

Every run must generate `$ev/README.md` containing:
1. What was tested (exact scenario and flags).
2. What was observed (verifiable metrics, terminal states, child process PIDs).
3. Sandbox cleanup proof: assert all child task sandboxes and background processes are terminated.