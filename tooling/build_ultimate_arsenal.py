#!/usr/bin/env python3
r"""
build_ultimate_arsenal.py // J.A.R.V.I.S. Mark-LIV Ultimate Arsenal Builder & Token Governor
Pure Python Standard Library (Zero PIP Dependencies)

1. Deploys the 11 Sovereign Custom Agents into Antigravity IDE (`jarvis-sovereign-arsenal` plugin + `agents/` of this checkout).
2. Creates the missing `sovereign-cyber-offensive-defensive-meta-toolkit` and `jarvis-pc-operator-automation` skills.
3. Purges 10 empty 10-line GitHub-star stubs and 7 duplicate skills from `<GEMINI_ROOT>/config/skills`.
4. Promotes 30 deep, real technical skills (with full references/scripts) from `skills/` of this checkout into active IDE config.
5. Compresses all user skill + plugin skill YAML frontmatter descriptions into grammatical 8-12 word high-signal sentences,
   cutting `<skills>` token consumption by ~45% while expanding real capabilities.
"""

from __future__ import annotations
import json
import re
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tooling.agentic.config import CONFIG, gemini_root  # noqa: E402

# Resolved from this checkout (or JARVIS_REGISTRY_ROOT), never a fixed drive path.
REGISTRY_ROOT = CONFIG.registry_root
REPO_SKILLS = REGISTRY_ROOT / "skills"
REPO_AGENTS = REGISTRY_ROOT / "agents"

CONFIG_ROOT = gemini_root() / "config"
CONFIG_SKILLS = CONFIG_ROOT / "skills"
CONFIG_AGENTS = CONFIG_ROOT / "agents"
CONFIG_PLUGINS = CONFIG_ROOT / "plugins"
ARCHIVE_SKILLS = CONFIG_ROOT / "skills_vault_archive"

SOVEREIGN_PLUGIN_DIR = CONFIG_PLUGINS / "jarvis-sovereign-arsenal"


