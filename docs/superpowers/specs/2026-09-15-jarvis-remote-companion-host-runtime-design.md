# J.A.R.V.I.S. Remote Companion Host Runtime — Design

**Status:** Approved for implementation by repository owner on 2026-09-15.

**Base:** `main` at `b034111bafc8c0b37f83c5f8ac60d763d5c3172b`.

## Intent

The mobile device is not a second J.A.R.V.I.S. runtime. The authoritative J.A.R.V.I.S. instance remains on the user's home PC, where the Cognitive Runtime, Governor, memory, context, skills, repositories, files, credentials, adapters and local integrations already exist. The mobile device is a thin remote companion that can attach to that runtime, converse with it, inspect state, approve bounded actions and reconnect to long-running missions.

Target user flow:

```text
PC powers on
  -> J.A.R.V.I.S. host starts in background
  -> runtime restores durable state and becomes ONLINE
  -> remote transport becomes reachable

phone anywhere
  -> opens J.A.R.V.I.S. Companion
  -> authenticates as a paired device
  -> sees HOME-PC / ONLINE
  -> sends a message or command
  -> command executes on the home PC runtime
  -> events/results stream back to the phone
  -> phone can disconnect/reconnect without destroying the PC-side mission
```

## Goals

1. Keep one authoritative cognitive runtime on the PC.
2. Start the host automatically with the user session/system without requiring a terminal or browser.
3. Allow a paired mobile client to reach the host from LAN and, through a private remote transport, from another network.
4. Persist remote sessions and event cursors so intermittent mobile connectivity does not erase mission state.
5. Reuse the existing runtime, Governor, routing, memory, receipts and authorization boundaries rather than creating a parallel agent stack.
6. Preserve the existing local HUD and current LAN companion behavior while introducing versioned remote-session APIs.
7. Keep shipped runtime code Python standard-library-only unless a later plan explicitly changes that release constraint.
8. Make the mobile experience installable as a PWA before introducing a native Expo/React Native client.
9. Avoid direct public exposure of the J.A.R.V.I.S. HTTP port as the default remote-access architecture.
10. Keep observable remote state limited to explicit receipts/events; no private chain-of-thought is required or exposed.

## Non-goals

- Running a second autonomous J.A.R.V.I.S. brain on the phone.
- Mirroring the full Cognitive Vault, repository checkout or provider credentials onto the phone.
- Replacing the existing agentic runtime, planner, Governor, memory fabric, model router or tool router.
- Making WAN port-forwarding of `8899` the recommended deployment model.
- Building a native mobile app before the remote protocol and PWA behavior are stable.
- Inventing cloud execution when the PC is offline. If the PC is offline, the companion reports the host as offline.

## Existing foundation

The repository already has useful primitives:

- `jarvis.py --remote` delegates to `tooling/jarvis_server.py`.
- `tooling/jarvis_server.py --remote` can bind beyond loopback.
- `tooling/remote_auth.py` creates and persists a companion token and can build a LAN URL.
- `tooling/http_security.py` allows loopback or authenticated private-network requests and intentionally rejects public source addresses.
- `tests/test_remote_companion.py` covers QR generation, token validation, private-LAN access and public-IP rejection.
- `ui/chat-session.js` already models a page-lifetime authorization grant for `/api/chat`.

These components become compatibility inputs, not dead code.

## Architectural principles

### One brain, multiple clients

All mobile requests terminate in the same PC-side runtime used by the desktop HUD. A remote request may create or resume a mission, but it must not create a second planner, memory system or independent authority plane.

### Transport is not authority

Network reachability and runtime authorization are different concerns. Tailscale/Headscale, a future relay, LAN Wi-Fi or another private transport only establishes a path to the host. J.A.R.V.I.S. still authenticates the device/session and applies its own action authorization and Governor rules.

### No public port by default

The host remains loopback-only unless remote mode is explicitly enabled. Remote-anywhere support must prefer a private overlay or outbound relay architecture. Router port-forwarding is documented only as unsupported/high-risk compatibility behavior, not as the normal path.

### Durable session, ephemeral connection

A browser tab or cellular socket may disappear at any time. The durable object is the PC-side remote session and its event journal. Connections are replaceable attachments to that session.

### Reconnect by cursor

Every user-visible remote event has a monotonically increasing `seq`. A client reconnects with `after=<last_seq>` and receives only missing events. Event sequence belongs to one session and is deterministic under restart.

### Explicit device identity

The current bearer token remains a migration/compatibility mechanism. The target model is a paired device registry with an opaque device id and a secret/key fingerprint stored on the PC. Raw long-lived device secrets are never returned by status endpoints.

## Component model

### 1. `RemoteSessionStore`

New module: `tooling/remote_sessions.py`.

Responsibilities:

