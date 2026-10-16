---
name: ripgrep
description: Ferramenta canônica BurntSushi/ripgrep (69,133 estrelas).
squad: Hyperion-FullStack
version: 1.0.0
upstream: https://github.com/BurntSushi/ripgrep
---

# RIPGREP // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) (69,133 estrelas ⭐)
- **Linguagem / Stack:** Rust
- **Esquadrão Responsável:** `Hyperion-FullStack`
- **Missão:** ripgrep recursively searches directories for a regex pattern while respecting your gitignore

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação determinística em conformidade com o Protocolo SSP-v13.
- **Consumo de Contexto:** Não leia o código fonte inteiro a menos que seja estritamente necessário. Use os comandos abaixo para executar a tarefa diretamente no terminal.

## 3. Comandos Homologados & Receitas de Execução

```bash
brew install ripgrep
sudo port install ripgrep
choco install ripgrep
scoop install ripgrep
winget install BurntSushi.ripgrep.MSVC
sudo pacman -S ripgrep
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar tarefas relacionadas a `ripgrep`:
1. Verifique se o executável ou dependência está presente via terminal (`where ripgrep` ou `Get-Command ripgrep`).
2. Se ausente, sugira a instalação via gestor de pacotes (ex: `winget`, `pip`, `npm`, `cargo`) ou clone isolado em `staging/`.
3. Execute a ação solicitada, analise os resultados e entregue o objetivo final.