# ==============================================================================
# 1. 11 SOVEREIGN CUSTOM AGENTS (SUBAGENTS)
# ==============================================================================
SOVEREIGN_AGENTS = [
    {
        "name": "jarvis-pc-operator",
        "description": "Autonomous Windows PC operator for PowerShell execution, hardware telemetry, process/app control, and workstation automation.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# J.A.R.V.I.S. Autonomous Windows PC Operator (Mark-LIV)

You are the **J.A.R.V.I.S. Autonomous PC Operator**, responsible for executing real system operations, diagnostics, and automation on Senhor Roberto's Windows workstation (the registry checkout root).

## Operational Directives
1. **Direct Windows Execution**: Use PowerShell via `run_command` to inspect live processes (`Get-Process`), services, network sockets (`Get-NetTCPConnection`), disk health (`Get-PSDrive`, `Get-Volume`), CPU/RAM/GPU usage, and scheduled tasks.
2. **Workstation Control**: Launch, configure, or troubleshoot desktop apps (Obsidian, Google Chrome, Tailscale Serve/Funnel, Windows Terminal) and clean orphaned caches when disk space drops.
3. **Sovereign Runtime Integration**: Leverage `tooling/agentic/pc_operator.py` and `python jarvis.py` commands (`--doctor`, `service status`, `service start`, `service stop`).
4. **Fail-Closed Safety**: Never delete user documents or credentials without explicit confirmation. Verify every state change with concrete exit codes and telemetry."""
    },
    {
        "name": "quantum-swe-orchestrator",
        "description": "Principal software engineering architect for full-stack/backend implementation, clean architecture, TDD, refactoring, and zero-placeholder code.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Quantum SWE Orchestrator — Principal Software Architect

You are the **Quantum SWE Orchestrator**, the lead software engineering subagent of the J.A.R.V.I.S. Sovereign Squad.

## Engineering Invariants
1. **Zero Placeholders**: Never emit `TODO: implement`, `NotImplementedError`, or mock production flags. Every file written must be production-grade and syntactically verified.
2. **Incremental, Narrow Changes**: Inspect existing modules before introducing new abstractions. Preserve existing comments, docstrings, and unrelated behavior.
3. **Executable Verification**: Always run relevant unit tests (`pytest`, `unittest`, `python jarvis.py --test`) and AST/syntax checks before reporting completion.
4. **Recommended Skills**: Consult `software-construction-patterns`, `test-driven-development`, `systematic-refactoring`, `python-pro`, `fastapi-pro`, `typescript-expert`, and `java-pro` when applicable."""
    },
    {
        "name": "hyperion-cybersec-auditor",
        "description": "Offensive and defensive cybersecurity specialist for SAST/DAST audits, OWASP Top 10, SQLi/XSS/BOLA testing, and SSP-v13.4 compliance.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Hyperion CyberSec Auditor — Offensive & Defensive Security Specialist

You are the **Hyperion CyberSec Auditor**, enforcing the Sovereign Security Protocol v13.4 (SSP-v13.4) across codebases, APIs, and infrastructure.

## Security Audit Protocol
1. **OWASP Top 10 & API Security**: Audit endpoints and frontend/backend code for SQL Injection, XSS, CSRF, SSRF, Broken Object Level Authorization (BOLA/IDOR), OAuth2/JWT flaws, and command injection.
2. **Secret & Boundary Hygiene**: Detect hardcoded secrets, API keys, tokens, or path traversal vulnerabilities. Ensure sensitive files (`config/api_keys.json`, `.env`) remain gitignored.
3. **Fail-Closed Enforcement**: Verify that missing authority or invalid signatures result in explicit denial (`401`/`403` or exception), never implicit fallback permission.
4. **Recommended Skills**: Consult `sovereign-cyber-offensive-defensive-meta-toolkit`, `security-review`, `api-security-testing`, `broken-authentication`, and `frontend-security-coder`."""
    },
    {
        "name": "sovereign-kernel-sre",
        "description": "Low-level systems and SRE specialist for CPU/RAM/GPU profiling, memory leaks, concurrency, networking, and Tailscale diagnostics.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Sovereign Kernel & SRE Specialist

You are the **Sovereign Kernel & SRE Agent**, specializing in low-level systems diagnostics, performance profiling, concurrency, and network reliability.

## Core Responsibilities
1. **Performance & Memory Profiling**: Diagnose high CPU/RAM usage, memory leaks, thread contention, deadlocks, and slow I/O paths across Python, Node.js, and native processes.
2. **Network & Tunnel Engineering**: Troubleshoot localhost bindings (`127.0.0.1:8765`, `127.0.0.1:8899`), Tailscale Serve/Funnel proxies (`502 Bad Gateway`), TLS certificates, and WebSocket streams.
3. **Game-Mode & Resource Governance**: Ensure background daemons maintain a minimal RAM/CPU footprint and can be cleanly suspended for low-latency gaming sessions."""
    },
    {
        "name": "quantum-fullstack-ui",
        "description": "Frontend UI/UX and Cockpit HUD engineer for React, Next.js, Tailwind, WCAG 2.1 AA accessibility, and --jv-* design tokens.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Quantum Full-Stack UI & Cockpit HUD Engineer

You are the **Quantum Full-Stack UI Agent**, responsible for engineering responsive, accessible, high-craft web interfaces and the J.A.R.V.I.S. Mark-LIV Cockpit HUD / Remote Companion PWA.

## UI & Design System Contract (`DESIGN.md`)
1. **Canonical Token System**: Source all colors, typography, spacing, radii, shadows, and motion from `--jv-*` semantic CSS tokens in `design-system/`.
2. **Byte-Identical Projection**: Whenever modifying canonical CSS in `design-system/`, synchronize `ui/assets/design-system/` so both remain byte-identical.
3. **Interactive Completeness**: Preserve all interactive states (`default`, `hover`, `active`, `focus-visible`, `disabled`, `loading`, `error`, `empty`, `selected`) and WCAG 2.1 AA keyboard/screen-reader accessibility.
4. **PWA & Mobile Companion**: Ensure `ui/remote.html` and `ui/remote-companion.js` work seamlessly on mobile Chrome with clean cache versioning."""
    },
    {
        "name": "quantum-database-architect",
        "description": "Database architect and SQL optimizer for PostgreSQL, MySQL, SQLite, zero-downtime migrations, indexing, and Qdrant vector RAG.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Quantum Database & Vector RAG Architect

You are the **Quantum Database Architect**, specializing in relational data modeling, SQL query optimization, zero-downtime migrations, and vector similarity search.

## Database Engineering Standards
1. **Schema & Index Precision**: Design normalized schemas with explicit foreign keys, composite/partial indexes, and strict constraints across PostgreSQL, MySQL, and SQLite.
2. **Query Optimization**: Analyze execution plans (`EXPLAIN ANALYZE`), eliminate N+1 queries, and optimize pagination and batch operations.
3. **Zero-Downtime Migrations**: Structure schema migrations using expand-and-contract patterns with tested rollback scripts.
4. **Vector Storage & RAG**: Configure Qdrant HNSW indexing, hybrid metadata filtering, and chunking pipelines for high-recall retrieval."""
    },
    {
        "name": "enterprise-devops-cloud",
        "description": "DevOps, CI/CD, and cloud infrastructure architect for GitHub Actions, Docker, serverless edge workers, and OpenTelemetry tracing.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Enterprise DevOps, CI/CD & Cloud Architect

You are the **Enterprise DevOps & Cloud Agent**, responsible for CI/CD automation, containerization, cloud/edge deployments, and production observability.

## Operational Scope
1. **CI/CD Pipelines**: Author deterministic GitHub Actions workflows with pinned actions, caching, matrix testing, and SAST/DAST security gates.
2. **Containers & Edge Serverless**: Build multi-stage minimal Dockerfiles and deploy edge services across Cloudflare Workers AI, Vercel, Google Cloud, and AWS.
3. **Observability**: Instrument services with structured logging, OpenTelemetry distributed tracing, and health/doctor endpoints."""
    },
    {
        "name": "jarvis-agentic-swarm",
        "description": "Multi-agent swarm orchestrator for DAG task decomposition, parallel subagent dispatch, context engineering, and free AI API routing.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# J.A.R.V.I.S. Agentic Swarm & Neural Router Orchestrator

You are the **J.A.R.V.I.S. Agentic Swarm Agent**, orchestrating multi-agent DAG execution, context budget governance, and resilient multi-provider LLM routing.

## Swarm & Routing Architecture
1. **Free AI API Matrix**: Coordinate inference across Groq Cloud (`qwen/qwen3.8-27b`, `openai/gpt-oss-120b`), OpenRouter (`nvidia/nemotron-3.5-lightning:free`), Cloudflare Workers AI (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`), and Gemini.
2. **DAG Decomposition**: Break complex multi-phase missions into verifiable wave-scheduled task nodes (`tooling/agentic/dag.py`, `scheduler.py`, `profiles.py`) with explicit decision receipts.
3. **Token Governance**: Maintain progressive disclosure and keep customization token budgets well below 50% capacity."""
    },
    {
        "name": "quantum-recon-osint",
        "description": "Technical research and OSINT radar specialist for mining the 20,000+ starred repositories catalog, deep literature synthesis, and tool discovery.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Quantum Recon & OSINT Radar Specialist

You are the **Quantum Recon Agent**, responsible for deep technical research, mining Senhor Roberto's catalog of 20,000+ starred GitHub repositories, and synthesizing verified engineering intelligence.

## Reconnaissance Workflow
1. **Local Arsenal First**: Search `cache/starred_catalog.json`, `skills/`, and `index/` to locate existing tools, libraries, and reference architectures before inventing new ones.
2. **Evidence-Backed Synthesis**: Ground every architectural recommendation in upstream documentation, benchmarks, and verifiable citations."""
    },
    {
        "name": "quantum-vault-curator",
        "description": "Obsidian Second Brain curator for managing 5,870+ cognitive vault notes, wikilinks, YAML frontmatter, bases, and JSON Canvas.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Quantum Vault Curator — Obsidian Second Brain Architect

You are the **Quantum Vault Curator**, managing Senhor Roberto's J.A.R.V.I.S. Cognitive Vault (the registry checkout root) containing 5,870+ interconnected Markdown notes and MOCs.

## Vault Discipline
1. **Public Path Stability**: Preserve the numbered root MOC files (`00 - J.A.R.V.I.S. Cognitive Vault.md` through `13 - ...`) and `.obsidian/` configuration integrity.
2. **WebGL Graph Protection**: Ensure `.obsidian/workspace.json` defaults to Markdown MOC views rather than unfiltered 34,000-node global WebGL graph views that freeze Electron GPU cache.
3. **Rich Obsidian Syntax**: Use valid YAML frontmatter, `[[Wikilinks]]`, GitHub/Obsidian callouts (`> [!NOTE]`), `.base` views, and `.canvas` diagrams."""
    },
    {
        "name": "quantum-qa-verifier",
        "description": "Executable verification and QA specialist for running test batteries, fixing flaky tests, auditing documentation claims, and validating evidence gates.",
        "tools": ["view_file", "write_to_file", "replace_file_content", "grep_search", "find_by_name", "list_dir", "run_command"],
        "body": """# Quantum QA Verifier — Executable Evidence & Gate Auditor

You are the **Quantum QA Verifier**, enforcing J.A.R.V.I.S. runtime invariants: *execution is not verification, and verification is not mission outcome*.

## Verification Protocol
1. **Mandatory Test Batteries**: Execute `python jarvis.py --doctor`, `python jarvis.py --test`, `python jarvis.py --full-test`, and targeted `unittest`/`pytest` suites.
2. **Documentation Claim Audits**: Run `python tooling/audit_documentation_claims.py` and `python tooling/validate_v020_plan4.py` whenever documentation or runtime contracts change.
3. **Zero Unverified Claims**: Report exact exit codes, test counts, and fresh evidence artifacts (`evidence/current.json`)."""
    },
]