- Create and reopen durable sessions.
- Persist session metadata atomically under `state/remote_sessions.json`.
- Append bounded, serializable events under `state/remote_events/<session_id>.jsonl`.
- Allocate monotonically increasing event sequence numbers.
- Track `device_id`, `created_at`, `last_seen_at`, `status`, optional `mission_id`, and last acknowledged client sequence.
- Reject unsupported future schema versions.
- Reconstruct state after process restart without relying on in-memory objects.

Session states:

```text
OPEN -> DETACHED -> OPEN
OPEN -> CLOSED
DETACHED -> CLOSED
CLOSED is terminal
```

Connection loss moves only the attachment to detached; it does not silently cancel a running mission.

### 2. `RemoteProtocol`

New module: `tooling/remote_protocol.py`.

Defines versioned JSON envelopes independent of HTTP:

```json
{
  "protocol": "jarvis-remote/1",
  "session_id": "...",
  "device_id": "...",
  "request_id": "...",
  "kind": "message",
  "payload": {"text": "continue the TCC-DS mission"}
}
```

Server events use:

```json
{
  "protocol": "jarvis-remote/1",
  "session_id": "...",
  "seq": 42,
  "kind": "assistant_message",
  "mission_id": "...",
  "payload": {"text": "..."},
  "created_at": 1789510000.0
}
```

Protocol parsing validates types and maximum payload sizes before the request reaches runtime code.

### 3. `RemoteRuntimeBridge`

New module: `tooling/remote_runtime_bridge.py`.

This is the only remote-specific layer allowed to talk to the existing cognitive runtime. It translates remote protocol messages into existing mission/runtime inputs, preserves correlation ids and emits explicit receipt/status events back into the remote session journal.

It does not implement its own planner, routing or memory.

Initial message kinds:

- `message`
- `resume_mission`
- `cancel_request`
- `approve_action`
- `ping`

Initial server event kinds:

- `host_status`
- `session_opened`
- `user_message_accepted`
- `mission_status`
- `assistant_message`
- `approval_required`
- `action_receipt`
- `error`

### 4. `RemoteHostService`

New module: `tooling/remote_host.py` plus platform registration scripts.

The host owns process lifecycle, readiness and state publication. The HTTP server remains a child/embedded server implementation; it is not itself the durable service abstraction.

Required host state:

```json
{
  "schema_version": 1,
  "host_id": "home-pc-...",
  "status": "ONLINE",
  "pid": 1234,
  "started_at": 1789510000.0,
  "port": 8899,
  "remote_enabled": true,
  "transport": "lan|overlay|relay|none"
}
```

Host state is informational. Stale PID/status data must be detected and not treated as proof that the process is alive.

### 5. Background/autostart integration

Public CLI target:

```text
python jarvis.py service install
python jarvis.py service start
python jarvis.py service stop
python jarvis.py service status
python jarvis.py service uninstall
```

Platform strategy:

- Windows: per-user Scheduled Task at logon, launched with `pythonw.exe` when available; no administrator requirement for the default path.
- Linux: user-level `systemd --user` unit.
- macOS: user `LaunchAgent` plist.

Registration is idempotent and generated from the current checkout path. Unit tests validate generated command/config text; platform-specific integration checks are additive and may skip when the platform facility is unavailable.

### 6. Remote HTTP API

Existing routes remain compatible. New routes are versioned under `/api/remote/v1`.

Minimum surface:

```text
GET  /api/remote/v1/host
POST /api/remote/v1/sessions
GET  /api/remote/v1/sessions/<id>
POST /api/remote/v1/sessions/<id>/messages
GET  /api/remote/v1/sessions/<id>/events?after=<seq>&limit=<n>
POST /api/remote/v1/sessions/<id>/ack
POST /api/remote/v1/sessions/<id>/close
```

The first implementation uses bounded long-poll/fetch semantics rather than making WebSocket support a prerequisite. A later adapter may add SSE/WebSocket while preserving the same protocol envelopes and event cursor semantics.

### 7. Device pairing

Target pairing flow:

```text
PC HUD -> Create pairing challenge -> QR code
phone -> scans challenge -> sends proof
PC -> records device identity -> returns one-time device credential
phone -> stores credential in browser/app secure storage where available
future requests -> device credential + session binding
```

Pairing challenges are single-use and expire. The PC exposes device listing and revocation. Compatibility bearer tokens remain supported during migration but are not the final persistent-device model.

### 8. Remote transport

Transport modes are intentionally separated from the protocol:

- `local`: loopback desktop HUD.
- `lan`: existing private IPv4/IPv6 network access.
- `overlay`: recommended first "anywhere" mode using a private device network such as Tailscale/Headscale; J.A.R.V.I.S. does not need to own that product's control plane.
- `relay`: future optional outbound J.A.R.V.I.S. relay adapter for users who do not want an overlay-network app on the phone.

The code exposes a transport capability/status interface. It does not hard-wire runtime semantics to a single vendor.

### 9. Mobile Companion PWA

The existing HUD becomes progressively installable:

- `ui/manifest.webmanifest`
- `ui/service-worker.js`
- `ui/remote-companion.js`
- responsive companion shell reusing the canonical design system

