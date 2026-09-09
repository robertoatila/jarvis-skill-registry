# Operacao 9: Plano de Adaptacao em Staging (9 Candidatos Restantes)

**Skill Registry v1.0.0 - Planejamento Governamental de Staging Adaptation**
- **Modo de Operacao**: `DRY-RUN / PLANEJAMENTO ESTRITO`
- **Mutacoes Canonicas Executadas**: `ZERO`
- **Candidatos Incluidos**: **9 artefatos classificados como NEEDS_ADAPTATION**
- **Data/Hora (UTC)**: 2026-09-02T20:47:16.5590836Z

---

## 1. Resumo dos 9 Candidatos para Adaptacao em Staging

| Candidato Original | Nome Adaptado Proposto | Tamanho | SHA-256 Original | Politica de Seguranca Gate 2 |
| :--- | :--- | :--- | :--- | :--- |
| **security-research** | `security-research-audit` | 7785 B | `3110b1ce31999b...` | `READ_ONLY_INSPECTION` |
| **tech-debt-audit** | `tech-debt-audit` | 13215 B | `39530a6d8bef1c...` | `NON_MUTATING_INSPECTION` |
| **github-triage** | `github-issue-pr-triage` | 17119 B | `ebdf623f6da692...` | `TRIAGE_ONLY_NO_UNAUTHORIZED_WRITES` |
| **hyperplan** | `hyperplan-orchestrator` | 25905 B | `c4d62069605a90...` | `CONTEXT_SAFE_PLANNING` |
| **remove-deadcode** | `deadcode-elimination` | 7262 B | `2323273413f220...` | `TEST_VERIFIED_DESTRUCTION_PREVENTION` |
| **work-with-pr** | `pr-review-resolution` | 18663 B | `2daaab7275a5dc...` | `NON_DESTRUCTIVE_PR_WORKFLOW` |
| **opencode-qa** | `opencode-runtime-qa` | 11537 B | `59fc3708b6b662...` | `SANDBOX_ISOLATION_ENFORCED` |
| **pre-publish-review** | `package-pre-publish-audit` | 17136 B | `a4a46f747a6819...` | `SECRET_LEAKAGE_PREVENTION` |
| **publish** | `governed-package-publish` | 21937 B | `17746aab1bc06f...` | `STRICT_FORCE_PUSH_BLOCK_MANDATORY` |

---

## 2. Detalhamento Tecnico das Adaptacoes Planejadas

### 1. security-research -> security-research-audit
- **Candidato ID**: `cand-20260901T210534834Z-5a61c6e4`
- **Origem em Staging**: `.agents/skills/security-research/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/security-research-audit/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Internal agent path references (.omo/evidence/)
  - Coupling to specific vulnerability scanning output formats
- **Adaptacoes Obrigatorias**:
  1. Normalize frontmatter name to 'security-research-audit'.
  1. Parameterize evidence directory to .
  1. Generalize dependency vulnerability hunting instructions (npm audit, pip-audit, cargo-audit, snyk).
  1. Ensure read-only inspection contract: forbids live automated exploit attempts.
- **Invariante de Seguranca**: `READ_ONLY_INSPECTION`

### 2. tech-debt-audit -> tech-debt-audit
- **Candidato ID**: `cand-20260901T210536037Z-afadf6dc`
- **Origem em Staging**: `.agents/skills/tech-debt-audit/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/tech-debt-audit/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Hardcoded repo tags and monorepo packaging schemas
  - Vendor-specific debt categorization
- **Adaptacoes Obrigatorias**:
  1. Normalize frontmatter name and description to universal standards.
  1. Establish universal debt classification (Architectural, Testing, Documentation, Dependency, Code Quality).
  1. Parameterize workspace scan scope and exclude generated/build artifacts.
  1. Produce structured Markdown / JSON Debt Scorecard.
- **Invariante de Seguranca**: `NON_MUTATING_INSPECTION`

### 3. github-triage -> github-issue-pr-triage
- **Candidato ID**: `cand-20260901T210530115Z-e3733fd3`
- **Origem em Staging**: `.agents/skills/github-triage/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/github-issue-pr-triage/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Specific bot label conventions
  - Private triage workflow automations
- **Adaptacoes Obrigatorias**:
  1. Normalize name to 'github-issue-pr-triage'.
  1. Standardize gh CLI commands with non-interactive flags (--json, --limit).
  1. Decouple custom label taxonomies into customizable workflow configuration.
  1. Ensure triage outputs actionable prioritization matrices without automated push/write actions.
- **Invariante de Seguranca**: `TRIAGE_ONLY_NO_UNAUTHORIZED_WRITES`

### 4. hyperplan -> hyperplan-orchestrator
- **Candidato ID**: `cand-20260901T210530791Z-f4fdd0fc`
- **Origem em Staging**: `.agents/skills/hyperplan/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/hyperplan-orchestrator/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Complex internal openagent meta-tags
  - Verbose prompt scaffolding
- **Adaptacoes Obrigatorias**:
  1. Normalize frontmatter name to 'hyperplan-orchestrator'.
  1. Streamline plan stages into atomic markdown phases compatible with standard LLM contexts.
  1. Preserve Manus-style persistent file-based planning conventions.
  1. Eliminate redundant internal macro definitions.