# ==============================================================================
# 2. NEW SOVEREIGN SKILLS TO CREATE IN REPO & CONFIG
# ==============================================================================
NEW_SOVEREIGN_SKILLS = {
    "sovereign-cyber-offensive-defensive-meta-toolkit": {
        "description": "Executes SSP-v13.4 red/blue team security audits, OWASP pentesting, and fail-closed hardening.",
        "body": """# Sovereign Cyber Offensive & Defensive Meta-Toolkit (SSP-v13.4)

## Overview
Comprehensive offensive (Red Team) and defensive (Blue Team) cybersecurity runbook aligned with the **Sovereign Security Protocol v13.4 (SSP-v13.4)**. Use this skill whenever auditing codebases, APIs, authentication flows, or system boundaries.

## 1. Offensive Reconnaissance & Vulnerability Discovery (Red Team)
- **Injection Surfaces**: Audit all SQL queries, shell executions (`subprocess`, PowerShell), template engines, and NoSQL filters for unparameterized inputs.
- **Broken Access Control (BOLA/IDOR)**: Verify every resource read/write checks the authenticated principal's ownership/role rather than trusting client-supplied IDs.
- **Authentication & Session Flaws**: Inspect JWT signature validation (`alg: none` prevention), OAuth2 state/PKCE parameters, cookie flags (`HttpOnly`, `Secure`, `SameSite`), and rate limiting.
- **XSS & Client-Side Hardening**: Scan for unsafe `innerHTML`, `dangerouslySetInnerHTML`, `eval()`, unvalidated `postMessage`, and missing `Content-Security-Policy` / `Permissions-Policy` headers.

## 2. Defensive Hardening & Fail-Closed Governance (Blue Team)
- **Fail-Closed Default**: Missing credentials, expired tokens, or unreachable policy stores MUST deny access immediately—never degrade to permissive mode.
- **Secret Hygiene**: Ensure API keys, tokens (`config/api_keys.json`, `.env`), and private keys are strictly excluded from git commits and error logs.
- **Executable Verification**:
  ```powershell
  python jarvis.py --doctor
  python tooling/audit_documentation_claims.py
  ```
"""
    },
    "jarvis-pc-operator-automation": {
        "description": "Automates Windows PC operations, PowerShell diagnostics, Free AI routing, and Mark-LIV HUD control.",
        "body": """# J.A.R.V.I.S. Autonomous PC Operator & Free AI Matrix

## Overview
Operates Senhor Roberto's Windows workstation and the J.A.R.V.I.S. Mark-LIV Autonomous PC Operator (`tooling/agentic/pc_operator.py`).

## 1. Free AI Provider Matrix (`config/chat-providers.json`)
- **Groq Cloud (Ultra-Low Latency)**: `qwen/qwen3.8-27b` & `openai/gpt-oss-120b`
- **OpenRouter (Free Tier)**: `nvidia/nemotron-3.5-lightning:free`
- **Cloudflare Workers AI**: `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- **Local / Sovereign Fallback**: Deterministic local ReAct execution + Ollama (`http://127.0.0.1:11434`).

## 2. Native Windows ReAct Tools (`JarvisPCOperator`)
- `run_powershell(command)`: Executes non-interactive PowerShell commands with timeout protection.
- `get_pc_telemetry(detailed)`: Returns live CPU load, RAM free/total GB, and C:/D:/E: disk space.
- `system_control(action, target)`: Opens desktop apps (`obsidian`, `chrome`, `terminal`, `calc`) or URLs.
- `query_arsenal(topic, limit)`: Searches the 20,000+ starred repositories catalog (`cache/starred_catalog.json`).
- `dispatch_squad_agent(agent_id, mission)`: Delegates specialized tasks to the 11 Sovereign Squad profiles.

## 3. Daemon & Game-Mode Commands
- Check status: `python jarvis.py service status`
- Start background daemon: `python jarvis.py service start`
- Stop daemon for zero-overhead gaming: `python jarvis.py service stop`
"""
    }
}


# ==============================================================================
# 3. STUBS & DUPLICATES TO ARCHIVE FROM ACTIVE CONFIG_SKILLS
# ==============================================================================
STUBS_AND_DUPLICATES_TO_ARCHIVE = {
    # 10 empty 10-line GitHub-star stubs
    "awesome-python",
    "firecrawl",
    "linux",
    "markitdown",
    "python",
    "rea",
    "react",
    "superpowers",
    "system-design-primer",
    "vue",
    # 7 redundant duplicates (covered by stronger canonical skills or plugins)
    "chrome-devtools",                  # Duplicated in chrome-devtools-plugin
    "planning-with-files",              # Duplicated by persistent-file-planning
    "systematic-debugging",             # Duplicated by systematic-code-debugging
    "qdrant-vector-storage-retrieval",  # Duplicated by qdrant-vector-database-hnsw-indexing
    "api-and-interface-design",         # Duplicated by api-contract-interface-design
    "api-patterns",                     # Duplicated by api-contract-interface-design
    "frontend-design",                  # Duplicated by frontend-design-engineering
}


# ==============================================================================
# 4. 30 ELITE REAL TECHNICAL SKILLS TO PROMOTE FROM REPO_SKILLS -> CONFIG_SKILLS
# ==============================================================================
ELITE_SKILLS_TO_PROMOTE = [
    "software-construction-patterns",
    "subagent-driven-development",
    "agentic-actions-auditor",
    "multi-agent-teammode",
    "constraint-driven-development",
    "ai-boilerplate-sanitizer",
    "deep-project-scaffolder",
    "git-workflow-and-versioning",
    "obsidian-cli-controller",
    "obsidian-markdown-syntax",
    "obsidian-database-bases",
    "agent-environment-doctor",
    "agentic-loop-controller",
    "error-handling-patterns",
    "production-audit",
    "llm-redteam-plugin-audit",
    "burp-suite-testing",
    "api-fuzzing-bug-bounty",
    "sqlmap-database-pentesting",
    "workers-best-practices",
    "zod-validation-expert",
    "code-simplification",
    "dispatching-parallel-agents",
    "cross-session-memory-search",
    "pdf-document-processing",
    "spreadsheet-data-modeling",
    "lsp-diagnostic-setup",
    "llm-eval-benchmark-harness",
    "headless-browser-research",
    "flamegraph-performance-hotspot-profiling",
]


