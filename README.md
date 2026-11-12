<p align="center">
  <img src=".github/assets/jarvis-hero.svg" alt="J.A.R.V.I.S. — Autonomous Cognitive Runtime" width="100%">
</p>

<h1 align="center">J.A.R.V.I.S.</h1>

<p align="center">
  <strong>Local-First Autonomous Cognitive Runtime, Sovereign Skill Registry &amp; Evidence-Governed MCP Plane</strong>
</p>

<p align="center">
  <a href="https://jarvis-skill-registry.vercel.app" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/Live%20Site-jarvis--skill--registry.vercel.app-74cdff?logo=vercel&logoColor=black" alt="Live Project Site"></a>
  <a href="QUICKSTART.md"><img src="https://img.shields.io/badge/Python-3.10%2B%20Stdlib%20Launcher-3776AB?logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="tooling/jarvis_mcp_server.py"><img src="https://img.shields.io/badge/Protocol-MCP%20JSON--RPC%202.0-00A3E0" alt="MCP JSON-RPC 2.0"></a>
  <a href="docs/ARCHITECTURE_5_LAYERS.md"><img src="https://img.shields.io/badge/Architecture-5%20Isolated%20Layers-0F766E" alt="5 Isolated Layers"></a>
  <a href="evidence/current.json"><img src="https://img.shields.io/badge/Release%20v0.2.0-DIRECT__VALIDATION__REQUIRED-D97706" alt="Release Gate Status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-2563EB" alt="Apache 2.0 License"></a>
  <a href="#sovereign-arsenal-42872-curated-repositories--fast-search"><img src="https://img.shields.io/badge/Arsenal-42%2C872%20Repos-7C3AED?logo=github&logoColor=white" alt="42k Repos"></a>
  <a href="skills/"><img src="https://img.shields.io/badge/Skills-166%20Canonical-10B981" alt="166 Skills"></a>
  <a href="#master-verification-battery"><img src="https://img.shields.io/badge/Tests-python%20jarvis.py%20----full--test-10B981?logo=python&logoColor=white" alt="Run the test battery locally"></a>
  <a href="#zero-cost-sovereign-multi-provider-matrix"><img src="https://img.shields.io/badge/Inference-Groq%20LPU%20%7C%20Ollama%20Offline-F55036" alt="Multi-Inference"></a>
</p>

<p align="center">
  <a href="https://jarvis-skill-registry.vercel.app" target="_blank" rel="noopener noreferrer"><strong>Official Site ↗</strong></a> ·
  <a href="#why-jarvis">Why J.A.R.V.I.S.</a> ·
  <a href="#30-second-quickstart-zero-dependencies">Quickstart</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#sovereign-mcp-gateway">MCP Gateway</a> ·
  <a href="#platform-adapters--tactical-squadrons">Adapters</a> ·
  <a href="#benchmarks--verification">Benchmarks</a> ·
  <a href="#direct-evidence-governance">Governance</a> ·
  <a href="#repository-layout--documentation">Docs</a>
</p>

---

**J.A.R.V.I.S.** (*Joint Autonomous Real-time Verified Intelligence System*) transforms ad-hoc prompts, fragmented `SKILL.md` files, and unverified AI outputs into a **deterministic, local-first engineering runtime**. Built on cryptographic integrity (SHA-256 + Merkle anchoring), bounded UTF-8 context admission, explicit authority rings (`R0`–`R3`), and structured execution receipts, it bridges a canonical arsenal of **166 governed skills** and **42,872 curated repositories** directly into **Google Antigravity**, **Cursor IDE**, **Claude Code**, **OpenAI Codex CLI**, **Windsurf**, and **GitHub Copilot**.

> [!IMPORTANT]
> **Status & Evidence Contract:** The repository is actively maintained on the `v0.2.0` runtime track (`DIRECT_VALIDATION_REQUIRED` in [`evidence/current.json`](evidence/current.json)). J.A.R.V.I.S. **does not use GitHub Actions as a validation gate** — every subsystem claim is governed by reproducible direct JSON receipts audited by [`tooling/audit_documentation_claims.py`](tooling/audit_documentation_claims.py). The canonical project landing page is live at <a href="https://jarvis-skill-registry.vercel.app" target="_blank" rel="noopener noreferrer"><strong><code>https://jarvis-skill-registry.vercel.app</code> ↗</strong></a>.

