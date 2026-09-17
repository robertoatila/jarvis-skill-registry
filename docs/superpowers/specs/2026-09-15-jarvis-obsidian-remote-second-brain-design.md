# J.A.R.V.I.S. Bidirectional Obsidian + Universal Remote Second Brain Design

**Status:** APPROVED DIRECTION / IMPLEMENTATION NOT STARTED BY THIS DOCUMENT  
**Date:** 2026-09-15  
**Repository:** `robertoatila/jarvis-skill-registry`  
**Base inspected:** `main` at `b034111bafc8c0b37f83c5f8ac60d763d5c3172b`  
**Related in-flight work:** PR #17 `feat: remote companion host runtime`

## 1. Objective

Evolve the existing J.A.R.V.I.S. Cognitive Vault from a primarily one-way projection surface into a durable, bidirectional, event-driven second brain while keeping the PC-side J.A.R.V.I.S. runtime authoritative.

The same home-PC runtime must also be reachable from any approved device — phone, tablet, notebook, desktop browser or later a native app — without creating a second J.A.R.V.I.S. instance and without requiring the device to be on the same LAN.

A third concern is capability memory: J.A.R.V.I.S. must be able to remember an explicitly imported catalog of external capabilities, including ChatGPT browser-side skills/plugins/connectors, but must never pretend that a remembered capability is locally installed or invokable when it is not.

## 2. Current State That Must Be Preserved

The repository already has:

- an Obsidian vault at the repository root;
- `.obsidian/` configuration;
- `00 - J.A.R.V.I.S. Cognitive Vault.md` and related MOCs;
- `JARVIS-Brain-Map.canvas`;
- `tooling/agentic/vault.py` with `CognitiveVaultBridge`;
- `tooling/agentic/vault_projection.py` with managed-region Markdown and Canvas projection;
- `tooling/agentic/workspace_hub.py` exposing Obsidian detection and `--sync-obsidian`;
- `tooling/Sync-ObsidianVault.ps1` as a compatibility entry point;
- persistent memory/runtime work from J.A.R.V.I.S. v0.2 Plan 2;
- PR #17 implementing durable remote sessions, runtime bridge, `/api/remote/v1/*`, and resident-host liveness work.

The existing projection safety properties must remain intact: preserve human-authored content, update only JARVIS-owned regions/nodes by default, use atomic writes/backups, and reject unsafe linked vault paths.

## 3. Core Invariants

1. **One brain.** The PC-side J.A.R.V.I.S. runtime remains the only authoritative planner/Governor/memory/model-router/tool-router stack.
2. **Obsidian is a human-facing second-brain interface, not a competing authority.** Vault content can provide evidence and candidate knowledge; Markdown text alone never grants execution permission.
3. **Human content is preserved.** Autonomous writes target JARVIS-owned managed regions or JARVIS-owned notes unless a separate explicit mutation contract exists.
4. **No self-feedback loops.** JARVIS must distinguish its own projections from human edits and avoid repeatedly ingesting its own writes.
5. **Provenance before memory.** Every candidate memory derived from the Vault retains source path, content hash, observed timestamp, and event/candidate identity.
6. **Capability memory is not capability execution.** Knowing that a ChatGPT skill exists is distinct from having a local adapter or a verified delegated provider session capable of invoking it.
7. **Any-device remote access means network-location independent, not public-port exposure.** Clients may connect from 4G/5G, another Wi-Fi, another city or another PC, but the default design must use private/outbound transport rather than direct public forwarding of port 8899.
8. **Device identity is individual and revocable.** Do not use one permanent shared token for every device as the target architecture.
9. **Sessions survive client loss.** Temporary browser/app/network loss must not kill the PC-side mission. Clients resume by cursor/session identity.
10. **Truthful availability.** A device UI must not report the host, a skill, a provider, or a mission as available unless the corresponding liveness/availability evidence is current.

## 4. Target Architecture

