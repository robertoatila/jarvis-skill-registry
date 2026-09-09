---
title: 04 - Laboratorio de Ingestao Autonoma
type: ingestion-lab
tags:
  - ingestion
  - autonomous-pipeline
  - read-analyze-propose
---

# Laboratorio de Ingestao Autonoma J.A.R.V.I.S.

> [!CHECK] Principio READ-ANALYZE-PROPOSE
> Qualquer repositorio importado passa por clone raso isolado em staging/ingestion/, varredura estatica de 13 regras e pontuacao de qualidade de 0 a 100. Nenhuma mutacao atinge o baseline sem aprovacao explicita.

[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]

## Como Usar pelo Terminal

```powershell
# Analisar qualquer repositorio pelo shorthand ou URL:
skillctl ingest microsoft/autogen
skillctl ingest https://github.com/vllm-project/vllm
```

## Candidatos Atualmente em Staging

- **anthropic-quickstarts** (Caminho: staging/ingestion/anthropic-quickstarts)
- **autogen** (Caminho: staging/ingestion/autogen)
- **crewAI** (Caminho: staging/ingestion/crewAI)
- **GoDefender** (Caminho: staging/ingestion/GoDefender)
- **httpx** (Caminho: staging/ingestion/httpx)
- **PentestGPT** (Caminho: staging/ingestion/PentestGPT)
- **sovereign-autonomous-agents-and-rag-meta-engine** (Caminho: staging/ingestion/sovereign-autonomous-agents-and-rag-meta-engine)
- **sovereign-cyber-offensive-defensive-meta-toolkit** (Caminho: staging/ingestion/sovereign-cyber-offensive-defensive-meta-toolkit)
- **SWE-agent** (Caminho: staging/ingestion/SWE-agent)
