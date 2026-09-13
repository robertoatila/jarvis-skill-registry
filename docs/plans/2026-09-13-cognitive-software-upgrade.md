# Cognitive software upgrade — discovery and execution record

Source: PROMPT-JARVIS-COGNITIVE-RUNTIME-SOFTWARE-UPGRADE.md, remote d2e91ef, merged into local main preserving four earlier commits. Initial tracked image modification ui/assets/jarvis_core.png is UNRELATED and remains untouched. Earlier contract/recovery/fitness increments are COMPLETE within their documented scope. Baseline: `python -B run_tests.py`, 250 passing tests / 40 suites.

## Discovery before implementation

| Existing component | Current responsibility | Gap | Smallest extension / affected files |
| --- | --- | --- | --- |
| ModelRouter / ModelCandidate | Privacy/cost/context selection | IDs in Python defaults; no tool/network/availability requirements; unstable ties; empty catalog defaults to populated | Validated capability request and explicit execution policy; manifest defaults in config; model_router.py |
| ToolRouter / ToolCandidate | Capability/risk filtering | Substring matching; permission/network not input | Exact capabilities and optional policy allowlist; tool_router.py |
| ContextGovernor / ContextReceipt | File reads, hashes, summaries | No deterministic per-call compiler or mandatory overflow | Extend existing module with bounded context compilation and source receipts |
| CognitiveGovernor | Autonomy and repeated-action stop | Confidence does not drive an inference decision | Explicit confidence/evidence gate using caller thresholds |
| JarvisAgenticRuntime | Attempts, local adapters, verification, state | Model decision is advisory; resume differs | Narrow inference entry point reusing routers/governor/context; explicit registered backend boundary |
| jarvis_server.py forward_external_llm | Provider-specific HTTP and key handling | UI/server-coupled, no scoped reusable inference contract | Preserve legacy UI path; do not claim new policy applies to it |
| FailureClass / recovery gate | Failure taxonomy, recorded-effect blocking | No pure inference fallback binding | Bounded candidate transitions; deny mutable tool execution in new inference path |
| MemoryFabric / snapshots | Four tiers, provenance, lexical retrieval | Session/agent isolation and selective write not uniform | Scoped opt-in inference memory access; existing metadata and snapshot storage |
| NoRepeatReadCache | Content hash read cache | Not a policy/version-scoped inference-result cache | Extend context module with bounded deterministic result cache; policy checked before hits |
| DecisionReceipt / Span | Decision and runtime evidence | Model invocation/context/fallback absent | Structured metadata; hashes/references rather than raw prompts |

## Repository-wide coverage and limits

Inspected root docs, canonical architecture/roadmap/security contracts, Python agentic modules and their consumers, server provider path, schema/PowerShell tooling layout, tests and CI workflows. Registry governance uses PowerShell; UI/server and agentic runtime are distinct surfaces. No claim of line-by-line review of every skill, staged source or binary asset. No PowerShell executable is available here, so Windows/Linux/macOS PowerShell CI cannot be reproduced locally. No Python project-wide typecheck/lint config was located. UI, federation, n8n and hardware are outside this prompt's implementation scope.

Compatibility strategy: keep legacy APIs/default catalog import available; new strict execution requires explicit contracts and registered backends. No implicit cloud fallback or fabricated backend success. Existing server egress, stale success evidence and unrecorded mutable effects remain separate blockers; the upgrade must not certify them indirectly.

Increment order: manifests/policy/routing; context; confidence; typed bounded inference fallback; isolated opt-in memory/cache/trace; regressions and documented limits. Each increment gets focused tests before the next.

## Implemented scope and compatibility