---

## Why J.A.R.V.I.S.

Most agentic frameworks optimize for fast demos while leaving context bloat, silent tool drift, and unverified success claims unchecked. J.A.R.V.I.S. enforces rigorous systems-engineering invariants at every layer:

| Dimension | Conventional Agent Frameworks (AutoGPT, CrewAI) | J.A.R.V.I.S. Sovereign Cognitive Runtime |
| :--- | :--- | :--- |
| **Context Window Control** | Unbounded prompt concatenation until silent model truncation | Deterministic `compile_context()` budget in `serialized_utf8_bytes` with explicit loaded/omitted receipts |
| **Tool & Skill Integrity** | Unpinned markdown snippets copied across repositories | Canonical SHA-256 digests, Merkle root anchoring (`urn:skill-registry:merkle-tree:v1`), and `.skill-registry.lock` |
| **Execution Authority** | Implicit shell, file, and network execution on every turn | Ringed capability gates (`R0` Read-Only → `R3` Sovereign Mutation) + fail-closed quarantine barrier |
| **Completion Semantics** | LLM self-reported *"Done!"* without executable evidence | `EvidenceVerifier` validates exit codes, stdout, and hashes before granting `PASS` status |
| **Runtime Dependencies** | Heavy external Python/Node orchestration dependencies | **Zero-dependency Python 3.10+ standard-library launcher** (`python jarvis.py`) + local Cockpit HUD |
| **Multi-IDE Interoperability** | Locked into a single editor or proprietary extension | 6 cross-platform adapters + unified 8-tool **MCP JSON-RPC 2.0** server over `stdio` |
| **Local Offline Sovereignty** | Forced cloud subscription lock-in and vendor telemetry | 100% offline-capable via local Ollama models (`qwen2.5:7b`, `deepseek-r1:8b`) on Drive `D:\` + Groq LPU |

---

## 30-Second Quickstart (Zero Dependencies)

The core launcher uses **only the Python 3.10+ standard library**. No virtual environment, heavy pip compilation, or API key is required to inspect the runtime, run pre-flight diagnostics, or launch the local Cockpit HUD.

```bash
# 1. Clone the repository
git clone https://github.com/robertoatila/jarvis-skill-registry.git
cd jarvis-skill-registry

# 2. Verify local prerequisites (offline, zero network calls, < 1 second)
python jarvis.py --doctor

# 3. Launch the local Holomat Mark-LIV Cockpit on http://127.0.0.1:8899
python jarvis.py
```

### Essential Developer Commands

```bash
# Start on a custom port without auto-opening a browser
python jarvis.py --port 9000 --no-browser

# Fast server & contract self-test
python jarvis.py --test

# Master verification battery (prints its own suite and test counts)
python jarvis.py --full-test

