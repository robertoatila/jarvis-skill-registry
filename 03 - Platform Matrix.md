---
title: 03 - Matriz Multiplataforma (6 Targets)
type: platform-matrix
platforms_count: 6
lockfiles_count: 6
total_pins: 870
tags:
  - platforms
  - lockfiles
  - multi-target
---

# Matriz de Adaptacao Multiplataforma (6 Targets)

> [!NOTE] 870 Combinacoes Deterministicas Homologadas (Release v1.1.0)
> O Skill Registry exporta automaticamente cada uma das 145 skills para 6 ecossistemas distintos com 100% de paridade funcional.

[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]

| Plataforma Alvo | Modo de Entrega | Formato Gerado | Arquivo Lockfile (Baseline) |
| :--- | :--- | :--- | :--- |
| Cursor AI | System Prompt Rules | `.cursorrules` / prompt injection | `releases/v1.1.0/lockfiles/cursor.lock.json` |
| Gemini / Antigravity | Native Workspace Skill | `SKILL.md` + frontmatter standard | `releases/v1.1.0/lockfiles/gemini.lock.json` |
| Codex CLI & IDE | Native Codex Skill Directory | `.codex/skills/<name>/SKILL.md` | `releases/v1.1.0/lockfiles/codex.lock.json` |
| Claude CLI & Desktop | Context & Instructions | `CLAUDE.md` & system context | `releases/v1.1.0/lockfiles/claude.lock.json` |
| ChatGPT Desktop & Apps | Apps SDK & Custom Action | MCP Manifest + Action JSON | `releases/v1.1.0/lockfiles/chatgpt.lock.json` |
| Generic Agent | Open Standard Markdown | Standard Agent `SKILL.md` | `releases/v1.1.0/lockfiles/generic.lock.json` |
