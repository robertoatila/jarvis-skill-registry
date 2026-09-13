# GitNexus Engineering Plan

> Task: Close the gap between documented and operational cognitive runtime behavior.
> Evidence verified at commit 91909f69bed720274a148a4411090f90d4511889; GitNexus unavailable, source-derived fallback mode used.
> Evidence provenance schema 2; global dirty digest 0a9c85780067d9afcd0764f307b60891e3cee927ee11eaeb5ec7826d10fd82cd; cited-path manifest 10 sorted entries; exact generated plan path excluded.

## 1. Objective

Make the local runtime portable and causally honest: a routed decision must bind to a real executor, execution without an executor must fail closed, resource usage must be measured/estimated/unknown rather than invented, context reads must be contained and receipted, governor state must be mission-scoped, and release claims must match reproducible evidence.

## 2. Current Behaviour

- [verified] `tooling/agentic/config.py` defaults to a machine-specific `E:/.skill-registry` root, causing 14 baseline failures/errors on Linux.
- [verified] `tooling/agentic/runtime.py` records Tool/Model DecisionReceipts but executes the pre-existing local/infra branch independently of the selected candidates.
- [verified] A task without action or command returns synthetic success text.
- [verified] Context reads resolve a joined path but do not prove containment under the workspace root.
- [verified] The runtime owns one CognitiveGovernor instance whose loop state survives across missions unless reset manually.

## 3. Relevant Architecture

The execution path is planner → scheduler → admission → routing → policy → adapter/command → verification → attempt/evidence. Configuration is imported by state, memory, telemetry and discovery subsystems. Documentation promotes the selected local scope to release-candidate status.

## 4. GitNexus Findings

GitNexus was not installed/indexed in this checkout. Findings are source-derived from targeted reads and the independent `python -B run_tests.py` baseline (231 run, 217 pass, 8 fail, 6 error).

## 5. Statement-Level PDG Findings

No PDG layer was available. Source inspection shows routing receipts are produced at runtime.py:358–370, while the actual executor is selected again by branch conditions at runtime.py:493–514; the selected candidates do not control that branch.

## 6. Proposed Changes

- `tooling/agentic/config.py` and agentic root constants: derive portable repository root with environment override.
- `tooling/agentic/runtime.py`: introduce an explicit execution binding, fail closed on unresolved tool/model and missing executor, reset governor per mission, attach causal receipt IDs, and record non-fabricated usage.
- `tooling/agentic/context_governor.py`: enforce workspace containment; enrich receipts with relevance, confidence, provenance and delivery mode; support summary/reference reuse.
- `tooling/agentic/tool_router.py`: require all requested capabilities and replace fabricated confidence with unknown/observed metadata.
- Tests: cover cross-mission governor isolation, path escape denial, router-to-executor binding, no-action rejection and receipt lineage.
- Roadmap/release report/README: replace certification claims with the evidence actually reproduced after the changes.

## 7. Implementation Sequence

1. Repair root portability and make the original 231-test baseline reproducible.
2. Add failing contract tests for containment, mission scope, missing executor and binding.
3. Implement execution binding and fail-closed dispatch.
4. Integrate ContextGovernor receipts into task execution and causal evidence.
5. Harden router capability semantics and resource accounting.
6. Align documentation, run complete tests, static compilation and security audit.

## 8. Test Strategy

Run targeted unittest modules after each contract change, then `python -B run_tests.py`, `python -m compileall -q tooling tests examples`, and the repository pre-publish security audit. Negative scenarios must prove no executor/no binding/path escape cannot be reported as executed or verified.

## 9. Risk and Impact Analysis

The highest compatibility risk is legacy planner tasks that relied on synthetic no-action success. The change intentionally rejects them unless a concrete adapter or command exists. Router capability tightening may block loosely described tasks; tests and planner defaults must provide explicit executable capabilities.

## 10. Files Expected to Change

| File | Symbols | Reason |
| --- | --- | --- |
| `tooling/agentic/runtime.py` | `JarvisAgenticRuntime.execute_goal` | causal binding and fail-closed execution |
| `tooling/agentic/context_governor.py` | `ContextReceipt`, `read_with_receipt` | containment and context economics |
| `tooling/agentic/config.py` | `DEFAULT_ROOT`, `load_config` | portability |
| `tooling/agentic/tool_router.py` | `matches_capabilities`, `route_tool` | complete capability match |
| `tests/` | runtime/context/router tests | regression and integration evidence |
| `docs/roadmap/`, `reports/`, `README.md` | maturity claims | credibility alignment |

## 11. Reusable Implementation Context

```yaml
implementation_context:
  task_summary: "Close cognitive runtime contracts and align claims with evidence"
  evidence_provenance:
    schema_version: 2
    head_commit: "91909f69bed720274a148a4411090f90d4511889"
    generated_plan_path: "docs/plans/2026-09-12-gitnexus-plan-cognitive-contract-closure.md"
    global_dirty_digest:
      algorithm: "sha256"
      canonicalization: "gitnexus-evidence-provenance-v2 NUL-framed UTF-8 records"
      value: "0a9c85780067d9afcd0764f307b60891e3cee927ee11eaeb5ec7826d10fd82cd"
    cited_path_manifest_count: 10
  files_to_modify:
    - file: "tooling/agentic/runtime.py"
      symbols: ["JarvisAgenticRuntime.execute_goal"]
      intended_change: "Bind decisions to actual execution and fail closed"
    - file: "tooling/agentic/context_governor.py"
      symbols: ["ContextReceipt", "ContextGovernor.read_with_receipt"]
      intended_change: "Contain reads and make context spending explainable"
  tests:
    - file: "tests/test_agentic_cognitive_contract_closure.py"
      scenarios: ["cross-mission isolation", "path escape denial", "missing executor rejection", "binding lineage"]
  verification_commands:
    - "python -B run_tests.py"
    - "python -m compileall -q tooling tests examples"
    - "python tooling/audit_pre_publish_security.py"
  assumptions: []
  open_questions: []
  avoid:
    - "Do not preserve synthetic execution success for compatibility"
    - "Do not claim measured token or model cost without observations"
```

## 12. Assumptions and Open Questions

No blocking open question. External tool/model invocation remains outside this local milestone; the router must truthfully block candidates without a registered executable adapter.

## 13. Definition of Done

- Full suite passes from a non-Windows checkout without generating an `E:` tree.
- Every successful task has an execution binding, concrete executor result, verification result and causal receipt lineage.
- Context traversal is rejected and repeated reads can return bounded summary/reference payloads.
- Governor loop history is isolated per mission.
- Documentation reports exact reproduced checks and preserves unimplemented/blocked scope.
