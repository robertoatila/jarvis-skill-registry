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

Python 3.12 is recommended. PowerShell is required for the broader governance/distribution suites used by CI.

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

## Adding a target adapter

Create or update the relevant adapter profile under `adapters/` and keep the implementation aligned with the repository's target-adapter schema and development guide:

- `schemas/target-adapter-profile.schema.json`
- `docs/ADAPTER_DEVELOPMENT_GUIDE.md`

State the evidence level honestly. Documentation compatibility, CI compatibility and empirical live verification are different claims.

## Validation before a PR

Minimum portable checks:

```bash
python jarvis.py --doctor
python jarvis.py --full-test
python benchmarks/context_budget_benchmark.py
```

For changes that touch the broader registry/distribution system, also run the relevant PowerShell/bootstrap checks documented in CI.

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
