# Repository and all-branch review — 2026-09-21

## Scope and evidence boundary

Inventory of all 70 remote branches present at the initial fetch, 1,826 tracked paths on main, ancestry/differences and non-mutating merge simulations for every divergent branch. Python AST parsing covered 427 distinct blobs across those branches. Focused source review covered durable migrations, context confinement, artifacts, recovery, remote command/task execution, authorization, device pairing, evidence manifests and historical deployment configurations. This is a repository-wide engineering review, not a claim that every line or platform was exhaustively verified.

Main snapshot: `9d1102a257a84a78fda9c30374b545e19bd9557f`. The subsequently created `fix/preserve-migration-provenance` branch is PR #68 (`b901e6b5f33f71716bf9d5e4de563ec7a0b9871c`); its code tree matches locally tested commit `4693da8628c4c0ce09e420e84e71466d5474bcc1`. It increases the remote branch count to 71. This report does not assert current state beyond these snapshots.

No GitHub Actions results were used. No branches were deleted or merged. Merge simulations do not prove runtime compatibility. Divergent commit counts alone do not mean code is missing from main, especially after squash merges.

## Confirmed findings

1. **P1 — PR #53 inline-code filter accepts equivalent interpreter forms.** In `tooling/remote_commands.py`, `normalize_command_payload` compares whole arguments against `-c` / `--eval`. It accepts `python -cprint(23)`, `python -Icprint(23)` and `node --eval=console.log(23)`. Both Python forms were independently executed locally and printed 23. The normalization acceptance was demonstrated for Node; Node execution was not needed. Explicit device/session/digest approval is still required: this finding does not demonstrate unauthenticated execution. Fix argument parsing and add negatives before physical acceptance. The autonomous planner reuses this normalizer, so its admission path also needs coverage.
2. **P2 — output cap is applied after unbounded capture in PR #53.** `_execute` uses `subprocess.run(stdout=PIPE, stderr=PIPE)` and only slices to `MAX_OUTPUT_CHARS` after completion. The cap bounds the returned receipt, not peak memory used while collecting output. This is a source-level resource finding; no OOM/load test was performed. Use bounded streaming or a quota-controlled spool and explicit truncation/termination policy.
3. **P2 — migration provenance discarded on durable reload.** Reproduced on main for Artifact, ExecutionAttempt and Mission. Fixed by PR #68, with a model round-trip regression and disk save/reload coverage. No identity synthesis or authority changes introduced.
4. **P2 — active branches lag current fixes.** PR #53 at `b482fd6c048a32a3cbc7290d87457b421db2c1e9` and PR #56 at `50009c9d256bb2abeee48a7c99216405e3b5c594` are each six commits behind main. Both merge simulations are clean. Their current snapshots lack later context/artifact/recovery changes on main; passing their own older tests does not validate the combined tree. Reconcile and rerun before advancing acceptance.
5. **Historical deployment branches must not be promoted wholesale.** `validation/v020-plan4-linux-68ce4d0` and `validation/v020-plan4-linux2-68ce4d0` contain build commands that check out candidate `68ce4d055d913f0f95a91b920c5f5454c0fd15f6`; one also introduces a root Vercel configuration. These are experiment snapshots, not current deployment configuration.
6. **Release evidence remains incomplete.** `evidence/current.json` explicitly requires direct Windows/Linux/macOS portable runtime, Windows legacy governance and Chromium browser validation. Local unit/Node/integration results below do not close these gates or certify protocol Intermediário. Existing PR descriptions referring to Actions PASS must not be treated as current evidence.

## Direct validation

