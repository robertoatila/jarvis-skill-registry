---
name: jarvis-pc-operator-automation
description: Automates Windows PC operations, PowerShell diagnostics, Free AI routing, and Mark-LIV HUD.
---

# J.A.R.V.I.S. Autonomous PC Operator & Free AI Matrix

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
