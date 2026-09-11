"""
examples/04_lockfile_and_merkle_verification.py
===============================================
J.A.R.V.I.S. Autonomous Agentic Runtime // Protocol v2.0
Zero PIP Dependencies // Pure Python 3.12 Standard Library

This example demonstrates:
  1. Deterministic resolution of capabilities to canonical skills.
  2. Cryptographic lockfile generation (skill-lock.json) with SHA-256 Merkle root.
  3. Verifying lockfile integrity against bit-level corruption or tampering.
  4. Fail-closed rejection when tamper or hash mismatch is detected.
"""

from __future__ import annotations
import sys
import json
from pathlib import Path

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic.config import JarvisRuntimeConfig
from tooling.agentic.package_manager import CognitivePackageManager


def main():
    print("=" * 70)
    print("  J.A.R.V.I.S. // EXAMPLE 04: LOCKFILE & MERKLE VERIFICATION")
    print("=" * 70)

    config = JarvisRuntimeConfig(registry_root=_REPO_ROOT)
    pkg_mgr = CognitivePackageManager(config=config)
    lockfile_path = config.state_dir / "example-skill-lock.json"

    # 1. Generate Lockfile
    capabilities = ["systematic-code-debugging", "comprehensive-code-review"]
    print(f"[*] Section 1: Generating Lockfile for Capabilities: {capabilities}")
    lock = pkg_mgr.generate_lockfile(
        workspace_root=config.registry_root,
        capabilities=capabilities,
        lockfile_path=lockfile_path
    )

    print(f"    - Lockfile Path  : {lockfile_path}")
    print(f"    - Lock ID        : {lock['lock_id']}")
    print(f"    - Merkle Root    : {lock['integrity']['merkle_root']}")
    print(f"    - Resolved Skills: {[s['id'] for s in lock['skills']]}")

    # 2. Verify Valid Lockfile
    print("\n[*] Section 2: Cryptographic Verification (Unmodified Lockfile)")
    is_valid, errors = pkg_mgr.verify_lockfile(lockfile_path)
    print(f"    - Verification Result : {'PASS' if is_valid else 'FAIL'}")
    print(f"    - Errors              : {errors if errors else 'None (Bit-for-bit intact)'}")
    assert is_valid is True, "Authentic lockfile must verify successfully!"
    print("    >>> Merkle Integrity Verified: 100% authentic and untampered.")

    # 3. Simulate Malicious Tamper
    print("\n[*] Section 3: Tamper Detection (Fail-Closed Anti-Tamper Test)")
    tampered_lockfile_path = config.state_dir / "tampered-skill-lock.json"
    tampered_data = dict(lock)
    # Modify a skill content hash maliciously
    tampered_data["skills"][0]["canonical_content_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"
    tampered_lockfile_path.write_text(json.dumps(tampered_data, indent=2), encoding="utf-8")

    tamper_valid, tamper_errors = pkg_mgr.verify_lockfile(tampered_lockfile_path)
    print(f"    - Tampered Lockfile   : {tampered_lockfile_path.name}")
    print(f"    - Verification Result : {'PASS' if tamper_valid else 'FAIL (BLOCKED)'}")
    print(f"    - Detected Errors     : {tamper_errors}")
    assert tamper_valid is False, "Tampered lockfile MUST fail verification!"
    print("    >>> Invariant Verified: Merkle hash mismatch detected and blocked fail-closed.")

    # Clean up test artifacts
    if tampered_lockfile_path.exists():
        tampered_lockfile_path.unlink()
    if lockfile_path.exists():
        lockfile_path.unlink()

    print("\n" + "=" * 70)
    print(">>> SUCCESS: Lockfile & Merkle Verification Verified Deterministically!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