| Snapshot | Check | Result |
| --- | --- | --- |
| main 9d1102a | `python jarvis.py --full-test` | 99 suites, 623 PASS (previous turn, same checkout) |
| fix 4693da8 / identical published code tree b901e6b | `python jarvis.py --full-test` | 99 suites, 624 PASS |
| fix 4693da8 | `python -m unittest discover -s tests -p 'test*.py'` | 716 PASS |
| fix 4693da8 | Node chat-session / runtime-observability / operational-cockpit | 21 PASS |
| fix 4693da8 | Plan 4 integration gate | 4 commands PASS |
| fix 4693da8 | doctor, Python preflight, documentation claim audit | PASS; 0 governed-document violations |
| fix 4693da8 | context budget benchmark | PASS; 4,140 → 2,197 serialized UTF-8 bytes; limit 2,200 |
| PR #53 b482fd6 | `python jarvis.py --full-test` | 104 suites, 678 PASS |
| PR #53 b482fd6 | `node tests/remote_companion_node_test.js` | PASS |
| PR #56 50009c9 | `python jarvis.py --full-test` | 97 suites, 615 PASS |
| all 70 initial branch tips | Python AST, 427 unique blobs | Only intentional broken-syntax fixture fails |

The syntax exception is `staging/orchestration/broken-syntax-tool/implementation.py`, created/exercised by `tests/test_agentic_swe.py::test_syntax_error_failure`. It is a negative fixture, not a production syntax regression. No browser session, live provider, physical Windows/macOS, PowerShell governance or production deployment was exercised in this review. Master discovery includes `test_agentic_*.py`; the broader unittest run covers additional test modules, explaining the higher count.

## Branch disposition

40 branches are ancestors of main; 11 divergent branches merge to exactly the current main tree; 13 produce merge conflicts; 5 add changes with a clean merge simulation; main is the remaining branch. Backups and release/tag references are preserved. A clean merge is not authorization to merge.

