---
name: subfinder
description: Ferramenta canônica projectdiscovery/subfinder (14,569 estrelas).
squad: Neuro-Cognitive
version: 1.0.0
upstream: https://github.com/projectdiscovery/subfinder
---

# SUBFINDER // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [projectdiscovery/subfinder](https://github.com/projectdiscovery/subfinder) (14,569 estrelas ⭐)
- **Linguagem / Stack:** Go
- **Esquadrão Responsável:** `Neuro-Cognitive`
- **Missão:** Fast passive subdomain enumeration tool.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
subfinder -h
Subfinder supports environment variables to specify custom paths for configuration files:
- `SUBFINDER_CONFIG` - Path to config.yaml file (overrides default `$CONFIG/subfinder/config.yaml`)
- `SUBFINDER_PROVIDER_CONFIG` - Path to provider-config.yaml file (overrides default `$CONFIG/subfinder/provider-config.yaml`)
`subfinder` requires **go1.26** to install successfully. Run the following command to install the latest version:
Learn about more ways to install subfinder here: https://docs.projectdiscovery.io/tools/subfinder/install.
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `subfinder`:
1. Verifique se o executável ou dependência está presente via terminal (`where subfinder` ou `Get-Command subfinder`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
