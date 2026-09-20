# Runtime Execution Contract — evidence-first reassessment

Audit date: 2026-09-12. Source baseline: local commit `23612c9`; clean worktree, one commit ahead of origin/main. No interrupted uncommitted changes were found. This revision supersedes the previous document's unsupported implementation/certification claims, not its safety goals.

Scope: foundational contracts only. No new scheduler, planner, agents, learning engine, infrastructure or federation implementation. Existing symbols are reused. Paths below are relative to the repository; agentic module paths are under `tooling/agentic/`.

Classification: **EXISTING** = concrete mechanism located; **PARTIAL** = incomplete enforcement; **MISSING** = absent in inspected paths; **CONFLICTING** = behavior contradicts contract; **AMBIGUOUS** = insufficient evidence; **NOT_APPLICABLE** = outside this local audit. Documentation, persisted schema, enforcement and tested invariants are separate evidence.

## 1. Existing-mechanisms map

| Classification | Path / symbol | Implemented or persisted behavior | Consumers | Limitation |
| --- | --- | --- | --- | --- |
| EXISTING | models.py: Mission, TaskNode, ExecutionAttempt | Mission owns DAG; task retains action, requirements and individual attempts; attempts persist executor IDs, independent states, effects, references, budgets and trace fields | runtime.py execute_goal/resume_mission; DAG and state deserialization | Optional fields are not proof that every producer populates them |
| EXISTING | models.py: ExecutionState, VerificationState, RecoveryState, MissionOutcome | Four separate enum dimensions on attempts | Runtime, serializers, contract tests | TaskStatus remains an aggregate legacy lifecycle; consistency is not globally validated |
| PARTIAL | models.py: validate_schema_version, ExecutionAttempt.from_dict | Version checks and legacy parsing | StateStore, DAG, checkpoints | Legacy identifiers can be synthesized; complete migration provenance and compatibility matrix are absent |
| PARTIAL | state_store.py: AuthoritativeStateStore | Mission JSON via atomic save; invalid load quarantined | Runtime load/save | Atomic replacement is not distributed locking, multi-file transaction or power-loss durability proof; sanitized IDs may collide |
| PARTIAL | resilience.py: CheckpointManager, ReplayEngine | DAG snapshots, ready-state recovery, retry preparation | Recovery APIs and tests; runtime also has separate resume logic | Not an accepted-event reducer; unknown-effect recovery differs between entry points |
| PARTIAL | adapters/local.py: LocalAction, LocalActionResult, LocalActionAdapter | Confined reads and writes, size limits, expected hash conflict checks | Runtime/local tests | No common capability-negotiated cancel/reconcile interface; runtime context read uses another path |
| PARTIAL | infrastructure.py: InfrastructureSkillDriver.run_command | Shell process, timeout, result snippets and duration | Runtime command execution | Regex denylist is not sandboxing; output is bounded after capture, not during capture |
| CONFLICTING | planner_resolver.py: generated COMMAND_EXIT_ZERO requirement; runtime.py: execute_goal/resume_mission | Planner can generate print-only verification; runtime takes verification command as execution command | Default plans and mission execution | Executing a check cannot prove that the requested work was performed |
| PARTIAL | runtime.py: execution_binding dict | Main path compares selected tool to built-in executor and stores causal IDs | Main attempt metadata | No general adapter/model binding contract; resume path differs; model recommendation is not model invocation |
| PARTIAL | verification.py: VerificationEngine, VerificationEvidence | Checks real files/hash/commands/HTTP, retains UTC/hash/result payload | Runtime verification; mission completion | Missing generalized freshness/environment validation; VERIFIED tasks bypass recheck; command verification can itself cause effects |
| PARTIAL | models.py: Artifact.compute_hash | SHA-256 and size from bytes; producer and environment fields | Artifact serializers / checks | Legacy string artifacts accepted; hash is not signature or authenticated producer; no universal reuse gate |
| PARTIAL | budgets.py: BudgetTracker; models.py: MissionBudget | Token, call, iteration/time counters and limits | Runtime and admission estimates | Main/resume accounting differs; resume still supplies 140 tokens; no complete cost reservation/restart reconciliation |
| PARTIAL | admission.py: AdmissionGate.evaluate_task | Dependencies, agent matching, scopes, estimated budget, risk | Runtime admission | BLOCKED lacks permanent unschedulable distinction; unknown estimates and approved flags do not prove safe dispatch |
| PARTIAL | scheduler.py; dag.py | Existing waves, dependency/conflict handling | Runtime and scheduler tests | Queue/event/retry/global limits, fairness and live dispatch guarantees need integration evidence |
| PARTIAL | telemetry.py: Span, TelemetryCollector | Span IDs, append JSONL, recent buffer capped at 200 | Fitness and metrics | Write exceptions are printed, not durably retried; no exactly-once or durable dedup guarantee |
| CONFLICTING | fitness.py: evaluate_skill | Filters some attributed failures | Ranking / runtime fitness | If filter removes all spans, fallback reintroduces all; missing attribution also remains eligible |
| PARTIAL | learning.py: record_observation/promote_candidate | Observation/pattern/heuristic tiers and count thresholds | Runtime / learning consumers | Evidence list length does not prove distinct, fresh, verified corroboration; confidence is heuristic |
| PARTIAL | federation.py: FederationRouter | Node catalog, capacity/profile routing, envelope digest | Routing callers / tests | Unkeyed SHA-256 is not authentication; registration accepts declared trust |
| EXISTING | tooling/jarvis_server.py: QuantumAgentEngine | Class and instantiated QUANTUM_ENGINE located | Server API | Presence does not certify safe autonomous execution |
| CONFLICTING | skills/agentic-loop-controller/SKILL.md | Requires references/full-workflow.md and references/define-goal.md | Skill users | Published directory contains only SKILL.md. Restore from verified source; do not invent missing procedures |

