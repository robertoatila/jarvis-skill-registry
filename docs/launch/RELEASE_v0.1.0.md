# J.A.R.V.I.S. v0.1.0 — Cognitive Runtime Foundation

v0.1.0 defines the first public product boundary for J.A.R.V.I.S.: a local-first cognitive-runtime foundation that can be cloned, validated and launched without pretending the full autonomous target is already complete.

## Highlights

### Three-command local onboarding

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

The zero-dependency launcher validates the checkout, starts the existing local HUD/server boundary and exposes explicit `--doctor`, `--test` and `--full-test` modes.

### Explicit execution and verification semantics

The runtime foundation models execution attempts separately from verification, recovery and mission outcome. A successful process/tool call is not automatically treated as a verified task result.

### Bounded inference foundation

The repository contains provider-neutral bounded inference primitives with capability/policy filtering, bounded context, confidence-controlled fallback and scoped cache/memory behavior.

### Governed skills and adapters

The existing skill registry, governance tooling and adapter/distribution components remain part of the public foundation.

### Local HUD and cognitive vault

The release includes the local HUD/server code plus the Markdown/Obsidian cognitive-vault projection used to inspect and organize project knowledge.

## Release validation model

The release is fail-closed. `v0.1.0` is created only for the current `main` HEAD after both required push workflows report success:

- **JARVIS Validation**
- **Sovereign Security Protocol v13 (SSP-v13) Audit**

After the tag is created, the tag-triggered release workflow validates the exact tagged commit again before publishing the GitHub Release:

- portable Python master battery;
- `python jarvis.py --doctor`;
- `python jarvis.py --test`;
- reproducible context-budget benchmark;
- canonical pre-publish audit;
- legacy registry bootstrap;
- Phase 29 OCI packaging/integrity suite.

The published release attaches machine-readable benchmark and OCI evidence plus a release-evidence Markdown record containing the exact tag, commit and workflow run URL.

### Pre-tag baseline

The merged onboarding commit `ab8aba9644117a4521fe69d301108f3b23793242` passed both required push workflows on `main` before this release pipeline was staged.

Recorded baseline evidence from the launch candidate:

- **Portable Python master battery:** 281/281 tests passed across 42 suites.
- **Portable runtime matrix:** Windows, Ubuntu and macOS passed the master battery, public launcher checks, context benchmark and pre-publish audit.
- **Launcher:** `python jarvis.py --doctor` passed; `python jarvis.py --test` passed.
- **Legacy PowerShell governance:** 145/145 tests passed across Phases 25–33 in the dedicated Windows compatibility job.
- **Context budget fixture:** 1,673 serialized UTF-8 bytes admitted from a 7,428-byte naive envelope under a 1,800-byte budget; 5,755 bytes were not admitted.

The release workflow, not this historical baseline, is authoritative for the exact tagged release.

### Benchmark claim boundary

The context benchmark measures **serialized UTF-8 bytes only**. It does not prove provider-token savings, dollar savings, answer-quality improvement, lower latency or end-to-end agent superiority.

### Node validation status

Older project documentation referenced six Node tests at an earlier server-boundary revision. No current Node test entry point or JavaScript test harness was found in this release candidate, so **v0.1.0 does not claim Node-test validation**. If a reproducible Node suite is restored, it should be added to CI before a future release claims it.

## Known boundaries

v0.1.0 does **not** certify:

- general autonomous execution across arbitrary external systems;
- empirical model-routing superiority;
- universal browser behavior;
- production deployment hardening;
- provider availability;
- security of every catalogued third-party skill;
- provider-token, cost, latency or quality improvements from the context benchmark;
- a current Node/browser test suite.

## What comes next

The next milestone focuses on stronger empirical evidence:

1. repository-scale context/resource benchmarks;
2. adapter-attempt proof and real usage accounting;
3. stricter risk/authorization behavior;
4. deeper attempt integration;
5. measured routing quality;
6. memory admission/retrieval evaluation;
7. external contributor workflows;
8. restoration or replacement of the historical Node/browser validation path.

## Feedback wanted

The most useful feedback is concrete and reproducible: a broken quickstart, an incorrect contract assumption, a benchmark design flaw, a missing provider/adapter, or a case where execution and verification semantics produce the wrong outcome.
