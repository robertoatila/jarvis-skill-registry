# J.A.R.V.I.S. Remote Companion Host Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the home PC the always-on authoritative J.A.R.V.I.S. host and let a mobile companion securely attach from LAN or another network, resume durable sessions, converse with the same runtime and approve bounded actions without duplicating the cognitive stack.

**Architecture:** Introduce a transport-agnostic remote protocol and durable session journal first, then expose versioned HTTP routes, add a resident host lifecycle, make the existing HUD an installable mobile PWA, migrate shared-token access to paired-device identity, and finally add private-overlay/relay transports. Every remote command crosses the existing runtime/Governor/authorization boundaries; network reachability never becomes execution authority.

**Tech Stack:** Python 3.12 standard library; existing `http.server` host; vanilla HTML/CSS/JavaScript PWA; Node built-in test runner where applicable; PowerShell for Windows user autostart; systemd user units on Linux; LaunchAgent on macOS; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-15-jarvis-remote-companion-host-runtime-design.md`

## Global Constraints

- One authoritative J.A.R.V.I.S. runtime remains on the PC; never create a mobile-side planner, Governor, memory fabric, model router or tool router.
- Preserve local HUD behavior and current LAN `--remote` compatibility while the new protocol is introduced.
- Keep shipped Python runtime code standard-library-only.
- Do not make public WAN port-forwarding of `8899` the default architecture.
- Remote transport establishes reachability only; J.A.R.V.I.S. authorization remains authoritative.
- Session/event state must survive process restart and must reject unsupported future schemas.
- Duplicate `request_id` values must not duplicate mutable effects.
- Remote event payloads expose explicit state/receipts, not private chain-of-thought.
- Unknown or ambiguous execution outcomes remain explicit; never synthesize success.
- Mobile endpoints are bounded and cursor-based; never dump the full vault/repository state.
- `v0.1.0` remains immutable.

---

## File map

### New runtime modules

- `tooling/remote_protocol.py` — versioned JSON protocol validation and envelope construction.
- `tooling/remote_sessions.py` — durable session metadata, idempotency index and append-only event journal.
- `tooling/remote_runtime_bridge.py` — translation between remote protocol messages and the existing cognitive runtime.
- `tooling/remote_host.py` — host lifecycle/readiness state and service process contract.
- `tooling/remote_devices.py` — pairing challenges, device registry and revocation.
- `tooling/remote_transport.py` — transport capability/status abstraction for local/LAN/overlay/relay.
- `tooling/remote_service.py` — platform-neutral generation/dispatch for per-user autostart registration.

### Existing runtime files to extend

- `tooling/jarvis_server.py` — `/api/remote/v1` routes and static PWA assets.
- `tooling/http_security.py` — authenticated remote-device request guard after device pairing lands.
- `tooling/remote_auth.py` — compatibility token remains; later provides migration/pairing bootstrap only.
- `jarvis.py` — `service install|start|stop|status|uninstall` and remote-host CLI entry points.

### Mobile/PWA

- `ui/manifest.webmanifest` — install metadata.
- `ui/service-worker.js` — static shell cache only.
- `ui/remote-companion.js` — host/session/reconnect client.
- `ui/index.html` — manifest/service-worker registration and mobile remote shell hooks.
- `ui/jarvis.css` — focused mobile companion layouts using the existing design system.

### Platform integration

- `tooling/service/windows.py` — Scheduled Task command/config generation.
- `tooling/service/linux.py` — user systemd unit generation.
- `tooling/service/macos.py` — LaunchAgent plist generation.
- `tooling/service/__init__.py` — platform adapter selection.

### Tests

- `tests/test_agentic_remote_protocol.py`
- `tests/test_agentic_remote_sessions.py`
- `tests/test_agentic_remote_bridge.py`
- `tests/test_agentic_remote_host.py`
- `tests/test_agentic_remote_devices.py`
- `tests/test_agentic_remote_transport.py`
- `tests/test_agentic_remote_service.py`
- `tests/test_remote_companion.py` — compatibility coverage remains.
- `tests/test_remote_companion_session.cjs` — browser-side protocol/reconnect tests.

---

## Task 1 — Durable remote protocol and session core

**Files:**
- Create: `tooling/remote_protocol.py`
- Create: `tooling/remote_sessions.py`
- Create: `tests/test_agentic_remote_protocol.py`
- Create: `tests/test_agentic_remote_sessions.py`

**Interfaces:**
- Produces `PROTOCOL_VERSION = "jarvis-remote/1"`.
- Produces `RemoteProtocolError(ValueError)`.
- Produces `parse_client_envelope(value: object) -> dict`.
- Produces `RemoteSessionStore(state_dir: Path, clock: Callable[[], float] = time.time, id_factory: Callable[[], str] | None = None)`.
- Produces `create_session(device_id: str) -> dict`.
- Produces `get_session(session_id: str) -> dict | None`.
- Produces `append_event(session_id: str, kind: str, payload: dict, mission_id: str | None = None) -> dict`.
- Produces `events_after(session_id: str, after: int = 0, limit: int = 100) -> list[dict]`.
- Produces `ack(session_id: str, seq: int) -> dict`.
- Produces `remember_request(session_id: str, request_id: str, result: dict) -> tuple[dict, bool]`, where the boolean is `True` only for the first acceptance.

- [ ] **Step 1: Write RED protocol tests**

```python
import unittest
from tooling.remote_protocol import PROTOCOL_VERSION, RemoteProtocolError, parse_client_envelope

