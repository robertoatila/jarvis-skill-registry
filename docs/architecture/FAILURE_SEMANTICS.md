# Failure Semantics — current behavior and required invariants

Evidence-first audit: 2026-09-12, baseline `23612c9`. Canonical companion to [Runtime Execution Contract](RUNTIME_EXECUTION_CONTRACT.md). Paths below are under tooling/agentic/. This replaces unsupported claims of complete enforcement. Matrix rules are required policy, not a claim that retry handlers already implement them.

## 1. Existing behavior and consumers

### Recovery increment — 2026-09-13

**PARTIAL, bounded enforcement now implemented:** ReplayEngine.recovery_block_reason rejects recorded RECONCILIATION_REQUIRED, COMPENSATION_REQUIRED, IDEMPOTENCY_KEY_REQUIRED and UNSAFE_TO_RETRY effects, and pending/unrecoverable recovery states. A proposed compensating action and a nonempty provenance hash do not release the gate. A supplied key does not prove durable idempotency enforcement.

CheckpointManager.recover_mission reports blocked_tasks without changing the blocked task's attempts, outcome or retry count, and returns dag_ready=false when any task is blocked. Runtime resume_mission and execute_goal(Mission) preflight the entire unfinished mission and return BLOCKED before scheduling, invocation or state changes. The whole mission pauses conservatively, including independent tasks; this avoids making blocked dependencies executable through static waves.

ReplayEngine.can_replay_task uses the same gate; force=True in replay_mission_dag cannot bypass it. These updates supersede the corresponding counter-only/reconciliation omissions in the baseline table below. They do not implement reconciliation or automatic unblocking: recovery evidence needs a future accepted-state protocol. Do not delete historical effects or mark recovery complete just to make retry eligible.

Remaining limitations: missing/inaccurate effect records, unvalidated IDEMPOTENT/RETRY_SAFE declarations, direct adapter calls, legacy counter-only eligibility without recorded blockers, cancellation, compensation ownership, authenticated grants and durable deduplication are still unresolved. VERIFIED tasks retain their existing freshness limitations. This is not complete recovery certification.

Evidence: tests/test_agentic_recovery_guards.py adds six tests covering blocked modes, pending states, explicit idempotent compatibility, forced replay, checkpoint restoration and both runtime entry points. Baseline focused suites: 17 passed; with guard tests: 23 passed. `python -B run_tests.py`: 246 passed, 40 suites, no failures/errors. Runner excludes its recursive test_agentic_system wrapper; these are local regression results, not remote fault-injection proof.

| Classification | Path / symbol | Current behavior | Consumers / limitation |
| --- | --- | --- | --- |
| EXISTING | models.py: FailureClass, FailureAttribution | Separate cause taxonomy and accountable entity | Runtime, attempt persistence, diagnostics; presence does not establish causal accuracy |
| EXISTING | models.py: SideEffectRecord, SideEffectType, IdempotencySemantics | Explicit effect, target, expected/observed change, rollback/compensation/provenance fields | Attempts and resilience; optional/incomplete records remain possible |
| CONFLICTING | runtime.py: execute_goal/resume_mission | retryable may be set from verification failure and remaining retry count | Attempts consumed by recovery; lacks mandatory effect reconciliation |
| CONFLICTING | resilience.py: CheckpointManager.recover_mission | RUNNING/PENDING/READY/FAILED become READY when retries remain | Checkpoint API; cannot infer no effect from interruption |
| CONFLICTING | runtime.py: resume_mission | Own interrupted-task recovery path | Runtime callers; fixing ReplayEngine alone would not close recovery |
| CONFLICTING | resilience.py: ReplayEngine.can_replay_task | Checks verified/count/key/UNSAFE_TO_RETRY; otherwise can allow mutable work | replay_mission_dag; RECONCILIATION_REQUIRED is not an enforced prerequisite |
| PARTIAL | resilience.py: can_automatically_compensate | Tests nonempty provenance_hash and compensation_action | Compensation helper and replay; does not prove ownership or completed compensation |
| CONFLICTING | resilience.py: generate_compensating_action_dag | Can create rollback task from write scopes; some absent-effect paths bypass provenance guard | Recovery API; a proposed task is not a performed rollback/compensation |
| PARTIAL | infrastructure.py: run_command | Timeout returns TIMEOUT/124 after p.kill() | Runtime; cannot establish descendant or remote-effect state |
| CONFLICTING | fitness.py: evaluate_skill | Excludes some non-skill failures then falls back to all spans when none remain | Skill ranking; can penalize a skill solely for node failures |
| PARTIAL | failure_attribution.py: diagnose_failure | Heuristic log/result classification and confidence constants | Runtime diagnostics; not independent causal proof |