- ModelCandidate validation and new immutable InferencePolicy/InferenceRequirements extend ModelRouter. Provider IDs/default estimates moved to config/model-catalog.json; DEFAULT_MODELS remains import-compatible. Historical catalog values are configuration examples, not current prices or measured quality. New execution uses only explicitly registered backends, never that illustrative catalog as proof of availability.
- Model routing checks locality, network, model allowlist, availability, context, tools, capability and estimated budget before configurable scoring. Ties use model ID. Empty catalogs no longer silently load defaults. ToolRouter adds policy/network filtering and exact capability matching; substring matching is intentionally removed. Existing aliases/wildcards remain explicit catalog declarations.
- compile_context extends the context module, deduplicates content while retaining references, prioritizes mandatory items and rejects mandatory overflow/staleness. JSON envelope and references consume the same bounded UTF-8 byte estimate; provider tokenizer usage is not claimed measured.
- CognitiveGovernor.confidence_action returns ACCEPT, VERIFY_EVIDENCE, GATHER_EVIDENCE or TRY_ELIGIBLE_ALTERNATIVE. execute_inference requires an independent verifier, valid evidence references and a configured threshold. Unknown/low confidence cannot silently become accepted success.
- InferenceBackends is the missing narrow adapter boundary, not a second runtime. Registered callbacks receive frozen call-local requests and are serialized per shared backend. No actual provider transport, credentials, GPU or external service is required by tests. Caller-supplied adapters are trusted code; this is not OS network sandboxing against a malicious callback.
- JarvisAgenticRuntime.execute_inference performs bounded candidate fallback and creates existing ExecutionAttempt records on TaskNode. TRANSIENT, EXTERNAL_SERVICE and MALFORMED_RESULT may try another eligible candidate; POLICY, AUTHORIZATION and unknown exceptions stop. Each candidate is visited at most once. Effectful tool calls are explicitly BLOCKED in this entry point until a complete authorized tool binding exists. No silent adapter fallback.
- Scoped memory reuses MemoryFabric snapshots under a hash of mission/agent/session/policy. Writes are opt-in, independently accepted, confidence-qualified, expiry-bounded and content-deduplicated. Retrieval is budgeted, scope-confined and rejects expired facts. No automatic cross-session memory sharing or lifecycle promotion.
- InferenceCache is bounded and copy-on-access. Key includes scope, normalized task, manifest/version/binding, context hash, requirements, policy, threshold and contract version. Policy is evaluated before lookup; verifier runs on hits; TTL cannot exceed context evidence expiry. Re-registering a backend invalidates old binding keys. Cache is process-local, not a durable semantic cache.
- Result trace contains routing/rejections, context receipt, attempt IDs, chosen models, cache state, confidence action, failure transitions, references, hashes, timing, estimate reservations and memory-write count. Raw context/output and backend exception payloads are not embedded in the trace. Full result text is returned separately to the caller. Task attempts are serialized by existing APIs; execute_inference does not silently save a parent Mission the caller did not provide.

## Repository reanalysis results

- 116 files under schemas/: valid JSON syntax; not a claim of validating every schema instance or cross-schema constraint.
- 154 skills/*/SKILL.md inspected for literal backtick references under references/, scripts/, assets/: 285 unique missing local paths. Heuristic excludes wildcard/placeholder paths; results require source-package verification before repair. The missing loop-controller references are part of this broader distribution gap.
- 42 Python test files and 34 PowerShell test scripts found before new test additions were finalized. The standard agentic runner intentionally excludes its recursive system wrapper.
- tooling Python compilation and ui/jarvis.js syntax checks passed. Existing UI binary modification remains UNRELATED and excluded from commits.

## Checks actually executed

- Baseline: python -B run_tests.py — 250 passed / 40 suites.
- Initial targeted command referenced nonexistent tests.test_agentic_m4_cognitive_routing — import error; corrected to the discovered tests.test_agentic_m4_adaptation_learning. No product failure was hidden by that typo.
- python -B -m unittest tests.test_agentic_software_upgrade tests.test_agentic_cognitive_contract_closure — 8 passed at the routing increment.
- python -B -m unittest tests.test_agentic_software_upgrade tests.test_agentic_m4_adaptation_learning — 14 passed at the context increment.
- python -B -m unittest tests.test_agentic_software_upgrade — progressively 14, 19 and 20 passed as integration tests were added; final suite contains 21 tests.
- Final python -B run_tests.py — 271 passed / 41 suites; no failures/errors. Provider tests use explicitly identified local test doubles, including cloud-labelled manifests; no cloud traffic was sent.
- python -m compileall -q tooling; node --check ui/jarvis.js; git diff --check — passed.
- PowerShell CI matrix/bootstrap/governance scripts — NOT RUN: pwsh/powershell absent. No full cross-platform certification or deployment claimed.
- Canonical security protocol was not invoked: it requires the user's explicit invocation. Reading CI configuration did not activate that separate workflow.

## Metrics, not marketing

No comparable production inference baseline exists, so no token/cost savings percentage is claimed. Test count changed 250 -> 271. In a controlled repeated-request fixture, two identical scoped requests invoke the backend once and the second is a cache hit; changing session produces another invocation. Context output stays within the declared serialized-byte accounting budget. Time in trace is measured with perf_counter; actual provider token usage and cost remain UNKNOWN. Estimated cost reservation is charged before each attempted backend invocation, including failed invocations. Historical default price/quality metadata is not empirical evidence.

## Residual blockers / next increment

The original UI/server provider path and autonomous goal planner do not automatically use execute_inference. Effectful inference tools remain blocked; global authorization intersection, legacy recovery of unrecorded effects, stale success admission and provider-token accounting remain open. Trusted callbacks must enforce transport timeouts/output bounds and declared locality; Python callback registration is not a security sandbox. Memory snapshots retain existing single-writer limitations. Core default catalog files must be packaged with distributions.

Next highest-impact increment: migrate the existing server provider transport behind the explicit inference adapter/policy boundary, with actual provider response validation, token usage and deadlines. This must be separately scoped because this prompt excludes HUD behavior changes; do not certify local_only for the legacy server through tests of the new entry point.
