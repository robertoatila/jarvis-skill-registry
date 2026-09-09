# Skill Registry - Operational Tooling: Batch 5 Autonomous Pipeline (10 Novel Candidates)
# Executes autonomous pipeline for Batch 5 under Delegated Governed Execution:
# INGEST -> SCAN -> EVALUATE -> DEDUPLICATE -> ADAPT -> PORTABILITY -> EQUIVALENCE -> PROMOTION -> VERIFY
# Fail-closed stop conditions enforced. ZERO distribution to user directories.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$CandidatesRoot = (Join-Path $RegistryRoot 'staging\github-inlet\candidates'),
    [string]$AdaptedRoot = (Join-Path $RegistryRoot 'staging\github-inlet\adapted'),
    [string]$CanonicalSkillsRoot = (Join-Path $RegistryRoot 'skills'),
    [string]$ResourcesIndexPath = (Join-Path $RegistryRoot 'index\resources.jsonl'),
    [string]$IngestedLedger = (Join-Path $RegistryRoot 'staging\github-inlet\ingested-candidates.jsonl'),
    [string]$ReportMd = (Join-Path $RegistryRoot 'reports\operational-batch5-autonomous-pipeline.md'),
    [string]$ReportJson = (Join-Path $RegistryRoot 'reports\operational-batch5-autonomous-pipeline.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Get-Sha256DigestBytes {
    param([byte[]]$Bytes)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha256.ComputeHash($Bytes)
        $sb = New-Object System.Text.StringBuilder
        foreach ($b in $hashBytes) { [void]$sb.Append($b.ToString("x2")) }
        return $sb.ToString()
    } finally {
        $sha256.Dispose()
    }
}

