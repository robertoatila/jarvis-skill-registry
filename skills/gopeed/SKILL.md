---
name: gopeed
description: Ferramenta canônica GopeedLab/gopeed (26,937 estrelas).
squad: Hyperion-FullStack
version: 1.0.0
upstream: https://github.com/GopeedLab/gopeed
---

# GOPEED // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [GopeedLab/gopeed](https://github.com/GopeedLab/gopeed) (26,937 estrelas ⭐)
- **Linguagem / Stack:** Dart
- **Esquadrão Responsável:** `Hyperion-FullStack`
- **Missão:**   A fast, modern download manager for HTTP, BitTorrent, Magnet, and ed2k. Cross-platform, built with Golang and Flutter.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
go install github.com/GopeedLab/gopeed/cmd/gopeed@latest
git clone git@github.com:GopeedLab/gopeed.git
go build -tags nosqlite -ldflags="-w -s" -buildmode=c-shared -o ui/flutter/windows/libgopeed.dll github.com/GopeedLab/gopeed/bind/desktop
cd ui/flutter
flutter build windows
go build -tags nosqlite -ldflags="-w -s" -buildmode=c-shared -o ui/flutter/macos/Frameworks/libgopeed.dylib github.com/GopeedLab/gopeed/bind/desktop
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `gopeed`:
1. Verifique se o executável ou dependência está presente via terminal (`where gopeed` ou `Get-Command gopeed`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
