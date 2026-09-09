# 🤝 Contributing to J.A.R.V.I.S. // Skill Registry

We love contributions! Whether you are proposing a new canonical skill, optimizing an adapter for a new agent ecosystem, reporting a bug, or polishing accessibility and UX, your help is welcome.

This project is governed by the **Sovereign Security Protocol v13 (SSP-v13)** to maintain enterprise-grade cryptographic stability, zero-leak security, and fail-closed governance.

---

## 🧭 Table of Contents

1. [Code of Conduct](#-code-of-conduct)
2. [Getting Started & Local Setup](#-getting-started--local-setup)
3. [Architecture Invariants (5 Layers)](#-architecture-invariants)
4. [Sovereign Security Protocol v13 (SSP-v13)](#-sovereign-security-protocol-v13-ssp-v13)
5. [Proposing a New Canonical Skill](#-proposing-a-new-canonical-skill)
6. [Pre-Submission Checklist](#-pre-submission-checklist)
7. [Submitting a Pull Request](#-submitting-a-pull-request)

---

## 📜 Code of Conduct

Please review our [Code of Conduct](CODE_OF_CONDUCT.md) before participating. We are committed to providing a friendly, welcoming, and harassment-free experience for everyone.

---

## 🛠️ Getting Started & Local Setup

### Prerequisites
- **Python**: 3.10+ (Python 3.12 recommended)
- **PowerShell**: PowerShell 7+ (`pwsh`) or Windows PowerShell 5.1
- **Node.js**: 18+ (optional, for starred tools sync)
- **Obsidian**: (optional, for second-brain visualization)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/skill-registry.git
cd skill-registry
```

### 2. Configure Local Environment
```bash
# Copy example configuration template (DO NOT commit real keys)
cp config/api_keys.example.json config/api_keys.json
cp .env.example .env
```

### 3. Run the Self-Test Bootstrap
```bash
pwsh -File ./tooling/Bootstrap.ps1
```

### 4. Launch J.A.R.V.I.S. Command Center HUD
```bash
# Windows
./tooling/Launch-Jarvis.vbs

# Or direct Python
python tooling/jarvis_server.py --port 8899
```
Access the Command Center at: **`http://localhost:8899`**

---

## 🏛️ Architecture Invariants

All contributions must respect the 5-Layer Core Architecture:

1. **Layer 1 — Core**: Content SHA-256 digests, Merkle Tree anchoring, and Fail-Closed Quarantine Link.
2. **Layer 2 — Intelligence**: Structural AST, capability taxonomy, and semantic deduplication.
3. **Layer 3 — Resolution**: Project stack detection, capability mapping, and deterministic lockfiles (`.lock`).
4. **Layer 4 — Distribution**: Transactional multi-platform distribution engine (Gemini, Claude, Codex, ChatGPT, Cursor, Generic).
5. **Layer 5 — Experience**: J.A.R.V.I.S. Command Center HUD, MCP server, REST API gateway, and Obsidian Cognitive Vault.

---

## 🛡️ Sovereign Security Protocol v13 (SSP-v13)

Before submitting any code, your changes must pass the **13 Invariant Security Laws**:

- **SSP13-01 // Zero Secret Leakage**: Run `python tooling/audit_pre_publish_security.py` to confirm zero active tokens or credentials exist in your PR.
- **SSP13-02 // Merkle Integrity**: Any change to active canonical skills must re-verify against the cryptographic root anchor.
- **SSP13-04 // Token Governance**: Frontmatter descriptions must be $\le 15$ words with zero embedded shell scripts in YAML.
- **SSP13-09 // WCAG 2.1 AA**: All UI elements must maintain high contrast, semantic ARIA landmarks, and `:focus-visible` keyboard accessibility.

---

## 📦 Proposing a New Canonical Skill

To contribute a new skill:

1. **Directory Structure**: Create `skills/<kebab-case-name>/SKILL.md`.
2. **Frontmatter Constraints**:
   ```yaml
   ---
   name: your-skill-name
   description: Concise, active description under 15 words explaining exactly what the tool does.
   ---
   ```
3. **Zero Placeholders**: Include working, verified scripts or references. Never include dummy or simulated code.
4. **License Compatibility**: Ensure upstream code has a permissive license (MIT, Apache-2.0, BSD).

---

## 🧪 Pre-Submission Checklist

Run these commands locally before pushing your branch:

```bash
# 1. Run Pre-Publish Security Audit (MUST Exit 0)
python tooling/audit_pre_publish_security.py

# 2. Run Test Suite
pwsh -File ./tooling/Bootstrap.ps1

# 3. Check for unstaged sensitive files
git status
```

---

## 🚀 Submitting a Pull Request

1. Create a descriptive branch: `git checkout -b feature/your-feature-name`
2. Commit your changes: `git commit -m "feat(skills): add openrouter-ai-sdk canonical skill"`
3. Push to your fork: `git push origin feature/your-feature-name`
4. Open a Pull Request on GitHub using our [PR Template](.github/PULL_REQUEST_TEMPLATE.md).
