---
name: aria2
description: Ferramenta canônica aria2/aria2 (43,129 estrelas).
squad: Hyperion-FullStack
version: 1.0.0
upstream: https://github.com/aria2/aria2
---

# ARIA2 // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [aria2/aria2](https://github.com/aria2/aria2) (43,129 estrelas ⭐)
- **Linguagem / Stack:** C++
- **Esquadrão Responsável:** `Hyperion-FullStack`
- **Missão:** aria2 is a lightweight multi-protocol & multi-source, cross platform download utility operated in command-line. It supports HTTP/HTTPS, FTP, SFTP, BitTorrent and Metalink.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
# Uso canônico padrão para aria2:
aria2 --help
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `aria2`:
1. Verifique se o executável ou dependência está presente via terminal (`where aria2` ou `Get-Command aria2`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
