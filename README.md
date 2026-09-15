<p align="center">
  <img src=".github/assets/jarvis-hero.svg" alt="J.A.R.V.I.S. — Autonomous Cognitive Runtime" width="100%">
</p>

<h1 align="center">J.A.R.V.I.S. Skill Registry</h1>

<p align="center"><strong>A local-first cognitive runtime for AI agents: persistent memory, dynamic skills, bounded context, tool/model routing and verified execution.</strong></p>

<p align="center">
  <a href="https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0"><img alt="Release" src="https://img.shields.io/github/v/release/robertoatila/jarvis-skill-registry?display_name=tag&sort=semver"></a>
  <a href="https://github.com/robertoatila/jarvis-skill-registry/actions/workflows/ci.yml"><img alt="JARVIS Validation" src="https://github.com/robertoatila/jarvis-skill-registry/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/robertoatila/jarvis-skill-registry/actions/workflows/security-protocol-v13.yml"><img alt="SSP-v13 Audit" src="https://github.com/robertoatila/jarvis-skill-registry/actions/workflows/security-protocol-v13.yml/badge.svg?branch=main"></a>
  <a href="LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-4e8dff.svg"></a>
  <a href="https://github.com/robertoatila/jarvis-skill-registry/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/robertoatila/jarvis-skill-registry?style=flat"></a>
</p>

<<<<<<< HEAD
**Development status (2026-09-13):** M0–M6 modules are present, but the full-release certification claim was contradicted by reproducible authorization and file-protection failures. The current reanalysis fixes these boundaries and records selected tests; end-to-end autonomous execution remains uncertified. Start with the [current reanalysis](reports/reanalysis/20260913/REVIEW.md), then the historical [M0 report](reports/MILESTONE_ZERO.md) and [canonical roadmap](docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md).
=======
<p align="center">
  <a href="https://jarvis-skill-registry.vercel.app"><strong>Live site</strong></a> ·
  <a href="https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0"><strong>Get v0.1.0</strong></a> ·
  <a href="QUICKSTART.md"><strong>Quickstart</strong></a> ·
  <a href="https://github.com/robertoatila/jarvis-skill-registry/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22"><strong>Good first issues</strong></a> ·
  <a href="docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md"><strong>Roadmap</strong></a>
</p>
>>>>>>> 8f65117c4561b012121269e1afabe49cfe04c3a4

<p align="center">
  <a href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Frobertoatila%2Fjarvis-skill-registry%2Ftree%2Fmain%2Fsite&project-name=jarvis-skill-registry&repository-name=jarvis-skill-registry"><img src="https://vercel.com/button" alt="Deploy the J.A.R.V.I.S. landing with Vercel"></a>
</p>

<<<<<<< HEAD
| Area | Present in the repository | Validation boundary |
| --- | --- | --- |
| Skill registry | Catalog, governance and distribution tooling | Existing system; M0 does not re-audit every catalog entry |
| Execution foundation | Mission/task/attempt models, DAG, policy, state, profiles and scheduler | Selected contract and unit behavior validated; integration gaps remain |
| Verification | Source inspection, verification requirements and evidence structures | Partial; syntax checks alone do not prove functional success |
| Runtime intelligence | Planning, disclosure, repository intelligence, budgets and learning modules | Partial; actual attempt wiring and measured usage need hardening |
| Human interfaces | Local HUD, Markdown notes and Obsidian canvas | Existing; live behavior not validated in M0 |
| Cognitive direction | Context Governor, Cognitive Governor, tool/model routing and Memory Fabric modules | Implemented components; integrated behavior and persistence still require validation |
=======
Most agents can call tools. J.A.R.V.I.S. is being built to answer the harder questions around every call: **what context is worth loading, which capability should act, how much resource should be spent, what evidence proves success, and what should be remembered afterward?**
>>>>>>> 8f65117c4561b012121269e1afabe49cfe04c3a4

> The target is not maximum autonomy. It is **maximum verified usefulness per resource unit**.

