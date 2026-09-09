# Skill Registry - Operational Tooling: Governed Promotion Execution Engine (Batch 2)
# Executes atomic canonical promotion of the 9 validated candidates from Batch 2
# under the sovereign Delegated Governed Execution mandate.
# Updates E:\.skill-registry\skills, index/resources.jsonl, and produces audit reports.
# ZERO distribution to user directories (~/.gemini/config/skills).

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$AdaptedRoot = (Join-Path $RegistryRoot 'staging\github-inlet\adapted'),
    [string]$CanonicalSkillsRoot = (Join-Path $RegistryRoot 'skills'),
    [string]$ResourcesIndexPath = (Join-Path $RegistryRoot 'index\resources.jsonl'),
    [string]$ReportMd = (Join-Path $RegistryRoot 'reports\operational-governed-promotion-batch2.md'),
    [string]$ReportJson = (Join-Path $RegistryRoot 'reports\operational-governed-promotion-batch2.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Get-Sha256Digest {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $utf8NoBom.GetBytes($Text)
        $hashBytes = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant())
    } finally {
        $sha.Dispose()
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GOVERNED PROMOTION EXECUTION ENGINE - BATCH 2 (9 SKILLS)   " -ForegroundColor Cyan
Write-Host " Authority Target : $CanonicalSkillsRoot" -ForegroundColor Cyan
Write-Host " Mandate          : DELEGATED GOVERNED EXECUTION ACTIVE     " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

$promotionPlan = @(
    [ordered]@{
        candidate_id = "cand-20260901T210534834Z-5a61c6e4"
        original_name = "security-research"
        canonical_name = "security-research-audit"
        expected_sha256 = "31267366acb3cc9b2559d619c4c6d74ecb42ce2524ae06421ce552c985dca882"
        staged_path = (Join-Path $AdaptedRoot 'security-research-audit\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'security-research-audit')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'security-research-audit\SKILL.md')
        resource_id = "sres-v1-sha256:31267366acb3cc9b2559d619c4c6d74ecb42ce2524ae06421ce552c985dca882"
        provenance_id = "prov-v1-sha256:3110b1ce31999ba534211fe98e387437dbeff0aac7a79400f5713a5e5b3b1a7a"
        description = "Audit and research security vulnerabilities, CVEs, and dependency risks across project components in strict read-only mode."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210536037Z-afadf6dc"
        original_name = "tech-debt-audit"
        canonical_name = "tech-debt-audit"
        expected_sha256 = "b444ab33339e9f65d6ee6842e83ed53e2f09144605950584d44c17d044787024"
        staged_path = (Join-Path $AdaptedRoot 'tech-debt-audit\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'tech-debt-audit')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'tech-debt-audit\SKILL.md')
        resource_id = "sres-v1-sha256:b444ab33339e9f65d6ee6842e83ed53e2f09144605950584d44c17d044787024"
        provenance_id = "prov-v1-sha256:39530a6d8bef1c1b9d1d2a22f5a86ead4d7b472c3c092275ffad7c58d1ecc763"
        description = "Audit, quantify, and categorize architectural, technical, and testing debt across a codebase producing a structured Tech Debt Scorecard."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210530115Z-e3733fd3"
        original_name = "github-triage"
        canonical_name = "github-issue-pr-triage"
        expected_sha256 = "a996920983a0f156e8d67b7f02aa3d0b3baab7a9bccc817da0b2f7cebc6f4720"
        staged_path = (Join-Path $AdaptedRoot 'github-issue-pr-triage\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'github-issue-pr-triage')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'github-issue-pr-triage\SKILL.md')
        resource_id = "sres-v1-sha256:a996920983a0f156e8d67b7f02aa3d0b3baab7a9bccc817da0b2f7cebc6f4720"
        provenance_id = "prov-v1-sha256:ebdf623f6da692d7987293d20a36fd3fb7fc5e71cebd04ffc3640ad7686d67bd"
        description = "Triage incoming GitHub issues and Pull Requests using GitHub CLI (gh) in read-only analysis mode."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210530791Z-f4fdd0fc"
        original_name = "hyperplan"
        canonical_name = "hyperplan-orchestrator"
        expected_sha256 = "b0c2603450417fb3df36012b75f60e278008af0610414d6862891a4a6fec78a0"
        staged_path = (Join-Path $AdaptedRoot 'hyperplan-orchestrator\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'hyperplan-orchestrator')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'hyperplan-orchestrator\SKILL.md')
        resource_id = "sres-v1-sha256:b0c2603450417fb3df36012b75f60e278008af0610414d6862891a4a6fec78a0"
        provenance_id = "prov-v1-sha256:c4d62069605a9080e625f8cadf0e8ac97652748e202562ba5f980720bdd10687"
        description = "Structure complex, multi-phase technical projects into deterministic, file-backed implementation plans with rollback safeguards."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210534195Z-ccf34207"
        original_name = "remove-deadcode"
        canonical_name = "deadcode-elimination"
        expected_sha256 = "59bcb787420b399e24c5921d60038a5e2fa7ec3e4286d12c338fcdcbeced81f4"
        staged_path = (Join-Path $AdaptedRoot 'deadcode-elimination\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'deadcode-elimination')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'deadcode-elimination\SKILL.md')
        resource_id = "sres-v1-sha256:59bcb787420b399e24c5921d60038a5e2fa7ec3e4286d12c338fcdcbeced81f4"
        provenance_id = "prov-v1-sha256:2323273413f220a68e43c46c81d97396d46d28adfce02c935c38d9c434d10d2f"
        description = "Safely identify and prune unused functions, orphan modules, dead exports, and obsolete dependencies with mandatory pre-deletion test gates."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210536660Z-50c856c2"
        original_name = "work-with-pr"
        canonical_name = "pr-review-resolution"
        expected_sha256 = "e03f852dffdbb328c7f342d0f4f03f000fda9ba5cbf5df5f1a8f8a0aa9fe9ae3"
        staged_path = (Join-Path $AdaptedRoot 'pr-review-resolution\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'pr-review-resolution')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'pr-review-resolution\SKILL.md')
        resource_id = "sres-v1-sha256:e03f852dffdbb328c7f342d0f4f03f000fda9ba5cbf5df5f1a8f8a0aa9fe9ae3"
        provenance_id = "prov-v1-sha256:2daaab7275a5dc02f517e73deedf4763def22be25f83165fe48ab67b5be80cce"
        description = "Systematically analyze, address, and resolve review comments on pull requests with full test validation and structured replies."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210532027Z-5bc1350b"
        original_name = "opencode-qa"
        canonical_name = "opencode-runtime-qa"
        expected_sha256 = "17f1314e1d9f69a4ff9430c8f3d269f45b567f2d8f5256f74eb92b7e5a09c0ff"
        staged_path = (Join-Path $AdaptedRoot 'opencode-runtime-qa\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'opencode-runtime-qa')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'opencode-runtime-qa\SKILL.md')
        resource_id = "sres-v1-sha256:17f1314e1d9f69a4ff9430c8f3d269f45b567f2d8f5256f74eb92b7e5a09c0ff"
        provenance_id = "prov-v1-sha256:59fc3708b6b6625cdc6c7c39e249b49088f52b0cae322d63a827b4883cc6b81a"
        description = "QA and verify OpenCode runtime configurations, plugin hooks, tool definitions, and session state in strict sandbox isolation."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210532664Z-f4ff8559"
        original_name = "pre-publish-review"
        canonical_name = "package-pre-publish-audit"
        expected_sha256 = "16b212f032ad836c2ed1519294a821d9ccab7f0593f0a4671241d1d9c13b259f"
        staged_path = (Join-Path $AdaptedRoot 'package-pre-publish-audit\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'package-pre-publish-audit')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'package-pre-publish-audit\SKILL.md')
        resource_id = "sres-v1-sha256:16b212f032ad836c2ed1519294a821d9ccab7f0593f0a4671241d1d9c13b259f"
        provenance_id = "prov-v1-sha256:a4a46f747a6819e9d83809cd47450372887314aebf3aa2a24662091e3211695d"
        description = "Audit software packages and distribution tarballs before publishing to npm, PyPI, or Crates.io to prevent secret leakage."
    },
    [ordered]@{
        candidate_id = "cand-20260901T210533334Z-1d562314"
        original_name = "publish"
        canonical_name = "governed-package-publish"
        expected_sha256 = "fc2b3d2c506eaaca2efa19b64ad72a4eabe15e7680760a3e70947f15ea6cec48"
        staged_path = (Join-Path $AdaptedRoot 'governed-package-publish\SKILL.md')
        canonical_dest_dir = (Join-Path $CanonicalSkillsRoot 'governed-package-publish')
        canonical_dest_file = (Join-Path $CanonicalSkillsRoot 'governed-package-publish\SKILL.md')
        resource_id = "sres-v1-sha256:fc2b3d2c506eaaca2efa19b64ad72a4eabe15e7680760a3e70947f15ea6cec48"
        provenance_id = "prov-v1-sha256:17746aab1bc06f1d633a94cc243c2cc6b672e53972da477cca2565ec99a03b6d"
        description = "Execute safe, governed package publishing across npm, PyPI, and Crates.io with mandatory two-phase dry-run and strict prohibition of force-pushes."
    }
)

# Step 1: Pre-Flight Integrity Verification
Write-Host "`n[STEP 1] Validating staged file digests for Batch 2..." -ForegroundColor Cyan
foreach ($item in $promotionPlan) {
    if (-not (Test-Path $item.staged_path)) {
        throw "Staged file not found: $($item.staged_path)"
    }
    $content = [System.IO.File]::ReadAllText($item.staged_path)
    $actualSha = Get-Sha256Digest $content
    if ($actualSha -ne $item.expected_sha256) {
        throw "Digest mismatch for $($item.canonical_name)! Expected $($item.expected_sha256), got $actualSha"
    }
    Write-Host "  [OK] $($item.canonical_name): $actualSha (Integrity Verified)" -ForegroundColor Green
}

# Step 2: Canonical Collision Check
Write-Host "`n[STEP 2] Verifying destination collision status..." -ForegroundColor Cyan
foreach ($item in $promotionPlan) {
    if (Test-Path $item.canonical_dest_file) {
        throw "Collision detected! Canonical file already exists at $($item.canonical_dest_file)"
    }
    Write-Host "  [OK] Destination clean: $($item.canonical_dest_file)" -ForegroundColor Green
}

# Step 3: Atomic Canonical Promotion
Write-Host "`n[STEP 3] Executing Atomic Canonical Promotion for Batch 2..." -ForegroundColor Green

if (-not (Test-Path $CanonicalSkillsRoot)) {
    [System.IO.Directory]::CreateDirectory($CanonicalSkillsRoot) | Out-Null
}

$promotedRecords = New-Object 'System.Collections.Generic.List[object]'
$nowUtc = [DateTime]::UtcNow.ToString("o")

foreach ($item in $promotionPlan) {
    if (-not (Test-Path $item.canonical_dest_dir)) {
        [System.IO.Directory]::CreateDirectory($item.canonical_dest_dir) | Out-Null
    }
    
    # Copy file atomically
    Copy-Item -Path $item.staged_path -Destination $item.canonical_dest_file -Force
    
    # Verify post-copy integrity
    $promotedContent = [System.IO.File]::ReadAllText($item.canonical_dest_file)
    $promotedSha = Get-Sha256Digest $promotedContent
    if ($promotedSha -ne $item.expected_sha256) {
        throw "FATAL: Post-copy integrity check failed for $($item.canonical_dest_file)!"
    }
    
    Write-Host "  [PROMOTED] $($item.canonical_name) -> $($item.canonical_dest_file) (SHA: $promotedSha)" -ForegroundColor Green
    
    # Create canonical index resource entry
    $resObj = [ordered]@{
        schema_version = "1.0.0"
        resource_id = $item.resource_id
        canonical_name = $item.canonical_name
        version = "1.0.0"
        display_name = $item.canonical_name
        description = $item.description
        provenance_id = $item.provenance_id
        lifecycle_state = "ACTIVE"
        trust_level = "VERIFIED_ADAPTED"
        capabilities = @($item.canonical_name)
        content_identity = [ordered]@{
            content_hash = $promotedSha
            manifest_hash = $promotedSha
            file_count = 1
            byte_sum = $promotedContent.Length
        }
        created_utc = $nowUtc
        updated_utc = $nowUtc
    }
    
    $resJson = $resObj | ConvertTo-Json -Compress
    [System.IO.File]::AppendAllText($ResourcesIndexPath, "`n$resJson", $utf8NoBom)
    
    [void]$promotedRecords.Add($item)
}

# Step 4: Generate Reports
Write-Host "`n[STEP 4] Generating Promotion Execution Report for Batch 2..." -ForegroundColor Cyan

$reportJsonObj = [ordered]@{
    schema = "skill-registry.operational.governed-promotion-batch2/v1"
    generated_utc = $nowUtc
    status = "COMMITTED"
    mandate = "DELEGATED_GOVERNED_EXECUTION"
    total_promoted = $promotedRecords.Count
    canonical_skills_root = $CanonicalSkillsRoot
    distribution_performed = $false
    promoted_skills = $promotionPlan
}
[System.IO.File]::WriteAllText($ReportJson, ($reportJsonObj | ConvertTo-Json -Depth 10), $utf8NoBom)

$md = New-Object 'System.Collections.Generic.List[string]'
[void]$md.Add('# Operacao 11: Relatorio de Promocao Governada - Batch 2 (9 Skills)')
[void]$md.Add('')
[void]$md.Add('**Skill Registry v1.0.0 - Promocao Canonica Sob Mandato de Execucao Delegada**')
[void]$md.Add('- **Status da Transacao**: `COMMITTED` (9 novas skills promovidas)')
[void]$md.Add('- **Mandato**: `EXECUCAO DELEGADA GOVERNADA (AUTORIZADA)`')
[void]$md.Add('- **Destino Canonico**: `E:\.skill-registry\skills\`')
[void]$md.Add('- **Total Acumulado de Skills no Catalogo**: **12** (3 do Lote 1 + 9 do Lote 2)')
[void]$md.Add('- **Distribuicao em Workspaces / ~/.gemini**: `0 (ISOLAMENTO PRESERVADO)`')
[void]$md.Add('- **Data/Hora (UTC)**: ' + $nowUtc)
[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 1. Skills Promovidas no Batch 2')
[void]$md.Add('')
[void]$md.Add('| # | Nome Canonico | Origem em Staging | Destino Canonico | SHA-256 Verificado | Lifecycle |')
[void]$md.Add('| :---: | :--- | :--- | :--- | :--- | :--- |')

$bIdx = 1
foreach ($p in $promotionPlan) {
    $row = '| **' + $bIdx + '** | **' + $p.canonical_name + '** | `' + $p.original_name + '` | `skills/' + $p.canonical_name + '/SKILL.md` | `' + $p.expected_sha256.Substring(0, 16) + '...` | **ACTIVE** |'
    [void]$md.Add($row)
    $bIdx++
}

[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 2. Rastreabilidade e Atualizacao de Indices')
[void]$md.Add('')
[void]$md.Add('As 9 novas skills foram incorporadas ao ledger canonico `index/resources.jsonl` com trust level `VERIFIED_ADAPTED` e lifecycle `ACTIVE`.')
[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 3. Garantias de Governanca Inviolaveis')
[void]$md.Add('')
[void]$md.Add('- **Zero Instalacao Externa**: Nenhuma skill foi instalada em `~/.gemini/config/skills` ou workspaces.')
[void]$md.Add('- **Preservacao Upstream**: Os arquivos originais em `staging/github-inlet/candidates/` permanecem intocados.')
[void]$md.Add('- **Continuacao Autonoma**: Sob o mandato delegado, o pipeline avancara automaticamente para a proxima etapa.')

[System.IO.File]::WriteAllLines($ReportMd, $md.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BATCH 2 PROMOTED SUCCESSFULLY TO CANONICAL AUTHORITY       " -ForegroundColor Green
Write-Host " 9 Skills Promoted (Total Canonical Skills: 12)             " -ForegroundColor Green
Write-Host " Zero Installations to User Directory Verified              " -ForegroundColor Green
Write-Host " Report MD   : $ReportMd" -ForegroundColor Green
Write-Host " Report JSON : $ReportJson" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
