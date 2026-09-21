# J.A.R.V.I.S. Mark-LIV — Holomat Quantum Cockpit Implementation

**Source blueprint:** `23 - Master Prompt & Especificacao da Nova Interface J.A.R.V.I.S. Mark-LIV (Holomat Quantum Cockpit).md`

## Implementation strategy

The Mark-LIV cockpit is an additive product surface over the existing HUD and
Python runtime. It does **not** create a second frontend application, routing
system or backend state model.

The existing sidebar/tab contract remains authoritative. Mark-LIV launches or
reuses those panels when appropriate and adds cockpit-native views only where
the blueprint explicitly needs a denser presentation.

## Runtime truth sources

The cockpit avoids fixed marketing counters. Runtime values are read from the
existing server contracts:

- `/api/status` — catalogue count, starred count, Merkle root, backend and context budget;
- `/api/system/telemetry` — CPU, RAM, disk, uptime, active runtime threads and subsystem state;
- `/api/keys/status` — configured inference providers;
- `/api/agentic/telemetry` — measured spans and observed average latency;
- `/api/agentic/dag/active` — one canonical Mission DAG plus wave schedule;
- `/api/runtime/missions` and mission timelines — persisted receipts/evidence;
- `/api/skills` — canonical skills plus invocation counts observed in the recent telemetry window;
- `/api/starred?limit=all` — full starred repository catalogue;
- `/api/repos/100k?limit=all` — curated 100k+ repository catalogue and official links;
- `/api/memory` — bounded episodic/semantic recall stream.

Prompt example numbers such as 319 skills or 3,706 repositories are **not**
hardcoded into the cockpit. If the runtime does not measure something, the UI
renders `—`, `UNAVAILABLE` or an equivalent explicit state.

## Canonical design-system integration

`DESIGN.md` remains authoritative.

Mark-LIV extends the canonical token source in
`design-system/tokens.css` with semantic `--jv-mark-*` tokens for the
Holomat palette, dense type scale, glass blur, motion and reactor glows.
The runtime projection in `ui/assets/design-system/tokens.css` is kept
byte-identical.

The reusable glass surface is a canonical component:

- `.jv-holomat-panel` in `design-system/components.css`;
- projected byte-identically to `ui/assets/design-system/components.css`.

`ui/mark-liv.css` consumes those tokens and the canonical primitive. It does
not contain raw hex/rgb color literals, independent font families, raw blur
values or raw motion durations. Structural geometry such as SVG dimensions,
circular gauges and responsive breakpoints remains local to the composition.

The Mark-LIV semantic token extension also defines light-theme overrides so the
cockpit preserves hierarchy when the existing theme control switches away from
the default OLED-dark presentation.

## Visual contract

Implemented by `ui/mark-liv.css` plus the canonical design system:

- OLED deep-space canvas;
- Arc Reactor cyan, quantum amber, sovereign green and quarantine red;
- holographic glass panels;
- subtle CRT/scanline overlay;
- concentric reactor rings and topbar reactor mark;
- circular host gauges;
- high-density repository matrix;
- responsive module deck and quick-action dock;
- tactical Orbitron/Rajdhani display typography with JetBrains Mono telemetry;
- reduced-motion handling;
- desktop, notebook and mobile breakpoints.

## Interaction contract

Implemented in `ui/mark-liv-cockpit.js`:

- four-phase operational rail;
- runtime protocol/governance badge plus partial Merkle identity;
- inference-provider indicator;
- context/headroom meter with safe/warn/critical state derived from measured utilization;
- CPU, RAM, disk, active-thread and context gauges;
- temperature/power surfaces that remain `—` when no standard host sensor is available;
- interactive Mission DAG using real nodes, edges, task states and scheduled waves;
- keyboard/click node detail with dependencies and verification counts;
- recent persisted mission receipts loaded from runtime observability;
- bounded memory recall feed built with text nodes;
- combined STARRED + 100K+ repository radar with deduplication, search, star ordering and official links;
- six Mark-LIV module launchers;
- quick voice-profile selector that reuses the existing voice control;
- optional browser speech recognition that fills the existing chat composer without auto-sending;
- reactive waveform driven by actual speech/listening events;
- dependency-free native keyword highlighting over already escaped code;
- quick dock for Remote Companion, ingest/radar, local audit execution, Obsidian sync and fullscreen.

## Arsenal and Radar evidence

The existing Arsenal remains the authoritative skill browser. Its visible
catalogue/security counts are derived from the loaded skill list instead of
stale literals.

`/api/skills` exposes `observed_invocations` from the recent 500 telemetry
spans. Skill cards render that measured count rather than a decorative counter.

The Mark-LIV Radar combines the full starred catalogue and 100k+ catalogue in
the browser, deduplicates by repository identity, searches the complete dataset
and limits only the number of DOM rows rendered at one time.

## Backend contract repairs made while implementing the cockpit

The implementation review exposed several pre-existing route defects that
directly affected truthful Mark-LIV data:

