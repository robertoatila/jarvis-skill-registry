# Plano Formal de Proposta de Promocao (Promotion Proposal Plan)

**Skill Registry v1.0.0 - Planejamento Governamental de Promocao (Dry-Run)**
- **Status**: DRY-RUN / DRAFT ONLY (Zero gravacoes no catalogo canonico)
- **Candidatos em Pauta**: **3 candidatos PROMOTION_READY**
- **Data/Hora (UTC)**: 2026-09-01T21:18:46.9681856Z

---

## 1. Resumo Executivo das Propostas

| Proposta | Candidato Origem | Destino Canonico Proposto | Score | Veredito Recomendado |
| :--- | :--- | :--- | :--- | :--- |
| prop-20260901-001-codex-qa | **codex-qa** | codex-plugin-qa | 90+ | **ADAPT_FIRST** |
| prop-20260901-002-senpi-qa | **senpi-qa** | subagent-task-qa | 90+ | **ADAPT_FIRST** |
| prop-20260901-003-get-unpublished-changes | **get-unpublished-changes** | git-unpublished-changes-audit | 90+ | **ADAPT_FIRST** |

---

## 2. Detalhamento Tecnico das 3 Propostas

### Proposta 1: codex-qa -> codex-plugin-qa

- **ID da Proposta**: `prop-20260901-001-codex-qa`
- **Candidato em Staging**: `cand-20260901T210528629Z-6af6f606`
- **Repositorio de Origem**: `code-yeongyu/oh-my-openagent`
- **Caminho de Origem**: `.agents/skills/codex-qa/SKILL.md`
- **Hash SHA-256 (No-BOM)**: `84a533b8f266a91351e67eda2ac1a2dd896afcbd20437cd7624e4b5c649b07ae`
- **Destino Canonico Proposto**: `E:\.skill-registry\skills/codex-plugin-qa/SKILL.md`
- **Skills Canonicas Relacionadas**: test-driven-development, verification-before-completion, javascript-testing-patterns
- **Analise de Conflito**: Zero destructive namespace collisions. Supplements test-driven-development with specialized Codex isolated runtime QA.
- **Estrategia de Rollback**: Atomic removal of skills/codex-plugin-qa/ directory and reversion of .skill-registry.lock Merkle anchor.
- **Decisao Recomendada**: **ADAPT_FIRST**
- **Racional**: Exceptional QA methodology for Codex plugins, but contains hardcoded repo paths that should be generalized during adaptation before final canonical promotion.

#### Adaptacoes Necessarias antes da Ingestao Canonica:
1. Generalize repository-specific paths (packages/omo-codex) into parameterized workspace variables ({PLUGIN_DIR}).
1. Normalize frontmatter name to 'codex-plugin-qa' to prevent collision with generic QA tools.
1. Add explicit cross-platform fallbacks for Windows environments lacking tmux/pty.

#### Impacto nos 6 Targets Suportados:
| Target Platform | Nivel de Suporte / Impacto |
| :--- | :--- |
| **gemini_antigravity** | COMPATIBLE (Markdown/YAML frontmatter) |
| **codex** | NATIVE_TARGET (Primary execution surface) |
| **claude_code** | COMPATIBLE (Tool/Command execution) |
| **chatgpt** | COMPATIBLE (Instructions/Prompt mode) |
| **cursor** | COMPATIBLE (Via .cursorrules integration) |
| **generic_agents** | COMPATIBLE (Standard markdown structure) |

---

### Proposta 2: senpi-qa -> subagent-task-qa

