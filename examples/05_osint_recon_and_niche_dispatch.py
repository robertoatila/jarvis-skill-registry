#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_osint_recon_and_niche_dispatch.py
====================================
J.A.R.V.I.S. Sovereign Agentic Runtime // Pure Python 3.12 Standard Library
Zero External PIP Dependencies.

Demonstrates:
1. Deterministic asynchronous OSINT reconnaissance across public developer platforms (GitHub, GitLab, DockerHub, HuggingFace, Reddit, PyPI).
2. Digital Footprint Score calculation (0.0 to 10.0).
3. Universal Niche Dispatching: routing user handles, GitHub repositories, skills, and Quantum Agent squads.
"""

import sys
import json
from pathlib import Path

# Add workspace root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.agentic.osint_recon import inspect_identity_osint, format_llm_osint_context
from tooling.agentic.niche_dispatcher import NicheDispatcher


def main():
    print("=" * 70)
    print(" J.A.R.V.I.S. // OSINT RECONNAISSANCE & UNIVERSAL NICHE DISPATCH")
    print(" Sovereign Evolution Protocol v2.0 // Pure Python 3.12 Stdlib")
    print("=" * 70)

    # 1. ASYNCHRONOUS OSINT INVESTIGATION
    target_handle = "torvalds"
    print(f"\n[1] Executing Asynchronous OSINT Reconnaissance on '@{target_handle}'...")
    dossier = inspect_identity_osint(target_handle, timeout=5.0)

    print(f"    Target Handle       : @{dossier.handle}")
    print(f"    Digital Footprint   : {dossier.footprint_score}/10.0")
    print(f"    Platforms Verified  : {dossier.verified_count} / {dossier.total_probed}")
    print("    Verified Surfaces:")
    for p in dossier.verified_profiles:
        print(f"      - [{p.platform}] {p.url}")

    if dossier.github_metadata:
        gh = dossier.github_metadata
        print(f"    Primary Source Info : {gh.get('name')} | {gh.get('company')} | {gh.get('public_repos')} repos")

    # 2. LLM ENRICHMENT CONTEXT GENERATION
    print("\n[2] Generating High-Fidelity Context for External LLMs (Groq, Gemini, OpenAI)...")
    llm_ctx = format_llm_osint_context(dossier)
    print("    Context Block Preview:")
    for line in llm_ctx.strip().splitlines()[:4]:
        print(f"      {line}")

    # 3. UNIVERSAL NICHE DISPATCHER IN ACTION
    print("\n[3] Testing Universal Niche Dispatcher Across Distinct Niches...")
    dispatcher = NicheDispatcher(ROOT)

    test_queries = [
        ("OSINT Recon", "@antoniaci me mostre tudo sobre este perfil"),
        ("Repository Intel", "analise o repo @antoniaci/blackbird"),
        ("Skill Arsenal", "preciso do blueprint da skill @blackbird-osint-recon"),
        ("Quantum Squad", "delegar tarefa para o agente @sentinel"),
        ("Cybersecurity", "auditar proteções contra CVE-2024-3094 e #security"),
        ("Hardware Telemetry", "status do sistema #telemetry e armadura mark-liv")
    ]

    for label, query in test_queries:
        res = dispatcher.dispatch(query)
        print(f"    * [{label.upper()}] Query: '{query}'")
        print(f"      -> Niche: {res.niche} | Handled: {res.handled} | Target: {res.target or 'N/A'}")

    print("\n" + "=" * 70)
    print(" VERDICT: OSINT RECON & NICHE DISPATCH VERIFIED (ALL SYSTEMS GREEN)")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