## 2. Command, attempt and state contracts

### Capability-driven inference entry point (2026-09-13)

Server continuation: /api/chat now uses the shared inference adapter contract with explicit cloud authorization and a single selected provider. Chat replies remain UNVERIFIED instead of inventing confidence/evidence. See [server boundary and client migration](SERVER_INFERENCE_BOUNDARY.md). Provider-reported tokens populate attempt accounting when supplied; cache hits do not recharge historical usage.

JarvisAgenticRuntime.execute_inference is an explicit pure-inference entry point. It reuses TaskNode/ExecutionAttempt, ModelRouter, ContextReceipt, CognitiveGovernor and MemoryFabric, with provider transport behind adapters/inference.py. Callers register a validated ModelCandidate and trusted stateless callback in runtime.inference_backends, then supply InferencePolicy, InferenceRequirements, bounded context items and an independent verifier. No backend is implicitly available; missing candidates return BLOCKED. Tool effects return an explicit separate-authorization blocker.

The policy is narrowed by config.offline_only. Network-requiring local/LAN adapters are denied when network is denied; no implicit localhost exemption is introduced. Registered adapters must accurately declare locality/network and enforce their own transport deadlines; the boundary is not an OS sandbox. Context is deterministically compiled under a serialized UTF-8 byte estimate, never misreported as measured provider tokens. Unknown confidence, stale mandatory evidence, overflow and policy failures have distinct observable stop/transition codes.

Results carry a structured trace with reason codes and hashes, while actual invocations/cache retrievals create existing attempt records on the supplied task. Parent mission persistence remains explicit. The old execute_goal and server transport APIs keep their existing execution paths and limitations. See [upgrade discovery, migration notes and checks](../plans/2026-09-13-cognitive-software-upgrade.md). The entire autonomous runtime is not certified by these bounded inference tests.

Continuation 2026-09-13: the shared recorded-effect recovery gate now blocks unsafe replay/checkpoint recovery and returns status=BLOCKED from resume_mission and execute_goal(Mission) before scheduling or invocation. BLOCKED is an API result, not a new persisted execution/outcome state. The persisted unknown outcome is preserved; no retry charge or synthetic recovery attempt is created for a blocked runtime call. See the dated [failure-semantics increment](FAILURE_SEMANTICS.md) for exact scope and remaining gaps. Six added recovery tests and the 246-test local runner passed.

A command requests work; an event describes a past observation; authoritative state records the accepted current situation; HUD/Vault projections are derived views. Neither telemetry nor a replayed event grants permission to execute. Existing module separation approximates control, execution and evidence planes, but does not prove enforcement across them.

Task identity persists across attempts. Each attempt needs a unique identity and a link to its owning task. A local validation change in this audit rejects foreign-task and duplicate-ID attempts both at record_attempt and construction/deserialization. Failure leaves history and retry_count unchanged. It does not impose new numbering rules or change the serialized schema.