# Audit documentation truth and anti-drift invariants
python tooling/audit_documentation_claims.py
```

> **Provider Setup (Optional):** Provider-backed chat is strictly opt-in. Copy `config/api_keys.example.json` to `config/api_keys.json` only after reviewing [`docs/architecture/SERVER_INFERENCE_BOUNDARY.md`](docs/architecture/SERVER_INFERENCE_BOUNDARY.md).

---

## Architecture

J.A.R.V.I.S. combines a **5-layer sovereign registry stack** ([`docs/ARCHITECTURE_5_LAYERS.md`](docs/ARCHITECTURE_5_LAYERS.md)) with a **9-stage governed runtime loop** ([`docs/architecture/RUNTIME_EXECUTION_CONTRACT.md`](docs/architecture/RUNTIME_EXECUTION_CONTRACT.md)).

### 1. The 5-Layer Sovereign Registry Stack

<p align="center">
  <img src="docs/assets/jarvis-runtime-architecture.svg" alt="J.A.R.V.I.S. 5-Layer Runtime Architecture" width="100%">
</p>

```mermaid
flowchart TB
    L5["LAYER 5 — EXPERIENCE: MCP Server (Stdio) · Local REST Gateway · Mark-LIV Cockpit HUD"]
    L4["LAYER 4 — DISTRIBUTION: 8-Step ACID Lifecycle · Target Adapters · Ed25519 / OCI Packaging"]
    L3["LAYER 3 — RESOLUTION: Project Manifest Detection · Capability Solver · Sealed .skill-registry.lock"]
    L2["LAYER 2 — INTELLIGENCE: 42,872-Repo Radar · 64 CART Random Forest · Semantic Taxonomy"]
    L1["LAYER 1 — CORE INTEGRITY: Normalized UTF-8 SHA-256 · Merkle Tree Root · Fail-Closed Quarantine"]

    L5 --> L4 --> L3 --> L2 --> L1
```

### 2. The 9-Stage Governed Turn Lifecycle

Every turn produces structured decision receipts rather than opaque chain-of-thought claims:

```mermaid
flowchart LR
    S1["1. Intent Intake"] --> S2["2. Authority Check (R0-R3)"]
    S2 --> S3["3. Skill & Radar Lookup"]
    S3 --> S4["4. Bounded Context Admission"]
    S4 --> S5["5. Model / Fixture Routing"]
    S5 --> S6["6. Sandboxed Execution"]
    S6 --> S7["7. Evidence Verifier"]
    S7 --> S8["8. Governor Verdict"]
    S8 --> S9["9. Immutable Timeline Receipt"]
```

### Core Runtime Subsystems

| Subsystem | Canonical Module | Responsibility |
| :--- | :--- | :--- |
| **Runtime Launcher & HUD** | [`jarvis.py`](jarvis.py) · [`tooling/jarvis_server.py`](tooling/jarvis_server.py) | Local HTTP boundary, `/chat-session.js` cockpit loader, diagnostics (`--doctor`), and offline-safe runtime controls |
| **Context Governor** | [`tooling/agentic/context_governor.py`](tooling/agentic/context_governor.py) | Prioritizes mandatory governance sources first, enforces byte budgets, drops stale/irrelevant inputs, and emits admission receipts |
| **Cognitive Governor** | [`tooling/agentic/cognitive_governor.py`](tooling/agentic/cognitive_governor.py) | Evaluates confidence, authority boundaries, retry ceilings, and halt/continue verdicts (`EVIDENCE_AND_CONFIDENCE_SUFFICIENT`) |
| **Memory & Vault Plane** | [`tooling/agentic/memory.py`](tooling/agentic/memory.py) · [`tooling/agentic/vault.py`](tooling/agentic/vault.py) | Separates ephemeral working state, versioned project memory, and curated Obsidian Cognitive Vault MOCs (5,870+ notes) |
| **Verification & Receipts** | [`tooling/agentic/verification.py`](tooling/agentic/verification.py) · [`tooling/agentic/execution_receipt.py`](tooling/agentic/execution_receipt.py) | Validates exit codes, schema invariants, and artifact hashes before allowing any task state to transition to `PASS` |
| **Design System** | [`design-system/`](design-system/) · [`DESIGN.md`](DESIGN.md) | Canonical CSS token architecture (`tokens.css`, `components.css`, `patterns.css`) projected identically into [`ui/assets/design-system/`](ui/assets/design-system/) |

### 3. End-to-End Multimodal Execution & Voice Pipeline

The local execution engine bridges real-time voice, mobile remote companions, IDE reasoning agents, and the persistent cognitive vault:

```mermaid
flowchart TD
    subgraph INP["Input Layer"]
        A["Voice Stream / Mic"] -->|Local Audio| B["Whisper STT Engine"]
        R["Mobile Remote Companion (Tailscale)"] -->|Authenticated HTTP/WS| C["J.A.R.V.I.S. Core Engine"]
        B -->|Parsed Intent| C
    end

    subgraph REA["Reasoning & Delegation"]
        C -->|ReAct Tool Loop| D["Claude Code · Codex · OpenCode"]
        C -->|Sovereign Gateway MCP| E["166 Canonical Skills Registry"]
        C -->|Offline Intent Classifier| CLF["64 CART Trees Random Forest"]
        E -->|Sandboxed Run| F["OSINT · Cadastral · PowerShell"]
    end

    subgraph OUT["State & Output"]
        C -->|Persistent Context & MOCs| G["Obsidian Vault Memory (5,870+ Notes)"]
        C -->|Synthesized Response| H["Edge Neural / Kokoro TTS"]
        H -->|Audio Output| I["Speaker Output"]
        C -->|State Telemetry| J["Mark-LIV Holographic Cockpit (:8899)"]
    end