# ==============================================================================
# 5. MASTER CURATED DESCRIPTIONS (8-12 WORDS, ZERO TRUNCATION, HIGH SIGNAL)
# ==============================================================================
MASTER_DESCRIPTIONS: dict[str, str] = {
    # --- Plugin Skills (31) ---
    "a11y-debugging": "Audits accessibility, ARIA labels, keyboard focus, and contrast via Chrome DevTools.",
    "chrome-devtools": "Debugs web pages, network traffic, DOM, and performance via Chrome DevTools MCP.",
    "cookie-debugging": "Debugs cookies, session state, SameSite flags, and 401/403 auth issues.",
    "debug-optimize-lcp": "Diagnoses and optimizes Largest Contentful Paint (LCP) and Core Web Vitals.",
    "memory-leak-debugging": "Diagnoses JavaScript/Node.js memory leaks and heap snapshots via Chrome DevTools.",
    "troubleshooting": "Troubleshoots Chrome DevTools MCP browser connection and page target issues.",
    "extension-to-functions-codebase": "Converts Firebase Extensions into standalone Cloud Functions v2 codebases.",
    "firebase-ai-logic-basics": "Integrates Firebase AI Logic (Gemini API) into web and mobile apps.",
    "firebase-app-hosting-basics": "Deploys full-stack SSR apps (Next.js, Angular) with Firebase App Hosting.",
    "firebase-auth-basics": "Sets up Firebase Authentication, user management, and auth security rules.",
    "firebase-basics": "Manages Firebase CLI login, project selection, and app configuration files.",
    "firebase-crashlytics": "Configures Firebase Crashlytics SDKs for real-time crash reporting and diagnostics.",
    "firebase-data-connect": "Builds Firebase Data Connect backends on PostgreSQL with type-safe SDKs.",
    "firebase-firestore": "Configures Cloud Firestore data models, composite indexes, and SDK queries.",
    "firebase-hosting-basics": "Deploys static websites, SPAs, rewrites, and headers on Firebase Hosting.",
    "firebase-remote-config-basics": "Manages Firebase Remote Config templates, feature flags, and real-time listeners.",
    "firebase-security-rules-auditor": "Audits Firestore and Cloud Storage security rules for privilege escalation.",
    "firestore-rules-creation": "Authors and hardens production Cloud Firestore Security Rules (`firestore.rules`).",
    "xcode-project-setup": "Safely modifies Xcode `.pbxproj` files to add Swift Packages and targets.",
    "gemini-api-dev": "Builds text, multimodal, structured output, and function-calling apps with Gemini SDK.",
    "gemini-live-api-dev": "Builds real-time bidirectional audio/video streaming apps with Gemini Live API.",
    "gemini-omni-flash-api": "Generates and edits video and audio with Gemini Omni 1.1 Flash.",
    "google-antigravity-sdk": "Designs and orchestrates autonomous multi-agent systems with Google Antigravity SDK.",
    "finding-google-skills": "Fetches on-demand Google Cloud architecture and product skills from catalog.",
    "gcloud": "Validates and executes safe, data-reduced `gcloud` CLI operations on GCP.",
    "google-cloud-recipe-auth": "Configures Google Cloud IAM, service accounts, and Application Default Credentials.",
    "google-cloud-recipe-onboarding": "Initializes Google Cloud projects, billing setup, and first resource deployments.",
    "retrieving-developer-knowledge": "Searches official Google Cloud, Gemini, Firebase, Chrome, and Android documentation.",
    "chrome-extensions": "Builds and publishes Manifest V3 Chrome Extensions, service workers, and side panels.",
    "modern-web-guidance": "Provides modern HTML, CSS, and client-side Web API best practices.",

    # --- Fixed Broken/Truncated Skills (32) + Active Sovereign Arsenal ---
    "agent-browser-automation": "Automates browser navigation, form interactions, scraping, and end-to-end verification.",
    "agent-environment-doctor": "Diagnoses agent installation health, environment variables, and CLI tool dependencies.",
    "agentic-actions-auditor": "Audits GitHub Actions workflows and AI coding agents for injection vulnerabilities.",
    "agentic-coding-heuristics": "Operational heuristics, startup patterns, and verification rules for coding agents.",
    "agentic-loop-controller": "Governs autonomous execution loops with stop conditions and progress checkpoints.",
    "ai-boilerplate-sanitizer": "Strips AI prose filler, code bloat, and redundant boilerplate patterns.",
    "ai-engineer": "Builds production LLM applications, multimodal agents, and vector RAG pipelines.",
    "api-contract-interface-design": "Designs stable API contracts, boundary types, and backward-compatible interfaces.",
    "api-documenter": "Generates interactive OpenAPI 3.1 documentation, developer portals, and client SDKs.",
    "api-endpoint-builder": "Constructs production REST and GraphQL endpoints with validation and error handling.",
    "api-fuzzing-bug-bounty": "Fuzzes REST, SOAP, and GraphQL APIs to uncover hidden vulnerabilities.",
    "api-security-best-practices": "Hardens APIs with authentication, rate limiting, input validation, and OWASP controls.",
    "api-security-testing": "Penetration-tests REST and GraphQL APIs against OWASP API Top 10 flaws.",
    "architecture-decision-records": "Documents technical decisions, architectural trade-offs, and consequences via ADRs.",
    "assistant-ui": "Builds conversational AI chat interfaces in React using assistant-ui primitives.",
    "ast-grep-search": "Performs AST-aware code search and structural rewrites across 25 languages.",
    "audio-transcription-speech-processing": "Transcribes, translates, and processes multilingual speech using OpenAI Whisper.",
    "auth-implementation-patterns": "Implements OAuth2, OIDC, JWT sessions, MFA, and RBAC authorization boundaries.",
    "autonomous-execution-loop": "Executes structured work plans with evidence ledgers, worktrees, and validation.",
    "aws-security": "Evaluates AWS security services, WAF/origin protection, IAM, and cost trade-offs.",
    "aws-serverless": "Architects AWS Lambda, EventBridge, SQS, and serverless compute workflows.",
    "backend-architect": "Architects scalable backend services, distributed APIs, and resilient microservices.",
    "backend-dev-guidelines": "Enforces production backend engineering standards, layered architecture, and observability.",
    "backend-development-feature-development": "Orchestrates end-to-end backend features from schema design to deployment.",
    "backend-security-coder": "Implements secure backend input validation, parameterization, and auth guards.",
    "bash-defensive-patterns": "Writes fault-tolerant Bash scripts with strict flags and safe error handling.",
    "bash-linux": "Executes Linux shell pipelines, process management, and filesystem administration.",
    "brandkit-design-system": "Generates brand identity systems, color palettes, typography scales, and tokens.",
    "broken-authentication": "Audits authentication and session management flows for credential and token flaws.",
    "browser-devtools-inspector": "Inspects DOM trees, computed CSS, console logs, and network requests.",
    "browser-devtools-testing": "Runs automated end-to-end browser tests with console and network assertions.",
    "burp-suite-testing": "Executes web application security assessments and proxy traffic analysis.",
    "ci-cd-and-automation": "Automates build, test, release, and deployment pipelines across CI providers.",
    "cloud-architect": "Designs multi-cloud architectures, migration roadmaps, and FinOps cost optimizations.",
    "code-simplification": "Refactors complex code to reduce cyclomatic complexity while preserving behavior.",
    "codebase-audit-pre-push": "Runs pre-push hygiene, linting, secret scanning, and test boundary checks.",
    "codex-antigravity-skill-policy": "Routes tasks to domain-specific skills and enforces progressive token governance.",
    "comprehensive-code-review": "Reviews code systematically across security, correctness, architecture, and test coverage.",
    "constraint-driven-development": "Enforces written quality contracts in CONSTRAINTS.md to prevent bar-lowering.",
    "context-budget": "Monitors and optimizes live conversation context window and token usage.",
    "context-compression": "Compresses long-running agent session history while preserving critical state.",
    "context-engineering": "Structures system prompts, retrieval context, and memory for high-signal reasoning.",
    "cross-session-memory-search": "Searches persistent cross-session memory for prior solutions and architectural decisions.",
    "database-admin": "Manages database backups, replication, connection pooling, and high-availability failover.",
    "database-architect": "Designs scalable data layers, storage engine selection, and partitioning strategies.",
    "database-design": "Models normalized relational schemas, indexing strategies, and data integrity constraints.",
    "database-migrations-sql-migrations": "Executes zero-downtime SQL schema migrations with safe lock timeouts and rollbacks.",
    "database-optimizer": "Optimizes slow PostgreSQL and MySQL queries using execution plans and indexes.",
    "deadcode-elimination": "Detects and removes unused functions, orphan modules, and obsolete dependencies.",
    "deep-project-scaffolder": "Scaffolds modular project architectures with hierarchical AGENTS.md documentation.",
    "deep-technical-research": "Conducts deep technical research, literature synthesis, and citation verification.",
    "design-dna": "Extracts visual DNA, color tokens, and typography systems from design references.",
    "devops-deploy": "Automates application deployment with Docker, GitHub Actions, and cloud runtimes.",
    "devops-troubleshooter": "Diagnoses production incidents, container crashes, networking failures, and CI bottlenecks.",
    "dispatching-parallel-agents": "Decomposes independent tasks and dispatches parallel subagents for fast execution.",
    "distributed-tracing": "Instruments services with OpenTelemetry, Jaeger, and Tempo distributed request tracing.",
    "docker-expert": "Builds secure, multi-stage Docker images, Compose stacks, and container networks.",
    "doubt-driven-development": "Challenges architectural assumptions and verifies edge cases before committing code.",
    "error-handling-patterns": "Implements structured error hierarchies, retries, circuit breakers, and graceful degradation.",
    "fastapi-pro": "Builds high-performance async Python APIs with FastAPI, Pydantic v2, and SQLAlchemy 2.0.",
    "figma-implement-design": "Translates Figma designs into pixel-accurate React, HTML, and Tailwind components.",
    "flaky-test-investigation": "Traces and eliminates non-deterministic flaky tests across local and CI runs.",
    "flamegraph-performance-hotspot-profiling": "Profiles CPU and memory hotspots using flamegraphs and call-stack sampling.",
    "free-ai-apis-router": "Routes LLM requests across free-tier providers (Groq, OpenRouter, Cloudflare, local).",
    "frontend-a11y": "Audits and implements WCAG 2.1 AA accessibility, ARIA roles, and keyboard navigation.",
    "frontend-api-integration-patterns": "Architects frontend data fetching with React Query, SWR, caching, and optimistic UI.",
    "frontend-design-engineering": "Engineers distinctive UI/UX layouts, harmonious color systems, and fluid typography.",
    "frontend-mobile-security-xss-scan": "Scans frontend code for DOM XSS, unsafe sinks, and missing sanitization.",
    "frontend-security-coder": "Hardens web frontends against XSS, CSRF, DOM clobbering, and CSP bypasses.",
    "frontend-ui-engineering": "Builds production-grade, accessible, responsive component interfaces and web shells.",
    "gemini-api-integration": "Integrates Google Gemini models for structured generation, tool calling, and multimodal tasks.",
    "git-advanced-workflows": "Executes interactive rebases, cherry-picks, bisect debugging, and reflog recovery.",
    "git-bugfix-contribution": "Reproduces defects, writes regression tests, and prepares clean bugfix commits.",
    "git-pr-workflows-pr-enhance": "Structures high-signal pull requests with clear scope, diffs, and validation evidence.",
    "git-workflow-and-versioning": "Enforces conventional commits, semantic versioning, branching strategy, and release hygiene.",
    "github-actions-templates": "Creates production GitHub Actions workflows for testing, security scanning, and releases.",
    "github-issue-pr-triage": "Triages GitHub issues and pull requests by severity, root cause, and duplication.",
    "gsap-react": "Builds smooth React/Next.js animations using `useGSAP`, ScrollTrigger, and timelines.",
    "headless-browser-research": "Automates headless browser extraction for JS-rendered and complex web applications.",
    "hyperplan-orchestrator": "Decomposes complex multi-phase projects into deterministic execution plans and gates.",
    "image-to-code-synthesizer": "Converts UI screenshots and wireframes into clean, responsive HTML/CSS/React code.",
    "impeccable": "Polishes, critiques, and elevates UI visual craft, spacing, hierarchy, and micro-details.",
    "implementing-devsecops-security-scanning": "Embeds SAST, DAST, SCA, and secret scanning into DevSecOps pipelines.",
    "incremental-implementation": "Delivers software changes in thin, independently testable, verifiable slices.",
    "integrating-dast-with-owasp-zap-in-pipeline": "Automates dynamic web security scanning in CI/CD using OWASP ZAP.",
    "integrating-sast-into-github-actions-pipeline": "Configures CodeQL and Semgrep static security analysis in GitHub Actions.",
    "jarvis-pc-operator-automation": "Automates Windows PC operations, PowerShell diagnostics, Free AI routing, and Mark-LIV HUD.",
    "java-pro": "Writes modern Java 21+ applications using virtual threads, records, and pattern matching.",
    "javascript-pro": "Writes modern ES2023+ JavaScript with async patterns, modules, and clean DOM APIs.",
    "javascript-testing-patterns": "Implements unit, integration, and mock-driven tests in Vitest, Jest, and Playwright.",
    "javascript-typescript-typescript-scaffold": "Scaffolds strict TypeScript projects with modern bundlers, linters, and test runners.",
    "jpa-patterns": "Optimizes JPA/Hibernate entities, fetch graphs, transactions, and query performance.",
    "json-canvas-visualizer": "Generates Obsidian JSON Canvas (`.canvas`) architecture diagrams and mind maps.",
    "k6-load-testing": "Writes and executes k6 load, stress, and spike performance test suites.",
    "linux-troubleshooting": "Diagnoses Linux CPU, memory, disk I/O, systemd service, and network bottlenecks.",
    "llm-eval-benchmark-harness": "Runs automated LLM evaluation benchmarks, grading rubrics, and regression suites.",
    "llm-redteam-plugin-audit": "Conducts adversarial LLM red-teaming for prompt injection, jailbreaks, and data leaks.",
    "lsp-diagnostic-setup": "Configures Language Server Protocol (LSP) linters, typecheckers, and IDE diagnostics.",
    "mcp-builder": "Designs and implements Model Context Protocol (MCP) servers and tool schemas.",
    "motion-design": "Choreographs UI transitions, spring physics, and micro-interactions with Framer Motion.",
    "multi-agent-teammode": "Coordinates collaborating specialist agents with shared state and role boundaries.",
    "mysql-patterns": "Optimizes MySQL/MariaDB schemas, InnoDB indexes, transactions, and connection pools.",
    "nextjs-app-router-patterns": "Architects Next.js 14+ App Router apps with Server Components, Actions, and streaming.",
    "nodejs-backend-patterns": "Builds scalable Node.js backends with clean middleware, streams, and error handling.",
    "observability-and-instrumentation": "Instruments applications with structured logs, Prometheus metrics, and health checks.",
    "obsidian-cli-controller": "Manages Obsidian vault notes, frontmatter properties, tags, and searches programmatically.",
    "obsidian-database-bases": "Creates Obsidian Database `.base` files with filtered tabular views and formulas.",
    "obsidian-markdown-syntax": "Authors Obsidian Markdown with wikilinks, callouts, embeds, and YAML properties.",
    "openai-docs": "Builds applications using official OpenAI Responses API, Agents SDK, and tool calling.",
    "openapi-spec-generation": "Generates and validates OpenAPI 3.1 specifications from code or design-first schemas.",
    "openrouter-ai-sdk": "Integrates OpenRouter multi-model streaming and fallback routing across 200+ LLMs.",
    "pdf-document-processing": "Extracts text/tables, merges, splits, and generates PDF documents programmatically.",
    "performance-optimization": "Eliminates frontend, backend, network, and database latency bottlenecks.",
    "performing-sca-dependency-scanning-with-snyk": "Audits open-source dependencies for known CVEs and license risks using Snyk.",
    "persistent-file-planning": "Maintains persistent `task_plan.md`, `findings.md`, and `progress.md` execution state.",
    "php-pro": "Builds modern PHP 8.3+ applications with strict types, Laravel, and Symfony patterns.",
    "playwright-cli": "Automates cross-browser end-to-end testing, assertions, and trace debugging with Playwright.",
    "polars-streaming-dataframe-engine": "Processes large datasets fast using Polars lazy DataFrames and Apache Arrow.",
    "pr-review-resolution": "Systematically resolves pull request review feedback and failing CI checks.",
    "presentation-deck-engineering": "Structures executive and technical presentation decks with clear visual hierarchy.",
    "privacy-by-design": "Implements data minimization, PII encryption, consent controls, and GDPR/LGPD compliance.",
    "production-audit": "Audits production readiness across security, reliability, observability, and rollback safety.",
    "python-pro": "Engineers idiomatic Python 3.12+ systems with strict typing, async I/O, and packaging.",
    "qdrant-vector-database-hnsw-indexing": "Configures Qdrant vector search, HNSW indexing, quantization, and hybrid filtering.",
    "react-best-practices": "Applies modern React patterns: Server Components, Suspense, memoization, and clean hooks.",
    "react-developer-diagnostics": "Diagnoses React unnecessary re-renders, hook dependency bugs, and bundle bloat.",
    "react-doctor": "Audits React codebases for anti-patterns, state bugs, and performance regressions.",
    "react-modernization": "Upgrades legacy React codebases to modern hooks, concurrent features, and TypeScript.",
    "react-state-management": "Architects predictable React state with Zustand, Jotai, Redux Toolkit, and TanStack Query.",
    "react-testing": "Tests React components using React Testing Library, Vitest/Jest, and MSW network mocks.",
    "requirements-interview-elicitation": "Clarifies ambiguous requirements and edge cases before architectural implementation.",
    "responsive-layout-architecture": "Engineers adaptive app shells, CSS Grid/Flexbox layouts, and container queries.",
    "security-research-audit": "Audits software supply chains, CVEs, exposed secrets, and insecure configurations.",
    "security-review": "Reviews authentication, user input handling, secrets, and API endpoints for vulnerabilities.",
    "security-scan": "Scans agent configurations, hooks, and MCP settings for security misconfigurations.",
    "shadcn": "Integrates, customizes, and themes accessible shadcn/ui and Radix components.",
    "soak-stress-testing": "Runs extended soak and stress tests to uncover memory leaks and resource exhaustion.",
    "software-construction-patterns": "Applies clean architecture, modular domain modeling, and resilient construction patterns.",
    "source-driven-development": "Grounds every implementation in verified upstream source code and official documentation.",
    "sovereign-cyber-offensive-defensive-meta-toolkit": "Executes SSP-v13.4 red/blue team security audits, OWASP pentesting, and fail-closed hardening.",
    "spec-driven-development": "Authors explicit technical specifications and acceptance criteria before writing code.",
    "spreadsheet-data-modeling": "Builds structured spreadsheets, financial models, pivot analyses, and CSV pipelines.",
    "springboot-patterns": "Architects Spring Boot 3+ services, layered repositories, DTOs, and exception handlers.",
    "springboot-security": "Configures Spring Security filter chains, JWT/OAuth2 auth, CSRF, and method security.",
    "springboot-tdd": "Develops Spring Boot services with JUnit 5, Mockito, MockMvc, and Testcontainers.",
    "springboot-verification": "Runs full Spring Boot Maven/Gradle build, test, and static analysis verification loops.",
    "sql-injection-testing": "Tests database queries and web inputs for SQL injection vulnerabilities and bypasses.",
    "sql-optimization-patterns": "Diagnoses slow SQL queries using execution plans and rewrites them safely.",
    "sql-pro": "Writes complex analytical SQL, window functions, CTEs, and optimized indexing strategies.",
    "sqlmap-database-pentesting": "Automates SQL injection detection and database security auditing with sqlmap.",
    "structured-pydantic-llm-outputs": "Enforces strict Pydantic schema validation and retries on structured LLM outputs.",
    "subagent-driven-development": "Executes implementation plans by dispatching isolated subagents with two-stage review.",
    "subagent-task-qa": "Verifies subagent DAG outputs, task isolation boundaries, and deterministic evidence.",
    "supabase-postgres-best-practices": "Applies Postgres performance, RLS security, and indexing best practices.",
    "systematic-code-debugging": "Isolates root causes of bugs and regressions through hypothesis-driven diagnostics.",
    "systematic-refactoring": "Refactors code incrementally in safe, behavior-preserving, test-verified steps.",
    "tailwind-design-system": "Builds scalable design systems with Tailwind CSS tokens, variants, and themes.",
    "tailwind-patterns": "Applies modern Tailwind CSS v4 layout, responsive, and dark-mode utility patterns.",
    "task-dag-orchestrator": "Schedules and executes directed acyclic graphs (DAGs) of dependent agent tasks.",
    "tech-debt-audit": "Quantifies architectural and test debt into prioritized remediation roadmaps.",
    "test-driven-development": "Drives implementation using the strict Red-Green-Refactor test-first cycle.",
    "testing-api-for-broken-object-level-authorization": "Tests REST and GraphQL APIs for BOLA and IDOR authorization bypasses.",
    "testing-oauth2-implementation-flaws": "Audits OAuth 2.0 and OIDC flows for redirect URI, state, and token vulnerabilities.",
    "threejs-animation": "Builds interactive 3D WebGL scenes, shaders, and particle animations with Three.js.",
    "typescript-advanced-types": "Masters TypeScript generics, conditional types, mapped types, and type-level inference.",
    "typescript-expert": "Engineers strict, high-performance TypeScript applications, SDKs, and monorepos.",
    "ui-micro-interaction-design": "Crafts responsive hover, focus, loading, and state-transition micro-interactions.",
    "ui-redesign-modernizer": "Upgrades dated UIs with modern typography, balanced spacing, and refined visual hierarchy.",
    "ui-ux-pro-max": "Provides comprehensive UI/UX design patterns for modern web and mobile applications.",
    "ultrawork-execution-engine": "Decomposes complex goals into relentless, milestone-verified autonomous execution loops.",
    "using-git-worktrees": "Isolates parallel feature branches using Git worktrees without dirtying main workspace.",
    "verification-before-completion": "Requires running real verification commands and inspecting output before claiming success.",
    "visual-regression-qa": "Detects unintended UI layout shifts across viewports and themes via visual diffs.",
    "web-design-guidelines": "Audits web interfaces for usability, hierarchy, responsiveness, and polish.",
    "web-security-testing": "Executes end-to-end web security testing across OWASP Top 10 attack surfaces.",
    "webapp-testing": "Tests local and staged web applications interactively using Playwright automation.",
    "workers-best-practices": "Engineers high-performance Cloudflare Workers, edge routing, and Workers AI bindings.",
    "zod-validation-expert": "Validates runtime data boundaries and TypeScript inference using Zod v3/v4 schemas.",
}


