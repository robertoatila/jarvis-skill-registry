# Server chat inference boundary

Date: 2026-09-13. Extends the existing server transport and adapters/inference.py; no new orchestrator.

Current evidence note (2026-09-18): a pinned Playwright/Chromium HUD smoke harness now exists and exercises the actual local server fixture, but fresh browser execution evidence is still required before the browser gate can be marked PASS. The 2026-09-13 test counts below remain dated historical evidence, not the current whole-repository count.

## Implemented behavior and authorization

POST /api/chat retains message/provider/model/apiKey inputs and reply/provider/model/niche/target/live_search/timestamp outputs. Added fields: status, usage and metadata trace. Empty messages retain the greeting; invalid input types return HTTP 400. Valid blocked requests return JSON with status=BLOCKED and an explicit reason.

Cloud requires all of these conditions:

1. Server environment JARVIS_CHAT_ALLOW_CLOUD is exactly 1.
2. JARVIS_CHAT_TOKEN is configured and matches the request Authorization: Bearer header.
3. The explicitly selected provider occurs in JARVIS_CHAT_PROVIDERS, a server-owned comma-separated allowlist.
4. An explicit model and its provider credential are available.

Credentials are resolved only after authorization and only for the selected provider. API-key prefixes do not authenticate the chat caller. No automatic provider/model fallback, live search, global private-memory injection or chat-message memorization occurs in this route.

## Compatibility and client migration

This deliberately tightens previously unauthenticated cloud access. JSON field names remain compatible, but provider=auto/heuristic and missing model no longer select cloud implicitly. The HUD now accepts an operator-provided access token, distinct from the provider API key. It retains this grant only in a JavaScript closure and clears the input immediately after loading it. Remove-token and pagehide revoke the local grant for future requests; they do not cancel in-flight requests or revoke the server token. Reload requires re-entry. Only the fixed /api/chat request receives the Authorization header, with redirects refused. No access token is persisted in browser storage. Existing provider-key storage and other endpoints have not been migrated. Provider and model selection are explicit; missing grants/configuration fail closed. Replies display BLOCKED or UNVERIFIED as text, including provider content as text rather than HTML. Other server endpoints remain outside this change.

Operator configuration (never commit actual tokens):

```text
JARVIS_CHAT_ALLOW_CLOUD=1
JARVIS_CHAT_PROVIDERS=openai,groq,gemini,openrouter
JARVIS_CHAT_TOKEN=<operator-managed access token>
```

Allow only providers required for the deployment. Unset flags/grants fail closed; stored provider credentials do not enable cloud. Configure provider credentials through the existing mechanism or submit apiKey on an authenticated request. Endpoint formats are in config/chat-providers.json. No provider model availability is guessed or certified. Deployment transport/access control for other endpoints remains a separate concern.

## Adapter and failure semantics

HttpInferenceAdapter implements the existing immutable InferenceRequest -> InferenceResult callable boundary. It can also be registered with InferenceBackends and a deployment-owned model manifest. Server chat uses explicit single-provider binding rather than inventing model quality/cost estimates for scoring.

Before HTTP, the adapter again rejects local_only, network denial and missing explicit allowed_models membership. Redirects are denied to prevent forwarding credentials to another destination. Gemini keys are headers rather than URL query parameters. Each invocation makes one HTTP request with a 20-second socket timeout and a 1 MiB bounded read. Socket timeout is not a proven total deadline against slow streaming; full deadline/cancellation semantics remain open.

HTTP 401/403 -> AUTHORIZATION; 429/5xx -> TRANSIENT; timeout -> TIMEOUT with outcome unknown; connection error -> EXTERNAL_SERVICE; invalid/oversized output -> MALFORMED_RESULT. There are no retries in the adapter/chat route. Provider exception payloads and keys are omitted from returned diagnostics.

## Evidence and usage

A schema-valid provider reply is UNVERIFIED, not a verified mission result. Confidence remains unknown and evidence_refs empty. Chat therefore does not fabricate evidence to pass execute_inference's stricter independent verification gate; no memory/learning promotion occurs.

Provider-reported prompt/completion tokens are preserved when available; missing counts remain null. Registered runtime invocation carries these counts into existing attempts and trace metadata. Cache hits record zero newly invoked model tokens rather than charging historical cached usage again. Actual monetary cost remains unknown.

## Checks and limits

- Eleven tests in tests/test_agentic_http_inference.py cover policy denial before network/credentials, explicit model/key binding, bounded reads, optional usage, Gemini headers, redirect refusal, error classification, no retries/fallback and POST authorization before dispatcher/memory work.
- One additional software-upgrade test covers token usage -> attempt and cache-hit accounting.
- python -B run_tests.py: 283 passed across 42 suites, no failures/errors.
- Python compilation, JavaScript syntax and git diff --check passed.
- HTTP is mocked. Handler tests compile the actual server class with isolated globals: importing the full legacy module otherwise synchronizes a user Vault as a side effect. The initially generated Vault diff was restored; tests no longer trigger it. Full server startup, live providers and browser authentication were not validated.

HUD continuation: six Node tests cover client denial, grant isolation, fixed destination/header, no retry, response classification and the actual control handlers with a minimal DOM harness. Browser rendering and live provider authorization remain unvalidated. Run `node --test tests/test_chat_session.cjs`; the eleven mocked HTTP tests were also rerun successfully. Residual gates include full deadlines, provider-specific model compatibility, legacy server startup side effects and authorization of other HTTP endpoints. This is not whole-server security certification.