```text
                         +----------------------------+
                         |   PHONE / TABLET / LAPTOP  |
                         | Browser/PWA; native later  |
                         +-------------+--------------+
                                       |
                          paired, authenticated session
                                       |
                         private/outbound remote transport
                                       |
                                       v
+--------------------------------------------------------------------+
|                         HOME PC / JARVIS HOST                       |
|                                                                    |
|  Resident Host -> Remote API -> Session Journal -> Runtime Bridge  |
|                                                |                   |
|                                                v                   |
|     +----------------------------------------------------------+   |
|     | ONE AUTHORITATIVE JARVIS COGNITIVE RUNTIME              |   |
|     | Governor | Context | Memory | Model Router | Tool Router |   |
|     +-----------+-----------------+----------------------------+   |
|                 |                 |                                |
|                 |                 +--> External Capability Catalog |
|                 |                      ChatGPT / Codex / etc.       |
|                 |                                                  |
|                 v                                                  |
|       Bidirectional Cognitive Vault Bridge                         |
|            |                    |                                  |
|       VaultWatcher        Managed Projector                        |
|            |                    |                                  |
|            +------> Memory Admission <-----+                       |
|                                      |                             |
|                                      v                             |
|                         Persistent Memory / Knowledge Graph         |
+--------------------------------------+-----------------------------+
                                       |
                                       v
                         OBSIDIAN MARKDOWN + CANVAS
```

## 5. Bidirectional Obsidian Layer

### 5.1 `VaultWatcher`

Introduce a standard-library-compatible watcher that observes the Vault without requiring Obsidian to be open.

The first implementation should prefer deterministic polling using metadata plus content hashes rather than introducing a mandatory native watcher dependency. It must support debounce/coalescing and restart-safe checkpoints.

Default observed content:

- `*.md` notes;
- `*.canvas` files needed by the knowledge graph;
- selected JARVIS metadata files if explicitly admitted.

Default ignored content:

- `.git/`;
- `backups/`;
- temporary projection files;
- runtime state not intended as human knowledge;
- most `.obsidian/` workspace/UI churn;
- generated JARVIS projections when the resulting hash matches a recorded projection receipt.

### 5.2 `VaultEventJournal`

Each meaningful change becomes a durable, bounded event rather than immediately becoming memory.

Minimum event fields:

```text
schema_version
event_id
path
kind              # created | modified | deleted | renamed
content_hash
previous_hash
observed_at
source             # human | jarvis_projection | unknown
projection_receipt
```

The journal must allow idempotent recovery after host restart.

### 5.3 `MemoryAdmissionPipeline`

Human-authored text is evidence, not automatically trusted instruction.

The admission pipeline converts relevant events into `MemoryCandidate` records containing at minimum:

```text
candidate_id
source_event_id
claim_or_summary
category
source_path
source_hash
observed_at
confidence
conflict_keys
risk_class
admission_state
```

Target states:

- `OBSERVED`
- `CANDIDATE`
- `ADMITTED`
- `REJECTED`
- `CONFLICT`
- `SUPERSEDED`

Low-risk project facts and navigation metadata may be auto-admitted when deterministic rules support them. Anything that changes authorization, execution boundaries, credentials, destructive-action permission, identity claims, or other high-impact authority must not become executable authority solely because it exists in a note.

### 5.4 Managed Projection

Keep `vault_projection.py` as the primitive for safe writes. Extend around it rather than bypassing it.

JARVIS may:

- update existing managed regions;
- update JARVIS-owned Canvas nodes/edges;
- create new JARVIS-owned notes in an explicit namespace/folder;
- create backlinks/MOC links;
- project mission state, verified memory, capability availability and evidence summaries.

Human-authored areas remain untouched by default.

## 6. Capability Memory: ChatGPT Browser Skills and Other External Tools

### 6.1 Explicit Boundary

J.A.R.V.I.S. **does not automatically know which skills/plugins/connectors are installed in ChatGPT in the browser**.

A capability visible to ChatGPT is platform-side state. The local J.A.R.V.I.S. process cannot infer or truthfully claim that state from a conversation, a remembered name, or a GitHub repository alone.

The target architecture therefore adds an `ExternalCapabilityCatalog`.

### 6.2 External Capability Record

