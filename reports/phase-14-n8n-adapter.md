# J.A.R.V.I.S. Skill Registry // Phase 14: n8n Adapter

- **Phase**: 14 n8n Adapter
- **Status**: **PASS**
- **Date (UTC)**: 2026-09-10T17:34:30Z
- **Commit**: `8fe7ec0`

---

## 1. Objective & Scope

Establish a sovereign bi-directional integration adapter for n8n workflow automations. Provide cryptographic HMAC-SHA256 signature verification for inbound webhook triggers, outbound execution evidence dispatching, and programmatic synthesis of copy-paste ready n8n workflow nodes.

---

## 2. Components Implemented & Reused

| Component | Status | Path | Purpose |
| :--- | :--- | :--- | :--- |
| `n8n-adapter.schema.json` | **CREATED** | `schemas/n8n-adapter.schema.json` | JSON Schema for n8n webhook triggers and outbound notifications. |
| `n8n.py` | **CREATED** | `tooling/agentic/adapters/n8n.py` | `N8nAdapter`, HMAC signature verification, and workflow generator. |
| `test_agentic_n8n.py` | **CREATED** | `tests/test_agentic_n8n.py` | Automated tests for HMAC signing, tampering detection, and workflow generation. |

---

## 3. Cryptographic Invariants Enforced

- **Constant-Time HMAC Verification**: Uses `hmac.compare_digest` to eliminate timing attacks on webhook signature validation.
- **Fail-Closed Security**: Inbound triggers with invalid or missing signatures are rejected with `PermissionError`.
- **Zero External Dependencies**: Pure Python 3.12 standard library (`hmac`, `hashlib`, `json`).

---

## 4. Verification Evidence

- **Command**: `python -m unittest tests/test_agentic_n8n.py`
- **Exit Code**: `0`
- **Results**: `4 passed, 0 failed` in `0.001s`
- **Phase Status**: `PASS`
- **Ready for Next Phase**: `15 Infrastructure Skills`