- **Invariante de Seguranca**: `CONTEXT_SAFE_PLANNING`

### 5. remove-deadcode -> deadcode-elimination
- **Candidato ID**: `cand-20260901T210534195Z-ccf34207`
- **Origem em Staging**: `.agents/skills/remove-deadcode/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/deadcode-elimination/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Assumptions of specific AST tools (ts-prune, knip) without fallbacks
- **Adaptacoes Obrigatorias**:
  1. Normalize frontmatter name to 'deadcode-elimination'.
  1. Add safety-first gate: require compilation and test verification BEFORE removing code.
  1. Add multi-language dead code discovery guidelines (TS/JS, Python, Go, Java, Rust).
  1. Enforce atomic git commit per deadcode removal batch.
- **Invariante de Seguranca**: `TEST_VERIFIED_DESTRUCTION_PREVENTION`

### 6. work-with-pr -> pr-review-resolution
- **Candidato ID**: `cand-20260901T210536660Z-50c856c2`
- **Origem em Staging**: `.agents/skills/work-with-pr/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/pr-review-resolution/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Internal agent PR comment formatting
  - Private code review bot references
- **Adaptacoes Obrigatorias**:
  1. Normalize name to 'pr-review-resolution'.
  1. Generalize PR feedback resolution workflow using gh api and git diff.
  1. Structure resolution checklist: Understand -> Reproduce -> Fix -> Test -> Reply.
  1. Forbid unverified force-pushes or PR closing actions.
- **Invariante de Seguranca**: `NON_DESTRUCTIVE_PR_WORKFLOW`

### 7. opencode-qa -> opencode-runtime-qa
- **Candidato ID**: `cand-20260901T210532027Z-5bc1350b`
- **Origem em Staging**: `.agents/skills/opencode-qa/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/opencode-runtime-qa/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Internal packages/opencode layout
  - Proprietary openagent turn assertions
- **Adaptacoes Obrigatorias**:
  1. Normalize name to 'opencode-runtime-qa'.
  1. Parameterize workspace runtime paths and test fixtures.
  1. Enforce sandbox isolation similar to codex-plugin-qa.
  1. Ensure cross-platform compatibility across Windows and POSIX environments.
- **Invariante de Seguranca**: `SANDBOX_ISOLATION_ENFORCED`

### 8. pre-publish-review -> package-pre-publish-audit
- **Candidato ID**: `cand-20260901T210532664Z-f4ff8559`
- **Origem em Staging**: `.agents/skills/pre-publish-review/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/package-pre-publish-audit/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - NPM-only publishing assumptions
  - Internal license and badge assertions
- **Adaptacoes Obrigatorias**:
  1. Normalize name to 'package-pre-publish-audit'.
  1. Expand pre-publish checks to support npm, PyPI, Cargo, and Maven.
  1. Audit bundle contents (npm pack --dry-run / cargo package --list) to prevent accidental secret leakage.
  1. Verify semantic versioning consistency and changelog updates.
- **Invariante de Seguranca**: `SECRET_LEAKAGE_PREVENTION`

### 9. publish -> governed-package-publish
- **Candidato ID**: `cand-20260901T210533334Z-1d562314`
- **Origem em Staging**: `.agents/skills/publish/SKILL.md`
- **Destino em Staging**: `staging/github-inlet/adapted/governed-package-publish/SKILL.md`
- **Acoplamentos Upstream a Eliminar**:
  - Unchecked push commands
  - Specific registry credentials handling
- **Adaptacoes Obrigatorias**:
  1. Normalize name to 'governed-package-publish'.
  1. CRITICAL GATE 2 ENFORCEMENT: Strictly prohibit 'git push --force' and 'git push -f' with hard failure rules.
  1. Require explicit two-phase dry-run: Dry-Run Verification -> Explicit Human Confirmation -> Publish.
  1. Decouple registry publish commands for npm, PyPI, and Crates.io with token safety guards.
- **Invariante de Seguranca**: `STRICT_FORCE_PUSH_BLOCK_MANDATORY`

---

## 3. Invariante Especial: Bloqueio de `git push --force` em `publish`

Conforme definido no Gate 2, a skill `governed-package-publish` (adaptada de `publish`) contera instrucoes formais de rejeicao expressa:
```text
CRITICAL POLICY: git push --force / git push -f is STRICTLY PROHIBITED.
Publishing workflows must always rely on linear, verified history tags.
```

---

## 4. Garantias e Invariantes de Governanca

1. **Zero Promocao Automatica**: Nenhuma das 9 skills sera promovida para `E:\.skill-registry\skills` nesta operacao.
2. **Zero Distribuicao**: Nenhum arquivo sera copiado para `~/.gemini/config/skills` ou outros targets.
3. **Isolamento de Staging**: Todo o trabalho sera confinado a `staging/github-inlet/adapted/`.
4. **Preservacao dos Originais**: Os arquivos brutos em `staging/github-inlet/candidates/` permanecem intocados.
5. **Parada Obrigatoria**: Este plano necessita de aprovacao explicita antes de qualquer gravacao.