| Branch | SHA | Behind | Ahead | Review disposition |
| --- | --- | ---: | ---: | --- |
| `backup/pr53-pre-clean-stack-e2fd9be` | `e2fd9be994b9` | 14 | 129 | Conflicts; preserve / review selectively |
| `backup/security-55-pre-mark-liv-sync-ec993ed` | `ec993ede76ca` | 14 | 28 | Conflicts; preserve / review selectively |
| `benchmark/3-repository-context-admission` | `edb2b2fcf49f` | 144 | 0 | Ancestor; no pending commits |
| `candidate/v0.2.0-plan4-d2ce802e` | `d2ce802eb878` | 22 | 0 | Ancestor; no pending commits |
| `docs/6-first-skill-walkthrough` | `378f1f173ace` | 139 | 0 | Ancestor; no pending commits |
| `docs/mark-liv-post-merge-closure` | `ccb96ed4c781` | 1 | 0 | Ancestor; no pending commits |
| `docs/obsidian-remote-second-brain-master-prompt` | `51bd29fb5e67` | 151 | 0 | Ancestor; no pending commits |
| `docs/v020-plan4-partial-linux-evidence` | `4bb815e4a6fc` | 16 | 2 | Additional changes; clean simulation only |
| `feat/5-reproducible-demo-capture` | `4c172881f72d` | 118 | 0 | Ancestor; no pending commits |
| `feat/mark-liv-holomat-cockpit` | `5e6e26c22376` | 14 | 165 | Conflicts; preserve / review selectively |
| `feat/remote-companion-host-runtime` | `985455439912` | 247 | 0 | Ancestor; no pending commits |
| `feat/remote-pc-command-runtime` | `b482fd6c048a` | 6 | 141 | Additional changes; clean simulation only |
| `fix/artifact-seal-integrity` | `90101a2c3303` | 4 | 3 | Already represented; merge adds no files/content |
| `fix/context-protected-path-boundary` | `2b600853b9fb` | 5 | 2 | Already represented; merge adds no files/content |
| `fix/n8n-signed-replay-safe-webhooks` | `11aa4f84544b` | 3 | 2 | Already represented; merge adds no files/content |
| `fix/recovery-attempt-lineage` | `976a8d3a0c2b` | 7 | 2 | Conflicts; preserve / review selectively |
| `fix/recovery-resume-lineage` | `c8b42a2d1dfd` | 6 | 5 | Already represented; merge adds no files/content |
| `fix/resume-token-accounting` | `32cec2a38b3d` | 10 | 3 | Already represented; merge adds no files/content |
| `fix/unknown-risk-fail-closed` | `9445988440ad` | 13 | 8 | Already represented; merge adds no files/content |
| `fix/unknown-side-effect-fail-closed` | `2d57895d0e4b` | 12 | 3 | Already represented; merge adds no files/content |
| `fix/v020-deterministic-js-mime` | `a413d79a54a6` | 35 | 0 | Ancestor; no pending commits |
| `fix/v020-gate-commit-binding` | `487f5ce704b4` | 29 | 0 | Ancestor; no pending commits |
| `fix/v020-quickstart-git-sha-authority` | `07862d0df205` | 17 | 0 | Ancestor; no pending commits |
| `fix/v020-recovery-script-import` | `10df10bce104` | 32 | 0 | Ancestor; no pending commits |
| `fix/v020-remote-companion-static-routes` | `10bafa7aeb74` | 23 | 0 | Ancestor; no pending commits |
| `fix/v020-windows-legacy-gate-sandbox` | `dd0656634ee4` | 20 | 0 | Ancestor; no pending commits |
| `growth/jarvis-experience-system-v2` | `f51841d498b4` | 351 | 26 | Conflicts; preserve / review selectively |
| `growth/jarvis-experience-system-v2-red` | `07be4dd4ad22` | 351 | 0 | Ancestor; no pending commits |
| `growth/jarvis-experience-system-v2-tests` | `07be4dd4ad22` | 351 | 0 | Ancestor; no pending commits |
| `growth/launch-100-stars` | `dc40baeb227b` | 363 | 13 | Conflicts; preserve / review selectively |
| `growth/live-site-discovery` | `3ed5351b56b4` | 353 | 7 | Conflicts; preserve / review selectively |
| `growth/max-reach-launch` | `1ac72e57d8b8` | 354 | 7 | Conflicts; preserve / review selectively |
| `main` | `9d1102a257a8` | 0 | 0 | Baseline |
| `planning/jarvis-v0.2.0-optimization` | `d0d3d6b96dc9` | 350 | 7 | Conflicts; preserve / review selectively |
| `release/v0.1.0` | `93d45149ecf4` | 362 | 9 | Conflicts; preserve / review selectively |
| `release/v0.1.0-dispatch-fix` | `3887c6a64cc9` | 361 | 4 | Conflicts; preserve / review selectively |
| `release/v0.1.0-evidence-repair` | `055c59e3cfca` | 359 | 4 | Already represented; merge adds no files/content |
| `release/v0.1.0-refspec-fix` | `35c9c183ca4c` | 360 | 2 | Already represented; merge adds no files/content |
| `release/v0.2-plan2-task4-validation` | `996602c938e3` | 297 | 0 | Ancestor; no pending commits |
| `repair/merge-6755bfa` | `8204a11a35ff` | 343 | 0 | Ancestor; no pending commits |
| `security/55-protocol-v13-2-intermediate` | `50009c9d256b` | 6 | 41 | Additional changes; clean simulation only |
| `security/approval-grant-attenuation` | `d0dfbe824938` | 8 | 3 | Already represented; merge adds no files/content |
| `security/federation-fail-closed-trust` | `2061b3a8b29c` | 11 | 3 | Already represented; merge adds no files/content |
| `test/2-portable-quickstart-verification` | `ddc6bfa982e8` | 128 | 0 | Ancestor; no pending commits |
| `test/4-deterministic-inference-transport` | `d30105be8542` | 148 | 0 | Ancestor; no pending commits |
| `v0.2/browser-hud-smoke` | `63aebf76e0b3` | 55 | 0 | Ancestor; no pending commits |
| `v0.2/cockpit-accessibility-theme-contracts` | `8020a27357ab` | 77 | 0 | Ancestor; no pending commits |
| `v0.2/deterministic-provider-fixture` | `aeb7a69cec6b` | 68 | 0 | Ancestor; no pending commits |
| `v0.2/direct-evidence-gates` | `596e90712744` | 52 | 0 | Ancestor; no pending commits |
| `v0.2/documentation-consolidation` | `e063a99130f8` | 45 | 0 | Ancestor; no pending commits |
| `v0.2/evidence-manifest-claim-audit` | `bceaa86c8740` | 47 | 0 | Ancestor; no pending commits |
| `v0.2/governor-context-memory-routing` | `ea75d2a814b4` | 265 | 0 | Ancestor; no pending commits |
| `v0.2/hud-runtime-integration-fixture` | `c7d72546aaf0` | 75 | 0 | Ancestor; no pending commits |
| `v0.2/mission-timeline-projection` | `c7072601aa13` | 109 | 0 | Ancestor; no pending commits |
| `v0.2/observability-receipt-ledger` | `b2ebddd20bbf` | 113 | 0 | Ancestor; no pending commits |
| `v0.2/operational-cockpit-ui` | `d565a294c2ed` | 85 | 0 | Ancestor; no pending commits |
| `v0.2/plan3-direct-validation-gate` | `446232d02fe2` | 71 | 0 | Ancestor; no pending commits |
| `v0.2/plan4-execution-status` | `ecaca867a6ce` | 42 | 0 | Ancestor; no pending commits |
| `v0.2/plan4-runner-blockers` | `e0c9aa35a9c4` | 40 | 0 | Ancestor; no pending commits |
| `v0.2/plan5-direct-release-plan` | `60a758668617` | 37 | 0 | Ancestor; no pending commits |
| `v0.2/repository-context-benchmark` | `dcef1fc77e6d` | 63 | 0 | Ancestor; no pending commits |
| `v0.2/restart-recovery-gate` | `c23361d275ff` | 65 | 0 | Ancestor; no pending commits |
| `v0.2/runtime-observability-api` | `8917504d598b` | 105 | 0 | Ancestor; no pending commits |
| `v0.2/runtime-observability-client` | `e9e690bcff5d` | 101 | 0 | Ancestor; no pending commits |
| `v0.2/server-observability-api` | `b856b41cf3cd` | 108 | 2 | Conflicts; preserve / review selectively |
| `v0.2/trusted-runtime-receipts` | `4831a73e5c94` | 349 | 41 | Conflicts; preserve / review selectively |
| `validation/v020-plan4-browser-28f3785c` | `28f3785c24d1` | 28 | 0 | Ancestor; no pending commits |
| `validation/v020-plan4-browser-28f3785c-r2` | `28f3785c24d1` | 28 | 0 | Ancestor; no pending commits |
| `validation/v020-plan4-linux-68ce4d0` | `fdca2dbbae6e` | 41 | 2 | Additional changes; clean simulation only |
| `validation/v020-plan4-linux2-68ce4d0` | `9f6cf3a4643a` | 41 | 2 | Additional changes; clean simulation only |

## Recommended order

1. Review and merge the narrowly scoped provenance fix after normal review.
2. Correct PR #53 interpreter argument admission and bound subprocess output collection; preserve exact digest approvals.
3. Reconcile #53/#56 with main and repeat direct tests on the resulting commits.
4. Complete Windows physical pairing/approval/execution/reconnect/revocation and the remaining platform/release gates.
5. Separately review branch cleanup: ancestry/tree equivalence identifies candidates, not permission to delete backups or release history.

Machine-readable branch details and full SHAs are in `2026-09-21-all-branches.json`. Test log hashes are in `2026-09-21-review-evidence.json`. Historical evidence is never promoted to a newer commit merely because tests passed on an older branch.
