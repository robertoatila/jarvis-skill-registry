# J.A.R.V.I.S. Skill Registry & Cognitive Runtime

<p align="center">
  <img src=".github/assets/jarvis-hero.svg" alt="J.A.R.V.I.S. — a governed path from intent to verified outcomes" width="100%">
</p>

<p align="center"><strong>A local-first sovereign cognitive runtime for AI agents, built around governed skills, bounded context, persistent episodic memory, and evidence-aware execution.</strong></p>

<p align="center">
  <a href="https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0"><img alt="Latest release" src="https://img.shields.io/github/v/release/robertoatila/jarvis-skill-registry?display_name=tag&sort=semver&color=00f2fe"></a>
  <a href="LICENSE"><img alt="Apache-2.0 license" src="https://img.shields.io/badge/license-Apache--2.0-4e8dff.svg"></a>
  <a href="https://github.com/robertoatila/jarvis-skill-registry/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/robertoatila/jarvis-skill-registry?style=flat&color=ffd700"></a>
  <a href="#"><img alt="Architecture" src="https://img.shields.io/badge/architecture-5%20Tactical%20Squadrons-a855f7.svg"></a>
  <a href="#"><img alt="Skills" src="https://img.shields.io/badge/governed%20skills-392%20canonical-00f5a0.svg"></a>
  <a href="#"><img alt="Radar Matrix" src="https://img.shields.io/badge/starred%20radar-27%2C900%2B%20repos-cyan.svg"></a>
  <a href="#"><img alt="Security" src="https://img.shields.io/badge/security-SSP--v13.4%20Fail--Closed-green.svg"></a>
  <a href="#"><img alt="MCP Gateway" src="https://img.shields.io/badge/MCP%20Gateway-jarvis--sovereign--gateway-blue.svg"></a>
  <a href="#"><img alt="Sovereignty" src="https://img.shields.io/badge/execution-100%25%20Local%20%2F%20Offline%20First-blue.svg"></a>
</p>

<p align="center">
  <a href="https://jarvis-skill-registry.vercel.app"><strong>Project Site</strong></a> ·
  <a href="QUICKSTART.md"><strong>Quickstart</strong></a> ·
  <a href="docs/README.md"><strong>Documentation</strong></a> ·
  <a href="#-sovereign-mcp-gateway-integration"><strong>MCP Gateway</strong></a> ·
  <a href="docs/roadmap/JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md"><strong>Roadmap</strong></a> ·
  <a href="docs/vault/COGNITIVE_ATLAS.md"><strong>Cognitive Vault</strong></a> ·
  <a href="https://github.com/robertoatila/jarvis-skill-registry/issues"><strong>Issues</strong></a>
</p>

---

J.A.R.V.I.S. is an open-source, local-first runtime for building AI agents whose tools, context, execution, and memory can be governed, audited, and mathematically verified. The system addresses a fundamental operational question: **what evidence should be required before an agent action is trusted?**

The repository is under active development. Its public [`v0.1.0 — Cognitive Runtime Foundation`](https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0) release is the immutable baseline; the broader `v0.2.0` program progresses under direct evidence gates. Current status is tracked machine-readably in [`evidence/current.json`](evidence/current.json).

---

## ⚡ Core Capabilities