Compatibility: previously accepted malformed histories now raise ValueError; AuthoritativeStateStore may quarantine them on load. Preserve and inspect such records; never silently discard, relabel or renumber them. Empty legacy histories remain valid. Public mutable dataclasses still allow direct list mutation; mission-wide identity and transition validation remain open.

Required, not universally enforced:

- Finished means executor terminated or returned; verified means an explicit check of the desired result passed.

- Outcome cannot become succeeded merely because exit code is zero or a path exists.
- Attempt IDs identify invocations; idempotency keys identify logical effects and must remain stable across retries of the same effect. Do not include attempt_number in the logical key.

- Input/output references must not become arbitrary payload or secret storage.
- Binding, attempt, produced artifact, verification and resource receipt must refer to the same actual invocation.

- Snapshot schema validation must not treat migrated/synthetic identifiers as authenticated lineage.

## 3. Evidence, time and interoperability

Artifact freshness concerns the bytes and dependencies. Verification freshness concerns applicability of a check. Evidence freshness concerns whether an observation still supports a claim. VERIFIED at T1 is not VERIFIED at T2 by implication. VerificationEvidence currently has verified_utc but not a complete valid_until/fingerprint invalidation protocol.

Required reuse gate: locate, check bytes/hash, validate producer/provenance, compare environment/dependencies, evaluate freshness, then reuse or reverify. Hashing authenticates neither the producer nor the truth of the content. Keep raw transcript as audit material, not authority.

ExecutionAttempt.environment_fingerprint and Artifact.environment exist as dictionaries. Required meaningful fields, when relevant: OS, architecture, runtime version, dependency lock hash, skill version, repository commit, configuration hash and node identity. Population and validation are incomplete; UNKNOWN must not be filled with invented measurements.

Runtime durations, infrastructure commands, BudgetTracker and telemetry spans use perf_counter; UTC/time.time are used for audit timestamps and some IDs. Expiry/heartbeat behavior under clock jumps, uniqueness of time-derived IDs and cross-restart deadline reconstruction are not validated here. Monotonic values cannot be carried unchanged across processes.

Adapters should declare supported cancel/timeout/idempotency/key/reconcile/compensation/verification/dry-run/streaming capabilities. No common enforced negotiation was located in local, infrastructure and n8n paths. Missing support must block an operation requiring it; do not add no-op methods masquerading as support. Protocol/runtime/schema versions and capability flags need separate negotiation before external execution.

Telemetry delivery is best-effort local append with possible loss and duplicates, not exactly-once. No durable accepted-event reconstruction contract is demonstrated. ReplayEngine prepares retries; deterministic projection reconstruction remains a separate future requirement. It must never authorize repeating external effects.

## 4. Acceptance answers and unresolved gates

| # | Question | Evidence-backed answer |
| --- | --- | --- |
| 1 | Task? | TaskNode: stable unit of intent/dependencies/actions/verification and attempt history |
| 2 | Attempt? | ExecutionAttempt: distinct persisted invocation, not just retry_count; identity validation strengthened here |
| 3 | Execution ended? | ExecutionState FINISHED or failure/cancel/timeout terminal observation; not a verified outcome |
| 4 | Verified? | VerificationEngine evaluates requirements; current placeholder commands weaken desired-state proof |
| 5 | Failure versus unknown? | FailureClass and OUTCOME_UNKNOWN exist; runtime paths do not consistently preserve unknown effects |
| 6 | Retry permitted? | See failure matrix; current counter-based paths are insufficient |
| 7 | Reconcile required? | Unknown mutable outcome without proven idempotency; not consistently enforced |
| 8 | Compensation allowed? | Proven owned effect plus authorized compensating action and verification; nonempty hash alone insufficient |
| 9 | Effects identified? | SideEffectRecord has type, target, expected/observed change; completeness at each adapter is unproven |
| 10 | Idempotency? | IdempotencySemantics enum and keys exist; no demonstrated durable effect deduplication |
| 11 | Attribution? | FailureAttributionEngine plus enum; heuristic diagnosis and fitness fallback conflict remain |
| 12 | Effective permission? | Policy/admission/profile checks are partial; seven-way intersection is a required contract, not current proof |
| 13 | Authority vs data? | Runtime policy and explicit authorization govern; repo/tool/remote content is data. Enforcement incomplete |
| 14 | Secrets? | Telemetry regex redaction exists; no common SecretReference provider contract found in agentic paths |
| 15 | Artifact integrity? | Artifact hash/size fields and hash check exist; optional metadata and path strings weaken reuse |
| 16 | Stale? | STALE vocabulary exists; general expiry/dependency invalidation not enforced |
| 17 | Environment evidence? | Optional dictionaries exist, no mandatory comparable fingerprint |
| 18 | Cancellation? | Process timeout kills child shell; acknowledgment, descendants and external effects remain unknown |
| 19 | Unschedulable? | Admission BLOCKED may mean missing prerequisites or impossible capability; no durable distinction |
| 20 | Replay safe? | Retry preparation does not itself execute; subsequent dispatch still needs fresh authorization/effect reconciliation |
| 21 | Fitness inputs? | Only known verified outcomes with fresh trusted evidence and valid attribution should count; current filtering insufficient |
| 22 | Learning inputs? | Qualified observation with provenance/environment, distinct evidence and bounded promotion; counts alone insufficient |
| 23 | Node identity? | Self-declared catalog identity plus digest; no demonstrated proof of key possession |
| 24 | Capabilities negotiated? | Profile/capacity matching exists; mutual protocol/schema feature negotiation missing in inspected router |
| 25 | Blocking gates? | Below; these are requirements, not passed certifications |

