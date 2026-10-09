---
name: sqlmap
description: Ferramenta canônica sqlmapproject/sqlmap (38,638 estrelas). Automatic SQL injection and database takeover tool
squad: Cyberspace-Offensive
version: 1.0.0
upstream: https://github.com/sqlmapproject/sqlmap
---

# SQLMAP // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [sqlmapproject/sqlmap](https://github.com/sqlmapproject/sqlmap) (38,638 estrelas ⭐)
- **Linguagem / Stack:** Python
- **Esquadrão Responsável:** `Cyberspace-Offensive`
- **Missão:** Automatic SQL injection and database takeover tool

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
# Uso canônico padrão para sqlmap:
sqlmap --help
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `sqlmap`:
1. Verifique se o executável ou dependência está presente via terminal (`where sqlmap` ou `Get-Command sqlmap`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
