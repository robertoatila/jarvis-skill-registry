# J.A.R.V.I.S. v0.1.0 — Cognitive Runtime Foundation

> Draft release notes. Publish only from a commit whose CI and documented validation evidence are green.

## Why this release exists

v0.1.0 defines the first public product boundary for J.A.R.V.I.S.: a local-first cognitive-runtime foundation that can be cloned, validated and launched without pretending the full autonomous target is already complete.

## Highlights

### Three-command local onboarding

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

The new zero-dependency launcher validates the checkout, starts the existing local HUD/server boundary and exposes explicit `--doctor`, `--test` and `--full-test` modes.

### Explicit execution and verification semantics

The runtime foundation models execution attempts separately from verification, recovery and mission outcome. A successful process/tool call is not automatically treated as a verified task result.

### Bounded inference foundation

The repository contains provider-neutral bounded inference primitives with capability/policy filtering, bounded context, confidence-controlled fallback and scoped cache/memory behavior.

### Governed skills and adapters

The existing skill registry, governance tooling and adapter/distribution components remain part of the public foundation.

### Local HUD and cognitive vault

The release includes the local HUD/server code plus the Markdown/Obsidian cognitive-vault projection used to inspect and organize project knowledge.

## Validation

Before publishing this release, replace the placeholders below with evidence from the exact tag:

- Python master battery: `<COUNT> tests / <COUNT> suites / PASS`
- Node tests: `<COUNT> / PASS`
- Multi-platform CI: `<RUN URL / PASS>`
- Pre-publish audit: `<PASS>`
- Launcher doctor: `<OS / Python / PASS>`

The pre-launch baseline recorded before the onboarding PR was **283 Python tests across 42 suites plus 6 Node tests**. Do not reuse that number as v0.1.0 evidence unless the release-tag commit reproduces it or improves it.

## Known boundaries

v0.1.0 does **not** certify:

- general autonomous execution across arbitrary external systems;
- empirical model-routing superiority;
- universal browser behavior;
- production deployment hardening;
- provider availability;
- security of every catalogued third-party skill;
- benchmarked token/cost savings unless a reproducible benchmark is included with the tag.

## What comes next

The next milestone focuses on stronger empirical evidence:

1. reproducible context/resource benchmarks;
2. adapter-attempt proof and real usage accounting;
3. stricter risk/authorization behavior;
4. deeper attempt integration;
5. measured routing quality;
6. memory admission/retrieval evaluation;
7. external contributor workflows.

## Feedback wanted

The most useful feedback is concrete and reproducible: a broken quickstart, an incorrect contract assumption, a benchmark design flaw, a missing provider/adapter, or a case where execution and verification semantics produce the wrong outcome.