## 5. Required quality gates (open)

- **Scheduler:** execution/verification separation; deterministic ready selection; bounded concurrency/queues/retries; conflict ownership; cancellation aftermath; restart and unknown-outcome tests; age/priority/risk/resource and mission fairness. Existing scheduler must meet these before expanded use.

- **Infrastructure:** classified complete effects; stable logical idempotency; inspect/reconcile where necessary; provenance before compensation; effective scoped grants; safe secret materialization; independent desired-state verification.
- **Learning:** known outcome; valid/fresh evidence; attributable cause; authenticated provenance and environment; distinguish experimental samples; confidence UNKNOWN permitted; promotion cannot alter policy/budgets/audit.

- **Federation:** authenticated node identity; scoped authorization; protocol/schema/capability negotiation; artifact integrity; correlated results; leases and unknown-outcome reconciliation; explicit clock assumptions.

Priority order: close existing foundation, then reuse runtime consumers. Optional external transcript ingestion, n8n integration and infrastructure skill ingestion are NOT_APPLICABLE to this implementation scope.

## 6. Checks and evidence limitations

Continuation 2026-09-13, fitness attribution: excluded non-skill/unknown failures no longer affect any fitness scoring dimension or sample count. All-excluded histories use the existing unobserved prior. Main execution and resume now carry attempt_id/failure_attribution into Span.evidence_summary. The [dated failure-semantics increment](FAILURE_SEMANTICS.md) supersedes the baseline fitness fallback finding above. Four new fitness tests plus attempt/span integration assertions passed; final local runner: 250 tests, 40 suites. Evidence freshness, success admission and authenticated attribution remain incomplete.

Baseline command:
`python -B -m unittest tests.test_agentic_contracts tests.test_agentic_foundation tests.test_agentic_m1_foundation tests.test_agentic_resilience tests.test_agentic_verification tests.test_agentic_m3_dispatch_recovery`

Baseline: 41 passed; after lineage validation: 45 passed. Four new contract tests cover rejected foreign/duplicate append, unchanged counters, and invalid construction/restoration. These checks do not certify network providers, authentication, distributed durability, all schema migrations or system-wide security.

Additional executed checks:

- `python -B -m unittest tests.test_agentic_cognitive_contract_closure tests.test_agentic_m6_hardening_faults`: 13 passed (58 post-change tests across both commands, not a whole-repository suite).

- `python -m compileall -q tooling/agentic/models.py tests/test_agentic_contracts.py`: exit 0; syntax compilation, not type checking.
- `git diff --check`: exit 0.

- In-memory diagnostic with `python -B -` called N8nAdapter.parse_inbound_trigger without a signature: accepted. ReplayEngine.can_replay_task returned True for a FAILED task with an OUTCOME_UNKNOWN attempt and EXTERNAL_WRITE / RECONCILIATION_REQUIRED effect. No effect was executed. Both affected modules were unchanged in this audit; these are existing gaps, not new validation regressions.

No external deployment, full-repository lint/typecheck, provider integration, live HUD/Vault or security certification was attempted. Initial clean worktree means there were no interrupted hunks to classify COMPLETE/PARTIAL/BROKEN/UNRELATED; prior committed work remains preserved. No push, tag or release was performed.

See [Failure Semantics](FAILURE_SEMANTICS.md), [Trust Boundaries](../security/TRUST_BOUNDARIES.md) and [canonical roadmap](../roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md).
