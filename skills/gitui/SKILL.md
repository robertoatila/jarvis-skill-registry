---
name: gitui
description: Ferramenta canônica gitui-org/gitui (22,577 estrelas).
squad: Hyperion
version: 1.0.0
upstream: https://github.com/gitui-org/gitui
---

# GITUI // Habilidade Operacional J.A.R.V.I.S.

## 1. Visão Tática e Propósito
- **Repositório Upstream:** [gitui-org/gitui](https://github.com/gitui-org/gitui) (22,577 estrelas ⭐)
- **Linguagem / Stack:** Rust
- **Esquadrão Responsável:** `Hyperion`
- **Missão:** Operações interativas de Git ultrarrápidas diretamente no terminal, staging em nível de bloco/hunk, visualização instantânea de diffs e resolução de conflitos sem overhead gráfico.

## 2. Diretrizes de Uso para o J.A.R.V.I.S.
- **Soberania Local:** Interação direta com o repositório Git local sem telemetria externa.
- **Controle Cirúrgico:** Ideal para auditorias pré-commit, inspeção visual de mudanças e staging granular.

## 3. Comandos Homologados & Receitas de Execução

```bash
# Lançar GitUI no repositório atual
gitui

# Lançar GitUI especificando o diretório de trabalho
gitui -d E:\.skill-registry

# Visualizar log e árvore de commits
# Dentro do GitUI: tecla 'l' para log, 's' para status, 'd' para diff
```

## 4. Integração em Missões Autônomas
1. Empregar quando inspeção visual detalhada de hunks e diffs de arquivos modificados for requerida pelo operador.
2. Usar em combinação com `tooling/audit_pre_publish_security.py` antes de aprovação final de commits.