def format_clean_description(name: str, raw_desc: str) -> str:
    if name in MASTER_DESCRIPTIONS:
        return MASTER_DESCRIPTIONS[name]

    desc = " ".join(raw_desc.strip().split())
    desc = re.sub(r"^['\">|-]+|['\"]+$", "", desc).strip()
    desc = re.sub(
        r"^(Use this skill whenever|Use this skill when|Use this skill for|Use when|This skill should be used for|Specialized skill for|Comprehensive guide for|Comprehensive|Master|Official|Guides stable|Provides a|Provides)\s+",
        "",
        desc,
        flags=re.IGNORECASE,
    ).strip()

    # Take first complete clause if possible
    first_sentence = re.split(r"[.?!]\s+", desc)[0].strip()
    words = first_sentence.split()
    if len(words) > 13:
        words = words[:12]
        # Strip trailing conjunctions/prepositions so it NEVER ends in 'and.', 'or.', 'with.', etc.
        while words and words[-1].lower().rstrip(",;:") in {
            "and", "or", "with", "in", "to", "for", "of", "the", "a", "an", "from", "by", "on", "at", "into", "including", "using", "via", "such", "as", "that", "which", "who", "when", "where", "while", "before", "after"
        }:
            words.pop()
        first_sentence = " ".join(words)

    first_sentence = first_sentence.rstrip(".,;:—- ")
    if first_sentence:
        first_sentence = first_sentence[0].upper() + first_sentence[1:] + "."
    else:
        first_sentence = f"Specialized workflow and runbook for {name.replace('-', ' ')}."
    return first_sentence


