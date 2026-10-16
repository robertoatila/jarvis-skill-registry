---
name: firecrawl
description: Ferramenta canônica firecrawl/firecrawl (191,878 estrelas).
squad: Neuro-Cognitive
version: 1.0.0
upstream: https://github.com/firecrawl/firecrawl
---

# FIRECRAWL // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) (191,878 estrelas ⭐)
- **Linguagem / Stack:** TypeScript / Node.js / Python SDK
- **Esquadrão Responsável:** `Neuro-Cognitive`
- **Missão:** Conversão estruturada de qualquer página web ou domínio em Markdown de altíssima fidelidade e tokens otimizados para RAG, bypass de anti-bot, execução de JavaScript via Playwright headless e extração de schemas JSON.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local / Self-Hosted:** Empregar preferencialmente a instância self-hosted local via Docker para total privacidade sob o Protocolo Soberano SSP-v13.4.
- **Preservação de Contexto:** Utilizar a conversão em Markdown limpo para alimentar o Context Governor sem sobrecarregar a janela de tokens.

## 3. Comandos Homologados & Receitas de Execução

```python
# Uso via SDK Python nativo (ou requisição REST local):
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_url="http://localhost:3002")

# Raspar uma única URL para Markdown limpo:
scrape_result = app.scrape_url("https://example.com", params={"formats": ["markdown"]})
print(scrape_result["markdown"])

# Crawl profundo de documentação técnica:
crawl_result = app.crawl_url("https://docs.example.com", params={"limit": 10, "scrapeOptions": {"formats": ["markdown"]}})
```

```bash
# Execução self-hosted via Docker Compose local:
docker run -d -p 3002:3002 mendableai/firecrawl:latest
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar pesquisa técnica aprofundada ou ingestão de documentação externa:
1. Verifique se o endpoint local do Firecrawl ou serviço headless está ativo.
2. Utilize o modo `map` para descobrir a estrutura de URLs antes de realizar o crawl completo.
3. Converta o conteúdo extraído em notas Markdown para o vault Obsidian sob `06 - Referências Externas`.