FailureAttribution includes PLANNER, RESOLVER, AGENT, SKILL, TOOL, NODE, DEPENDENCY, ENVIRONMENT, EXTERNAL_SERVICE, POLICY and UNKNOWN. A timeout is an observation about response timing; it is not evidence that a remote mutation did not occur.

## 2. Required operation-sensitive retry matrix

Legend: C = conditional on fresh authorization, budget, deadline, bounded attempts/backoff and evidence that another try can help. R = reconcile unknown or partial mutable effects first. Compensation is never automatic merely because a failure class suggests it. Different skill requires replanning and a new authorized binding, not a hidden retry.

| FailureClass | Retry | Same node | Different node | Reconcile first | Compensation | Blocks dependents / human gate / fitness |
| --- | --- | --- | --- | --- | --- | --- |
| TRANSIENT | C after temporary cause | C | C if state transferable | R for unknown writes | Only owned effects | Yes until verified; escalate exhausted; attribution required |
| PERMANENT | No identical retry | No | Not a cure | R if partial effects | Conditional | Yes; corrected plan/input needed; blame not inferred |
| VALIDATION | After diagnosis/correction | C | Only environment evidence | R if mutation already occurred | Conditional | Yes; independent recheck; not automatically SKILL |
| POLICY | No bypass | No | No bypass | Inspect only if authorized | Separately authorized | Yes; policy owner decision; no skill penalty |
| AUTHORIZATION | Only fresh valid grant | C after grant | No privilege shopping | Authorized inspection | New scoped grant | Yes; explicit approval/authentication; no skill penalty |
| CONFLICT | After ownership/version resolution | C | No duplicate owner | R | Conditional | Yes; escalate ambiguous owner; no default skill penalty |
| TIMEOUT | C for proven safe retry | C | C with fencing/correlation | R for unknown writes | Never before inspection | Yes; unknown effect may require human; cause UNKNOWN until evidence |
| RESOURCE_EXHAUSTED | After authorized capacity/budget change | C | C within same authority | R | Conditional | Yes; cannot self-increase budget; resource attribution |
| DEPENDENCY_FAILURE | After dependency verified | C | Not independently | R | Conditional | Yes; dependency owner; not dependent skill penalty |
| EXTERNAL_SERVICE | C after service recovery | C | Only valid routing | R for uncertain response | Conditional | Yes; provider evidence; no automatic skill penalty |
| MALFORMED_RESULT | Inspect actual state first | C | C after diagnosis | R | Conditional | Yes; tool/output origin must be established |
| INTEGRITY_FAILURE | Quarantine and diagnose | No blind retry | C with trusted source | R | No untrusted provenance | Yes; security review; no learning from corrupt evidence |
| COMPATIBILITY | After compatible binding | C if repaired | C after handshake | R | Conditional | Yes; compatibility proof; no automatic skill penalty |
| CANCELLED | No automatic restart | Explicit new request | Explicit new request | R if effects uncertain | Conditional | Yes; cancellation aftermath must be known |
| UNKNOWN | No blind retry | No until diagnosis | No evasion | R | No without provenance | Yes; cheapest valid inspection then escalate |

For PURE or READ_ONLY work, reconciliation of external writes is NOT_APPLICABLE only if the adapter actually guarantees no mutation. A command labelled read-only can still write. For LOCAL_WRITE and REPOSITORY_WRITE use target hash/version/ownership plus intended final state. EXTERNAL_WRITE, INFRASTRUCTURE_MUTATION and DESTRUCTIVE require stronger approval and unknown-outcome gates. Classify actual effects, not just task title or risk label.

