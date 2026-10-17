# J.A.R.V.I.S. Skill Registry & Cognitive Runtime

<p align="center">
  <img src=".github/assets/jarvis-hero.svg" alt="J.A.R.V.I.S. — a governed path from intent to verified outcomes" width="100%">
</p>

<p align="center"><strong>A local-first cognitive runtime for AI agents, built around governed skills, bounded context, persistent memory, and evidence-aware execution.</strong></p>

<p align="center">
  <a href="https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0"><img alt="Latest release" src="https://img.shields.io/github/v/release/robertoatila/jarvis-skill-registry?display_name=tag&sort=semver&color=00f2fe"></a>
  <a href="LICENSE"><img alt="Apache-2.0 license" src="https://img.shields.io/badge/license-Apache--2.0-4e8dff.svg"></a>
  <a href="https://github.com/robertoatila/jarvis-skill-registry/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/robertoatila/jarvis-skill-registry?style=flat&color=ffd700"></a>
  <a href="#"><img alt="Architecture" src="https://img.shields.io/badge/architecture-5%20Tactical%20Squadrons-a855f7.svg"></a>
  <a href="#"><img alt="Skills" src="https://img.shields.io/badge/governed%20skills-391%20canonical-00f5a0.svg"></a>
  <a href="#"><img alt="Sovereignty" src="https://img.shields.io/badge/execution-100%25%20Local%20%2F%20Offline%20First-cyan.svg"></a>
</p>

<p align="center">
  <a href="https://jarvis-skill-registry.vercel.app"><strong>Project site</strong></a> ·
  <a href="QUICKSTART.md"><strong>Quickstart</strong></a> ·
  <a href="docs/README.md"><strong>Documentation</strong></a> ·
  <a href="https://github.com/robertoatila/jarvis-skill-registry/issues"><strong>Issues</strong></a> ·
  <a href="docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md"><strong>Roadmap</strong></a> ·
  <a href="docs/vault/COGNITIVE_ATLAS.md"><strong>Cognitive Vault</strong></a>
</p>

---

J.A.R.V.I.S. is an open-source runtime for building AI agents whose tools, context, execution and memory can be governed, audited, and inspected. The project addresses a practical foundation: **what evidence should be required before an agent action is trusted?**

The repository is under active development. Its public [`v0.1.0 — Cognitive Runtime Foundation`](https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0) release is the immutable baseline; the broader `v0.2.0` program remains incomplete until its direct validation gates pass. Current status is tracked machine-readably in [`evidence/current.json`](evidence/current.json).

---

## ⚡ Core Capabilities

- 🛡️ **100% Local & Sovereign Execution**: Designed for local-first execution. Includes an offline cognitive reasoning core capable of zero-cloud operation, direct hardware awareness, and sub-millisecond local dispatch.
- 🎛️ **Mark-LIV Quantum HUD Cockpit**: Pure HTML5/ES Module tactical control surface served locally at `http://127.0.0.1:8899`, featuring real-time hardware telemetry, Arc Reactor state, voice profile synthesis, and browser microphone dictation.
- 🧠 **Dual-Layer Memory (Hipocampo)**: Merkle-rooted episodic memory ledger paired with a 23,800+ node Obsidian Cognitive Vault graph representation.
- ⚙️ **391 Governed Skills**: Curated canonical skills partitioned into explicit token budgets, ensuring prompts remain compact and resilient against context bloat.
- 🛰️ **23,500+ Starred Repository Radar**: High-performance SQLite FTS5 search matrix classifying elite open-source libraries, CLI tools, and frameworks into tactical squadrons.
- 🔒 **Fail-Closed Verification Gates**: Clear boundary between execution receipts and verified outcomes; actions enforce policy before credentials or network dispatch.

---

## 🏛️ The 5 Tactical Squadrons

All canonical capabilities and indexed repositories are partitioned into five specialized squadrons:

| Esquadrão | Foco Primário | Capacidades & Ferramentas Chave |
| :--- | :--- | :--- |
| **🦅 01 Cyberspace** | Cibersegurança Ofensiva & Pentest | BOLA/IDOR auditing, SQL injection analysis, XSS scans, binary inspection, reverse engineering. |
| **🛡️ 02 Aegis** | Defesa Ativa, Hardening & Criptografia | Merkle root verification, secrets rotation, OAuth2 validation, fail-closed access boundaries. |
| **🧠 03 Neuro-Cognitive** | Agentes Autônomos & RAG | Multi-agent DAG orchestration, semantic vector recall, local model dispatch, memory graphs. |
| **⚡ 04 Tactical** | Redes, Kernel & Baixo Nível | eBPF telemetry, high-throughput packet handling, socket proxies, low-level process inspection. |
| **🪐 05 Hyperion** | Arquitetura, DevTools & Frameworks | Reactive design systems, distributed tracing, high-performance AST parsing, clean code patterns. |

---

## 🚀 Quick Start

**Prerequisites:** Git, Python 3.10 or newer (Python 3.12 recommended), and a modern browser. The core launcher relies solely on the Python standard library.

```bash
# 1. Clone the repository
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry

# 2. Verify local environment prerequisites
python jarvis.py --doctor

# 3. Launch the Mark-LIV Tactical Cockpit
python jarvis.py
```

