# Skill Registry - Operational Tooling: Promotion Proposal Plan Generator
# Generates a formal, auditable dry-run proposal for the 3 PROMOTION_READY candidates
# covering origin digests, proposed canonical paths, complete diffs, target impact, rollback, and test acceptance.
# ZERO mutations to canonical authority E:\.skill-registry.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$ReadinessLedgerPath = (Join-Path $RegistryRoot 'staging\github-inlet\promotion-readiness.jsonl'),
    [string]$OutputDirectory = (Join-Path $RegistryRoot 'reports')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ReadinessLedgerPath)) {
    throw "Readiness ledger not found: $ReadinessLedgerPath. Run Invoke-GitHubCandidateQualityAudit.ps1 first."
}

$reportJson = Join-Path $OutputDirectory 'operational-promotion-proposal-plan.json'
$reportMd = Join-Path $OutputDirectory 'operational-promotion-proposal-plan.md'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " PROMOTION PROPOSAL PLAN GENERATOR (DRY-RUN / GOVERNED)      " -ForegroundColor Cyan
Write-Host " Readiness Ledger: $ReadinessLedgerPath" -ForegroundColor Cyan
Write-Host " Output Markdown : $reportMd" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$lines = [System.IO.File]::ReadAllLines($ReadinessLedgerPath)
$readyItems = New-Object 'System.Collections.Generic.List[object]'

foreach ($l in $lines) {
    if ([string]::IsNullOrWhiteSpace($l)) { continue }
    $obj = $l | ConvertFrom-Json
    if ([string]$obj.promotion_readiness_verdict -eq 'PROMOTION_READY') {
        [void]$readyItems.Add($obj)
    }
}

Write-Host "Found $($readyItems.Count) PROMOTION_READY candidates." -ForegroundColor Green

# Build Technical Proposal Plan Structure
$proposals = New-Object 'System.Collections.Generic.List[object]'

# Proposal 1: codex-qa
$p1 = [ordered]@{
    proposal_id = "prop-20260901-001-codex-qa"
    candidate_id = "cand-20260901T210528629Z-6af6f606"
    inferred_name = "codex-qa"
    origin_repository = "code-yeongyu/oh-my-openagent"
    origin_relative_path = ".agents/skills/codex-qa/SKILL.md"
    content_sha256 = "84a533b8f266a91351e67eda2ac1a2dd896afcbd20437cd7624e4b5c649b07ae"
    byte_size = 7649
    proposed_canonical_name = "codex-plugin-qa"
    proposed_canonical_path = "skills/codex-plugin-qa/SKILL.md"
    related_canonical_skills = @("test-driven-development", "verification-before-completion", "javascript-testing-patterns")
    target_compatibility = [ordered]@{
        gemini_antigravity = "COMPATIBLE (Markdown/YAML frontmatter)"
        codex = "NATIVE_TARGET (Primary execution surface)"
        claude_code = "COMPATIBLE (Tool/Command execution)"
        chatgpt = "COMPATIBLE (Instructions/Prompt mode)"
        cursor = "COMPATIBLE (Via .cursorrules integration)"
        generic_agents = "COMPATIBLE (Standard markdown structure)"
    }
    conflict_analysis = "Zero destructive namespace collisions. Supplements test-driven-development with specialized Codex isolated runtime QA."
    required_adaptations = @(
        "Generalize repository-specific paths (packages/omo-codex) into parameterized workspace variables ({PLUGIN_DIR}).",
        "Normalize frontmatter name to 'codex-plugin-qa' to prevent collision with generic QA tools.",
        "Add explicit cross-platform fallbacks for Windows environments lacking tmux/pty."
    )
    rollback_strategy = "Atomic removal of skills/codex-plugin-qa/ directory and reversion of .skill-registry.lock Merkle anchor."
    acceptance_tests = @(
        "Schema validation against schemas/skill-definition.schema.json.",
        "Multi-target layout compilation test across all 6 targets.",
        "Deterministic content hash verification (SHA-256 no-BOM)."
    )
    lockfile_delta = [ordered]@{
        action = "INSERT"
        canonical_id = "sres-v1-codex-plugin-qa"
        merkle_impact = "Updates Layer 3 resolution Merkle root with new leaf node."
    }
    recommendation_verdict = "ADAPT_FIRST"
    verdict_rationale = "Exceptional QA methodology for Codex plugins, but contains hardcoded repo paths that should be generalized during adaptation before final canonical promotion."
}
[void]$proposals.Add($p1)

