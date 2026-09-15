# JARVIS Experience System v2 — Implementation Plan

**Goal:** improve the existing J.A.R.V.I.S. HUD with a canonical visual system, retractable navigation and evidence-based operational progression without replacing the current runtime or inventing a CRM domain.

## Ground truth

- Frontend: vanilla HTML/CSS/JavaScript.
- Server: zero-dependency Python local runtime.
- Existing HUD tab contract is preserved.
- `design-system-export/` is absent; no export migration is claimed.
- `ui/jarvis.css` and the existing large HUD remain compatibility surfaces and are not rewritten wholesale.

## Execution sequence

1. Add a failing contract suite for visual-system files, runtime projection, component states, showcase and sidebar behavior.
2. Add canonical tokens, primitives and composition patterns under `design-system/`.
3. Project canonical CSS byte-for-byte into HUD-served assets.
4. Add a progressive `ui/experience-system.js` layer that mirrors the existing tabs and reads existing live telemetry.
5. Add a navigable design-system showcase covering dark/light themes and meaningful UI states.
6. Add root `DESIGN.md` and `AGENTS.md`, then merge design-system guidance into existing README/contribution docs.
7. Exercise the portable test battery, HUD self-test and cross-platform CI; fix regressions until green.
8. Merge only after the exact PR head passes required checks and then validate `main` again.

## Product decisions

- CRM concepts supplied in the source prompt are treated as UX inspiration only (dense workflows, sidebar IA, professional gamification). JARVIS remains a cognitive runtime/skill registry.
- Gamification becomes **operational progression**: goals, challenges and achievements must map to observable evidence, quality or reliability outcomes.
- Missing metrics render as unmeasured rather than receiving synthetic scores.
- The design-system showcase may use coherent fictitious values only when visibly marked DEMO.

## Validation boundary

This plan does not retroactively modify `v0.1.0` release evidence. Any larger post-change test count describes the current branch/main state, not the immutable release baseline.
