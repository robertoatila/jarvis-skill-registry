---
name: ffmpeg
description: Ferramenta canônica FFmpeg/FFmpeg (65,235 estrelas). Mirror of https://git.ffmpeg.org/ffmpeg.git
squad: Hyperion-FullStack
version: 1.0.0
upstream: https://github.com/FFmpeg/FFmpeg
---

# FFMPEG // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) (65,235 estrelas ⭐)
- **Linguagem / Stack:** C
- **Esquadrão Responsável:** `Hyperion-FullStack`
- **Missão:** Mirror of https://git.ffmpeg.org/ffmpeg.git

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
# Uso canônico padrão para ffmpeg:
ffmpeg --help
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `ffmpeg`:
1. Verifique se o executável ou dependência está presente via terminal (`where ffmpeg` ou `Get-Command ffmpeg`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
