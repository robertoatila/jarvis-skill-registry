# J.A.R.V.I.S. Repository Instructions

This file is the cross-agent entry point for work in this repository. Keep it concise; detailed contracts stay in their canonical documents.

## Canonical references

Read the relevant source before changing behavior:

- [`README.md`](README.md) — product position, validated baseline and repository map.
- [`DESIGN.md`](DESIGN.md) — visual system and UI contract.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution shape and validation expectations.
- [`SECURITY.md`](SECURITY.md) — repository security/reporting guidance.
- [`docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md`](docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md) — implementation direction.
- [`docs/architecture/SERVER_INFERENCE_BOUNDARY.md`](docs/architecture/SERVER_INFERENCE_BOUNDARY.md) — provider/server trust boundary.
- [`docs/ARCHITECTURE_5_LAYERS.md`](docs/ARCHITECTURE_5_LAYERS.md) — legacy distribution architecture that remains supported.

If instructions are scoped by a deeper `AGENTS.md` in the future, the deeper file governs that subtree where it conflicts with this root file.

## Runtime invariants

Preserve these distinctions:

- execution is not verification;
- verification is not mission outcome;
- required context is not silently truncated;
- missing authority is not implicit permission;
- persistent memory keeps provenance/freshness information;
- benchmark claims state exactly what was measured;
- planned architecture is not presented as validated behavior.

Do not move or retarget the immutable `v0.1.0` tag. New release behavior goes through the repository release workflow.

## UI and design-system work

Follow [`DESIGN.md`](DESIGN.md).

- Canonical visual code is under `design-system/`.
- New color, font, spacing, radius, shadow and motion values come from semantic `--jv-*` tokens.
- Keep the served CSS projection in `ui/assets/design-system/` byte-identical to the canonical CSS.
- Preserve all meaningful states: default, hover, active, focus-visible, disabled, loading, error, empty and selected where applicable.
- Preserve existing HUD tab IDs and behavior unless an intentional routing migration explicitly changes the contract.
- Do not invent telemetry, gamification scores or empirical claims to make the interface look populated.

## Change discipline

Prefer narrow, incremental changes over rewrites. Inspect existing code before introducing an equivalent abstraction. Preserve unrelated documentation and behavior. When an expected input/file is absent, record the absence rather than fabricating migration work.

Do not commit credentials, API keys, access tokens or personal secrets. Do not weaken fail-closed behavior to make a demo pass.

## Validation

Portable baseline:

```bash
python jarvis.py --doctor
python jarvis.py --full-test
python jarvis.py --test
python benchmarks/context_budget_benchmark.py
```

CI additionally exercises Windows compatibility/governance and the repository's pre-publish audit. Changes are not complete until the relevant test matrix is green and the changed user-facing route has been exercised.
