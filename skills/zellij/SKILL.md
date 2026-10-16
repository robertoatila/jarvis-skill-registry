---
name: zellij
description: Ferramenta canônica zellij-org/zellij (35,748 estrelas).
squad: Hyperion
version: 1.0.0
upstream: https://github.com/zellij-org/zellij
---

# ZELLIJ // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [zellij-org/zellij](https://github.com/zellij-org/zellij) (35,748 estrelas ⭐)
- **Linguagem / Stack:** Rust / WebAssembly
- **Esquadrão Responsável:** `Hyperion`
- **Missão:** Orquestração de workspaces em terminal com persistência de sessões, layouts declarativos em KDL, painéis flutuantes e extensibilidade nativa via plugins WASM sandboxed.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Operação 100% local sob o Protocolo Soberano SSP-v13.4.
- **Isolamento de Processos:** Criar e gerenciar sessões nomeadas para execução autônoma paralela de builds, testes e servidores (ex: `jarvis-runtime`, `jarvis-tests`).
- **Layouts Declarativos:** Usar layouts KDL para inicializar grids de monitoramento de processos e consoles simultâneos.

## 3. Comandos Homologados & Receitas de Execução

```bash
# Iniciar ou anexar a uma sessão nomeada do J.A.R.V.I.S.
zellij attach -c jarvis-cockpit

# Listar sessões ativas
zellij list-sessions

# Executar comando isolado em novo painel flutuante
zellij run --floating -- python jarvis.py --doctor

# Enviar comandos ou ações para painel existente
zellij action write-chars "python benchmarks/context_budget_benchmark.py"
```

## 4. Integração em Missões Autônomas
Quando o operador solicitar orquestração de terminais ou tarefas de longa duração:
1. Verifique a existência de binário sovereign em `D:\Program Files\jarvis-arsenal\binaries\` ou PATH.
2. Defina sessões nomeadas (`jarvis-*`) para permitir reconexão limpa sem perda de estado.
3. Utilize painéis flutuantes temporários para gates de verificação rápidos.
