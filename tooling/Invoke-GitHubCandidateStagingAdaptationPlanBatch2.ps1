# Skill Registry - Operational Tooling: Staging Adaptation Plan for Batch 2 (9 Candidates)
# Produces an auditable, non-mutating adaptation plan for the 9 remaining candidates in staging.
# ZERO mutations to canonical authority, ZERO automatic execution, ZERO installations.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$EvaluatedLedger = (Join-Path $RegistryRoot 'staging\github-inlet\evaluated-candidates.jsonl'),
    [string]$ReportMd = (Join-Path $RegistryRoot 'reports\operational-staging-adaptation-plan-batch2.md'),
    [string]$ReportJson = (Join-Path $RegistryRoot 'reports\operational-staging-adaptation-plan-batch2.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " OPERACAO 9: PLANO DE ADAPTACAO EM STAGING (9 CANDIDATOS)   " -ForegroundColor Cyan
Write-Host " Modo: DRY-RUN / PLANEJAMENTO DETALHADO                     " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$planItems = @(
    [ordered]@{
        candidate_id = "cand-20260901T210534834Z-5a61c6e4"
        original_name = "security-research"
        proposed_name = "security-research-audit"
        byte_size = 7785
        content_sha256 = "3110b1ce31999ba534211fe98e387437dbeff0aac7a79400f5713a5e5b3b1a7a"
        origin_relative_path = ".agents/skills/security-research/SKILL.md"
        upstream_couplings = @("Internal agent path references (.omo/evidence/)", "Coupling to specific vulnerability scanning output formats")
        required_adaptations = @(
            "Normalize frontmatter name to 'security-research-audit'.",
            "Parameterize evidence directory to ${EVIDENCE_DIR:-.evidence/security-research}.",
            "Generalize dependency vulnerability hunting instructions (npm audit, pip-audit, cargo-audit, snyk).",
            "Ensure read-only inspection contract: forbids live automated exploit attempts."
        )
        gate2_policy = "READ_ONLY_INSPECTION"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210536037Z-afadf6dc"
        original_name = "tech-debt-audit"
        proposed_name = "tech-debt-audit"
        byte_size = 13215
        content_sha256 = "39530a6d8bef1c1b9d1d2a22f5a86ead4d7b472c3c092275ffad7c58d1ecc763"
        origin_relative_path = ".agents/skills/tech-debt-audit/SKILL.md"
        upstream_couplings = @("Hardcoded repo tags and monorepo packaging schemas", "Vendor-specific debt categorization")
        required_adaptations = @(
            "Normalize frontmatter name and description to universal standards.",
            "Establish universal debt classification (Architectural, Testing, Documentation, Dependency, Code Quality).",
            "Parameterize workspace scan scope and exclude generated/build artifacts.",
            "Produce structured Markdown / JSON Debt Scorecard."
        )
        gate2_policy = "NON_MUTATING_INSPECTION"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210530115Z-e3733fd3"
        original_name = "github-triage"
        proposed_name = "github-issue-pr-triage"
        byte_size = 17119
        content_sha256 = "ebdf623f6da692d7987293d20a36fd3fb7fc5e71cebd04ffc3640ad7686d67bd"
        origin_relative_path = ".agents/skills/github-triage/SKILL.md"
        upstream_couplings = @("Specific bot label conventions", "Private triage workflow automations")
        required_adaptations = @(
            "Normalize name to 'github-issue-pr-triage'.",
            "Standardize gh CLI commands with non-interactive flags (--json, --limit).",
            "Decouple custom label taxonomies into customizable workflow configuration.",
            "Ensure triage outputs actionable prioritization matrices without automated push/write actions."
        )
        gate2_policy = "TRIAGE_ONLY_NO_UNAUTHORIZED_WRITES"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210530791Z-f4fdd0fc"
        original_name = "hyperplan"
        proposed_name = "hyperplan-orchestrator"
        byte_size = 25905
        content_sha256 = "c4d62069605a9080e625f8cadf0e8ac97652748e202562ba5f980720bdd10687"
        origin_relative_path = ".agents/skills/hyperplan/SKILL.md"
        upstream_couplings = @("Complex internal openagent meta-tags", "Verbose prompt scaffolding")
        required_adaptations = @(
            "Normalize frontmatter name to 'hyperplan-orchestrator'.",
            "Streamline plan stages into atomic markdown phases compatible with standard LLM contexts.",
            "Preserve Manus-style persistent file-based planning conventions.",
            "Eliminate redundant internal macro definitions."
        )
        gate2_policy = "CONTEXT_SAFE_PLANNING"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210534195Z-ccf34207"
        original_name = "remove-deadcode"
        proposed_name = "deadcode-elimination"
        byte_size = 7262
        content_sha256 = "2323273413f220a68e43c46c81d97396d46d28adfce02c935c38d9c434d10d2f"
        origin_relative_path = ".agents/skills/remove-deadcode/SKILL.md"
        upstream_couplings = @("Assumptions of specific AST tools (ts-prune, knip) without fallbacks")
        required_adaptations = @(
            "Normalize frontmatter name to 'deadcode-elimination'.",
            "Add safety-first gate: require compilation and test verification BEFORE removing code.",
            "Add multi-language dead code discovery guidelines (TS/JS, Python, Go, Java, Rust).",
            "Enforce atomic git commit per deadcode removal batch."
        )
        gate2_policy = "TEST_VERIFIED_DESTRUCTION_PREVENTION"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210536660Z-50c856c2"
        original_name = "work-with-pr"
        proposed_name = "pr-review-resolution"
        byte_size = 18663
        content_sha256 = "2daaab7275a5dc02f517e73deedf4763def22be25f83165fe48ab67b5be80cce"
        origin_relative_path = ".agents/skills/work-with-pr/SKILL.md"
        upstream_couplings = @("Internal agent PR comment formatting", "Private code review bot references")
        required_adaptations = @(
            "Normalize name to 'pr-review-resolution'.",
            "Generalize PR feedback resolution workflow using gh api and git diff.",
            "Structure resolution checklist: Understand -> Reproduce -> Fix -> Test -> Reply.",
            "Forbid unverified force-pushes or PR closing actions."
        )
        gate2_policy = "NON_DESTRUCTIVE_PR_WORKFLOW"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210532027Z-5bc1350b"
        original_name = "opencode-qa"
        proposed_name = "opencode-runtime-qa"
        byte_size = 11537
        content_sha256 = "59fc3708b6b6625cdc6c7c39e249b49088f52b0cae322d63a827b4883cc6b81a"
        origin_relative_path = ".agents/skills/opencode-qa/SKILL.md"
        upstream_couplings = @("Internal packages/opencode layout", "Proprietary openagent turn assertions")
        required_adaptations = @(
            "Normalize name to 'opencode-runtime-qa'.",
            "Parameterize workspace runtime paths and test fixtures.",
            "Enforce sandbox isolation similar to codex-plugin-qa.",
            "Ensure cross-platform compatibility across Windows and POSIX environments."
        )
        gate2_policy = "SANDBOX_ISOLATION_ENFORCED"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210532664Z-f4ff8559"
        original_name = "pre-publish-review"
        proposed_name = "package-pre-publish-audit"
        byte_size = 17136
        content_sha256 = "a4a46f747a6819e9d83809cd47450372887314aebf3aa2a24662091e3211695d"
        origin_relative_path = ".agents/skills/pre-publish-review/SKILL.md"
        upstream_couplings = @("NPM-only publishing assumptions", "Internal license and badge assertions")
        required_adaptations = @(
            "Normalize name to 'package-pre-publish-audit'.",
            "Expand pre-publish checks to support npm, PyPI, Cargo, and Maven.",
            "Audit bundle contents (npm pack --dry-run / cargo package --list) to prevent accidental secret leakage.",
            "Verify semantic versioning consistency and changelog updates."
        )
        gate2_policy = "SECRET_LEAKAGE_PREVENTION"
    },
    [ordered]@{
        candidate_id = "cand-20260901T210533334Z-1d562314"
        original_name = "publish"
        proposed_name = "governed-package-publish"
        byte_size = 21937
        content_sha256 = "17746aab1bc06f1d633a94cc243c2cc6b672e53972da477cca2565ec99a03b6d"
        origin_relative_path = ".agents/skills/publish/SKILL.md"
        upstream_couplings = @("Unchecked push commands", "Specific registry credentials handling")
        required_adaptations = @(
            "Normalize name to 'governed-package-publish'.",
            "CRITICAL GATE 2 ENFORCEMENT: Strictly prohibit 'git push --force' and 'git push -f' with hard failure rules.",
            "Require explicit two-phase dry-run: Dry-Run Verification -> Explicit Human Confirmation -> Publish.",
            "Decouple registry publish commands for npm, PyPI, and Crates.io with token safety guards."
        )
        gate2_policy = "STRICT_FORCE_PUSH_BLOCK_MANDATORY"
    }
)

# Generate JSON Report
$planReport = [ordered]@{
    schema = "skill-registry.operational.staging-adaptation-plan-batch2/v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    mode = "PLANNING_ONLY_NO_MUTATION"
    total_candidates_in_plan = $planItems.Count
    plan_items = $planItems
}
[System.IO.File]::WriteAllText($ReportJson, ($planReport | ConvertTo-Json -Depth 10), $utf8NoBom)

# Generate Markdown Report
$md = New-Object 'System.Collections.Generic.List[string]'
[void]$md.Add('# Operacao 9: Plano de Adaptacao em Staging (9 Candidatos Restantes)')
[void]$md.Add('')
[void]$md.Add('**Skill Registry v1.0.0 - Planejamento Governamental de Staging Adaptation**')
[void]$md.Add('- **Modo de Operacao**: `DRY-RUN / PLANEJAMENTO ESTRITO`')
[void]$md.Add('- **Mutacoes Canonicas Executadas**: `ZERO`')
[void]$md.Add('- **Candidatos Incluidos**: **9 artefatos classificados como NEEDS_ADAPTATION**')
[void]$md.Add('- **Data/Hora (UTC)**: ' + [DateTime]::UtcNow.ToString('o'))
[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 1. Resumo dos 9 Candidatos para Adaptacao em Staging')
[void]$md.Add('')
[void]$md.Add('| Candidato Original | Nome Adaptado Proposto | Tamanho | SHA-256 Original | Politica de Seguranca Gate 2 |')
[void]$md.Add('| :--- | :--- | :--- | :--- | :--- |')

foreach ($it in $planItems) {
    $row = '| **' + $it.original_name + '** | `' + $it.proposed_name + '` | ' + $it.byte_size + ' B | `' + $it.content_sha256.Substring(0, 14) + '...` | `' + $it.gate2_policy + '` |'
    [void]$md.Add($row)
}

[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 2. Detalhamento Tecnico das Adaptacoes Planejadas')
[void]$md.Add('')

$idx = 1
foreach ($it in $planItems) {
    [void]$md.Add('### ' + $idx + '. ' + $it.original_name + ' -> ' + $it.proposed_name)
    [void]$md.Add('- **Candidato ID**: `' + $it.candidate_id + '`')
    [void]$md.Add('- **Origem em Staging**: `' + $it.origin_relative_path + '`')
    [void]$md.Add('- **Destino em Staging**: `staging/github-inlet/adapted/' + $it.proposed_name + '/SKILL.md`')
    [void]$md.Add('- **Acoplamentos Upstream a Eliminar**:')
    foreach ($c in $it.upstream_couplings) {
        [void]$md.Add('  - ' + $c)
    }
    [void]$md.Add('- **Adaptacoes Obrigatorias**:')
    foreach ($ad in $it.required_adaptations) {
        [void]$md.Add('  1. ' + $ad)
    }
    [void]$md.Add('- **Invariante de Seguranca**: `' + $it.gate2_policy + '`')
    [void]$md.Add('')
    $idx++
}

[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 3. Invariante Especial: Bloqueio de `git push --force` em `publish`')
[void]$md.Add('')
[void]$md.Add('Conforme definido no Gate 2, a skill `governed-package-publish` (adaptada de `publish`) contera instrucoes formais de rejeicao expressa:')
[void]$md.Add('```text')
[void]$md.Add('CRITICAL POLICY: git push --force / git push -f is STRICTLY PROHIBITED.')
[void]$md.Add('Publishing workflows must always rely on linear, verified history tags.')
[void]$md.Add('```')
[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 4. Garantias e Invariantes de Governanca')
[void]$md.Add('')
[void]$md.Add('1. **Zero Promocao Automatica**: Nenhuma das 9 skills sera promovida para `E:\.skill-registry\skills` nesta operacao.')
[void]$md.Add('2. **Zero Distribuicao**: Nenhum arquivo sera copiado para `~/.gemini/config/skills` ou outros targets.')
[void]$md.Add('3. **Isolamento de Staging**: Todo o trabalho sera confinado a `staging/github-inlet/adapted/`.')
[void]$md.Add('4. **Preservacao dos Originais**: Os arquivos brutos em `staging/github-inlet/candidates/` permanecem intocados.')
[void]$md.Add('5. **Parada Obrigatoria**: Este plano necessita de aprovacao explicita antes de qualquer gravacao.')

[System.IO.File]::WriteAllLines($ReportMd, $md.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " PLANO DE ADAPTACAO DA OPERACAO 9 GERADO COM SUCESSO        " -ForegroundColor Green
Write-Host " Report MD   : $ReportMd" -ForegroundColor Green
Write-Host " Report JSON : $ReportJson" -ForegroundColor Green
Write-Host " Status      : PENDING_HUMAN_APPROVAL                       " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