- duplicate GET handlers for `/api/agentic/dag/active` were consolidated;
- the canonical DAG response now contains `mission_id + dag + schedule`;
- duplicate GET handlers for `/api/agentic/telemetry` were consolidated;
- telemetry now returns already-serialized span dictionaries instead of calling
  `.to_dict()` on dictionaries and falling into the error path;
- no-data telemetry uses nullable measurements instead of fake zero/100 values;
- duplicate POST handlers for `/api/agentic/execute` were consolidated;
- `GET` and `POST /api/repos/scan-new` remain distinct supported contracts;
- `/api/agentic/fitness` now uses the real `rank_skills()` API instead of a
  nonexistent `get_top_skills()` call.

## Remote Companion / PWA boundary

The service worker includes the Mark-LIV static assets because they are part of
the served HUD shell.

The existing `manifest.webmanifest` intentionally remains
**J.A.R.V.I.S. Remote Companion** with `start_url=/?remote=1`. Mark-LIV does
not hijack that PWA identity. Desktop/standalone cockpit viewing is provided by
the existing fullscreen/F11 control.

## Tests

Added or extended:

- `tests/test_mark_liv_cockpit_contract.py`;
- `tests/browser/hud-smoke.spec.cjs`;
- `tests/test_agentic_v020_hud_runtime_integration.py`;
- existing `tests/test_agentic_design_system_contract.py` continues to enforce
  byte-identical canonical/runtime CSS projections.

Contracts cover:

- shell asset wiring;
- four phases and six modules;
- real runtime endpoint use;
- interactive Wave Studio and receipts;
- truthful hardware sensor availability;
- combined repository radar;
- measured skill invocation counts;
- no hardcoded prompt counters;
- safe memory rendering;
- voice/microphone fallback and no auto-send;
- syntax highlighting after HTML escaping;
- Remote Companion PWA identity;
- design-token consumption and Holomat primitive reuse;
- responsive/reduced-motion behavior.

## Validation state

During implementation, current versions of the touched JavaScript files have
been repeatedly parsed successfully. Static cross-checks have also verified:

- canonical/runtime token projection equality;
- canonical/runtime component projection equality;
- zero raw color literals in `ui/mark-liv.css`;
- no local font-family declarations outside canonical tokens;
- tokenized blur and motion;
- unique Mark-LIV backend routes where method identity is the same;
- separate GET/POST repository-discovery contracts;
- renderer escaping remains effective after syntax highlighting.

The full Python and Playwright/browser battery has **not** been claimed from
this chat environment because it does not expose a repository execution
runtime. PR #54 must remain Draft until that battery runs on the exact branch
HEAD.

## Note 19 projection health

The existing `PersistentMemoryEngine` already writes memory updates into
`19 - Memoria Persistente e Conhecimento Episodico.md`. Mark-LIV now exposes a
bounded projection-health object through `/api/memory` containing only status,
note filename, attempt/success timestamps and error type. Absolute filesystem
paths are not returned to the browser.

The Hipocampo panel displays active-memory count, last memory update and Note 19
projection state (`SYNCED` / `ERROR` / unknown) while keeping the recall feed
bound to actual persisted memories.

## OmniRoute model truth

The inference panel consumes the existing `/api/keys/status` contract. It shows
the preferred provider plus the configured Groq/Gemini model only when those
fields are actually exposed by the host. `LOCAL_ONLY` is rendered explicitly as
local/heuristic execution; missing models remain unmeasured rather than being
invented.

## Runtime reuse and lifecycle

Mark-LIV now reuses authoritative data already loaded by the legacy HUD instead
of blindly polling duplicate endpoints:

- hardware telemetry is published as `jarvis:hardware-telemetry` and consumed by
  the cockpit; direct polling resumes only if the shared feed becomes stale;
- Starred and 100K+ repository catalogs are published as
  `jarvis:starred-repos` / `jarvis:100k-repos` and reused by the Radar;
- Radar loading is lazy and starts only near the viewport or on explicit
  interaction;
- periodic refreshes pause while the document is hidden and resume when visible;
- timers/observers are released on `pagehide`.

This keeps the existing HUD authoritative while reducing duplicate work.

## Truthful mission and telemetry states

Circular gauges start in `unavailable` mode and remain visually unavailable when
measurements are absent; missing values are not rendered as 0%. The amber disk
tone cannot override the unavailable state.

The four-phase stepper distinguishes system availability from mission progress:

- Decomposition is driven by the active DAG;
- Skill Selection is shown as `available` when the arsenal is loaded, not as a
  completed mission step;
- Governed Execution is driven by persisted EXECUTION receipts;
- Synthesis is driven by persisted VERIFICATION receipts;
- running/failed/ready phase colors reflect persisted mission evidence.

## Terminal Holomat skin

The existing chat renderer remains authoritative. When Mark-LIV is active, its
assistant/user message surfaces receive tokenized holographic glass styling,
tactical avatars and reduced-motion behavior without changing message semantics
or rendering code.
