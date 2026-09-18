# Contributing to J.A.R.V.I.S.

Contributions are welcome when they make the runtime easier to verify, run, extend or understand.

You do **not** need to understand the full architecture before opening a useful PR.

## Fast local setup

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py --doctor
python jarvis.py --full-test
```

Launch the local HUD with:

```bash
python jarvis.py
```

Python 3.12 is recommended. PowerShell is required only for the Windows legacy-governance compatibility gate and related registry/distribution checks.

## Good first contribution shapes

Prefer narrow, independently verifiable changes:

- add or improve one canonical skill;
- add a deterministic provider/adapter fixture;
- reproduce and test one bug;
- improve one quickstart/platform path;
- add one benchmark fixture with a strict claim boundary;
- improve HUD accessibility or diagnostics;
- document a runtime contract with source evidence.

Avoid PRs that mix architectural rewrites, unrelated formatting and feature work.

## Adding a canonical skill

Create:

```text
skills/<kebab-case-name>/SKILL.md
```

Use concise frontmatter and document the capability precisely. If the skill incorporates or depends on third-party material, preserve its license/provenance requirements.

For a complete first contribution from a fresh fork through PR evidence, follow [First External Skill Contribution](docs/contributing/FIRST_EXTERNAL_SKILL.md).

## Adding a New Target Platform Adapter

Create or update the relevant adapter profile under `adapters/` and keep the implementation aligned with:

- `schemas/target-adapter-profile.schema.json`
- `docs/ADAPTER_DEVELOPMENT_GUIDE.md`
- the target's declared filesystem/layout contract
- the repository's quarantine and explicit-approval boundaries

Evidence levels are not interchangeable. Use **VERIFIED_EMPIRICAL** only when the target behavior has actually been exercised against the real platform/environment with reproducible evidence. CI-only compatibility and documentation-derived compatibility must remain labeled at their narrower levels.

A target-adapter PR should state:

1. target platform and adapter identifier;
2. installation/discovery path;
3. lifecycle operations implemented;
4. collision and rollback behavior;
5. exact verification level and evidence;
6. known unsupported operations.

Do not upgrade a compatibility label because a schema parses or a fixture passes.

## Design system contributions

Visual changes use [`DESIGN.md`](DESIGN.md) as the contract and [`design-system/`](design-system/) as the canonical library. Prefer incremental reuse over parallel components. Do not add hard-coded color, typography, spacing or radius values when a `--jv-*` token already represents the intent; if a missing semantic token is genuinely needed, add it to the design system first and exercise it in the showcase.

Preserve the existing HUD panel IDs and runtime behavior unless the PR explicitly changes that contract. For UI work, validate the component-state contract and confirm the showcase remains reachable from the local Python server.

## Validation before a PR

Minimum portable checks:

```bash
python jarvis.py --doctor
python jarvis.py --full-test
python benchmarks/context_budget_benchmark.py
```

For v0.2 evidence work, use the responsibility-scoped runner (`python tooling/validate_v020_plan4.py --gate <gate>`) and attach the resulting JSON report where the gate is required. GitHub workflow status is not validation authority.

For changes that touch the broader registry/distribution system, run the relevant PowerShell/bootstrap checks or the Windows `legacy-governance` direct gate.

If your change affects sensitive execution, authorization, credentials or trust boundaries, follow the repository's [SECURITY.md](SECURITY.md) and the controls applicable to that change.

## Pull request evidence

A strong PR explains:

1. **Problem** — what observable problem exists?
2. **Change** — what is the smallest change that addresses it?
3. **Evidence** — which tests, fixtures or commands support the result?
4. **Boundary** — what does the evidence *not* prove?
5. **Risk** — what behavior could regress?

Use the repository PR template and include exact commands when possible.

## Runtime invariants worth preserving

- Execution is not verification.
- Verification is not mission outcome.
- Required context must never be silently truncated.
- Missing authority must not be treated as implicit permission.
- Persistent memory should retain provenance and freshness information.
- Benchmarks must state exactly what they measure.
- Planned architecture must not be presented as validated runtime behavior.

## Community

Be specific, reproducible and respectful. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

If you are unsure where to start, choose a small open issue whose acceptance criteria can be validated locally and ask a concrete implementation question there.
