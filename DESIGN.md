# J.A.R.V.I.S. Visual Contract

`DESIGN.md` is the repository's canonical visual contract. When UI code, screenshots, older CSS, prose or agent instructions disagree with this file, update the implementation to match this contract unless a newer explicitly approved contract supersedes it.

## Product character

J.A.R.V.I.S. is a local-first cognitive runtime and governed skill registry. Its interface should feel like a modern command center: precise, calm, high-information and responsive. “Futuristic” means strong hierarchy, live evidence and intentional motion — not excessive neon, decorative telemetry or science-fiction labels that obscure ordinary tasks.

The design must remain comfortable for daily work. Prefer legibility, predictable navigation and clear state over spectacle.

## Actual frontend stack

The current HUD is deliberately lightweight:

- vanilla HTML;
- vanilla CSS;
- vanilla JavaScript;
- the zero-dependency Python server in `tooling/jarvis_server.py`.

There is no project `package.json`, Tailwind installation or shadcn/ui installation. Do not introduce a framework or package manager solely to implement visual-system work.

## Source of truth

Canonical implementation lives in [`design-system/`](design-system/):

- `tokens.css` — visual tokens;
- `components.css` — primitives and states;
- `patterns.css` — composition patterns;
- `reference/` — non-runtime visual references.

The HUD-served CSS in `ui/assets/design-system/` is a runtime projection and must remain byte-identical to the canonical CSS. The navigable showcase lives at `/assets/design-system/index.html` when the local HUD is running.

`ui/jarvis.css` is a legacy compatibility layer. Migrate it incrementally; do not rewrite the entire HUD merely to normalize styling.

## Token rule

New product UI must not introduce independent hardcoded values for:

- color;
- font family or typographic scale;
- spacing;
- radius;
- shadow/glow;
- motion duration/easing;
- reusable control dimensions.

Add or reuse a semantic `--jv-*` token first. Literal values belong in the token source, not scattered through product surfaces. Media-query breakpoints and genuinely structural browser constraints may remain local when CSS custom properties cannot represent them.

## Visual hierarchy

Primary theme is dark and neutral with cyan/blue used for active command surfaces. Violet is secondary. Success, warning and danger colors are semantic only. Light theme must preserve hierarchy and is supported in the showcase for comfortable bright-environment use.

Use monospace for machine identifiers, receipts, hashes, metrics and shortcuts. Use the sans family for navigation, prose, controls and headings.

Avoid gratuitous uppercase. Reserve it for compact system labels, status chips and machine-oriented metadata.

## Component state contract

Every reusable component must represent the states that are meaningful for that component. Across the library this includes:

- default;
- hover;
- active;
- focus-visible;
- disabled;
- loading;
- error;
- empty;
- selected.

Do not encode critical state through color alone. Use labels, borders, icons/shapes or text as redundant signals.

## Navigation

The HUD uses a retractable left sidebar as the primary navigation model. The sidebar is an enhancement over the existing tab contract, not a new routing system. These canonical runtime panels remain stable:

- `tabNeural` — assistant/chat;
- `tabArsenal` — canonical skills;
- `tabIngest` — GitHub radar/ingestion;
- `tabSubagents` — agents/squads;
- `tabSecurity` — security review;
- `tabPipeline` — audit/mission execution;
- `tabObsidian` — cognitive vault.

Sidebar actions must delegate to the existing tab controls until the underlying routing layer is intentionally replaced. Collapse preference persists locally. Keyboard navigation remains first-class.

## Operational progression and gamification

Gamification is allowed only when it improves work quality and does not infantilize the product. The preferred model is **operational progression**, not arbitrary points.

Useful mechanics include:

- goals tied to observable completion criteria;
- challenges tied to reliability, quality, evidence or efficiency targets;
- achievements derived from verifiable events such as green gates, completed reviews or reproducible benchmarks;
- progression levels representing demonstrated maturity, not click frequency;
- individual progress and squad/team objectives when a real identity/team data source exists.

Never invent a score simply to make a dashboard feel active. If a live source is unavailable, display `—`, `not measured`, `demo` or equivalent. The runtime progression rail reads existing HUD telemetry only. Showcase values are explicitly marked DEMO.

## Evidence and claim boundary

UI presentation must preserve the repository's core semantic separation:

- execution is not verification;
- verification is not mission outcome;
- a process exit code is not independent proof;
- planned architecture is not validated runtime behavior;
- serialized-byte benchmarks are not token/cost/quality claims.

Status labels must reflect the backing state. Do not turn `UNVERIFIED` into a success-looking state or claim an unavailable metric.

## Accessibility and comfort

New UI must:

- expose visible `:focus-visible` treatment;
- remain keyboard-operable;
- preserve semantic labels/ARIA where native semantics are insufficient;
- support `prefers-reduced-motion`;
- remain usable at mobile widths;
- avoid rapid/persistent decorative animation;
- target readable contrast and WCAG 2.1 AA behavior where applicable.

## Motion

Motion communicates state transition, selection or task progress. It should be short, interruptible and nonessential. Avoid ambient motion that competes with telemetry. Reduced-motion users receive an equivalent static experience.

## Adding a new visual primitive

1. Confirm that an equivalent primitive does not already exist.
2. Add semantic tokens to `design-system/tokens.css` when needed.
3. Implement the primitive in `components.css`, or a multi-component composition in `patterns.css`.
4. Cover relevant interaction/data states.
5. Project canonical CSS byte-for-byte to `ui/assets/design-system/`.
6. Add examples to the showcase, including error/empty/loading behavior where meaningful.
7. Add or update a failing contract test before implementation behavior changes.
8. Run the repository validation battery.

## Reference exports

A `design-system-export/` directory was requested as an input source, but no such directory existed in the repository when this contract was created. No source export, Stitch/Google Labs `DESIGN.md`, reference HTML or design-system lint configuration was available to migrate. That absence is recorded in `design-system/reference/README.md`; do not fabricate migrated artifacts.