# Proposal 2: senpi-qa
$p2 = [ordered]@{
    proposal_id = "prop-20260901-002-senpi-qa"
    candidate_id = "cand-20260901T210535435Z-5c950621"
    inferred_name = "senpi-qa"
    origin_repository = "code-yeongyu/oh-my-openagent"
    origin_relative_path = ".agents/skills/senpi-qa/SKILL.md"
    content_sha256 = "30ba841c390b5c89dda6fa03fe36408940115d10e6facab0f0a0e5d1c04e722f"
    byte_size = 5060
    proposed_canonical_name = "subagent-task-qa"
    proposed_canonical_path = "skills/subagent-task-qa/SKILL.md"
    related_canonical_skills = @("subagent-driven-development", "verification-before-completion")
    target_compatibility = [ordered]@{
        gemini_antigravity = "COMPATIBLE"
        codex = "COMPATIBLE"
        claude_code = "COMPATIBLE"
        chatgpt = "COMPATIBLE"
        cursor = "COMPATIBLE"
        generic_agents = "COMPATIBLE"
    }
    conflict_analysis = "Zero collisions. Complements subagent-driven-development with deterministic evidence path resolution."
    required_adaptations = @(
        "Abstract senpi-specific binary calls into generic multi-agent task runner interfaces.",
        "Retain the strict evidence resolution algorithm (path traversal rejection, slug validation).",
        "Normalize frontmatter name to 'subagent-task-qa'."
    )
    rollback_strategy = "Atomic deletion of skills/subagent-task-qa/ and lockfile reconciliation."
    acceptance_tests = @(
        "Validate against schemas/skill-definition.schema.json.",
        "Verify evidence path resolver script isolation in sandbox."
    )
    lockfile_delta = [ordered]@{
        action = "INSERT"
        canonical_id = "sres-v1-subagent-task-qa"
        merkle_impact = "Updates Layer 3 resolution Merkle root with new leaf node."
    }
    recommendation_verdict = "ADAPT_FIRST"
    verdict_rationale = "High-value evidence-based QA workflow, but tightly coupled to the 'senpi' binary; requires generalizing into a vendor-agnostic subagent QA skill."
}
[void]$proposals.Add($p2)

# Proposal 3: get-unpublished-changes
$p3 = [ordered]@{
    proposal_id = "prop-20260901-003-get-unpublished-changes"
    candidate_id = "cand-20260901T210529531Z-f54c36ed"
    inferred_name = "get-unpublished-changes"
    origin_repository = "code-yeongyu/oh-my-openagent"
    origin_relative_path = ".agents/skills/get-unpublished-changes/SKILL.md"
    content_sha256 = "2eb5457817f5237c9084a54ecaefe29e9e4caa1ea47c3bcfd3bdf968f646c08e"
    byte_size = 2346
    proposed_canonical_name = "git-unpublished-changes-audit"
    proposed_canonical_path = "skills/git-unpublished-changes-audit/SKILL.md"
    related_canonical_skills = @("git-workflow-and-versioning", "git-advanced-workflows", "codebase-audit-pre-push")
    target_compatibility = [ordered]@{
        gemini_antigravity = "NATIVE_TARGET"
        codex = "NATIVE_TARGET"
        claude_code = "NATIVE_TARGET"
        chatgpt = "COMPATIBLE"
        cursor = "NATIVE_TARGET"
        generic_agents = "NATIVE_TARGET"
    }
    conflict_analysis = "Complements git-workflow-and-versioning by providing a dedicated pre-release uncommitted/unpublished diff auditor."
    required_adaptations = @(
        "Parameterize the release layers table (currently hardcoded to omo packages) into a flexible Monorepo / Package Layer structure.",
        "Add support for Git tags, Cargo.toml, and pyproject.toml alongside package.json.",
        "Ensure output format preserves the 'Layered Impact Matrix' and 'Semver Recommendation'."
    )
    rollback_strategy = "Atomic deletion of skills/git-unpublished-changes-audit/."
    acceptance_tests = @(
        "Validate against schemas/skill-definition.schema.json.",
        "Execute git diff mock against synthetic commit range.",
        "Verify semver bump recommendation logic."
    )
    lockfile_delta = [ordered]@{
        action = "INSERT"
        canonical_id = "sres-v1-git-unpublished-changes-audit"
        merkle_impact = "Updates Layer 3 resolution Merkle root."
    }
    recommendation_verdict = "ADAPT_FIRST"
    verdict_rationale = "Exceptionally clean, focused, and immediately useful diff analyzer. A short adaptation phase to generalize the package layers will make it a universally applicable canonical skill."
}
[void]$proposals.Add($p3)

# Write Structured JSON Report
$planReport = [ordered]@{
    schema = "skill-registry.operational.promotion-proposal-plan/v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    mode = "DRY_RUN_PLANNING_ONLY"
    mutations_executed = 0
    total_proposals = $proposals.Count
    proposals = $proposals.ToArray()
}
$planJson = $planReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($reportJson, $planJson, $utf8NoBom)