- **ID da Proposta**: `prop-20260901-002-senpi-qa`
- **Candidato em Staging**: `cand-20260901T210535435Z-5c950621`
- **Repositorio de Origem**: `code-yeongyu/oh-my-openagent`
- **Caminho de Origem**: `.agents/skills/senpi-qa/SKILL.md`
- **Hash SHA-256 (No-BOM)**: `30ba841c390b5c89dda6fa03fe36408940115d10e6facab0f0a0e5d1c04e722f`
- **Destino Canonico Proposto**: `E:\.skill-registry\skills/subagent-task-qa/SKILL.md`
- **Skills Canonicas Relacionadas**: subagent-driven-development, verification-before-completion
- **Analise de Conflito**: Zero collisions. Complements subagent-driven-development with deterministic evidence path resolution.
- **Estrategia de Rollback**: Atomic deletion of skills/subagent-task-qa/ and lockfile reconciliation.
- **Decisao Recomendada**: **ADAPT_FIRST**
- **Racional**: High-value evidence-based QA workflow, but tightly coupled to the 'senpi' binary; requires generalizing into a vendor-agnostic subagent QA skill.

#### Adaptacoes Necessarias antes da Ingestao Canonica:
1. Abstract senpi-specific binary calls into generic multi-agent task runner interfaces.
1. Retain the strict evidence resolution algorithm (path traversal rejection, slug validation).
1. Normalize frontmatter name to 'subagent-task-qa'.

#### Impacto nos 6 Targets Suportados:
| Target Platform | Nivel de Suporte / Impacto |
| :--- | :--- |
| **gemini_antigravity** | COMPATIBLE |
| **codex** | COMPATIBLE |
| **claude_code** | COMPATIBLE |
| **chatgpt** | COMPATIBLE |
| **cursor** | COMPATIBLE |
| **generic_agents** | COMPATIBLE |

---

### Proposta 3: get-unpublished-changes -> git-unpublished-changes-audit

- **ID da Proposta**: `prop-20260901-003-get-unpublished-changes`
- **Candidato em Staging**: `cand-20260901T210529531Z-f54c36ed`
- **Repositorio de Origem**: `code-yeongyu/oh-my-openagent`
- **Caminho de Origem**: `.agents/skills/get-unpublished-changes/SKILL.md`
- **Hash SHA-256 (No-BOM)**: `2eb5457817f5237c9084a54ecaefe29e9e4caa1ea47c3bcfd3bdf968f646c08e`
- **Destino Canonico Proposto**: `E:\.skill-registry\skills/git-unpublished-changes-audit/SKILL.md`
- **Skills Canonicas Relacionadas**: git-workflow-and-versioning, git-advanced-workflows, codebase-audit-pre-push
- **Analise de Conflito**: Complements git-workflow-and-versioning by providing a dedicated pre-release uncommitted/unpublished diff auditor.
- **Estrategia de Rollback**: Atomic deletion of skills/git-unpublished-changes-audit/.
- **Decisao Recomendada**: **ADAPT_FIRST**
- **Racional**: Exceptionally clean, focused, and immediately useful diff analyzer. A short adaptation phase to generalize the package layers will make it a universally applicable canonical skill.

#### Adaptacoes Necessarias antes da Ingestao Canonica:
1. Parameterize the release layers table (currently hardcoded to omo packages) into a flexible Monorepo / Package Layer structure.
1. Add support for Git tags, Cargo.toml, and pyproject.toml alongside package.json.
1. Ensure output format preserves the 'Layered Impact Matrix' and 'Semver Recommendation'.

#### Impacto nos 6 Targets Suportados:
| Target Platform | Nivel de Suporte / Impacto |
| :--- | :--- |
| **gemini_antigravity** | NATIVE_TARGET |
| **codex** | NATIVE_TARGET |
| **claude_code** | NATIVE_TARGET |
| **chatgpt** | COMPATIBLE |
| **cursor** | NATIVE_TARGET |
| **generic_agents** | NATIVE_TARGET |

---

## 3. Garantias Inviolaveis de Seguranca

1. **Nenhuma alteracao canÃ´nica executada**: O catalogo E:\.skill-registry e ~/.gemini/config/skills permanecem inalterados.
2. **Nenhuma ativacao de skill**: Nenhum adaptador gerou arquivos de distribuicao.
3. **Isolamento de Staging**: Todos os 20 arquivos ingeridos continuam restritos ao diretorio staging/github-inlet/candidates/.