class TestRemoteProtocol(unittest.TestCase):
    def test_accepts_versioned_message(self):
        result = parse_client_envelope({
            "protocol": PROTOCOL_VERSION,
            "session_id": "session-1",
            "device_id": "phone-1",
            "request_id": "req-1",
            "kind": "message",
            "payload": {"text": "continue"},
        })
        self.assertEqual(result["kind"], "message")
        self.assertEqual(result["payload"]["text"], "continue")

    def test_rejects_unknown_protocol(self):
        with self.assertRaises(RemoteProtocolError):
            parse_client_envelope({
                "protocol": "jarvis-remote/999",
                "session_id": "session-1",
                "device_id": "phone-1",
                "request_id": "req-1",
                "kind": "message",
                "payload": {"text": "continue"},
            })
```

- [ ] **Step 2: Write RED durable-session tests**

```python
import tempfile
import unittest
from pathlib import Path
from tooling.remote_sessions import RemoteSessionStore

class TestRemoteSessionStore(unittest.TestCase):
    def test_event_cursor_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            ids = iter(["session-1"])
            store = RemoteSessionStore(Path(tmp), clock=lambda: 1000.0, id_factory=lambda: next(ids))
            session = store.create_session("phone-1")
            first = store.append_event(session["session_id"], "host_status", {"status": "ONLINE"})
            second = store.append_event(session["session_id"], "assistant_message", {"text": "ok"})
            self.assertEqual((first["seq"], second["seq"]), (1, 2))

            reopened = RemoteSessionStore(Path(tmp), clock=lambda: 1001.0)
            events = reopened.events_after("session-1", after=1)
            self.assertEqual([event["seq"] for event in events], [2])

    def test_duplicate_request_id_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RemoteSessionStore(Path(tmp), id_factory=lambda: "session-1")
            store.create_session("phone-1")
            first, created_first = store.remember_request("session-1", "req-1", {"event_seq": 1})
            second, created_second = store.remember_request("session-1", "req-1", {"event_seq": 999})
            self.assertTrue(created_first)
            self.assertFalse(created_second)
            self.assertEqual(second, first)