The launcher starts the local runtime at `http://127.0.0.1:8899` and opens the Mark-LIV cockpit in your browser. For custom ports or headless environments, pass:

```bash
python jarvis.py --port 9000 --no-browser
```

To run smoke and battery tests:

```bash
python jarvis.py --test
python jarvis.py --full-test
```

The HUD starts without external provider keys. Provider-backed inference is optional and requires explicit local configuration; see [QUICKSTART.md](QUICKSTART.md) and the [server inference boundary](docs/architecture/SERVER_INFERENCE_BOUNDARY.md).

---

## 🎥 Visual Demonstrations

### Tactical Decision-to-Verification Flow
The demo loop illustrates a local decision-to-verification lifecycle using verified runtime receipts:

<p align="center">
  <a href="docs/launch/DEMO_90S_EVIDENCE.md"><img src="docs/assets/jarvis-demo-loop.gif" alt="J.A.R.V.I.S. local decision-to-verification demo" width="900"></a>
</p>

<p align="center">
  <a href="docs/assets/jarvis-demo-90s.mp4"><strong>Watch the 82-second demo video</strong></a> ·
  <a href="docs/launch/DEMO_90S_EVIDENCE.md"><strong>Read demonstration limits and evidence</strong></a>
</p>

### Obsidian Cognitive Vault (23,800+ Nodes)
Interactive knowledge topology showing episodic connections across skills, architectures, and repositories:

<p align="center">
  <a href="docs/assets/cognitive-vault-graph-animation.mp4"><img src="docs/assets/cognitive-vault-graph-animation-poster.png" alt="Open the Obsidian Cognitive Vault graph animation" width="900"></a>
</p>

<p align="center">
  <a href="docs/assets/cognitive-vault-graph-animation.mp4"><strong>Watch the graph exploration video</strong></a> ·
  <a href="docs/vault/COGNITIVE_ATLAS.md"><strong>Explore the Cognitive Atlas</strong></a>
</p>

---

## 📐 Architecture & Verification Flow

![J.A.R.V.I.S. architecture diagram](docs/assets/jarvis-runtime-architecture.svg)

The runtime follows a strict, observable cycle:
$$\text{Observe} \longrightarrow \text{Plan} \longrightarrow \text{Resolve} \longrightarrow \text{Execute} \longrightarrow \text{Verify} \longrightarrow \text{Measure} \longrightarrow \text{Learn}$$

1. **Observe**: Telemetry, hardware sensors, and user prompts captured deterministically.
2. **Plan**: Task decomposition into directed acyclic graphs (DAGs).
3. **Resolve**: Bounded selection of canonical skills within context budget limits.
4. **Execute**: Sovereign local or policy-authorized provider dispatch.
5. **Verify**: Cryptographic evidence check against declared exit codes and contracts.
6. **Measure**: Serialized UTF-8 byte context consumption and latency recording.
7. **Learn**: Provenance-preserving updates to persistent memory and episodic state.

---

## 📚 Canonical Documentation

| Resource | Scope & Purpose |
| :--- | :--- |
| [Quickstart Guide](QUICKSTART.md) | Setup, configuration, troubleshooting, and offline verification |
| [Documentation Architecture](docs/README.md) | Classification of canonical, active, supporting, and historical docs |
| [Runtime Execution Contract](docs/architecture/RUNTIME_EXECUTION_CONTRACT.md) | Authority, execution, verification, and recovery semantics |
| [Server Inference Boundary](docs/architecture/SERVER_INFERENCE_BOUNDARY.md) | Provider configuration and security boundaries |
| [Cognitive Atlas](docs/vault/COGNITIVE_ATLAS.md) | Obsidian hubs, graph profiles, preservation, and animation |
| [Remote Second Brain](docs/REMOTE_SECOND_BRAIN.md) | Vault synchronization and Remote Companion operations |
| [Current Evidence Manifest](evidence/current.json) | Direct validation gates and machine-readable evidence status |
| [Autonomous Roadmap](docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md) | Implementation direction and phased milestones |

---

## 🛡️ Project Governance & Verification Evidence

- **Baseline Tag:** [`v0.1.0 — Cognitive Runtime Foundation`](https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0), with direct evidence in [`docs/launch/RELEASE_v0.1.0.md`](docs/launch/RELEASE_v0.1.0.md).
- **Current Program:** `v0.2.0` remains `DIRECT_VALIDATION_REQUIRED` / `INCOMPLETE` until all direct evidence gates pass.
- **Evidence Policy:** Direct execution evidence must be collected fresh on target platforms (Windows, Linux, macOS). Workflow status or historical logs are not validation authority.
- **Benchmark Policy:** Context metrics represent serialized UTF-8 bytes measured directly from runtime receipts.

---

## 🤝 Contributing

We welcome focused contributions: specialized skills, test cases, bounded documentation fixes, or reproducible improvements. Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`AGENTS.md`](AGENTS.md) before submitting pull requests.

Security disclosures must follow [`SECURITY.md`](SECURITY.md). Community conduct is guided by the [Code of Conduct](CODE_OF_CONDUCT.md).

⭐ **If you find J.A.R.V.I.S. valuable, star this repository on GitHub to support open, verifiable, sovereign AI systems!**

---

## 📄 License

J.A.R.V.I.S. is licensed under the [Apache License 2.0](LICENSE). Curated skills and referenced open-source projects retain their respective upstream licenses.