```text
schema_version
source_id              # chatgpt-browser, codex, local, etc.
capability_id
name
provider
kind                   # skill | plugin | connector | model | tool
provenance
capabilities
availability_state
invocation_mode
last_observed_at
last_verified_at
metadata_hash
```

Recommended availability states:

- `KNOWN` — remembered/cataloged only;
- `UNVERIFIED` — source claims it, current availability not verified;
- `AVAILABLE_LOCAL` — locally executable through a verified adapter;
- `AVAILABLE_DELEGATED` — callable only through a verified provider/session;
- `UNAVAILABLE`;
- `REVOKED`.

### 6.3 ChatGPT Capability Import

Create a safe import contract so a browser-side or user-generated manifest can tell J.A.R.V.I.S. which ChatGPT capabilities are currently exposed.

The import must be explicit and provenance-bearing. It may eventually be supplied by a ChatGPT connector, browser companion, exported manifest or another authenticated bridge. It must not scrape browser secrets, cookies, session tokens or private browser storage.

J.A.R.V.I.S. can then remember:

> "ChatGPT Browser exposes capability X and it was last verified at time Y."

But it must not translate that into:

> "I can execute X locally."

unless a local or delegated invocation adapter has also been verified.

### 6.4 Obsidian Projection of Capabilities

Expose a human-readable capability MOC showing:

- locally executable skills;
- ChatGPT-only capabilities;
- delegated capabilities;
- stale/unverified capabilities;
- provenance and last verification time.

This makes Obsidian the visual inventory while structured runtime state remains authoritative.

## 7. Universal Remote Access From Any Device

### 7.1 Client Model

The baseline client is a responsive installable PWA so one implementation works on:

- Android browser/PWA;
- iPhone/iPad browser/PWA;
- Windows/macOS/Linux browser;
- tablets;
- secondary computers.

A native mobile application may be added later without changing the host protocol.

### 7.2 Remote Semantics

The device is a thin client. It must not contain the authoritative JARVIS memory, skills registry or planner.

The remote client receives only what it needs for the active user/session:

- host status;
- device/pairing status;
- conversation/session state;
- mission progress/events;
- response stream or event replay;
- explicitly requested artifacts/status.

### 7.3 Network Reachability

The target must work beyond LAN/Wi-Fi.

Do not require router port-forwarding as the default. Define a transport abstraction that can support one or more secure outbound/private methods, for example a private overlay network or outbound tunnel. Provider choice must remain replaceable.

The local HTTP server may remain bound in a safe/private topology; remote reachability is provided by the transport layer rather than by blindly making port 8899 public.

### 7.4 Device Pairing and Revocation

Evolve QR/token bootstrap into per-device identity.

Target flow:

1. JARVIS host creates a short-lived one-time pairing offer.
2. Device scans/opens the offer.
3. Host records a unique device identity and credential/key material.
4. Future sessions authenticate as that device.
5. Device can be individually named, inspected and revoked.
6. Revoking one device does not rotate every other device.

Target device states:

- `PENDING_PAIRING`
- `TRUSTED`
- `REVOKED`
- `EXPIRED`

### 7.5 Durable Sessions

PR #17 is the in-flight foundation for:

- versioned remote protocol;
- durable session store;
- request idempotency for completed requests;
- event journal/cursor replay;
- runtime bridge;
- `/api/remote/v1/*`;
- resident host state.

Implementation of this design must first determine whether PR #17 has merged. Do not independently recreate equivalent remote modules if they already exist in #17 or `main`.

## 8. Cross-System Data Flow

### Human writes in Obsidian

```text
Human edits note
-> VaultWatcher detects content-hash change
-> VaultEvent persisted
-> self-projection filter
-> MemoryAdmissionPipeline
-> candidate/conflict analysis
-> admission decision
-> persistent memory / knowledge graph
-> future JARVIS context can reference admitted knowledge
```

### JARVIS learns during a mission

```text
Mission/result/evidence
-> existing memory admission/governance
-> persistent structured memory
-> projection receipt
-> CognitiveVaultBridge
-> managed Markdown/Canvas projection
-> VaultWatcher sees the write but recognizes projection receipt
-> no feedback loop
```

### User connects from any device

