# JARVIS Design System

This directory is the canonical implementation source for the J.A.R.V.I.S. visual system. The root [`DESIGN.md`](../DESIGN.md) is the governing contract; this file is the library map and contribution guide.

## Library map

| Path | Responsibility |
| --- | --- |
| `tokens.css` | Color, typography, spacing, radius, sizing, shadow, motion and compatibility tokens |
| `components.css` | Reusable primitives and their interaction/state contracts |
| `patterns.css` | Composition patterns such as the retractable sidebar and operational progression rail |
| `reference/` | Preserved visual-reference notes/assets that are not runtime components |
| `../ui/assets/design-system/` | Runtime projection served by the local HUD; CSS files must be byte-identical to the canonical files here |
| `../ui/assets/design-system/index.html` | Navigable showcase of primitives, states and both themes |

The project is deliberately **not** a Tailwind/shadcn/npm application. The current UI stack is vanilla HTML, CSS and JavaScript served by the zero-dependency Python runtime. Do not introduce a frontend framework solely to consume this library.

## Component inventory

The canonical primitives are:

1. Button
2. Card
3. Badge
4. Status
5. Metric
6. Input
7. Select
8. Progress
9. Alert
10. Empty state
11. Skeleton
12. Table
13. Segmented control
14. Sidebar composition
15. Operational progression rail
16. Objective card/composition

State support is explicit. Where semantically applicable, components cover default, hover, active, focus-visible, disabled, loading, error, empty and selected states.

## Adding or changing a component

1. Read [`DESIGN.md`](../DESIGN.md).
2. Add or extend semantic tokens in `tokens.css` before introducing a new visual value.
3. Add the primitive to `components.css`; use `patterns.css` only for multi-component composition/layout behavior.
4. Preserve keyboard focus and reduced-motion behavior.
5. Project the canonical CSS byte-for-byte to `ui/assets/design-system/`.
6. Add every meaningful state to the showcase.
7. Extend `tests/test_agentic_design_system_contract.py` before changing behavior.
8. Run the portable JARVIS test battery and HUD self-test.

## Runtime integration

`ui/experience-system.js` is a progressive enhancement layer. It does not replace the existing HUD or duplicate its domain logic. It mirrors the existing tab controls, reads existing live DOM telemetry and adds navigation/progression surfaces without inventing backend state.

The existing `ui/jarvis.css` remains a compatibility layer while older HUD surfaces are migrated incrementally. New UI work should use the `--jv-*` tokens and canonical primitives instead of adding another parallel visual language.

## Reference material

No `design-system-export/` directory existed in the repository at the time this canonical library was created. Therefore no Claude Design/Stitch HTML export, `DESIGN.md`, lint config, thumbnail, manifest or duplicate component could be truthfully migrated from such a dump. The reference directory records that provenance rather than fabricating source material.