```

- [ ] **Step 3: Run RED tests**

Run:

```bash
python -m unittest discover -s tests -p "test_agentic_remote_protocol.py" -v
python -m unittest discover -s tests -p "test_agentic_remote_sessions.py" -v
```

Expected: FAIL because `tooling.remote_protocol` / `tooling.remote_sessions` do not exist.

- [ ] **Step 4: Implement minimal protocol validation**

Implementation requirements:

```python
PROTOCOL_VERSION = "jarvis-remote/1"
ALLOWED_CLIENT_KINDS = {"message", "resume_mission", "cancel_request", "approve_action", "ping"}
MAX_TEXT_CHARS = 32_768
```

Validate object type, exact protocol, non-empty string ids without CR/LF, allowed kind, object payload, and message text length. Return a normalized plain dict; do not introduce network behavior.

- [ ] **Step 5: Implement atomic durable sessions**

Persist metadata as `state_dir / "remote_sessions.json"` and events as `state_dir / "remote_events" / f"{session_id}.jsonl"`. Metadata writes use temp-file + `os.replace`. Reject schema versions other than `1`. `events_after` enforces `1 <= limit <= 500`. `ack` cannot move backwards or beyond the latest allocated event. `remember_request` persists the first result and returns it for duplicates.

- [ ] **Step 6: Run GREEN focused tests and portable battery**

```bash
python -m unittest discover -s tests -p "test_agentic_remote_protocol.py" -v
python -m unittest discover -s tests -p "test_agentic_remote_sessions.py" -v
python run_tests.py
python jarvis.py --doctor
python jarvis.py --test
```

- [ ] **Step 7: Commit**

```bash
git add tooling/remote_protocol.py tooling/remote_sessions.py tests/test_agentic_remote_protocol.py tests/test_agentic_remote_sessions.py
git commit -m "feat: add durable remote session protocol"
```

---

## Task 2 — Versioned remote HTTP API and runtime bridge

**Files:**
- Create: `tooling/remote_runtime_bridge.py`
- Create: `tests/test_agentic_remote_bridge.py`
- Modify: `tooling/jarvis_server.py`
- Extend: `tests/test_remote_companion.py`

**Interfaces:**
- Consumes `RemoteSessionStore` and protocol envelopes from Task 1.
- Produces `RemoteRuntimeBridge.handle(envelope: dict) -> dict`.
- Produces `/api/remote/v1/host`, `/sessions`, `/messages`, `/events`, `/ack`, `/close`.

- [ ] **Step 1: Write a RED bridge test proving the bridge delegates to one injected runtime callable and preserves `request_id`/`mission_id`.**
- [ ] **Step 2: Write RED HTTP tests using an in-process `HTTPServer` and temporary state directory; prove an authenticated session can be created, a message accepted, events replayed by cursor, and an unknown session returns 404.**
- [ ] **Step 3: Run focused tests and confirm failures are missing bridge/routes, not fixture errors.**
- [ ] **Step 4: Implement `RemoteRuntimeBridge` with an injected runtime adapter; do not create a planner/router/memory subsystem. Duplicate requests reuse the stored acceptance result.**
- [ ] **Step 5: Add bounded `/api/remote/v1` routes to `jarvis_server.py`. Existing `/api/chat` and local routes remain unchanged.**
- [ ] **Step 6: Run bridge, remote companion, full portable and launcher tests.**
- [ ] **Step 7: Commit `feat: bridge remote sessions into cognitive runtime`.**

HTTP contract examples to preserve in tests:

```json
POST /api/remote/v1/sessions
{"device_id":"phone-1"}

POST /api/remote/v1/sessions/session-1/messages
{"protocol":"jarvis-remote/1","session_id":"session-1","device_id":"phone-1","request_id":"req-1","kind":"message","payload":{"text":"continue"}}

