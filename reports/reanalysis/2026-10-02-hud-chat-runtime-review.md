# J.A.R.V.I.S. HUD and chat runtime review — 2026-10-02

## Scope and evidence boundary

This review covers the public `robertoatila/jarvis-skill-registry` repository on branch `improve/repository-health-20261001`, based on `main@a9bd767f9c08aaad0d738d9aca49239db68234ec`. It follows the reported state where the HUD obscured the chat and voice controls, provider setup was not trustworthy, and UI/API catalog data could imply facts that were not present in the source.

The review and tests ran in a clean audit checkout. They do not inspect or overwrite the live Obsidian Vault checkout, its unsynced files, or private credentials. Browser tests use deterministic local fixtures. No live provider, microphone, TTS service, deployment, or installed Obsidian session was used, so this report does not certify those paths. This is a source/runtime review, not a claim that every repository owned by the account was audited.

## Confirmed issues and changes

1. **The cockpit obscured the assistant surface.** The Mark-LIV cockpit is now mounted inside the operations tab, leaving the chat tab a usable full-height conversation surface. The microphone control is placed beside the message composer and reuses the existing voice profile. Dictation inserts editable text and does not send it automatically.
2. **Provider-key setup could report false success and persisted the key in browser storage.** The HUD removes any legacy `jarvis_ai_key`, validates the selected provider and recognized key prefix, waits for the server to confirm the exact provider, and clears the input only after success. Chat sends an explicit provider/model and the session access grant; the server resolves the selected provider's saved key from its local ignored configuration. Provider error text is rendered as text.
3. **Missing skill metadata looked verified.** The server now leaves absent descriptions and capabilities empty, versions unset, and security state `UNKNOWN` unless the repository policy explicitly flags a record. It includes metadata provenance and does not follow symlinked skill directories or files.
4. **Skill detail paths were not confined to direct skill files.** A dedicated resolver accepts only a direct, valid child of `skills/` and a regular `SKILL.md`, rejecting traversal and symlinks.
5. **Catalog counts and historical integrity data could be overstated.** The 100k+ endpoint validates catalog shape, tolerates malformed topics, bounds result limits, reports matched and returned totals separately, and counts the actually loaded index rather than trusting the declared total. Historical Merkle digests are kept as snapshots and never called current until this runtime recomputes them.
6. **Browser teardown could be logged as a server failure.** Expected broken-pipe/reset cases during JSON or static-file responses now end quietly rather than causing a second response attempt.
7. **Isolated validation could read more of a developer checkout than necessary.** Its disposable fixture now copies only tracked, allowlisted public files, excludes symlinks and paths resolving outside the checkout, constructs a coherent synthetic skill registry, and denies external network access to the test process.
8. **Cached interface resources were incomplete.** The service-worker shell cache is versioned to v10 and includes the experience design-system scripts and styles used by the interface.

## Validation

- `python jarvis.py --full-test`: **PASS — 656 tests, 656 passed, 0 failed, 0 errored** (71.179 seconds).
- `python -m unittest tests.test_mark_liv_cockpit_contract -v`: **PASS — 47 tests**.
- Playwright browser suite: **PASS — 5/5 scenarios**, including chat visibility, editable dictation, key-provider mismatch/success, honest unavailable-catalog state, and reload behavior.
- Node chat-session suite: **PASS — 7/7 tests**.
- `npm audit --audit-level=high`: **0 vulnerabilities**.
- `python tooling/audit_pre_publish_security.py`: **PASS** — 1,852 eligible files / 121,157,492 bytes scanned, no configured credential pattern found, and `config/api_keys.json` is ignored. This scanner explicitly does not prove the repository is globally secret-free or recompute the Merkle anchor.
- `git diff --check`: **PASS**. Git reports only the repository's existing LF-to-CRLF working-copy normalization notices.
- Earlier branch checks also reported `python jarvis.py --doctor` and `python jarvis.py --test` as passing; neither is a test of a live provider or machine voice device.

## Preserved content and remaining limits

The existing Obsidian graph animation video and poster remain tracked at `docs/assets/cognitive-vault-graph-animation.mp4` and `docs/assets/cognitive-vault-graph-animation-poster.png`; the demo video remains at `docs/assets/jarvis-demo-90s.mp4`. This change does not regenerate or alter those assets.

The local user Vault is intentionally not copied into this branch: its unreviewed dirty and untracked content is not part of this public-source candidate. The candidate therefore does not claim local/remote Vault synchronization. The live provider, browser speech support, microphone permissions, TTS output, and Graph View playback still require direct acceptance in the user's installed environment. The branch must also pass the exact-head remote checks and mergeability review before a merge can be claimed.
