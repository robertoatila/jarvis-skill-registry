# Skill Registry — Chaos Engineering & Resilience Verification

**Version:** 1.0.0 (Phase 24 Edition)

---

## 1. Chaos Simulation Scenarios

The registry includes automated chaos testing harnesses (`Invoke-RegistryChaosTest`) to prove resilience under extreme fault conditions:

| Scenario ID | Injected Fault | Expected Recovery Behavior | Verified Result |
| :--- | :--- | :--- | :--- |
| **CHAOS-01** | Truncated partial JSON line in index ledger | Automatic detection during startup; line truncated to last valid JSON object. | `PASS` |
| **CHAOS-02** | Dangling filesystem `.lock` from killed PID | `Test-RegistryLocks` detects dead PID; evicts lock without operator intervention. | `PASS` |
| **CHAOS-03** | Bit-flip in file payload under active deployment | `Test-RegistryDeploymentHealth` detects SHA-256 hash mismatch; triggers rollback. | `PASS` |
| **CHAOS-04** | Tampered quarantine anchor file | Core halts immediately in fail-closed state (`QuarantineGuardException`). | `PASS` |

---

## 2. Executing Chaos Resilience Tests

```powershell

# Run the built-in chaos suite

skillctl admin chaos

```