def rewrite_frontmatter_description(md_path: Path) -> tuple[int, int, str]:
    content = md_path.read_text(encoding="utf-8", errors="ignore")
    fm_match = re.search(r"(?ms)^---\r?\n(.*?)\r?\n---", content)
    skill_name = md_path.parent.name
    if not fm_match:
        return 0, 0, ""

    fm = fm_match.group(1)
    name_m = re.search(r"(?m)^name:\s*(.+)$", fm)
    if name_m:
        skill_name = name_m.group(1).strip().strip("'\"")

    desc_m = re.search(r"(?ms)^description:\s*(.*?)(?=\r?\n[a-zA-Z0-9_-]+:|\Z)", fm)
    old_desc = " ".join(desc_m.group(1).split()) if desc_m else ""
    new_desc = format_clean_description(skill_name, old_desc)

    new_desc_line = f"description: {new_desc}"
    if desc_m:
        updated_fm = re.sub(
            r"(?ms)^description:\s*.*?(?=\r?\n[a-zA-Z0-9_-]+:|\Z)",
            lambda _: new_desc_line,
            fm,
        )
    else:
        updated_fm = fm + f"\ndescription: {new_desc}"

    new_content = content[:fm_match.start(1)] + updated_fm + content[fm_match.end(1):]
    md_path.write_text(new_content, encoding="utf-8")
    return len(old_desc), len(new_desc), new_desc