```

---

## Sovereign MCP Gateway

Connect any MCP-compatible host (**Google Antigravity**, **Cursor IDE**, **Claude Desktop**, **Claude Code**, **Windsurf**) directly to [`tooling/jarvis_mcp_server.py`](tooling/jarvis_mcp_server.py):

```json
{
  "mcpServers": {
    "jarvis-sovereign-gateway": {
      "command": "python",
      "args": ["/absolute/path/to/jarvis-skill-registry/tooling/jarvis_mcp_server.py"]
    }
  }
}
```

### Exposed MCP Tools (8 Deterministic Endpoints)

| Tool Name | Ring | Capability |
| :--- | :---: | :--- |
| `jarvis_system_status` | `R0` | Returns live registry health, quarantine state, Merkle integrity status, and active runtime counters |
| `jarvis_query_arsenal` | `R0` | Searches indexed engineering skills by capability, domain, stack, or tactical squadron |
| `jarvis_get_skill` | `R0` | Progressively discloses a specific `SKILL.md` payload on demand without flooding global context |
| `jarvis_radar_search` | `R0` | Queries the curated GitHub intelligence radar (`06 - GitHub Starred Repositories.md` & domain MOCs) |
| `jarvis_consult_protocol` | `R0` | Retrieves normative architectural, security, or execution protocols from governance memory |
| `jarvis_verify_integrity` | `R1` | Runs cryptographic hash verification and schema contract checks across target artifacts |
| `jarvis_execute_mission` | `R2` | Dispatches a bounded, receipt-tracked multi-step mission under explicit governor supervision |
| `jarvis_weaponize_tool` | `R3` | Packages, hashes, and registers a validated workflow or script into the canonical skill arsenal |

---

## Platform Adapters & Tactical Squadrons

### Cross-IDE Adapter Matrix

Adapters follow the formal schema in [`docs/ADAPTER_DEVELOPMENT_GUIDE.md`](docs/ADAPTER_DEVELOPMENT_GUIDE.md) (`adapters/<platform>/adapter.json`), distinguishing `VERIFIED_EMPIRICAL` from `VERIFIED_DOCS` capabilities in [`schemas/platform-capabilities.json`](schemas/platform-capabilities.json):

- **Google Antigravity** (`.agents/skills`, native MCP & customization routing)
- **Cursor IDE** (`.cursor/rules` & MCP stdio integration)
- **Claude Code** (`CLAUDE.md`, slash skills & MCP server bindings)
- **OpenAI Codex CLI** (`AGENTS.md` & progressive skill disclosure)
- **Windsurf** & **GitHub Copilot** (workspace instruction & capability projection)

### The 5 Tactical Squadrons & Cognitive Vault

<p align="center">
  <img src="docs/assets/cognitive-vault-graph-map.svg" alt="J.A.R.V.I.S. Cognitive Vault Graph Universe — 5,870+ Notes, 33 MOCs, 5 Squadrons" width="100%">
</p>

Alongside executable Python, Node.js, and PowerShell tooling, the repository maintains an interconnected knowledge graph rooted at [`00 - J.A.R.V.I.S. Cognitive Vault.md`](00%20-%20J.A.R.V.I.S.%20Cognitive%20Vault.md), organizing capabilities into five operational squadrons:

1. **Command & Orchestration** — Autonomous execution loops, DAG task planning, context governance, and adversarial review.
2. **Backend, Data & Infrastructure** — Distributed systems, API contracts, SQL/migrations, containers, and observability.
3. **Frontend, UI & Motion Engineering** — Accessible interfaces, design tokens, state architecture, and CWV performance.
4. **Security & Red/Blue Verification** — Pre-push hygiene, OWASP/BOLA/XSS auditing, SAST/SCA gates, and fail-closed quarantine.
5. **AI Systems & Knowledge Radar** — Multi-model routing, structured outputs, MCP servers, and curated open-source intelligence.

### Sovereign Autonomous PC Operator (ReAct Engine)

J.A.R.V.I.S. operates as an active, local-first autonomous agent on the Windows workstation via the **ReAct (Reasoning + Acting)** execution loop in [`tooling/agentic/pc_operator.py`](tooling/agentic/pc_operator.py). Queries trigger real-time tool calling:

- **Windows PowerShell Execution (`run_powershell`)**: Direct OS interaction for hardware diagnostics, process control, and network probes.
- **42k Repository Radar (`query_arsenal`)**: Real-time semantic queries into the indexed 42,872 curated repositories and Obsidian notes.
- **Telemetry Extraction (`get_pc_telemetry`)**: Continuous CPU, RAM, GPU, and multi-drive storage telemetry.
- **Code Workspace Editing (`read_pc_file`, `write_pc_file`)**: Safe inspection and file generation with fail-closed bounds.
- **System & Window Control (`system_control`)**: Launching desktop IDEs, browsers, terminals, and Obsidian.
- **Swarm Delegation (`dispatch_squad_agent`)**: Routing missions to 11 specialized subagents.

---

## Sovereign Arsenal: 42,872 Curated Repositories & Fast Search

J.A.R.V.I.S. indexes a sovereign library of **42,872 curated repositories and engineering tools** across a high-performance **SQLite FTS5 full-text search engine** (`arsenal_library.sqlite` on Drive `D:\` and mirrored locally in `state/`) and an autonomous **64 CART Decision Trees Random Forest classifier** (`RandomForestSovereignController`) operating with sub-millisecond local inference:

> **Measurement Boundary:** `42,872` is the row count of the maintainer's local `arsenal_library.sqlite`, which is not tracked in this repository. A clean checkout has no such database: the server then answers from the tracked `cache/starred_catalog.json` fallback, and `GET /api/arsenal/stats` reports the count of whichever source is actually loaded (`status` tells you which). Treat the figure as a description of that workstation, not as something this checkout reproduces.

```mermaid
flowchart LR
    subgraph ARSENAL["42,872 Curated Repositories (SQLite FTS5 + Random Forest)"]
        H["Hyperion (19,522 repos)<br/>Agents, Multi-Agent Swarms & LLMs"]
        S["Systems (11,489 repos)<br/>Linux, Kernel, C++, Compilers & Performance"]
        F["FullStack (6,245 repos)<br/>React, TypeScript, Next.js, UI/UX & Tailwind"]
        C["Cyberspace & Aegis (3,072 repos)<br/>AppSec, CyberSec & OSINT Recon"]
        D["DevTools (2,547 repos)<br/>CLI, Testing, Docker & DevOps"]
    end
    subgraph ENGINE["J.A.R.V.I.S. Cognitive Core"]
        RF["64 CART Trees Random Forest<br/>Sub-millisecond Intent Routing"]
        FTS["FTS5 Fast Search (sub-20ms)<br/>/api/arsenal/search"]
        ROUTER["Multi-Model Router<br/>Groq LPU · Ollama Offline · Gemini"]
        OSINT["OSINT Blackbird Probe Matrix<br/>15+ Public Platforms"]
    end
    subgraph ACCESS["Unified Access Layer"]
        HUD["Mark-LIV HUD Cockpit (:8899)"]
        REMOTE["Remote Companion Mobile (Tailscale)"]
    end

    H & S & F & C & D --> RF & FTS
    RF & FTS --> ROUTER
    ROUTER --> HUD & REMOTE
