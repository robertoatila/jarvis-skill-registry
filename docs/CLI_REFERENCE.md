# J.A.R.V.I.S. Command-Line Interface (CLI) Reference

> **Pure Python 3.12 Standard Library — Zero PIP Dependencies.**  
> Access the complete sovereign agentic runtime directly from your terminal or CI/CD pipelines.

---

## Synopsis

```bash
python -m tooling.agentic.cli <command> [options]
```

---

## Commands

### 1. `status`
Displays the real-time operational health, security posture, active profiles, and subsystem state of the sovereign runtime.

```bash
python -m tooling.agentic.cli status
```

**Output Fields:**
- `Runtime Status`: Current engine status (`OPERATIONAL`).
- `Security Mode`: Active policy mode (`FAIL_CLOSED`).
- `Registry Root`: Local workspace path.
- `State Directory`: ACID persistence path.
- `Catalog Skills`: Count of discovered Level 0 canonical skills.
- `Agent Profiles`: Count of registered Quantum Agent profiles.
- `Federation Nodes`: Count of registered sovereign cluster nodes.
- `Active Missions`: Missions currently running or in verification.

---

### 2. `plan`
Plans a goal into a Directed Acyclic Graph (DAG) with dependency ordering, capability classification, and conflict-free execution wave scheduling.

```bash
python -m tooling.agentic.cli plan --goal "<goal_description>" [--capabilities <cap1> <cap2> ...]
```

**Options:**
- `--goal` *(required)*: Text description of the engineering objective.
- `--capabilities` *(optional)*: List of required skill capabilities (defaults to `systematic-code-debugging`).

**Example:**
```bash
python -m tooling.agentic.cli plan \
  --goal "Security audit of payment service and AST dependency verification" \
  --capabilities systematic-code-debugging comprehensive-code-review
```

---

### 3. `execute`
Executes an autonomous mission through the 9-stage closed loop:
`OBSERVE → PLAN → RESOLVE → DELEGATE → EXECUTE → VERIFY → MEASURE → LEARN → ADAPT`.

```bash
python -m tooling.agentic.cli execute --goal "<goal_prompt>" [--capabilities <cap1> <cap2> ...]
```

**Options:**
- `--goal` *(required)*: Prompt defining the engineering mission.
- `--capabilities` *(optional)*: Required capabilities list.

**Exit Codes:**
- `0`: Mission succeeded, all tasks verified with cryptographic evidence.
- `1`: Mission failed or circuit breaker tripped.

**Example:**
```bash
python -m tooling.agentic.cli execute \
  --goal "Audit auth vulnerability and verify zero regression"
```

---

### 4. `lock`
Generates a cryptographically sealed, bit-for-bit reproducible skill lockfile (`skill-lock.json`) with SHA-256 Merkle root calculation.

```bash
python -m tooling.agentic.cli lock --capabilities <cap1> [cap2 ...] [--output <path>]
```

**Options:**
- `--capabilities` *(required)*: Capabilities to resolve and lock.
- `--output` *(optional)*: Path to output file (defaults to `state/skill-lock.json`).

**Example:**
```bash
python -m tooling.agentic.cli lock \
  --capabilities systematic-code-debugging comprehensive-code-review \
  --output state/my-skill-lock.json
```

---

### 5. `test`
Executes the complete sovereign system test battery across all 30 test suites.

```bash
python -m tooling.agentic.cli test
```

**Exit Codes:**
- `0`: All test suites passed (`166/166 PASS`).
- `1`: One or more tests failed.

---

### 6. `audit`
Executes the pre-publish security audit scanner verifying that no secrets, credentials, or personal tokens are present in public repository files.

```bash
python -m tooling.agentic.cli audit
```

**Exit Codes:**
- `0`: Approved for publishing (100% secure, zero leaks, 14/14 invariants active).
- `1`: Security policy violation detected.

---

### 7. `osint`
Runs deterministic asynchronous OSINT reconnaissance across public platforms (GitHub, GitLab, DockerHub, HuggingFace, Reddit, PyPI, Dev.to, Gravatar) and calculates a digital footprint score.

```bash
python -m tooling.agentic.cli osint <handle>
```

**Example:**
```bash
python -m tooling.agentic.cli osint torvalds
```

---

### 8. `niche`
Dispatches an arbitrary query or `@mention` through the universal multi-niche engine (OSINT, Repo Intel, Skill Arsenal, Quantum Squads, Cybersecurity, Hardware Telemetry).

```bash
python -m tooling.agentic.cli niche "<query>"
```

**Examples:**
```bash
python -m tooling.agentic.cli niche "@antoniaci/blackbird"
python -m tooling.agentic.cli niche "@sentinel"
python -m tooling.agentic.cli niche "@blackbird-osint-recon"
```