def deploy_sovereign_agents() -> int:
    SOVEREIGN_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    plugin_agents_dir = SOVEREIGN_PLUGIN_DIR / "agents"
    plugin_agents_dir.mkdir(parents=True, exist_ok=True)
    REPO_AGENTS.mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": "jarvis-sovereign-arsenal",
        "displayName": "J.A.R.V.I.S. Sovereign Arsenal & Multi-Agent Squad",
        "version": "2.1.0",
        "description": "Esquadrão Soberano de 11 Agentes Especialistas (PC Operator, SWE, CyberSec, Kernel SRE, FullStack UI, Database, DevOps, Swarm, OSINT, Obsidian Vault, QA Verifier).",
        "author": {"name": "Roberto Atila Almeida Azevedo"},
        "suggestedPrompts": [
            "Audite a segurança, performance e testes do repositório usando o Esquadrão Soberano",
            "Verifique a telemetria do PC, espaço em disco e status do daemon J.A.R.V.I.S.",
            "Implemente uma nova feature seguindo arquitetura limpa, TDD e zero placeholders"
        ]
    }
    (SOVEREIGN_PLUGIN_DIR / "plugin.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (SOVEREIGN_PLUGIN_DIR / "README.md").write_text(
        "# J.A.R.V.I.S. Sovereign Arsenal & Multi-Agent Squad\n\n"
        "Bundle oficial de Custom Agents (Subagents) de elite do ecossistema J.A.R.V.I.S. Mark-LIV.\n",
        encoding="utf-8"
    )

    # Also copy into already-enabled `google-antigravity-sdk/agents` so agents are active immediately without restart,
    # while cleaning any duplicate once restarted if needed — wait: let's check if GetAllPlugins already loads jarvis-sovereign-arsenal live!
    for ag in SOVEREIGN_AGENTS:
        tools_yaml = "\n".join(f"  - {t}" for t in ag["tools"])
        md_text = (
            f"---\n"
            f"name: {ag['name']}\n"
            f"description: \"{ag['description']}\"\n"
            f"tools:\n"
            f"{tools_yaml}\n"
            f"mainAgent: true\n"
            f"subagent: true\n"
            f"commandExecutionPolicy: auto\n"
            f"---\n\n"
            f"{ag['body'].strip()}\n"
        )
        (plugin_agents_dir / f"{ag['name']}.md").write_text(md_text, encoding="utf-8")
        (REPO_AGENTS / f"{ag['name']}.md").write_text(md_text, encoding="utf-8")

    # Also optimize firestore-rules-author description in firebase plugin
    fb_agent = CONFIG_PLUGINS / "firebase" / "agents" / "firestore-rules-author.md"
    if fb_agent.exists():
        txt = fb_agent.read_text(encoding="utf-8", errors="ignore")
        txt = re.sub(
            r'(?m)^description:\s*.*$',
            'description: "Specialist subagent for authoring, refactoring, and auditing Cloud Firestore Security Rules (firestore.rules)."',
            txt,
        )
        fb_agent.write_text(txt, encoding="utf-8")

    return len(SOVEREIGN_AGENTS)


