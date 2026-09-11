# J.A.R.V.I.S. Runnable Examples

> **Pure Python 3.12 Standard Library — Zero `pip install` required.**
> Every example in this directory runs standalone with 100% deterministic reproducibility.

---

## Table of Contents

1. [Example 01: Quickstart Autonomous Mission](#example-01-quickstart-autonomous-mission)
2. [Example 02: Fail-Closed Security Guardrails](#example-02-fail-closed-security-guardrails)
3. [Example 03: Bayesian Fitness & Evolution](#example-03-bayesian-fitness--evolution)
4. [Example 04: Lockfile & Merkle Verification](#example-04-lockfile--merkle-verification)

---

### Example 01: Quickstart Autonomous Mission
Demonstrates initializing the sovereign runtime, planning a mission DAG, scheduling conflict-free execution waves, executing across the 9-stage closed loop, and verifying cryptographic evidence artifacts.

```bash
python examples/01_quickstart_autonomous_mission.py
```

**Key Concepts:**
- 9-Stage Sovereign Loop: `OBSERVE → PLAN → RESOLVE → DELEGATE → EXECUTE → VERIFY → MEASURE → LEARN → ADAPT`.
- Wave-based concurrency with read/write scope isolation.
- Cryptographic artifact generation and verification.

---

### Example 02: Fail-Closed Security Guardrails
Demonstrates the SSP-v13.2 Fail-Closed Policy Engine, enforcing the R0-R5 risk taxonomy, workspace boundary confinement, fail-closed blocking of R5 destructive actions (code 126), and strict non-self-approval gates for R4 infrastructure mutations.

```bash
python examples/02_fail_closed_security_guardrails.py
```

**Key Concepts:**
- R0–R5 Risk Classification.
- Workspace path confinement (blocking directory traversal).
- Anti-Self-Approval: Autonomous agents cannot sign off on their own mutations.

---

### Example 03: Bayesian Fitness & Evolution
Demonstrates the multi-dimensional skill fitness engine with Bayesian cold-start prior (`COLD_START_PRIOR = 0.75`), reproducible hash-based A/B variant experimentation, and the 3-tier knowledge promotion lifecycle (`OBSERVATION` $\to$ `PATTERN` $\to$ `VALIDATED_HEURISTIC`).

```bash
python examples/03_bayesian_fitness_and_evolution.py
```

**Key Concepts:**
- Unknown skills are never penalized to 0.0.
- Context hash guarantees identical assignments across executions.
- Anti-hasty generalization: Single-run execution is rejected fail-closed for promotion.

---

### Example 04: Lockfile & Merkle Verification
Demonstrates deterministic capability resolution, cryptographic lockfile generation (`skill-lock.json`), SHA-256 Merkle root calculation, and bit-level tamper detection.

```bash
python examples/04_lockfile_and_merkle_verification.py
```

**Key Concepts:**
- Bit-for-bit reproducible environments.
- SHA-256 Merkle root verification.
- Tampered content is instantly caught and rejected fail-closed.
