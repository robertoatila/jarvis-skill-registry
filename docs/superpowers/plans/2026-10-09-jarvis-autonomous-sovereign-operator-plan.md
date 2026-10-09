# J.A.R.V.I.S. Autonomous Sovereign Operator Plan (Mark-LIV Engine)

> **Canonical Forward Plan · Formulated 2026-10-09**
> **Repository:** `robertoatila/jarvis-skill-registry`
> **Governance:** Sovereign Security Protocol v13.4 (SSP-v13.4) · Fail-Closed · Zero Secrets Leak

---

## 1. Executive Summary & Paradigm Shift

Historically, J.A.R.V.I.S. operated as a high-density, structured catalog—a "grand library" recording thousands of tool descriptions, capabilities, and tags across markdown MOCs and JSON caches.

**The Operator Mandate:**
J.A.R.V.I.S. is not a librarian. J.A.R.V.I.S. is an **Autonomous Sovereign Operator**.
An operator does not merely consult tools: it **discovers**, **weaponizes**, **adapts**, and **directly executes** tools to achieve real mission outcomes on the operating system, with deterministic safety, zero token bloat, and verified evidence.

```
       [ 1. RADAR / CATALOG ]
                 │
                 ▼
     [ 2. WEAPONIZATION (SSP-v13) ]
                 │
                 ▼
     [ 3. REAL-TIME MCP ARSENAL ]
                 │
                 ▼
  [ 4. AUTONOMOUS MISSION EXECUTOR ]
```

---

## 2. Core Architectural Pillars

### Pillar I — Sovereign Arsenal & Sub-Millisecond MCP Gateway
- **Engine:** SQLite 3 database with FTS5 Full-Text Search and compound indexes (`state/arsenal_library.sqlite`).
- **Inventory:** 19,600+ tools dynamically classified across 5 Tactical Squads:
  1. *Neuro-Cognitive:* AI, LLM frameworks, agentic runtimes, embeddings, RAG.
  2. *Hyperion:* Full-stack engineering, web frameworks, APIs, databases, cloud tooling.
  3. *Aegis:* Defensive security, encryption, identity, compliance, auditing.
  4. *Cyberspace:* Offensive security, reverse engineering, binary analysis, OSINT.
  5. *Tactical:* Kernel operations, networking, low-level system utilities.
- **Gateway:** `tooling/jarvis_mcp_server.py` serving instant queries in <3ms over stdio JSON-RPC without LLM token consumption.

### Pillar II — Autonomous Weaponization Engine (`jarvis_weaponize_repo.py`)
- **Ingestion:** Fetches upstream repository trees, specifications, and README instructions via authenticated GitHub API with automatic rate-limit backoff.
- **Static Security Audit:** Runs fail-closed regex filters detecting exfiltration webhooks, obfuscated evaluation blocks, and unauthorized network bridges before admission.
- **Distillation:** Synthesizes actionable CLI syntax, parameters, flags, and installation recipes.
- **Crystalization:** Produces production-grade canonical skills in `skills/<tool_name>/SKILL.md` registered directly in the sovereign database.

### Pillar III — Active Mission Execution & Sandboxing (`jarvis_mission_executor.py`)
- **Execution Boundary:** Operates inside isolated ephemeral staging workspaces (`staging/missions/<id>` or `D:\jarvis-arsenal\missions\<id>`).
- **Safety Invariants:**
  - Bounded timeouts (default 30s - 300s) preventing hung or zombie processes.
  - Streaming stdout/stderr capture with truncation guards.
  - Fail-closed path checking: forbids destructive commands targeting root drives or protected OS directories (`C:\Windows`, `C:\Program Files`, root volume formats).
  - Explicit exit-code validation and JSON evidence emission.

### Pillar IV — Dual Neural Architecture (OmniRoute)
- **Groq LPU:**
  - Models: `llama-3.3-70b-versatile`, `deepseek-r1-distill-llama-70b`.
  - Tactical Role: Ultra-low latency chat stream, instant JSON schema validation, rapid triage (0 Antigravity token cost).
- **Gemini Engine:**
  - Models: `gemini-2.5-flash`, `gemini-1.5-pro`.
  - Tactical Role: Deep multimodal analysis, massive codebase ingestion (1M-2M context window), audio/image forensics.
- **Local Fallback:** Ollama offline inference + pure Python deterministic heuristics.

### Pillar V — Hardware Governance & Drive Storage Strategy
- **Machine Baseline:** AMD Ryzen 3 3200G, 16 GB RAM, Windows 10/11.
- **Drive `C:\` Protection:** Constrained to 18.7 GB free space. Zero temporary downloads, heavy package caches, or large model weights written to `C:\`.
- **Drive `D:\` Allocation (1.81 TB 100% Free):** Designated for the heavy Sovereign Arsenal:
  ```text
  D:\jarvis-arsenal\
  ├── binaries\    # Standalone tools (jadx, ffmpeg, scrcpy, ripgrep, subfinder)
  ├── models\      # Quantized GGUF / Ollama models (OLLAMA_MODELS target)
  ├── cache\       # Shallow git clones and upstream source archives
  └── missions\    # Ephemeral sandboxes for heavy task execution
  ```

---

## 3. Implementation Roadmap & Execution Tasks

### Task 1: Canonical Plan Documentation & Registration (Current)
- Record the Sovereign Operator Plan in `docs/superpowers/plans/2026-10-09-jarvis-autonomous-sovereign-operator-plan.md`.
- Register the plan in canonical document index (`docs/README.md`).

### Task 2: Build the Mission Execution Engine (`tooling/jarvis_mission_executor.py`)
- Pure Python 3.12 standard library subprocess wrapper.
- Sandbox management: creates and cleans mission-specific working directories.
- Command validation: prevents dangerous OS mutations (`rmdir /s /q C:\`, formatting, raw disk writes).
- Structured output logging: generates execution receipts (`state/missions/<mission_id>/receipt.json`).

### Task 3: MCP Gateway Integration
- Expose `jarvis_execute_mission` and `jarvis_weaponize_tool` tools in `tooling/jarvis_mcp_server.py`.
- Ensure tool routing integrates with existing `tooling/agentic/tool_router.py`.

### Task 4: Contract Test Suite (`tests/test_agentic_mission_executor.py`)
- Validate timeout enforcement.
- Validate security blocklist (fail-closed behavior).
- Validate execution receipts and evidence emission.
- Run through master battery `python jarvis.py --test`.

### Task 5: Security & Invariant Audit (SSP-v13.4)
- Run `python tooling/audit_pre_publish_security.py`.
- Confirm 0 secret leaks (zero GitHub PATs, zero Groq/Gemini raw tokens in tracked files).

### Task 6: Remote GitHub Publication
- Add and stage changed files.
- Commit to branch `feat/remote-pc-command-runtime`.
- Push to origin repository `robertoatila/jarvis-skill-registry`.

---

## 4. Verification Evidence Gates

| Gate ID | Description | Command | Success Criteria |
| :--- | :--- | :--- | :--- |
| **GATE-01** | Python Doctor Baseline | `python jarvis.py --doctor` | `PASS (All modules intact)` |
| **GATE-02** | Security Audit (SSP-v13.4) | `python tooling/audit_pre_publish_security.py` | `PASS (0 Leaks)` |
| **GATE-03** | Mission Executor Tests | `python -m unittest tests/test_agentic_mission_executor.py` | `PASS (100% test approval)` |
| **GATE-04** | Master Portable Tests | `python jarvis.py --test` | `PASS` |
| **GATE-05** | Git Remote Sync | `git push origin feat/remote-pc-command-runtime` | Upstream commit verified |
