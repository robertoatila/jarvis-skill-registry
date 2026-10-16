---
name: silero-vad
description: Ferramenta canônica snakers4/silero-vad (6,135 estrelas). Silero VAD is a pre-trained, enterprise-grade Voice Activity Detector with sub-millisecond inference and negligible memory footprint.
squad: Neuro-Cognitive
version: 1.0.0
upstream: https://github.com/snakers4/silero-vad
---

# SILERO-VAD // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [snakers4/silero-vad](https://github.com/snakers4/silero-vad) (6,135 estrelas ⭐)
- **Linguagem / Stack:** Python / ONNX / C++ / WebAssembly
- **Esquadrão Responsável:** `Neuro-Cognitive`
- **Missão:** Detecção precisa e ultra-rápida de atividade de voz (Voice Activity Detection - VAD) com latência menor que 1 milissegundo por chunk, footprint desprezível e suporte a ONNX Runtime sem depender de GPU.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação estritamente local em conformidade com o Protocolo SSP-v13.4.
- **Gate de Silêncio:** Utilizado como o detector de silêncio e finalização de sentença para conversação contínua sem necessidade de pressionar botões (*hands-free*).
- **Sem Envio para Nuvem:** Os frames de áudio permanecem 100% no dispositivo host.

## 3. Comandos Homologados & Receitas de Execução

```python
# Uso via ONNX Runtime puro em Python:
import onnxruntime
import numpy as np

session = onnxruntime.InferenceSession("silero_vad.onnx")
# chunk de áudio PCM 16kHz mono (512 amostras = 32ms)
# inputs: audio chunk, state, sampling_rate
```

```bash
# Instalação rápida via pip (ou ONNX standalone):
pip install silero-vad
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas de escuta contínua ou detecção de fala:
1. Verifique se o modelo ONNX ou pacote está disponível localmente.
2. Processe streams de áudio do microfone em janelas de 32ms (512 samples a 16kHz).
3. Dispare a transcrição local apenas quando a probabilidade de voz cruzar o limiar calibrado (padrão `0.5`).