Mobile primary views:

1. Host status (`HOME-PC`, online/offline, last seen, active mission count).
2. Chat/session timeline.
3. Pending approval cards.
4. Mission/activity state.
5. Device/session controls.

The service worker caches only static shell assets. Runtime/session responses are network-first and are not silently treated as current when offline.

### 10. Runtime authority and approvals

Remote origin does not grant additional authority. Any action that already requires authorization/approval locally continues to require it remotely. The mobile client may display and submit an explicit approval, but the server validates that the approval is bound to the exact immutable action/scope/budget context expected by the existing authorization subsystem.

A remote client cannot convert an unexecutable plan into success, bypass verification, or fabricate receipts.

## Data model

`state/remote_sessions.json` schema v1:

```json
{
  "schema_version": 1,
  "sessions": {
    "<session_id>": {
      "session_id": "<session_id>",
      "device_id": "<device_id>",
      "status": "OPEN",
      "created_at": 1789510000.0,
      "last_seen_at": 1789510000.0,
      "mission_id": null,
      "next_seq": 1,
      "last_ack_seq": 0
    }
  }
}
```

Events are append-only JSONL per session. Payloads must be JSON objects. Event files are bounded by explicit retention/compaction policy introduced before production-scale use; the initial implementation may enforce a conservative maximum event count/bytes and reject further unbounded growth rather than silently truncate active history.

## Failure semantics

- Host unavailable: client shows `OFFLINE`; no cloud runtime is invented.
- Transport unavailable: session remains durable; client can retry later.
- Invalid/expired device credential: request is rejected; session data is not returned.
- Unknown session: 404/typed protocol error; do not create implicitly.
- Closed session: new messages rejected; event history may remain readable to its authorized device until retention removes it.
- Corrupt session state: fail closed for mutation, preserve the file for diagnosis, and surface a host error.
- Unsupported future schema: reject rather than downgrade.
- Runtime request accepted but outcome unknown: emit an explicit `mission_status`/receipt state reflecting uncertainty; never synthesize success.
- Duplicate `request_id`: return/replay the prior acceptance/outcome linkage instead of causing a duplicate mutable effect.

## Performance and resource boundaries

- Session metadata operations should remain small and atomic.
- Event reads are cursor- and limit-bounded.
- Mobile endpoints never dump the full Cognitive Vault or full repository state.
- Companion context is derived through the existing Context Governor; remote transport is not an excuse to send larger context.
- Long-poll intervals and event batches are bounded to avoid tight reconnect loops.

## Delivery decomposition

This initiative is split into independently reviewable slices:

### Slice A — Durable remote protocol/session core

Pure Python, no HTTP/UI dependency. Provides protocol envelopes, durable sessions, idempotent request ids and event cursor replay.

### Slice B — Host API bridge

Adds `/api/remote/v1` routes and bridges a remote message into the existing runtime without introducing another cognitive stack.

### Slice C — Resident host lifecycle

Adds `jarvis.py service ...`, host status and platform autostart registration.

### Slice D — PWA companion

Makes the current HUD installable and adds a mobile-first remote session UI with reconnect.

### Slice E — Pairing/device registry

Replaces long-lived shared bearer-token usage with explicit paired-device identities and revocation.

### Slice F — Anywhere transport

Ships private-overlay discovery/configuration first, then an optional outbound relay adapter behind the same transport interface.

### Slice G — Authorization/receipts/operational hardening

Binds remote approvals to existing authorization grants, exposes correlated receipts, adds recovery tests, CI gates, docs and operational diagnostics.

## Acceptance criteria

The feature is considered complete only when all of the following are demonstrated on an exact commit:

1. PC host can be installed as a user background service and returns to ONLINE after user login/restart.
2. Local desktop HUD still works without remote mode.
3. Existing LAN companion compatibility still works.
4. A paired phone on another network can attach through an approved private transport without public router port-forwarding.
5. Phone can send a message that is executed by the PC-side J.A.R.V.I.S. runtime.
6. Phone can disconnect, reconnect and replay only events after its last acknowledged sequence.
7. A running PC-side mission survives phone disconnection.
8. Duplicate mobile request ids do not duplicate mutable effects.
9. Remote approvals cannot bypass existing authorization or verification semantics.
10. Host/session status never reports unknown outcomes as successful.
11. PWA can be installed and displays host offline state truthfully when the PC cannot be reached.
12. Portable runtime tests, legacy gates and relevant UI tests remain green.
13. `v0.1.0` remains immutable and untouched.

## Compatibility strategy

The current `--remote`, `RemoteAuthManager`, QR generator and LAN request guard remain operational while the new protocol is introduced. Migration is additive first. Deprecation of the shared token can occur only after paired-device access has equivalent test coverage and a documented upgrade path.

## Explicit boundary

This design defines the architecture and target behavior. It does not claim that remote-anywhere transport, platform autostart or the mobile PWA are already implemented. Implementation evidence belongs to the branch/PR and its tests, not to this design document.