```text
Browser/PWA on arbitrary network
-> private/outbound transport
-> paired device identity
-> existing remote session API
-> RemoteRuntimeBridge
-> same home-PC JARVIS runtime
-> same memory + same Vault + same skills
-> durable events returned to device
```

### ChatGPT capability becomes known to JARVIS

```text
Explicit ChatGPT capability manifest
-> validate schema/provenance
-> ExternalCapabilityCatalog
-> status = KNOWN/UNVERIFIED or AVAILABLE_DELEGATED
-> optional Obsidian capability MOC
-> router may consider capability only according to verified availability
```

## 9. Failure Semantics

- Missing/corrupt watcher checkpoint: rescan safely; do not invent events.
- Note changes while JARVIS projects: abort/retry using existing optimistic write check.
- Corrupt Markdown: preserve source; reject candidate extraction rather than rewriting it.
- Conflicting human facts: retain both provenance records and create `CONFLICT`; do not silently overwrite authority.
- Unverified ChatGPT manifest: catalog as unverified or reject; never claim executable availability.
- Provider session disappears: downgrade delegated capabilities; do not silently route to them.
- Remote transport down: host runtime continues locally; remote session can resume later.
- Client disconnects mid-mission: mission remains PC-side; reconnect via cursor/session.
- Host PC off: clients report truthful `OFFLINE`; no fake cloud JARVIS is created.

## 10. Testing Requirements

Use RED -> GREEN TDD for every implementation slice.

Required test families:

- Vault create/modify/delete detection;
- debounce and duplicate-event idempotency;
- restart checkpoint recovery;
- self-projection loop suppression;
- human-content preservation;
- managed-region and Canvas ownership preservation;
- candidate provenance and conflict handling;
- high-impact note text cannot grant execution authorization;
- ChatGPT capability import schema/provenance;
- remembered capability != local availability;
- delegated capability loses availability when provider verification expires;
- per-device pairing/revocation;
- wrong device cannot read another session;
- remote reconnect/cursor replay;
- host offline truthfulness;
- PWA flow on narrow and desktop viewports;
- existing full repository battery remains green on supported OSes.

## 11. Rollout Order

1. Vault event model + durable watcher checkpoint.
2. Memory candidate/admission layer for Vault events.
3. Bidirectional bridge with loop suppression and projection receipts.
4. External Capability Catalog.
5. Explicit ChatGPT capability-manifest import contract.
6. Capability projection into Obsidian.
7. Finish/consume PR #17 resident-host + durable remote foundation.
8. Per-device identity, pairing and revocation.
9. Provider-neutral remote transport adapter for beyond-LAN access.
10. Responsive/installable PWA for phone/tablet/desktop browsers.
11. End-to-end Obsidian + memory + capability + remote-session continuity tests.
12. Documentation, recovery runbook and final multi-platform gates.

## 12. Acceptance Criteria

The feature is complete only when all of the following are demonstrably true:

- editing an admitted Obsidian note can influence later JARVIS context through structured, provenance-bearing memory;
- JARVIS can project verified knowledge back to Obsidian without overwriting unrelated human content;
- JARVIS-generated projections do not recursively re-ingest themselves;
- external ChatGPT capabilities can be explicitly cataloged with provenance and availability state;
- JARVIS never claims a ChatGPT-only skill is locally executable without a verified adapter/session;
- a paired phone, tablet or secondary PC can connect from outside the home LAN to the same JARVIS host;
- disconnecting a remote device does not terminate the PC-side mission;
- revoking one device blocks that device without invalidating all others;
- turning off the home PC causes truthful remote `OFFLINE` state;
- no second authoritative memory/runtime is created on clients;
- existing repository tests/gates remain green.

## 13. Non-Goals For The First Implementation

- full GUI automation of the Obsidian desktop application;
- browser-cookie/session scraping from ChatGPT;
- copying ChatGPT private platform internals into the repository;
- making every remembered external capability automatically executable;
- synchronizing the full Vault onto every remote client;
- public unauthenticated Internet exposure of the JARVIS HTTP server;
- replacing the existing Governor, memory, router or authorization architecture.