Idempotency modes already exist: IDEMPOTENT, RETRY_SAFE, IDEMPOTENCY_KEY_REQUIRED, RECONCILIATION_REQUIRED, COMPENSATION_REQUIRED, UNSAFE_TO_RETRY. Idempotent final state does not imply safe duplicate notifications, billing or concurrency. A key stored in an in-memory set does not survive restart.

## 3. Recovery invariants and distinctions

Required sequence for uncertain remote result: retain OUTCOME_UNKNOWN, inspect the exact target using correlation/idempotency identity, determine actual state, then accept verified success, authorize safe retry, propose compensation or escalate. Lack of an inspect capability blocks unsafe retry; it does not justify assuming failure.

Rollback restores a known prior state within a mechanism that can truly restore it. Compensation is a new authorized effect that neutralizes a proven prior effect. A saga orders multiple such steps in reverse dependency order after failure. No saga engine is introduced in this audit.

**NO PROVENANCE → NO AUTOMATIC COMPENSATION.** Provenance must establish exact resource, producing attempt, ownership and observed change, not merely a nonempty digest. Proposed compensation must have scope/risk approval, conflict checks and independent verification. Completion of compensation is different from its availability.

Cancellation request, acknowledgment and confirmed cancellation are distinct. Required aftermath: determine whether effects occurred, children/remote jobs still run, artifacts are partial, verification is invalid, and reconcile/compensate/escalate accordingly. Current shell timeout is not a complete cancellation protocol.

ReplayEngine changes retry eligibility; it does not reconstruct a deterministic projection from accepted events. Event replay must be side-effect free; recovery dispatch is a new command requiring current permission, budget and effect checks. VERIFIED checkpoints need freshness validation before being trusted indefinitely.

## 4. Attribution, fitness and learning admission

### Fitness attribution increment — 2026-09-13

**Implemented, bounded:** SkillFitnessEngine now reuses FailureAttributionEngine.is_penalizable: only explicit SKILL attribution qualifies a failed span. Missing, UNKNOWN, non-skill and conflicting top-level/nested attributions are excluded. Failure categories such as MALFORMED_RESULT and MODEL_OUTPUT are not accountability identities and no longer qualify by themselves.

The same admitted sample population drives success rate, latency, token efficiency and sample_count. If no samples qualify, the existing cold-start prior is returned with sample_count=0; excluded failures are never reintroduced. is_cold_start now also covers observed histories with no attributable samples. Telemetry itself remains intact, so operational failure/cost analysis can still inspect excluded events.

Runtime execute_goal and resume_mission attach the recorded attempt_id and failure_attribution to the existing span evidence_summary. This preserves the causal link for fitness without a new schema or subsystem. Consumers of older spans without attribution must treat failed samples as unqualified; no historical attribution is invented.

Evidence: baseline fitness/M1/M5 suites passed 20 tests; four new tests cover all-excluded histories, mixed-history dimension invariance, conflicting attribution and telemetry persistence. Existing M1 execution/resume tests additionally assert attempt-to-span correlation. Final `python -B run_tests.py`: 250 passed across 40 suites, no failures/errors.

This supersedes the baseline empty-filter fallback finding. It does not authenticate attribution, validate freshness/environment or independently admit SUCCESS evidence. Existing cold-start prior, fixed recency heuristic, missing measurement semantics and legacy resume token estimates remain limitations. Phase 33 remains PARTIAL, and learning promotion gates remain open.

Required sample gate: known outcome, independent valid verification, fresh evidence, provenance, compatible environment, experiment label, attributable cause. Node/provider/policy/environment failures must not count as skill reliability failures. UNKNOWN attribution must remain unscored, not default to SKILL.

Current is_skill_penalizable and diagnosis helpers are useful but do not repair evaluate_skill's empty-filter fallback. LearningEngine count thresholds prevent a single direct promotion but do not validate distinct evidence or freshness; raw failure must remain an observation, not an immediately trusted heuristic.

Next minimal changes, **not implemented here**: unify recovery eligibility across checkpoint/resume/replay; fail closed for uncertain mutable outcomes; remove fitness fallback and require qualified samples; bind compensation to proven owned effects; add fault-injection tests for disconnect-after-effect, interrupted cancel, crash-after-write and all-node-failure fitness history. Scheduler, infrastructure, learning and federation gates remain open until those consumers enforce the contracts.
