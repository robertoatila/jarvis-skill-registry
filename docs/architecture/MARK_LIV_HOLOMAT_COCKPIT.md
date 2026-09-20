# J.A.R.V.I.S. Mark-LIV — Holomat Quantum Cockpit Implementation

**Source blueprint:** `23 - Master Prompt & Especificacao da Nova Interface J.A.R.V.I.S. Mark-LIV (Holomat Quantum Cockpit).md`

## Implementation strategy

The Mark-LIV cockpit is an additive UI layer over the existing HUD/runtime contracts.

It does **not** introduce a second frontend application or duplicate backend state. The cockpit reads the existing runtime endpoints and routes users into the existing panels:

- Terminal & Voice -> `tabNeural`
- Mission DAG -> `tabPipeline`
- Arsenal -> `tabArsenal`
- Radar -> existing repository/radar surfaces
- Hipocampo -> `tabObsidian`
- Mark-LIV Telemetry -> live cockpit telemetry cluster

## Runtime truth sources

The cockpit deliberately avoids fixed marketing counters. Values come from the current runtime:

- `/api/status` -> skills, starred catalog count, Merkle root, backend, context budget
- `/api/system/telemetry` -> CPU, RAM, disk, uptime, subsystem state
- `/api/keys/status` -> preferred/available inference providers
- `/api/agentic/telemetry` -> observed runtime latency/spans
- `/api/agentic/dag/active` -> Mission DAG preview
- `/api/memory` -> bounded memory-recall stream

The numbers mentioned in the design prompt (for example 319 skills / 3,706 repositories) are not hardcoded into the runtime UI.

## Visual contract

Implemented in `ui/mark-liv.css`:

- OLED deep-space canvas
- Arc Reactor cyan, quantum amber, sovereign green and quarantine red
- holographic glass panels
- CRT/scanline overlay
- concentric reactor rings
- circular telemetry gauges
- responsive module deck and floating quick-action dock
- reduced-motion handling
- desktop, notebook and mobile breakpoints

## Interaction contract

Implemented in `ui/mark-liv-cockpit.js`:

- four-phase operational rail
- live inference-provider indicator
- context/headroom meter
- live CPU/RAM/disk/context gauges
- Mission DAG SVG preview
- memory recall feed using DOM text nodes
- six Mark-LIV module launchers mapped to existing HUD panels
- quick dock for Remote Companion, ingest/radar, audit, Obsidian and fullscreen

Existing chat, mission receipts, Remote Companion, workspace and design-system modules remain authoritative.

## PWA

The service-worker cache now includes `mark-liv.css` and `mark-liv-cockpit.js`.
The manifest is branded as the Mark-LIV cockpit while retaining standalone display and the existing local JARVIS icon.

## Tests

Added/extended:

- `tests/test_mark_liv_cockpit_contract.py`
- `tests/browser/hud-smoke.spec.cjs`

Static contracts cover:

- shell asset wiring
- four phases
- six modules
- real runtime endpoint usage
- no hardcoded prompt counters
- safe dynamic memory rendering
- responsive/reduced-motion CSS
- PWA cache wiring

Browser smoke now checks cockpit visibility and module navigation while preserving the existing HUD navigation and receipt-truth checks.

## Validation state

During implementation the current versions of:

- `ui/mark-liv-cockpit.js`
- `ui/service-worker.js`
- `tests/browser/hud-smoke.spec.cjs`

were parsed successfully as JavaScript.

A full Python/browser test run has **not** been claimed in this document because this chat runtime does not expose a repository execution environment. The PR must remain Draft until the normal repository test battery is executed on the exact branch HEAD.
