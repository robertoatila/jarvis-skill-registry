---
title: Sincronizacao Soberana e Solucao da Discrepancia de Skills
type: audit-and-resolution
status: RESOLVED
sovereign_arsenal_count: 144
ide_global_config_path: C:\Users\Ad\.gemini\config\skills
sovereign_vault_path: E:\.skill-registry\skills
tags:
  - token-budget
  - skills-sync
  - antigravity
  - jarvis-arsenal
---

# ⚔️ Sincronização Soberana & Diagnóstico da Discrepância de Skills

> [!IMPORTANT] 🔍 Diagnóstico da Pergunta do Usuário
> **Pergunta**: *"TENHO 143 DE SKILLS ATIVAS NO ARSENAL DO JARVIS E NADA AQUI, TEM ALGUMA COISA ERRADA"*
> **Causa Raiz Identificada**: O Antigravity IDE lê as skills instaladas exclusivamente do diretório global `C:\Users\Ad\.gemini\config\skills`. As 144 skills do Arsenal Soberano do J.A.R.V.I.S. (como `autogen`, `agent-browser-automation`, `comprehensive-code-review`, etc.) residiam puramente em `E:\.skill-registry\skills` e não haviam sido exportadas para a pasta de configuração do IDE.

---

## 📊 1. Comparativo de Inventários

| Localização | Papel na Arquitetura | Total de Skills | Status de Visibilidade no IDE |
| :--- | :--- | :--- | :--- |
| `E:\.skill-registry\skills` | **Cofre Canônico Soberano** | **144 skills** | Oculto (não rastreado nativamente como raiz global) |
| `C:\Users\Ad\.gemini\config\skills` | **Configuração Global do IDE** | **165 pastas** | 110 ativas pelo filtro de token budget do IDE |

---

## 🛡️ 2. A Solução: Sincronização com Poda Ativa ($\le 25$ Palavras)

Para que o IDE exiba e utilize as skills do Arsenal Soberano **sem estourar o Token Budget** (atualmente com 61.7% disponível), o script [`tooling/Sync-SovereignArsenalToIde.ps1`](file:///e:/.skill-registry/tooling/Sync-SovereignArsenalToIde.ps1) espelha as skills aplicando a **Lei do Mito do Compounding**:

1. Copia o contrato `SKILL.md` canônico de `E:\.skill-registry\skills/<skill>` para `C:\Users\Ad\.gemini\config\skills/<skill>`.
2. Assegura que o campo `description` no frontmatter YAML possua rigorosamente $\le 25$ palavras.
3. Não duplica arquivos de lixo ou temporários.
4. Preserva os lockfiles criptográficos em `E:\`.
