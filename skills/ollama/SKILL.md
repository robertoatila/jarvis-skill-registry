---
name: ollama
description: Ferramenta canônica ollama/ollama (183,313 estrelas). Get up and running with Kimi, GLM, MiniMax, DeepSeek, gpt-oss, Qwen, Gemma and other models.
squad: Neuro-Cognitive
version: 1.0.0
upstream: https://github.com/ollama/ollama
---

# OLLAMA // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [ollama/ollama](https://github.com/ollama/ollama) (183,313 estrelas ⭐)
- **Linguagem / Stack:** Go
- **Esquadrão Responsável:** `Neuro-Cognitive`
- **Missão:** Get up and running with Kimi, GLM, MiniMax, DeepSeek, gpt-oss, Qwen, Gemma and other models.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
curl -fsSL https://ollama.com/install.sh | sh
irm https://ollama.com/install.ps1 | iex
curl -fsSL https://ollama.com/install.sh | sh
ollama
ollama launch claude
ollama launch openclaw
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `ollama`:
1. Verifique se o executável ou dependência está presente via terminal (`where ollama` ou `Get-Command ollama`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