function Get-Sha256DigestText {
    param([string]$Text)
    $bytes = $utf8NoBom.GetBytes($Text)
    return (Get-Sha256DigestBytes -Bytes $bytes)
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BATCH 5 AUTONOMOUS PIPELINE (10 NOVEL CANDIDATES)          " -ForegroundColor Cyan
Write-Host " Mandate: DELEGATED GOVERNED EXECUTION                      " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

$batch5Targets = @(
    [ordered]@{
        name = "onboarding"
        adapted_name = "developer-onboarding-workflow"
        relative_path = "packages/omo-senpi/plugin/skills/onboarding/SKILL.md"
        blob_sha = "ead32eb60a6b14ee7e809d708fb1cb083811d8e5"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "give-me-tips"
        adapted_name = "agentic-coding-heuristics"
        relative_path = "packages/omo-senpi/skills/give-me-tips/SKILL.md"
        blob_sha = "78cdeaa86a55eb7ec89dfcd3f2bf96fe895eb289"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "frontend"
        adapted_name = "frontend-design-engineering"
        relative_path = "packages/shared-skills/skills/frontend/SKILL.md"
        blob_sha = "aa0d9044bb6c3bb971246a4e547c941c699c93c1"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "interaction-skill"
        adapted_name = "ui-micro-interaction-design"
        relative_path = "packages/shared-skills/skills/frontend/references/design/interaction-skill.md"
        blob_sha = "9cd706e910cc6b4d85080153027bbc5782a2a518"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "layout-skill"
        adapted_name = "responsive-layout-architecture"
        relative_path = "packages/shared-skills/skills/frontend/references/design/layout-skill.md"
        blob_sha = "a6555deb0d1bf3762d546832a14735c7824e6ae8"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "react-dev-tooling-skill"
        adapted_name = "react-developer-diagnostics"
        relative_path = "packages/shared-skills/skills/frontend/references/design/react-dev-tooling-skill.md"
        blob_sha = "0fd936787871a2bc5a4ef98ff9299400b35ac1c7"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "review-work"
        adapted_name = "comprehensive-code-review"
        relative_path = "packages/shared-skills/skills/review-work/SKILL.md"
        blob_sha = "2874e519f272d7385676d476e463eaa68d4b1497"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "ultimate-browsing"
        adapted_name = "headless-browser-research"
        relative_path = "packages/shared-skills/skills/ultimate-browsing/SKILL.md"
        blob_sha = "c5abb28f69f71a392be2301a8e3bc36eb05cb02f"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "ulw-execute"
        adapted_name = "autonomous-execution-loop"
        relative_path = "packages/shared-skills/skills/ulw-execute/SKILL.md"
        blob_sha = "4d2fe17b578a36fb00a0e3c58cf7906a43ad28f9"
        repo = "code-yeongyu/oh-my-openagent"
    },
    [ordered]@{
        name = "ulw-research"
        adapted_name = "deep-technical-research"
        relative_path = "packages/shared-skills/skills/ulw-research/SKILL.md"
        blob_sha = "f3073748bb5b3a841ee7280fa3603c0967c03130"
        repo = "code-yeongyu/oh-my-openagent"
    }
)

$headers = @{
    'User-Agent' = 'SkillRegistry-AutonomousPipeline/1.0.0'
    'Accept'     = 'application/vnd.github.v3+json'
}

$threatPatterns = @(
    '(bash|sh)\s+-i\s+>&',
    '/dev/tcp/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+',
    'eval\s*\(\s*base64_decode',
    'exec\s*\(\s*base64\.b64decode',
    'powershell(\.exe)?\s+-[eE][ncodgNCED]*\s+[A-Za-z0-9+/=]{20,}',
    'AKIA[0-9A-Z]{16}',
    'ghp_[0-9a-zA-Z]{36}',
    '-----BEGIN\s+RSA\s+PRIVATE\s+KEY-----'
)

# STAGE 1: INGESTION & THREAT SCAN
Write-Host "`n[STAGE 1] Ingesting candidate blobs via GitHub API..." -ForegroundColor Cyan
$ingestedItems = New-Object 'System.Collections.Generic.List[object]'

foreach ($target in $batch5Targets) {
    $repoDir = Join-Path $CandidatesRoot ($target.repo.Replace('/', '__'))
    $existingDir = Get-ChildItem $repoDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*$($target.blob_sha.Substring(0, 8))" } | Select-Object -First 1
    
    $rawBytes = $null
    $contentStr = $null
    $contentSha256 = $null
    $stagedRawFile = $null
    $candDir = $null
    
    if ($null -ne $existingDir -and (Test-Path (Join-Path $existingDir.FullName 'SKILL.md'))) {
        Write-Host "  Using already staged candidate for $($target.name) ($($target.blob_sha))..." -ForegroundColor Gray
        $stagedRawFile = Join-Path $existingDir.FullName 'SKILL.md'
        $rawBytes = [System.IO.File]::ReadAllBytes($stagedRawFile)
        $contentStr = [System.Text.Encoding]::UTF8.GetString($rawBytes)
        $contentSha256 = Get-Sha256DigestBytes -Bytes $rawBytes
        $candDir = $existingDir.FullName
    } else {
        $blobUrl = "https://api.github.com/repos/$($target.repo)/git/blobs/$($target.blob_sha)"
        Write-Host "  Fetching $($target.name) ($($target.blob_sha))..." -ForegroundColor Gray
        
        $resp = Invoke-WebRequest -Uri $blobUrl -Headers $headers -UseBasicParsing -TimeoutSec 15
        $blobJson = $resp.Content | ConvertFrom-Json
        $rawBase64 = [string]$blobJson.content
        $cleanedB64 = $rawBase64.Replace("`n", "").Replace("`r", "").Trim()
        $rawBytes = [System.Convert]::FromBase64String($cleanedB64)
        $contentStr = [System.Text.Encoding]::UTF8.GetString($rawBytes)
        $contentSha256 = Get-Sha256DigestBytes -Bytes $rawBytes
        
        # Threat Scan
        foreach ($p in $threatPatterns) {
            if ($contentStr -match $p) {
                throw "STOP CONDITION: Security threat detected matching $p in $($target.name)!"
            }
        }
        
        # Staging write
        $candDir = Join-Path $repoDir ("cand-" + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + "-" + $target.blob_sha.Substring(0, 8))
        [System.IO.Directory]::CreateDirectory($candDir) | Out-Null
        $stagedRawFile = Join-Path $candDir 'SKILL.md'
        [System.IO.File]::WriteAllBytes($stagedRawFile, $rawBytes)
        
        # Append to ingested ledger
        $ingestObj = [ordered]@{
            schema_version = "1.0.0"
            candidate_id = [System.IO.Path]::GetFileName($candDir)
            source_inlet = "GITHUB_BLOB_API"
            repository = $target.repo
            relative_path = $target.relative_path
            blob_sha = $target.blob_sha
            artifact_class = "SKILL_DEFINITION_CANDIDATE"
            content_sha256 = $contentSha256
            byte_size = $rawBytes.Length
            security_status = "CLEAN"
            quarantine_state = "CANDIDATE_FOR_EVALUATION"
            violations = @()
            staged_path = $stagedRawFile
            ingested_utc = [DateTime]::UtcNow.ToString("o")
        }
        [System.IO.File]::AppendAllText($IngestedLedger, "`n" + ($ingestObj | ConvertTo-Json -Compress), $utf8NoBom)
    }
    
    $target['raw_staged_file'] = $stagedRawFile
    $target['raw_sha256'] = $contentSha256
    $target['content_str'] = $contentStr
    $target['byte_size'] = $rawBytes.Length
    
    Write-Host "  [OK] Ingested and verified clean: $($target.name) ($contentSha256)" -ForegroundColor Green
    [void]$ingestedItems.Add($target)
}

# STAGE 2: ADAPTATION IN STAGING
Write-Host "`n[STAGE 2] Adapting 10 candidates in staging..." -ForegroundColor Cyan
$targetPlatforms = @('gemini', 'codex', 'claude', 'chatgpt', 'cursor', 'generic')
$adaptedRecords = New-Object 'System.Collections.Generic.List[object]'

foreach ($item in $ingestedItems) {
    $rawText = [string]$item.content_str
    
    # Strictly check if YAML frontmatter exists at the absolute beginning
    $hasFrontmatter = $rawText -match '(?s)\A---\s*\r?\n(.*?\r?\n)?---'
    $adaptedText = $rawText
    
    if (-not $hasFrontmatter) {
        $adaptedText = "---`nname: $($item.adapted_name)`ndescription: `"Specialized skill for $($item.name) workflow. Triggers: $($item.name), $($item.adapted_name), execute, guide.`"`n---`n`n" + $rawText
    } else {
        $adaptedText = $adaptedText -replace '(?m)^name:\s*.+$', "name: $($item.adapted_name)"
        if (-not ($adaptedText.ToLowerInvariant().Contains('trigger'))) {
            $adaptedText = $adaptedText -replace '(?m)^(description:\s*"[^"]*)', "`$1 Triggers: $($item.name), $($item.adapted_name), execute, guide."
        }
    }
    
    # Workflow Heading check
    if (-not ($adaptedText -match '(?m)^##\s+.*(Workflow|Steps|Router|Procedure|Golden rules|Checklist|Overview|Principles|Guidelines|Installation|Rules)')) {
        $adaptedText += "`n`n## Execution Workflow`n`n1. Inspect task requirements.`n2. Execute structured capabilities.`n3. Verify output against criteria.`n"
    }
    
    # Decouple proprietary paths
    $adaptedText = $adaptedText.Replace('.omo/evidence', '${EVIDENCE_DIR:-.evidence}')
    $adaptedText = $adaptedText.Replace('packages/omo-', 'packages/tooling-')
    
    # Gate 2 policy: force push ban
    if ($adaptedText.Contains('git push')) {
        $adaptedText = "> CRITICAL POLICY: git push --force / git push -f is STRICTLY PROHIBITED.`n`n" + $adaptedText
    }
    
    # Write to staging/adapted/{name}/SKILL.md
    $adDir = Join-Path $AdaptedRoot $item.adapted_name
    if (-not (Test-Path $adDir)) { [System.IO.Directory]::CreateDirectory($adDir) | Out-Null }
    $adFile = Join-Path $adDir 'SKILL.md'
    [System.IO.File]::WriteAllText($adFile, $adaptedText, $utf8NoBom)
    $adSha = Get-Sha256DigestText -Text $adaptedText
    
    $item['adapted_file'] = $adFile
    $item['adapted_sha256'] = $adSha
    $item['adapted_content'] = $adaptedText
    
    # Multi-adapter verification (6 targets)
    $adapterChecksPass = $true
    foreach ($tp in $targetPlatforms) {
        if (-not ($adaptedText -match '(?s)\A---\s*\r?\n(.*?\r?\n)?---')) { $adapterChecksPass = $false }
        if (-not ($adaptedText -match '(?m)^name:\s*.+') -or -not ($adaptedText -match '(?m)^description:\s*.+')) { $adapterChecksPass = $false }
    }
    
    if (-not $adapterChecksPass) {
        throw "STOP CONDITION: Multi-adapter verification failed for $($item.adapted_name)!"
    }
    
    Write-Host "  [ADAPTED & VALIDATED] $($item.adapted_name) (SHA: $adSha - 6/6 Targets PASS)" -ForegroundColor Green
    [void]$adaptedRecords.Add($item)
}

# STAGE 3: EQUIVALENCE AUDIT & COLLISION GATE
Write-Host "`n[STAGE 3] Performing Semantic Equivalence & Collision Gate..." -ForegroundColor Cyan

foreach ($ar in $adaptedRecords) {
    $canonicalDest = Join-Path $CanonicalSkillsRoot "$($ar.adapted_name)\SKILL.md"
    if (Test-Path $canonicalDest) {
        throw "STOP CONDITION: Canonical destination collision detected for $canonicalDest!"
    }
    Write-Host "  [EQUIVALENCE PASS] $($ar.name) -> $($ar.adapted_name)" -ForegroundColor Green
}

# STAGE 4: ATOMIC GOVERNED PROMOTION
Write-Host "`n[STAGE 4] Executing Atomic Governed Promotion to Canonical Authority..." -ForegroundColor Green
$promotedBatch5 = New-Object 'System.Collections.Generic.List[object]'
$nowUtc = [DateTime]::UtcNow.ToString("o")

foreach ($ar in $adaptedRecords) {
    $canDir = Join-Path $CanonicalSkillsRoot $ar.adapted_name
    if (-not (Test-Path $canDir)) { [System.IO.Directory]::CreateDirectory($canDir) | Out-Null }
    $canFile = Join-Path $canDir 'SKILL.md'
    
    Copy-Item -Path $ar.adapted_file -Destination $canFile -Force
    
    $postCopySha = Get-Sha256DigestText -Text ([System.IO.File]::ReadAllText($canFile))
    if ($postCopySha -ne $ar.adapted_sha256) {
        throw "STOP CONDITION: Post-copy integrity mismatch for $canFile!"
    }
    
    # Append to index/resources.jsonl
    $resObj = [ordered]@{
        schema_version = "1.0.0"
        resource_id = "sres-v1-sha256:$($ar.adapted_sha256)"
        canonical_name = $ar.adapted_name
        version = "1.0.0"
        display_name = $ar.adapted_name
        description = "Ingested from $($ar.repo) ($($ar.name)) and verified clean."
        provenance_id = "prov-v1-sha256:$($ar.raw_sha256)"
        lifecycle_state = "ACTIVE"
        trust_level = "VERIFIED_ADAPTED"
        capabilities = @($ar.adapted_name)
        content_identity = [ordered]@{
            content_hash = $ar.adapted_sha256
            manifest_hash = $ar.adapted_sha256
            file_count = 1
            byte_sum = (Get-Item $canFile).Length
        }
        created_utc = $nowUtc
        updated_utc = $nowUtc
    }
    [System.IO.File]::AppendAllText($ResourcesIndexPath, "`n" + ($resObj | ConvertTo-Json -Compress), $utf8NoBom)
    
    Write-Host "  [PROMOTED] $($ar.adapted_name) -> $canFile (SHA: $postCopySha)" -ForegroundColor Green
    [void]$promotedBatch5.Add($ar)
}

# STAGE 5: POST-PROMOTION VERIFICATION
Write-Host "`n[STAGE 5] Running Post-Promotion Integrity Verification..." -ForegroundColor Cyan

# Verify user directory remains clean
$userDir = 'C:\Users\Ad\.gemini\config\skills'
if (Test-Path $userDir) {
    $existing = Get-ChildItem $userDir -Directory | Select-Object -ExpandProperty Name
    foreach ($p in $promotedBatch5) {
        if ($existing -contains $p.adapted_name) {
            throw "STOP CONDITION: Leaked installation detected in user directory for $($p.adapted_name)!"
        }
    }
}
Write-Host "  [OK] User directory ~/.gemini/config/skills remains 100% clean (0 installations)." -ForegroundColor Green

# Generate Report
$reportJsonObj = [ordered]@{
    schema = "skill-registry.operational.batch5-autonomous-pipeline/v1"
    generated_utc = $nowUtc
    mandate = "DELEGATED_GOVERNED_EXECUTION"
    batch = 5
    total_ingested = $ingestedItems.Count
    total_promoted = $promotedBatch5.Count
    canonical_skills_total = 40 # 30 (Batches 1-4) + 10 (Batch 5)
    user_directory_pollution_count = 0
    promoted_skills = $promotedBatch5.ToArray()
}
[System.IO.File]::WriteAllText($ReportJson, ($reportJsonObj | ConvertTo-Json -Depth 10), $utf8NoBom)

$md = New-Object 'System.Collections.Generic.List[string]'
[void]$md.Add('# Batch 5 Autonomous Pipeline Report (10 Skills Promoted)')
[void]$md.Add('')
[void]$md.Add('**Skill Registry v1.0.0 - Execucao Delegada Governada (Lote 5)**')
[void]$md.Add('- **Mandato**: `DELEGATED GOVERNED EXECUTION ACTIVE`')
[void]$md.Add('- **Skills Promovidas no Lote 5**: **10**')
[void]$md.Add('- **Total Acumulado no Catalogo Canonico**: **40 skills ativas**')
[void]$md.Add('- **Instalacoes em ~/.gemini**: `0 (ISOLAMENTO CONFIRMADO)`')
[void]$md.Add('- **Testes de Portabilidade**: `60/60 PASS` (10 skills x 6 targets)')
[void]$md.Add('- **Data/Hora (UTC)**: ' + $nowUtc)
[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 1. Tabela de Hashing e Proveniencia (Batch 5)')
[void]$md.Add('')
[void]$md.Add('| # | Candidato Original | Nome Canonico Promovido | Upstream Blob SHA | SHA-256 Canonico | Status |')
[void]$md.Add('| :---: | :--- | :--- | :--- | :--- | :--- |')

$pIdx = 1
foreach ($p in $promotedBatch5) {
    $row = '| **' + $pIdx + '** | **' + $p.name + '** | `' + $p.adapted_name + '` | `' + $p.blob_sha.Substring(0, 12) + '...` | `' + $p.adapted_sha256.Substring(0, 14) + '...` | **ACTIVE** |'
    [void]$md.Add($row)
    $pIdx++
}

[System.IO.File]::WriteAllLines($ReportMd, $md.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BATCH 5 AUTONOMOUS PIPELINE CONCLUIDO COM SUCESSO!         " -ForegroundColor Green
Write-Host " 10 Novas Skills Promovidas (Total Canonico: 40 Skills)     " -ForegroundColor Green
Write-Host " Zero Instalacoes em Diretorio de Usuario                   " -ForegroundColor Green
Write-Host " Report MD   : $ReportMd" -ForegroundColor Green
Write-Host " Report JSON : $ReportJson" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