GET /api/remote/v1/sessions/session-1/events?after=12&limit=100
```

---

## Task 3 — Resident host lifecycle and host status

**Files:**
- Create: `tooling/remote_host.py`
- Create: `tests/test_agentic_remote_host.py`
- Modify: `jarvis.py`

**Interfaces:**
- Produces `RemoteHostState` serialized with `schema_version=1`.
- Produces `RemoteHostController.start_foreground()`, `.status()`, `.write_state()`, `.clear_stale_state()`.
- Extends launcher with `python jarvis.py host --remote --no-browser` while retaining existing commands.

- [ ] **Step 1: RED tests for host state creation, stale PID rejection and clean shutdown state.**
- [ ] **Step 2: RED launcher tests proving legacy command construction is unchanged and host mode delegates to the existing server.**
- [ ] **Step 3: Implement minimal host state/readiness around the current server process rather than replacing the server.**
- [ ] **Step 4: Run focused + full tests.**
- [ ] **Step 5: Commit `feat: add resident remote host lifecycle`.**

---

## Task 4 — Cross-platform per-user autostart

**Files:**
- Create: `tooling/service/__init__.py`
- Create: `tooling/service/windows.py`
- Create: `tooling/service/linux.py`
- Create: `tooling/service/macos.py`
- Create: `tooling/remote_service.py`
- Create: `tests/test_agentic_remote_service.py`
- Modify: `jarvis.py`

**Interfaces:**
- Produces platform adapter operations `install`, `uninstall`, `status`, `start`, `stop`.
- Public CLI: `python jarvis.py service <operation>`.

- [ ] **Step 1: RED unit tests for generated Windows Scheduled Task command, Linux user unit and macOS LaunchAgent plist using paths containing spaces.**
- [ ] **Step 2: RED idempotency tests: repeated install generation is stable; uninstall of absent registration is a clean no-op result.**
- [ ] **Step 3: Implement Windows per-user logon registration, preferring `pythonw.exe` when present.**
- [ ] **Step 4: Implement Linux `systemd --user` and macOS LaunchAgent adapters.**
- [ ] **Step 5: Wire launcher commands and status output.**
- [ ] **Step 6: Run portable tests on all CI OSes; platform integration probes may skip only when the OS facility itself is absent.**
- [ ] **Step 7: Commit `feat: add per-user jarvis host autostart`.**

---

## Task 5 — Mobile Companion PWA and reconnect client

**Files:**
- Create: `ui/manifest.webmanifest`
- Create: `ui/service-worker.js`
- Create: `ui/remote-companion.js`
- Create: `tests/test_remote_companion_session.cjs`
- Modify: `ui/index.html`
- Modify: `ui/jarvis.css`

**Interfaces:**
- Produces browser `JarvisRemoteCompanion` with `connect`, `openSession`, `sendMessage`, `pollEvents`, `ack`, `close`.
- Persists only companion connection metadata needed for reconnect; never provider API keys or PC vault data.

- [ ] **Step 1: RED Node tests for event cursor advancement, reconnect from the last acknowledged sequence, duplicate event suppression and explicit offline state.**
- [ ] **Step 2: Implement the remote client against `/api/remote/v1`.**
- [ ] **Step 3: Add PWA manifest and static-shell-only service worker. API routes must not be served from stale cache as if live.**
- [ ] **Step 4: Add responsive host/status/chat/approval surfaces to the existing HUD without creating a second visual system.**
- [ ] **Step 5: Run Node tests plus existing chat-session tests and browser smoke when available.**
- [ ] **Step 6: Commit `feat: add installable mobile remote companion`.**

---

## Task 6 — Paired-device registry and token migration

**Files:**
- Create: `tooling/remote_devices.py`
- Create: `tests/test_agentic_remote_devices.py`
- Modify: `tooling/remote_auth.py`
- Modify: `tooling/http_security.py`
- Modify: `tooling/jarvis_server.py`

**Interfaces:**
- Produces single-use pairing challenges with explicit expiry.
- Produces device registry operations `pair`, `authenticate`, `list_devices`, `revoke`.
- Keeps the existing shared token only as compatibility/bootstrap while migration is active.

- [ ] **Step 1: RED tests for challenge expiry, single use, credential mismatch, device revocation and restart persistence.**
- [ ] **Step 2: Implement a durable schema-versioned registry storing credential fingerprints/derived authenticators rather than returning stored raw secrets from status APIs.**
- [ ] **Step 3: Add pairing routes and QR payload generation.**
- [ ] **Step 4: Extend request guard to accept paired-device authentication while preserving local/LAN compatibility tests.**
- [ ] **Step 5: Run focused, remote companion and full tests.**
- [ ] **Step 6: Commit `feat: add paired remote companion devices`.**

---

## Task 7 — Anywhere transport abstraction: overlay first

**Files:**
- Create: `tooling/remote_transport.py`
- Create: `tests/test_agentic_remote_transport.py`
- Modify: `tooling/remote_host.py`
- Modify: `tooling/remote_auth.py`
- Modify: `jarvis.py`

**Interfaces:**
- Produces transport status `none|local|lan|overlay|relay` with explicit reachability evidence.
- Produces configured companion URL without assuming the first detected LAN address is Internet-reachable.

- [ ] **Step 1: RED tests proving LAN address, configured overlay address and absent transport are distinguished.**
- [ ] **Step 2: Implement vendor-neutral overlay configuration (`JARVIS_REMOTE_HOSTNAME` / explicit CLI host) plus detection/reporting hooks; do not shell out to a vendor CLI to make runtime correctness depend on it.**
- [ ] **Step 3: Document Tailscale/Headscale as the first supported private-overlay deployment path because it gives the phone a private path to the PC without router port-forwarding.**
- [ ] **Step 4: Ensure request authorization still occurs inside J.A.R.V.I.S.; overlay membership alone never authorizes a session/action.**
- [ ] **Step 5: Run tests and commit `feat: support private overlay remote transport`.**

A future `relay` adapter may be added behind the same interface. It must use an outbound PC connection and preserve protocol/session semantics; it is not required for the first anywhere-capable release when overlay mode is proven.

---

## Task 8 — Remote approvals, receipts and mission continuity

**Files:**
- Modify: `tooling/remote_runtime_bridge.py`
- Integrate with existing `tooling/agentic/authorization.py` and receipt/runtime interfaces without duplicating them.
- Create/extend: `tests/test_agentic_remote_bridge.py`

- [ ] **Step 1: RED test: remote approval with wrong action/scope/budget binding is rejected.**
- [ ] **Step 2: RED test: phone disconnect leaves an accepted PC-side mission active/durable; reconnect replays later mission events.**
- [ ] **Step 3: RED test: ambiguous recovery result is surfaced as unknown/recovery-required rather than success.**
- [ ] **Step 4: Implement the minimal bridge adapters to existing authorization/receipt APIs.**
- [ ] **Step 5: Run full runtime/recovery tests.**
- [ ] **Step 6: Commit `feat: bind remote approvals to runtime authority`.**

---

## Task 9 — CI, operational diagnostics and documentation

**Files:**
- Modify relevant `.github/workflows/*` only where necessary to make remote protocol/service/PWA tests explicit.
- Update: `README.md`, `QUICKSTART.md`, relevant `docs/README.md` links.
- Create: `docs/remote-companion.md` operational guide.

- [ ] **Step 1: Add explicit CI steps for remote protocol/session tests and Node PWA client tests without weakening existing gates.**
- [ ] **Step 2: Add `python jarvis.py service status` and remote transport diagnostics to documented troubleshooting.**
- [ ] **Step 3: Document Windows home-PC setup and private-overlay phone access end to end.**
- [ ] **Step 4: Document Linux/macOS equivalents and the explicit offline behavior.**
- [ ] **Step 5: Run repository gates:**

```bash
python run_tests.py
python jarvis.py --doctor
python jarvis.py --test
python benchmarks/context_budget_benchmark.py
python tooling/audit_pre_publish_security.py
node --test tests/test_chat_session.cjs
node --test tests/test_remote_companion_session.cjs
```

- [ ] **Step 6: Commit `docs: publish remote companion operations and evidence`.**

---

## Task 10 — PR evidence and completion gate

- [ ] Rebase/merge current green `main` into the branch only if `main` advanced; rerun every relevant gate afterward.
- [ ] Confirm the branch did not move `v0.1.0`.
- [ ] Open/maintain a draft PR throughout implementation with exact-head evidence.
- [ ] Require Windows, Ubuntu and macOS portable jobs green.
- [ ] Record focused remote protocol/session/service/PWA test counts and exact commit SHA.
- [ ] Verify the user flow on the final candidate: background host online -> phone session -> message executed on PC -> disconnect -> reconnect by cursor -> continued session.
- [ ] Mark PR ready only after all mandatory evidence is green.
- [ ] Merge using the exact expected head SHA.
- [ ] Revalidate post-merge `main` before declaring the feature complete.

## Phase boundaries

The work can land incrementally if each PR is independently coherent:

```text
A. protocol + durable sessions
B. remote API + runtime bridge
C. resident service/autostart
D. mobile PWA + reconnect
E. paired devices
F. private overlay anywhere transport
G. approvals/receipts + CI/docs
```

If this branch grows too large before review, cut at these boundaries rather than shipping an unreviewable mega-PR.

## Agent execution prompt

Use the following as the canonical continuation prompt for an implementation agent:

```text
You are implementing J.A.R.V.I.S. Remote Companion Host Runtime in
robertoatila/jarvis-skill-registry.

Read first:
- docs/superpowers/specs/2026-09-15-jarvis-remote-companion-host-runtime-design.md
- docs/superpowers/plans/2026-09-15-jarvis-remote-companion-host-runtime.md

Invariant: the home PC remains the single authoritative J.A.R.V.I.S. runtime.
The phone is a thin client. Never create a second planner, Governor, memory,
model router, tool router or authorization plane.

Start from a green exact branch head. Follow the plan in order. For every
behavior change use strict RED -> verify RED -> minimal GREEN -> verify GREEN
TDD. Preserve local HUD behavior and current LAN remote compatibility. Do not
make public WAN port-forwarding the normal architecture. Keep shipped Python
runtime code standard-library-only. Keep v0.1.0 immutable.

For remote requests, preserve request/session/mission correlation, durable
cursor replay, idempotency and existing runtime authorization/verification
semantics. Unknown outcomes stay unknown; never fabricate success.

After each coherent task, run focused tests plus the portable battery and make
a focused commit. Keep the PR draft until exact-head CI is green on required
platforms. Before merge, re-check current main, integrate if needed, rerun gates,
and merge only with an expected-head guard.
```

## Completion definition

The initiative is complete when a phone on another network can connect through an approved private transport to the background J.A.R.V.I.S. host on the home PC, authenticate as a paired device, create/resume a durable session, send a command that is executed by the existing PC-side runtime, observe truthful correlated events/receipts, disconnect without killing the mission, and reconnect from its last acknowledged event cursor — with local behavior, portable gates and immutable v0.1.0 preserved.