<<<<<<< HEAD
The September 13 corrections add explicit local execution, persistent signed approvals, durable attempts, conservative recovery, transactional memory and truthful usage receipts. Natural-language plans still require explicit supported actions; provider calls and remote deployment are not certified. See the [current-reality assessment](docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md#2-current-reality).
=======
## Run it in three commands
>>>>>>> 8f65117c4561b012121269e1afabe49cfe04c3a4

J.A.R.V.I.S. uses a zero-dependency Python launcher for the local HUD:

<<<<<<< HEAD
The [consolidated interface](docs/CONNECTED-WORKSPACE.md) shares context directly from the existing mission plan. Connections appear in the existing Obsidian tab; synchronization updates the established MOCs and Canvas with verified backups. There is no separate workspace server or parallel skill selector.

Run the full fixture suite without copying private state, credentials or third-party skill bodies:

```powershell
python -B tooling/validate_isolated.py --report reports/local-validation.json
```

This creates a disposable checkout, synthetic skill catalog and empty state, denies external network in Python tests, and records the actual exit code and output. Node.js is used for the JavaScript security test; a missing Node runtime is reported as a skipped check.

The selected checks use Python's standard library. The recorded environment is Windows with Python 3.12.10; legacy registry commands also use PowerShell. Run from the repository root after obtaining a checkout:

```powershell
python -B -m unittest discover -s tests -p test_agentic_contracts.py -v
python -B -m unittest discover -s tests -p test_agentic_dag.py -v
=======
```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
>>>>>>> 8f65117c4561b012121269e1afabe49cfe04c3a4
```

The launcher validates the checkout, starts the local server on `http://127.0.0.1:8899` and opens the HUD. Provider-backed inference still requires explicit local provider configuration and authorization; the launcher does not silently invent credentials or bypass runtime policy.

Useful validation commands:

```bash
python jarvis.py --doctor     # prerequisites only; no network calls
python jarvis.py --test       # server self-test
python jarvis.py --full-test  # portable Python master battery
```

See [QUICKSTART.md](QUICKSTART.md) for configuration and troubleshooting.

## v0.1.0 is public — with evidence attached

The first public milestone, **Cognitive Runtime Foundation**, is available as an immutable tagged release: [**J.A.R.V.I.S. v0.1.0**](https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0).

The release workflow re-validates the exact tagged commit before publication and attaches machine-readable evidence. Current public baseline:

| Evidence | Result |
| --- | --- |
| Portable Python master battery | **281/281** tests across 42 suites |
| Portable runtime matrix | **Windows + Ubuntu + macOS** |
| Legacy PowerShell governance | **145/145** tests |
| Public launcher | `--doctor` PASS · `--test` PASS |
| Context-budget fixture | **7,428 B naive → 1,673 B admitted** under a 1,800 B budget |
| Release assets | `context-budget.json`, `phase-29-release-oci.json`, `RELEASE_EVIDENCE.md` |

The context benchmark measures **serialized UTF-8 bytes only**. It does not claim provider-token savings, dollar savings, lower latency, answer-quality improvement or end-to-end agent superiority. Those require separate empirical measurement.

## Why J.A.R.V.I.S. exists

Long-lived agents fail in predictable ways: context grows without discipline, model/tool choices are hard-coded, retries lose provenance, execution is confused with success, and memory becomes an unverified dump.

J.A.R.V.I.S. separates those concerns into explicit control planes:

| Problem | J.A.R.V.I.S. direction |
| --- | --- |
| Context rot and token waste | Context Governor expands information only when justified |
| One-model-fits-all routing | Capability/policy-aware model and tool selection |
| “Command exited 0” treated as success | Independent execution, verification, recovery and outcome states |
| Agent forgets what happened | Persistent episodic/semantic/procedural memory with provenance |
| Tool calls mutate blindly | Attempts, side effects, authorization and evidence are first-class records |
| Skills are scattered across ecosystems | Governed skill registry with target adapters and distribution tooling |

## What works today

This repository is **active development**, not a claim that the full autonomous target is already complete.

- **Skill registry:** catalog, governance, distribution and target-adapter tooling.
- **Execution foundation:** mission/task/attempt contracts, DAG execution, policy, persistence and scheduler components.
- **Bounded inference:** registered backends, capability/policy filtering, bounded context, confidence-controlled fallback and scoped cache/memory.
- **Verification primitives:** explicit requirements, evidence structures and independent state axes.
- **Human interfaces:** local HUD plus a Markdown/Obsidian cognitive vault.
- **Cognitive control plane:** Context/Cognitive governors, routing and memory primitives are partially integrated; empirical routing and broader external autonomy remain planned/hardening work.

Older documentation referenced six Node tests from an earlier server-boundary revision, but no current Node test entry point is present, so **v0.1.0 does not claim Node validation**. See the [v0.1.0 release evidence](docs/launch/RELEASE_v0.1.0.md) and the [published release](https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0).

## The execution model

![Target lifecycle: observe, plan, resolve, delegate, execute, verify, measure, learn and adapt.](docs/assets/jarvis-cognitive-loop.svg)

```text
observe
  ↓
plan
  ↓
resolve context / skill / tool / model
  ↓
execute
  ↓
verify with independent evidence
  ↓
measure cost / latency / risk
  ↓
learn what is safe and useful to retain
```

A task that ran is not automatically verified. A command that returned zero is not automatically useful. J.A.R.V.I.S. keeps execution state, verification state, recovery state and mission outcome separate so later decisions can reason from evidence instead of optimistic status flags.

## Architecture

![Architecture diagram: solid borders mark tested unit scope, dash-dot borders partial implementation, dashed borders planned components.](docs/assets/jarvis-runtime-architecture.svg)

The trusted foundation owns contracts, authority, durable attempts, artifacts, verification and budgets. Cognitive execution builds above it. The efficiency layer decides which context, tools and models are worth spending within those limits.

### Legacy five-layer distribution contract

The newer cognitive-runtime view sits above, rather than erasing, the repository's original five-layer distribution architecture. The canonical historical description remains in [docs/ARCHITECTURE_5_LAYERS.md](docs/ARCHITECTURE_5_LAYERS.md); **LAYER 5** is the experience/integration surface.

The legacy distribution matrix models six targets, including **Cursor IDE** and **Google Antigravity**, alongside Codex, Claude, ChatGPT and generic targets. Those compatibility records are part of the registry/distribution subsystem; they are not evidence that every cognitive-runtime feature is empirically validated on every target.

### Memory Fabric

![Planned Memory Fabric: working, episodic, semantic and procedural memory.](docs/assets/jarvis-memory-fabric.svg)

The memory direction separates transient working context from durable episodes, verified facts and supported procedures. Structured records remain authoritative; the Obsidian vault is a human projection, not the source of truth.

[Open the Cognitive Vault MOC](00%20-%20J.A.R.V.I.S.%20Cognitive%20Vault.md).

## Experience system and visual contract

The local HUD now has a canonical visual contract in [`DESIGN.md`](DESIGN.md) and a reusable library in [`design-system/`](design-system/). The existing runtime remains vanilla HTML/CSS/JavaScript served by the zero-dependency Python server; this layer does not introduce Tailwind, shadcn/ui or a frontend build dependency.

When the HUD is running, the browsable showcase is available at `http://127.0.0.1:8899/assets/design-system/index.html`. It demonstrates the canonical tokens, component states, dark/light themes, retractable navigation patterns and the professional operational-progression model used by J.A.R.V.I.S.

New visual work should consume the `--jv-*` tokens and primitives instead of adding hard-coded colors, typography, spacing or radii. Agent-facing rules are summarized in [`AGENTS.md`](AGENTS.md).

## Try the local HUD

```bash
python jarvis.py
```

Then use the HUD to inspect the current registry/runtime. For provider-backed chat, configure a supported provider using the example configuration files first. If authorization or provider configuration is missing, the runtime should report the operation as blocked/unverified rather than pretending it succeeded.

The server source is [tooling/jarvis_server.py](tooling/jarvis_server.py) and the HUD source is in [ui/](ui/).

## Evidence before claims

Architecture direction and validated behavior are deliberately separated. Current evidence and known gaps are recorded in:

- [v0.1.0 release](https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0)
- [Milestone Zero report](reports/MILESTONE_ZERO.md)
- [Autonomous Intelligence Plan](docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md)
- [Server inference boundary](docs/architecture/SERVER_INFERENCE_BOUNDARY.md)
- [Cognitive software upgrade record](docs/plans/2026-09-13-cognitive-software-upgrade.md)

Known work includes stricter unknown-risk handling, stronger adapter-attempt proof, real resource accounting, deeper attempt integration and broader policy/approval enforcement.

## Repository map

| Path | Purpose |
| --- | --- |
| [jarvis.py](jarvis.py) | Public zero-dependency launcher and validation entry point |
| [tooling/agentic/](tooling/agentic/) | Runtime contracts, routing, execution and cognitive components |
| [tooling/jarvis_server.py](tooling/jarvis_server.py) | Local HTTP server / HUD boundary |
| [skills/](skills/) | Canonical skills |
| [tests/](tests/) | Automated checks |
| [docs/roadmap/](docs/roadmap/) | Canonical implementation roadmap |
| [docs/launch/](docs/launch/) | Demo, release and public launch material |
| [docs/assets/](docs/assets/) | Architecture and identity assets |
| [site/](site/) | Static public landing page deployed at [jarvis-skill-registry.vercel.app](https://jarvis-skill-registry.vercel.app) |
| [00 - J.A.R.V.I.S. Cognitive Vault.md](00%20-%20J.A.R.V.I.S.%20Cognitive%20Vault.md) | Human-facing cognitive-vault map |

## Contribute without learning the whole runtime

The easiest useful contributions are intentionally small:

1. Run `python jarvis.py --doctor` and `python jarvis.py --full-test`.
2. Pick a [`good first issue`](https://github.com/robertoatila/jarvis-skill-registry/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or [`help wanted`](https://github.com/robertoatila/jarvis-skill-registry/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) task.
3. Add one skill, adapter, test, provider integration or reproducible bug case.
4. Open a PR with the evidence used to validate the change.

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md).

If the architecture is useful, **star the repository** so other agent-runtime builders can find it. If an assumption is wrong, a reproducible counterexample or focused issue is more valuable than a star.

## Project status

**v0.1.0 — Cognitive Runtime Foundation** is released. The next public milestone focuses on stronger empirical evidence: repository-scale context/resource benchmarks, adapter-attempt proof, real usage accounting, stricter authorization semantics, measured routing quality, memory admission/retrieval evaluation and external contributor feedback.

See [docs/launch/LAUNCH_PLAN.md](docs/launch/LAUNCH_PLAN.md), [docs/launch/DEMO_90S.md](docs/launch/DEMO_90S.md) and the [roadmap](docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md).

## License

The repository is licensed under the Apache License 2.0; see [LICENSE](LICENSE). Catalogued third-party repositories and skills retain their own licenses and provenance requirements; inclusion in the registry is not blanket permission to execute or redistribute upstream material.
