---
name: posting-tui
description: Ferramenta canônica darrenburns/posting (12,515 estrelas). Posting is a modern, keyboard-centric HTTP and REST client for the terminal with autocompletion, environments, and syntax highlighting.
squad: Tactical
version: 1.0.0
upstream: https://github.com/darrenburns/posting
---

# POSTING-TUI // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [darrenburns/posting](https://github.com/darrenburns/posting) (12,515 estrelas ⭐)
- **Linguagem / Stack:** Python (Textual)
- **Esquadrão Responsável:** `Tactical`
- **Missão:** Cliente HTTP/REST e testes de API com interface interativa rica de terminal (TUI), suporte a coleções declarativas, ambientes (.env), parâmetros dinâmicos e exportação rápida de requisições.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Testes e depuração de endpoints locais (como `/api/status`, `/api/chat`, `/api/tree`) sem vazamento de payloads.
- **Fail-Closed:** Headers de autenticação (Bearer tokens) gerenciados via variáveis locais de ambiente.

## 3. Comandos Homologados & Receitas de Execução

```bash
# Executar posting diretamente no terminal
posting

# Abrir coleção específica de endpoints
posting --collection ./collections/jarvis-api.json

# Executar requisição rápida com perfil de ambiente local
posting --env local
```

## 4. Integração em Missões Autônomas
1. Utilizar para validações interativas de APIs locais desenvolvidas no Cockpit J.A.R.V.I.S.
2. Armazenar coleções de testes de integração em formato JSON reutilizável.
