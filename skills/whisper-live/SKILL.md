---
name: whisper-live
description: Ferramenta canônica collabora/WhisperLive (4,325 estrelas). WhisperLive is a nearly-live speech-to-text implementation using Whisper and TensorRT/faster-whisper over WebSockets.
squad: Neuro-Cognitive
version: 1.0.0
upstream: https://github.com/collabora/WhisperLive
---

# WHISPER-LIVE // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [collabora/WhisperLive](https://github.com/collabora/WhisperLive) (4,325 estrelas ⭐)
- **Linguagem / Stack:** Python / faster-whisper / WebSockets
- **Esquadrão Responsável:** `Neuro-Cognitive`
- **Missão:** Transcrição contínua e em tempo quase real de voz para texto (STT) via WebSockets, permitindo que microfones locais enviem fluxos de áudio PCM diretamente para um servidor local Whisper sem latência de buffers longos.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação em servidor local na máquina ou rede privada sob o Protocolo SSP-v13.4.
- **Integração com Cockpit:** Permite transcrição simultânea de voz na interface do HUD Cockpit ou cliente móvel.

## 3. Comandos Homologados & Receitas de Execução

```bash
# Iniciar o servidor local WhisperLive:
python3 run_server.py --port 9090 --backend faster_whisper --model small

# Cliente de microfone local:
python3 client.py --server 127.0.0.1 --port 9090
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas de reconhecimento de voz contínuo:
1. Verifique a disponibilidade do servidor local de transcrição na porta 9090.
2. Encaminhe o stream de áudio do microfone via protocolo WebSocket loopback.
3. Repasse os tokens de texto parciais para o buffer de fala do J.A.R.V.I.S.
