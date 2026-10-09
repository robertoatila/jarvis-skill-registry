---
name: scrcpy
description: Ferramenta canônica Genymobile/scrcpy (151,594 estrelas). Display and control your Android device
squad: Hyperion-FullStack
version: 1.0.0
upstream: https://github.com/Genymobile/scrcpy
---

# SCRCPY // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) (151,594 estrelas ⭐)
- **Linguagem / Stack:** C
- **Esquadrão Responsável:** `Hyperion-FullStack`
- **Missão:** Display and control your Android device

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
Injecting input events requires the caller (or the source of the instrumentation, if any) to have the INJECT_EVENTS permission.
scrcpy --video-codec=h265 --max-size=1920 --max-fps=60 --no-audio --keyboard=uhid
scrcpy --video-codec=h265 -m1920 --max-fps=60 --no-audio -K  # short version
scrcpy --new-display=1920x1080 --start-app=org.videolan.vlc
scrcpy --new-display -x --keep-active --start-app=org.videolan.vlc --video-codec=h265 -b16M
scrcpy --video-source=camera --video-codec=h265 --camera-size=1920x1080 --record=file.mp4
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `scrcpy`:
1. Verifique se o executável ou dependência está presente via terminal (`where scrcpy` ou `Get-Command scrcpy`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