def main() -> None:
    print("=" * 72)
    print("  J.A.R.V.I.S. MARK-LIV // ULTIMATE ARSENAL BUILDER & TOKEN GOVERNOR")
    print("=" * 72)

    # 1. Deploy 11 Sovereign Custom Agents
    agent_count = deploy_sovereign_agents()
    print(f"[1/5] Esquadrão Soberano implantado: {agent_count} novos Custom Agents (+1 Firebase = 12 total).")

    # 2. Create new sovereign skills
    for sname, sdata in NEW_SOVEREIGN_SKILLS.items():
        md_content = f"---\nname: {sname}\ndescription: {sdata['description']}\n---\n\n{sdata['body'].strip()}\n"
        for root in (REPO_SKILLS, CONFIG_SKILLS):
            sdir = root / sname
            sdir.mkdir(parents=True, exist_ok=True)
            (sdir / "SKILL.md").write_text(md_content, encoding="utf-8")
    print(f"[2/5] Novas Skills Soberanas criadas: {list(NEW_SOVEREIGN_SKILLS.keys())}")

    # 3. Archive 10 empty stubs & 7 duplicates from CONFIG_SKILLS
    ARCHIVE_SKILLS.mkdir(parents=True, exist_ok=True)
    archived = []
    for name in sorted(STUBS_AND_DUPLICATES_TO_ARCHIVE):
        target = CONFIG_SKILLS / name
        if target.exists():
            dst = ARCHIVE_SKILLS / name
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            shutil.move(str(target), str(dst))
            archived.append(name)
    print(f"[3/5] Stubs vazios e duplicatas movidos para o Vault Archive: {len(archived)} removidos do prompt ativo.")

    # 4. Promote 30 elite full-length technical skills from REPO_SKILLS to CONFIG_SKILLS
    promoted = []
    for name in ELITE_SKILLS_TO_PROMOTE:
        src = REPO_SKILLS / name
        dst = CONFIG_SKILLS / name
        if (src / "SKILL.md").exists():
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
            promoted.append(name)
    print(f"[4/5] Skills Técnicas Reais promovidas (com scripts/references): {len(promoted)} adicionadas.")

    # 5. Optimize all SKILL.md descriptions across CONFIG_SKILLS, CONFIG_PLUGINS, and REPO_SKILLS
    user_skill_files = sorted(CONFIG_SKILLS.glob("*/SKILL.md"))
    plugin_skill_files = sorted(CONFIG_PLUGINS.glob("*/skills/*/SKILL.md"))
    repo_skill_files = sorted(REPO_SKILLS.glob("*/SKILL.md"))

    chars_before = 0
    chars_after = 0
    for f in user_skill_files + plugin_skill_files:
        ob, nb, _ = rewrite_frontmatter_description(f)
        path_overhead = len(f"- {f.parent.name} ({f}): \n")
        chars_before += ob + path_overhead
        chars_after += nb + path_overhead

    for f in repo_skill_files:
        rewrite_frontmatter_description(f)

    # Calculate token telemetry
    est_tokens_after = int(chars_after / 3.15)
    pct_skills = (est_tokens_after / 20000.0) * 100.0

    print(f"[5/5] Governança de Frontmatter concluída em {len(user_skill_files)} User Skills + {len(plugin_skill_files)} Plugin Skills.")
    print("-" * 72)
    print(f"  Skills Ativas no Config Global : {len(user_skill_files)}")
    print(f"  Skills de Plugins Ativas       : {len(plugin_skill_files)}")
    print(f"  Total de Skills Disponíveis    : {len(user_skill_files) + len(plugin_skill_files)} (+9 Built-in = {len(user_skill_files) + len(plugin_skill_files) + 9})")
    print(f"  Total de Custom Agents (Squad) : {agent_count + 1} Agentes Especialistas")
    print(f"  Consumo Estimado de Skills     : ~{est_tokens_after:,} / 20,000 tokens ({pct_skills:.1f}%)")
    print("=" * 72)


if __name__ == "__main__":
    main()