```

### Real-Time Fast Arsenal Endpoints

- **`GET /api/arsenal/stats`**: Breakdown of the tools in the loaded source (SQLite arsenal when present, otherwise the tracked catalog fallback): total, squad distribution, top languages, and flagship agents.
- **`GET /api/arsenal/search?q=<query>&squad=<squad>&limit=50`**: Sub-20ms SQLite FTS5 full-text query matching names, descriptions, and capabilities.
- **`POST /api/chat` (Sovereign Neural Routing)**: Multi-engine query resolution bridging local Random Forest (64 CART trees), Ollama models (`qwen2.5:7b`, `deepseek-r1:8b`), Groq LPUs (`qwen/qwen3.8-27b`), and async OSINT reconnaissance.

### Zero-Cost Sovereign Multi-Provider Matrix

J.A.R.V.I.S. maintains resilient multi-provider failover across top-tier AI endpoints:
- **Groq Cloud** (`qwen/qwen3.8-27b` via ultra-fast LPU inference)
- **Local Drive D: Offline** (Ollama `qwen2.5:7b` and `deepseek-r1:8b` running 100% locally)
- **OpenRouter & Cloudflare** (resilient fallback endpoints)

---

## Benchmarks & Verification

### Deterministic Context Admission Benchmark

[`benchmarks/repository_context_benchmark.py`](benchmarks/repository_context_benchmark.py) measures exact UTF-8 byte admission across a 12-source repository task fixture (`required`, `relevant`, `duplicate`, `stale`, and `irrelevant` roles):

```bash
python benchmarks/repository_context_benchmark.py
```

| Metric (`repository-context-admission-v1`) | Measured Value | Invariant |
| :--- | :---: | :--- |
| **Measurement Unit** | `serialized_utf8_bytes` | Exact UTF-8 payload accounting |
| **Naive Unbounded Payload** | `2,816 B` (12 sources) | Includes stale & irrelevant context |
| **Declared Context Budget** | `1,800 B` | Strict upper bound enforced by `compile_context()` |
| **Admitted Governed Payload** | **`1,638 B`** (7 sources) | **100%** of `required` sources preserved; `1,178 B` omitted |
| **Stale & Irrelevant Filtering** | `5` sources omitted | `stale-note.txt` + `irrelevant-*` deterministically excluded |

> **Measurement Boundary:** This benchmark reports `serialized_utf8_bytes` and deterministic source admission only; it does not claim provider token savings, latency gains, or dollar cost reductions.

### Master Verification Battery

```bash
python jarvis.py --full-test
```

The command prints a summary in this shape. The counts are produced by the run on your machine; this README does not pin them, because they change whenever a suite is added:

```text
======================================================================
     J.A.R.V.I.S. // AUTONOMOUS AGENTIC RUNTIME TEST BATTERY
  Sovereign Evolution Protocol v2.0 // Pure Python Stdlib (3.10+)