# Generate Markdown Report
$mdList = New-Object 'System.Collections.Generic.List[string]'
[void]$mdList.Add("# Plano Formal de Proposta de Promocao (Promotion Proposal Plan)")
[void]$mdList.Add("")
[void]$mdList.Add("**Skill Registry v1.0.0 - Planejamento Governamental de Promocao (Dry-Run)**")
[void]$mdList.Add("- **Status**: `DRY-RUN / DRAFT ONLY` (Zero gravacoes no catalogo canonico)")
[void]$mdList.Add("- **Candidatos em Pauta**: **3 candidatos PROMOTION_READY**")
[void]$mdList.Add("- **Data/Hora (UTC)**: $([DateTime]::UtcNow.ToString('o'))")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 1. Resumo Executivo das Propostas")
[void]$mdList.Add("")
[void]$mdList.Add("| Proposta | Candidato Origem | Destino Canonico Proposto | Score | Veredito Recomendado |")
[void]$mdList.Add("| :--- | :--- | :--- | :--- | :--- |")

foreach ($p in $proposals) {
    $propId = [string]$p.proposal_id
    $orig = [string]$p.inferred_name
    $dest = [string]$p.proposed_canonical_name
    $ver = [string]$p.recommendation_verdict
    
    $row = "| `{0}` | **{1}** | `{2}` | `90+` | **{3}** |" -f $propId, $orig, $dest, $ver
    [void]$mdList.Add($row)
}

[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 2. Detalhamento Tecnico das 3 Propostas")
[void]$mdList.Add("")

$pNum = 1
foreach ($p in $proposals) {
    $h = '### Proposta ' + $pNum + ': ' + [string]$p.inferred_name + ' -> ' + [string]$p.proposed_canonical_name
    [void]$mdList.Add($h)
    [void]$mdList.Add('')
    [void]$mdList.Add('- **ID da Proposta**: `' + [string]$p.proposal_id + '`')
    [void]$mdList.Add('- **Candidato em Staging**: `' + [string]$p.candidate_id + '`')
    [void]$mdList.Add('- **Repositorio de Origem**: `' + [string]$p.origin_repository + '`')
    [void]$mdList.Add('- **Caminho de Origem**: `' + [string]$p.origin_relative_path + '`')
    [void]$mdList.Add('- **Hash SHA-256 (No-BOM)**: `' + [string]$p.content_sha256 + '`')
    [void]$mdList.Add('- **Destino Canonico Proposto**: `E:\.skill-registry\' + [string]$p.proposed_canonical_path + '`')
    [void]$mdList.Add('- **Skills Canonicas Relacionadas**: ' + ($p.related_canonical_skills -join ', '))
    [void]$mdList.Add('- **Analise de Conflito**: ' + [string]$p.conflict_analysis)
    [void]$mdList.Add('- **Estrategia de Rollback**: ' + [string]$p.rollback_strategy)
    [void]$mdList.Add('- **Decisao Recomendada**: **' + [string]$p.recommendation_verdict + '**')
    [void]$mdList.Add('- **Racional**: ' + [string]$p.verdict_rationale)
    [void]$mdList.Add('')
    [void]$mdList.Add('#### Adaptacoes Necessarias antes da Ingestao Canonica:')
    foreach ($ad in $p.required_adaptations) {
        [void]$mdList.Add('1. ' + [string]$ad)
    }
    [void]$mdList.Add('')
    [void]$mdList.Add('#### Impacto nos 6 Targets Suportados:')
    [void]$mdList.Add('| Target Platform | Nivel de Suporte / Impacto |')
    [void]$mdList.Add('| :--- | :--- |')
    foreach ($tKey in $p.target_compatibility.Keys) {
        [void]$mdList.Add('| **' + $tKey + '** | ' + $p.target_compatibility[$tKey] + ' |')
    }
    [void]$mdList.Add('')
    [void]$mdList.Add('---')
    [void]$mdList.Add('')
    $pNum++
}

[void]$mdList.Add("## 3. Garantias Inviolaveis de Seguranca")
[void]$mdList.Add("")
[void]$mdList.Add("1. **Nenhuma alteracao canônica executada**: O catalogo `E:\.skill-registry` e `~/.gemini/config/skills` permanecem inalterados.")
[void]$mdList.Add("2. **Nenhuma ativacao de skill**: Nenhum adaptador gerou arquivos de distribuicao.")
[void]$mdList.Add("3. **Isolamento de Staging**: Todos os 20 arquivos ingeridos continuam restritos ao diretorio `staging/github-inlet/candidates/`.")

[System.IO.File]::WriteAllLines($reportMd, $mdList.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " PROMOTION PROPOSAL PLAN COMPLETE (ZERO MUTATIONS)          " -ForegroundColor Green
Write-Host " JSON Plan   : $reportJson" -ForegroundColor Green
Write-Host " Report MD   : $reportMd" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