- 🛡️ **100% Local & Sovereign Execution**: Built for local-first, zero-cloud execution. Includes an offline cognitive core capable of direct hardware telemetry inspection, sub-millisecond local dispatch, and strict data sovereignty.
- 🔌 **Sovereign MCP Gateway (`jarvis-sovereign-gateway`)**: Native Model Context Protocol (MCP) server providing standard tool interfaces (`jarvis_system_status`, `jarvis_query_arsenal`, `jarvis_get_skill`, `jarvis_radar_search`, `jarvis_verify_integrity`, `jarvis_consult_protocol`) for external agents.
- 🎛️ **Mark-LIV Quantum HUD Cockpit**: Pure HTML5/ES Module tactical control surface served locally at `http://127.0.0.1:8899`. Features real-time system metrics, Arc Reactor state machine, Microsoft Edge Neural TTS streaming voice, and browser speech recognition.
- ⚙️ **392 Governed Skills & 176 Active IDE Profiles**: Canonical skills partitioned into strict token budgets with 100% Go-schema-compliant frontmatters, preventing context bloat and parser decoding errors.
- 🛰️ **27,900+ Starred Repository Radar ("Alexandria Library")**: High-performance SQLite FTS5 search matrix classifying elite open-source libraries, frameworks, CLI utilities, and research papers into 5 specialized tactical squadrons.
- 🧠 **Dual-Layer Memory (Hipocampo)**: Merkle-rooted episodic memory ledger paired with an Obsidian Cognitive Vault graph featuring 33 numbered Map of Content (MOC) hubs and 5,870+ interconnected knowledge nodes.
- 🔒 **Sovereign Security Protocol (SSP-v13.4)**: Merkle-anchored, fail-closed security boundary enforcing 118 quarantine tombstones, automated secrets leakage scanning, and pre-publish hygiene checks.
- 📱 **Mobile Remote Companion**: Secure remote monitoring over LAN or HTTPS Tailscale Serve with QR-code one-time pairing and expiring cryptographic token authorization.

---

## 🏛️ The 5 Tactical Squadrons

All canonical capabilities and 27,900+ indexed repositories are partitioned into five specialized squadrons:

| Esquadrão | Foco Primário | Capacidades & Ferramentas Chave |
| :--- | :--- | :--- |
| **🦅 01 Cyberspace** | Cibersegurança Ofensiva & Pentest | BOLA/IDOR auditing, SQL injection analysis, XSS scans, binary inspection, reverse engineering (`jadx`, `burp-suite-testing`, `blackbird`). |
| **🛡️ 02 Aegis** | Defesa Ativa, Hardening & Criptografia | Merkle root verification, secrets rotation, OAuth2 validation, fail-closed access boundaries, DevSecOps pipelines. |
| **🧠 03 Neuro-Cognitive** | Agentes Autônomos, RAG & LLMs | Multi-agent DAG orchestration, semantic vector recall, local model dispatch, memory graphs (`qdrant`, `polars`, `dspy`, `crewai`). |
| **⚡ 04 Tactical** | Redes, Kernel & Baixo Nível | eBPF telemetry, high-throughput packet handling, socket proxies, low-level process inspection (`tmux`, `zellij`, `ffmpeg`, `aria2`). |
| **🪐 05 Hyperion** | Arquitetura, DevTools & Frameworks | Reactive design systems, distributed tracing, high-performance AST parsing, clean code patterns (`threejs`, `gsap`, `tailwind`, `fastapi`). |

---

## 🔌 Sovereign MCP Gateway Integration

J.A.R.V.I.S. exposes its capabilities to external AI coding assistants (**Google Antigravity**, **Claude Code**, **OpenAI Codex**, **Cursor**, **Cline**) through the `jarvis-sovereign-gateway` Model Context Protocol (MCP) server.

### Available MCP Tools

| Ferramenta | Parâmetros | Descrição |
| :--- | :--- | :--- |
| `jarvis_system_status` | *(nenhum)* | Telemetria completa em tempo real: status do runtime, versão do protocolo SSP, vault ativo e conformidade de token. |
| `jarvis_query_arsenal` | `query`, `category?`, `squadron?` | Busca semântica e filtrada no catálogo de 392 skills canônicas. |
| `jarvis_get_skill` | `skill_id` | Recupera as instruções canônicas completas (`SKILL.md`) sob demanda (Progressive Disclosure). |
| `jarvis_radar_search` | `term`, `category?`, `limit?` | Pesquisa de sub-milissegundo via SQLite FTS5 nos 27.900+ repositórios curados. |
| `jarvis_verify_integrity`| `target_path?` | Verificação de integridade Merkle contra tampering e tombstones de quarentena. |
| `jarvis_consult_protocol`| `topic` | Consulta normativa ao protocolo de segurança SSP-v13.4 e políticas de execução. |

