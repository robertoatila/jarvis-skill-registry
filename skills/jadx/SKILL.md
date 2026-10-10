---
name: jadx
description: Ferramenta canônica skylot/jadx (50,783 estrelas).
squad: Cyberspace-Offensive
version: 1.0.0
upstream: https://github.com/skylot/jadx
---

# JADX // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [skylot/jadx](https://github.com/skylot/jadx) (50,783 estrelas ⭐)
- **Linguagem / Stack:** Java
- **Esquadrão Responsável:** `Cyberspace-Offensive`
- **Missão:** Dex to Java decompiler

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
sudo pacman -S jadx
brew install jadx
flatpak install flathub com.github.skylot.jadx
git clone https://github.com/skylot/jadx.git
cd jadx
./gradlew dist
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `jadx`:
1. Verifique se o executável ou dependência está presente via terminal (`where jadx` ou `Get-Command jadx`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
