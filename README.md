<p align="center">
  <img src=".github/assets/jarvis-hero.svg" alt="J.A.R.V.I.S. — Autonomous Cognitive Runtime" width="100%">
</p>

# J.A.R.V.I.S. Skill Registry

**A local-first cognitive runtime for AI agents: persistent memory, dynamic skills, bounded context, tool/model routing and verified execution.**

Most agents can call tools. J.A.R.V.I.S. is being built to answer the harder questions around every call: **what context is worth loading, which capability should act, how much resource should be spent, what evidence proves success, and what should be remembered afterward?**

> The target is not maximum autonomy. It is **maximum verified usefulness per resource unit**.

## Run it in three commands

J.A.R.V.I.S. uses a zero-dependency Python launcher for the local HUD:

```bash
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry
python jarvis.py
```

The launcher validates the checkout, starts the existing local server on `http://127.0.0.1:8899` and opens the HUD. Provider-backed inference still requires explicit local provider configuration and authorization; the launcher does not silently invent credentials or bypass runtime policy.

Useful validation commands:

```bash
python jarvis.py --doctor     # prerequisites only; no network calls
python jarvis.py --test       # server self-test
python jarvis.py --full-test  # portable Python master battery
```

See [QUICKSTART.md](QUICKSTART.md) for configuration and troubleshooting.

## Why J.A.R.V.I.S. exists

Long-lived agents fail in predictable ways: context grows without discipline, model/tool choices are hard-coded, retries lose provenance, execution is confused with success, and memory becomes an unverified dump.

J.A.R.V.I.S. separates those concerns into explicit control planes:

| Problem | J.A.R.V.I.S. direction |
| --- | --- |
| Context rot and token waste | Context Governor expands information only when justified |
| One-model-fits-all routing | Capability/policy-aware model and tool selection |
| "Command exited 0" treated as success | Independent execution, verification, recovery and outcome states |
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

The last recorded server-boundary baseline passed **283 Python tests across 42 suites** plus **6 Node tests**. Those checks validate named local behaviors; they are **not** a security certificate or proof of live-provider/browser behavior.

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

The trusted foundation owns contracts, authority, durable attempts, artifacts, verification and budgets. Cognitive execution builds above it. The planned efficiency layer decides which context, tools and models are worth spending within those limits.

### Memory Fabric

![Planned Memory Fabric: working, episodic, semantic and procedural memory.](docs/assets/jarvis-memory-fabric.svg)

The memory direction separates transient working context from durable episodes, verified facts and supported procedures. Structured records remain authoritative; the Obsidian vault is a human projection, not the source of truth.

[Open the Cognitive Vault MOC](00%20-%20J.A.R.V.I.S.%20Cognitive%20Vault.md).

## Try the local HUD

```bash
python jarvis.py
```

Then use the HUD to inspect the current registry/runtime. For provider-backed chat, configure a supported provider using the example configuration files first. If authorization or provider configuration is missing, the runtime should report the operation as blocked/unverified rather than pretending it succeeded.

The existing server source is [tooling/jarvis_server.py](tooling/jarvis_server.py) and the HUD source is in [ui/](ui/).

## Evidence before claims

The project intentionally distinguishes architecture direction from validated behavior. Current evidence and known gaps are recorded in:

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
| [00 - J.A.R.V.I.S. Cognitive Vault.md](00%20-%20J.A.R.V.I.S.%20Cognitive%20Vault.md) | Human-facing cognitive-vault map |

## Contribute

The easiest useful contributions are intentionally small:

1. Run `python jarvis.py --doctor` and `python jarvis.py --full-test`.
2. Pick or open a narrowly scoped issue.
3. Add one skill, adapter, test, provider integration or reproducible bug case.
4. Open a PR with the evidence you used to validate the change.

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md).

## Project status and launch

The current public milestone is the **Cognitive Runtime Foundation**. The launch plan is deliberately evidence-gated: a short real demo, a three-command onboarding path, release notes, benchmark evidence and community-ready contribution surfaces come before broad promotion.

See [docs/launch/LAUNCH_PLAN.md](docs/launch/LAUNCH_PLAN.md) and [docs/launch/DEMO_90S.md](docs/launch/DEMO_90S.md).

## License

The repository contains an Apache License 2.0 text in [LICENSE](LICENSE). Catalogued third-party repositories and skills retain their own licenses and provenance requirements; inclusion in the registry is not blanket permission to execute or redistribute upstream material.