### MCP Client Configuration

Adicione ao seu arquivo de configuração MCP (`claude_desktop_config.json`, `settings.json` ou configuração de plugins do Antigravity):

```json
{
  "mcpServers": {
    "jarvis-sovereign-gateway": {
      "command": "python",
      "args": ["E:\\.skill-registry\\tooling\\mcp_gateway.py"],
      "env": {
        "JARVIS_VAULT_PATH": "E:\\.skill-registry\\skills",
        "JARVIS_FAIL_CLOSED": "true"
      }
    }
  }
}
```

---

## 🚀 Quick Start

**Prerequisites:** Python 3.10 or newer (Python 3.12 recommended), modern web browser, and Git. The core launcher relies solely on the Python standard library with zero external pip dependencies.

```bash
# 1. Clone the repository
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry

# 2. Verify local environment prerequisites
python jarvis.py --doctor

# 3. Launch the Mark-LIV Tactical Cockpit
python jarvis.py
```

The launcher starts the local runtime at `http://127.0.0.1:8899` and automatically opens the Mark-LIV cockpit in your browser.

### Advanced Launch Modes

```bash
# Launch with Mobile Remote Companion (LAN / QR Code pairing)
python jarvis.py --remote

# Custom port in headless mode (no browser window)
python jarvis.py --port 9000 --no-browser

# Run pre-flight server self-test
python jarvis.py --test

# Run full master test battery (contract & agentic suites)
python jarvis.py --full-test

# Install as background Windows resident host service
python jarvis.py service install
```

The HUD starts completely offline without external provider keys. Provider-backed inference is optional and requires explicit local configuration; see [QUICKSTART.md](QUICKSTART.md) and the [Server Inference Boundary](docs/architecture/SERVER_INFERENCE_BOUNDARY.md).

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

### Obsidian Cognitive Vault (5,870+ Nodes & 33 MOCs)
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

1. **Observe**: Hardware sensors, OS telemetry, and user prompts captured deterministically.
2. **Plan**: Task decomposition into directed acyclic graphs (DAGs) with explicit dependency checks.
3. **Resolve**: Bounded selection of canonical skills within explicit token budget limits.
4. **Execute**: Sovereign local or policy-authorized provider dispatch under sandbox profiles.
5. **Verify**: Cryptographic evidence check against declared exit codes, contracts, and SHA-256 digests.
6. **Measure**: Serialized UTF-8 byte context consumption and execution latency recording.
7. **Learn**: Provenance-preserving updates to episodic state and persistent memory.

---

## 📚 Canonical Documentation

| Resource | Scope & Purpose |
| :--- | :--- |
| [Quickstart Guide](QUICKSTART.md) | Setup, configuration, troubleshooting, and offline verification |
| [Documentation Architecture](docs/README.md) | Information classification of canonical, active, supporting, and historical docs |
| [5-Layer Architecture](docs/ARCHITECTURE_5_LAYERS.md) | Deep breakdown from Core Integrity up to Experience & MCP |
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
- **Security Audit (SSP-v13.4):** Evaluated deterministically with zero secret leakage across 3,074 eligible files (`python tooling/audit_pre_publish_security.py`).
- **Benchmark Policy:** Context metrics represent serialized UTF-8 bytes measured directly from runtime receipts.

---

## 🤝 Contributing

We welcome focused contributions: specialized skills, test cases, bounded documentation fixes, or reproducible improvements. Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`AGENTS.md`](AGENTS.md) before submitting pull requests.

Security disclosures must follow [`SECURITY.md`](SECURITY.md). Community conduct is guided by the [Code of Conduct](CODE_OF_CONDUCT.md).

⭐ **If you find J.A.R.V.I.S. valuable, star this repository on GitHub to support open, verifiable, sovereign AI systems!**

---

## 📄 License

J.A.R.V.I.S. is licensed under the [Apache License 2.0](LICENSE). Curated skills and referenced open-source projects retain their respective upstream licenses.