======================================================================
  Target Workspace   : <path of your checkout>
  Test Batteries     : <suites discovered> Suites
  Total Tests Run    : <count>
  Tests Passed       : <count>
  Tests Failed       : <count>
  Tests Errored      : <count>
  Execution Duration : <seconds>s
----------------------------------------------------------------------
  >>> VERDICT: <PASS | PASS_WITH_WARNINGS | FAIL>
======================================================================
```

The process exits non-zero when any suite fails or errors.

- **Python Runtime & Governance Suites:** every `tests/test_*.py` unittest module (context governor, cognitive governor, memory plane, server observability, design-system parity, information architecture, and claim auditor).
- **Node.js Cockpit & Session Entrypoints:** `tests/test_chat_session.cjs`, `tests/test_runtime_observability.cjs`, and `tests/test_operational_cockpit.cjs` (`node --test`).
- **Chromium Browser Smoke Harness:** `npm run test:browser` (`reports/v020-plan4-browser-ui-linux.json`).
- **Open-Source Packaging & Quarantine Suite:** `pwsh -File tests/Invoke-PackagingTests.ps1` (Apache-2.0 license, secret hygiene, `{USER_HOME}` schema portability, and Merkle/quarantine anchors).

---

## Direct-Evidence Governance

J.A.R.V.I.S. treats documentation accuracy as an executable test gate:

1. **No CI Theatre:** This repository **does not use GitHub Actions as a validation gate**. Hosted workflow badges never substitute for artifact-backed execution evidence.
2. **Machine-Readable Release Truth:** Current `v0.2.0` gate state lives in [`evidence/current.json`](evidence/current.json). Until fresh direct reports are recorded for the active `HEAD` across all required targets (`windows`, `linux`, `macos` for `portable-runtime`, plus `windows` for `legacy-governance`), release readiness remains `DIRECT_VALIDATION_REQUIRED` (`evidence_status: INCOMPLETE`) and the whole system is not certified as production-ready.
3. **Automated Claim Auditor:** Run [`tooling/audit_documentation_claims.py`](tooling/audit_documentation_claims.py) before every commit or pull request to verify zero unverified claims across governed docs.
4. **Public Distribution vs. Workstation Scope:** The public GitHub repository distributes the portable runtime, schemas, adapters, design system, benchmarks, and curated vault indexes cleanly, while workstation-only mounts (such as private credentials and heavy model weights) remain isolated outside Git.

---

## Repository Layout & Documentation

```text
jarvis-skill-registry/
├── jarvis.py                         # Zero-dependency Python 3.10+ CLI & HUD launcher
├── vercel.json                       # Root Vercel deployment spec for site/
├── package.json                      # Build script, metadata, keywords & browser test harness
├── tooling/
│   ├── jarvis_server.py              # Local HTTP runtime & HUD asset server
│   ├── jarvis_mcp_server.py          # 8-tool MCP JSON-RPC 2.0 server (stdio)
│   ├── audit_documentation_claims.py # Deterministic documentation claim auditor
│   ├── validate_v020_plan4.py        # Direct cross-platform evidence gate runner
│   └── agentic/                      # Context governor, cognitive governor, memory, verifier
├── adapters/                         # Platform adapters (Antigravity, Cursor IDE, Claude, Codex...)
├── site/                             # Production website (jarvis-skill-registry.vercel.app)
├── ui/                               # Mark-LIV Quantum Cockpit HUD & 3D Holographic Core
├── skills/                           # 166 canonical governed skills
├── schemas/                          # JSON-Schema contracts & platform capability matrices
├── design-system/                    # Canonical UI tokens, states & component CSS
├── benchmarks/                       # Reproducible repository_context_benchmark.py
├── governance/                       # Fail-closed quarantine-link.json & policy anchors
├── evidence/current.json             # Canonical machine-readable release & gate manifest
└── docs/README.md                    # Complete documentation index
```

Start exploring from [`docs/README.md`](docs/README.md):

- **Quickstart & Local Setup:** [`QUICKSTART.md`](QUICKSTART.md)
- **System Architecture & Merkle Core:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/ARCHITECTURE_5_LAYERS.md`](docs/ARCHITECTURE_5_LAYERS.md)
- **Runtime & Provider Security Boundary:** [`docs/architecture/RUNTIME_EXECUTION_CONTRACT.md`](docs/architecture/RUNTIME_EXECUTION_CONTRACT.md) · [`docs/architecture/SERVER_INFERENCE_BOUNDARY.md`](docs/architecture/SERVER_INFERENCE_BOUNDARY.md)
- **Adapter Authoring & Contributions:** [`docs/ADAPTER_DEVELOPMENT_GUIDE.md`](docs/ADAPTER_DEVELOPMENT_GUIDE.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Security & Fail-Closed Quarantine Policy:** [`SECURITY.md`](SECURITY.md)

---

## License

Licensed under the **Apache License, Version 2.0** — see [`LICENSE`](LICENSE) for full terms.
