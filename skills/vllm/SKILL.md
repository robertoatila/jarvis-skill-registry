---
name: vllm
description: Ferramenta canônica vllm-project/vllm (93,867 estrelas). A high-throughput and memory-efficient inference and serving engine for LLMs
squad: Neuro-Cognitive
version: 1.0.0
upstream: https://github.com/vllm-project/vllm
---

# VLLM // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [vllm-project/vllm](https://github.com/vllm-project/vllm) (93,867 estrelas ⭐)
- **Linguagem / Stack:** Python
- **Esquadrão Responsável:** `Neuro-Cognitive`
- **Missão:** A high-throughput and memory-efficient inference and serving engine for LLMs

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
uv pip install vllm
vllm download-kernels  # precompiled kernels for faster startup
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `vllm`:
1. Verifique se o executável ou dependência está presente via terminal (`where vllm` ou `Get-Command vllm`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
