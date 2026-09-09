# Skill Registry - Operational Tooling: GitHub Candidate Ingest, Security Scan & Quarantine
# Ingests strictly cataloged candidate blobs via GitHub Blobs API, verifies content SHA-256,
# enforces fail-closed quarantine security scanning, and registers immutable provenance records with zero execution.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$CandidateCatalogPath = (Join-Path $RegistryRoot 'staging\github-inlet\candidate-artifacts.jsonl'),
    [int]$MaxIngestCount = 35, # Process top N high-priority candidates per run
    [string[]]$ArtifactClassFilter = @('SKILL_DEFINITION_CANDIDATE', 'AGENT_CONFIG_ARTIFACT', 'CAPABILITY_ARTIFACT'),
    [string]$OutputDirectory = (Join-Path $RegistryRoot 'staging\github-inlet\candidates'),
    [string]$QuarantineDirectory = (Join-Path $RegistryRoot 'staging\github-inlet\quarantine')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $CandidateCatalogPath)) {
    throw "Candidate catalog not found: $CandidateCatalogPath. Run Invoke-GitHubDeepTriage.ps1 first."
}

if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
}
if (-not (Test-Path $QuarantineDirectory)) {
    New-Item -ItemType Directory -Path $QuarantineDirectory -Force | Out-Null
}

$ingestedLedger = Join-Path $RegistryRoot 'staging\github-inlet\ingested-candidates.jsonl'
$reportJson = Join-Path $RegistryRoot 'reports\operational-github-candidate-ingest.json'
$reportMd = Join-Path $RegistryRoot 'reports\operational-github-candidate-ingest.md'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Security threat patterns (fail-closed quarantine)
$threatPatterns = @(
    '(bash|sh)\s+-i\s+>&', # reverse shell
    '/dev/tcp/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', # network socket exfiltration
    'eval\s*\(\s*base64_decode', # obfuscated PHP eval
    'exec\s*\(\s*base64\.b64decode', # obfuscated python eval
    'powershell(\.exe)?\s+-[eE][ncodgNCED]*\s+[A-Za-z0-9+/=]{20,}', # encoded powershell command
    'AKIA[0-9A-Z]{16}', # AWS Access Key
    'ghp_[0-9a-zA-Z]{36}', # GitHub Token
    '-----BEGIN\s+RSA\s+PRIVATE\s+KEY-----' # Private Key
)

function Get-Sha256Digest {
    param([byte[]]$Bytes)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha256.ComputeHash($Bytes)
    $sb = New-Object System.Text.StringBuilder
    foreach ($b in $hashBytes) { [void]$sb.Append($b.ToString("x2")) }
    return $sb.ToString()
}

$headers = @{
    'User-Agent' = 'SkillRegistry-Operational-Scanner/1.0.0'
    'Accept'     = 'application/vnd.github.v3+json'
}
if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)) {
    $headers['Authorization'] = "token $env:GITHUB_TOKEN"
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GITHUB CANDIDATE INGEST & SECURITY SCANNER                 " -ForegroundColor Cyan
Write-Host " Catalog Path : $CandidateCatalogPath" -ForegroundColor Cyan
Write-Host " Target Staging: $OutputDirectory" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$lines = [System.IO.File]::ReadAllLines($CandidateCatalogPath)
$candidates = New-Object 'System.Collections.Generic.List[object]'

foreach ($l in $lines) {
    if ([string]::IsNullOrWhiteSpace($l)) { continue }
    $art = $l | ConvertFrom-Json
    if ($ArtifactClassFilter -contains [string]$art.artifact_class) {
        [void]$candidates.Add($art)
    }
}

Write-Host "Loaded $($candidates.Count) candidate artifacts matching class filter: $($ArtifactClassFilter -join ', ')." -ForegroundColor Cyan

$processLimit = [Math]::Min($MaxIngestCount, $candidates.Count)
$toProcess = $candidates[0..($processLimit - 1)]

$ingestedRecords = New-Object 'System.Collections.Generic.List[object]'
$passedCount = 0
$quarantinedCount = 0
$skippedCount = 0

foreach ($cand in $toProcess) {
    $repo = [string]$cand.repo_full_name
    $blobSha = [string]$cand.blob_sha
    $relPath = [string]$cand.relative_path
    $artClass = [string]$cand.artifact_class
    
    $safeRepoName = $repo.Replace('/', '__').Replace('\', '__')
    $safeFileName = [System.IO.Path]::GetFileName($relPath)
    $candId = "cand-" + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + "-" + $blobSha.Substring(0, 8)
    
    $blobUri = "https://api.github.com/repos/$repo/git/blobs/$blobSha"
    Write-Host "Fetching blob for $repo : $relPath ($blobSha)..." -ForegroundColor Gray
    
    try {
        $resp = Invoke-WebRequest -Uri $blobUri -Headers $headers -UseBasicParsing -TimeoutSec 15
        $blobJson = $resp.Content | ConvertFrom-Json
        
        $base64Content = [string]$blobJson.content
        $cleanedB64 = $base64Content.Replace("`n", "").Replace("`r", "").Trim()
        $rawBytes = [System.Convert]::FromBase64String($cleanedB64)
        $contentStr = [System.Text.Encoding]::UTF8.GetString($rawBytes)
        
        # Calculate content SHA-256
        $contentSha256 = Get-Sha256Digest -Bytes $rawBytes
        
        # Security Scanning
        $violations = New-Object 'System.Collections.Generic.List[string]'
        
        foreach ($pattern in $threatPatterns) {
            if ($contentStr -match $pattern) {
                [void]$violations.Add("THREAT_PATTERN_MATCH: $pattern")
            }
        }
        
        # Check size threshold
        if ($rawBytes.Length -gt 512000) {
            [void]$violations.Add("EXCESSIVE_FILE_SIZE: $($rawBytes.Length) bytes")
        }
        
        $isClean = ($violations.Count -eq 0)
        $quarantineState = if ($isClean) { "CANDIDATE_FOR_EVALUATION" } else { "QUARANTINED" }
        
        # Extract declared references / metadata (without executing or following)
        $detectedRefs = New-Object 'System.Collections.Generic.List[string]'
        if ($contentStr -match '(?i)requires?:\s*\[?([a-zA-Z0-9_\-,\s]+)\]?') {
            [void]$detectedRefs.Add($matches[1].Trim())
        }
        
        # Destination staging path
        $destDir = if ($isClean) {
            Join-Path $OutputDirectory "$safeRepoName\$candId"
        } else {
            Join-Path $QuarantineDirectory "$safeRepoName\$candId"
        }
        
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        $destFilePath = Join-Path $destDir $safeFileName
        [System.IO.File]::WriteAllBytes($destFilePath, $rawBytes)
        
        $record = [ordered]@{
            schema_version = "1.0.0"
            candidate_id = $candId
            source_inlet = "GITHUB_BLOB_API"
            repository = $repo
            relative_path = $relPath
            blob_sha = $blobSha
            artifact_class = $artClass
            content_sha256 = $contentSha256
            byte_size = $rawBytes.Length
            security_status = if ($isClean) { "CLEAN" } else { "THREAT_DETECTED" }
            quarantine_state = $quarantineState
            violations = $violations.ToArray()
            detected_references = $detectedRefs.ToArray()
            staged_path = $destFilePath.Substring($RegistryRoot.Length).TrimStart('\', '/')
            ingested_utc = [DateTime]::UtcNow.ToString("o")
        }
        
        [void]$ingestedRecords.Add($record)
        
        # Append to ingested candidates ledger
        $jsonStr = ($record | ConvertTo-Json -Compress)
        [System.IO.File]::AppendAllText($ingestedLedger, "$jsonStr`n", $utf8NoBom)
        
        if ($isClean) {
            $passedCount++
            Write-Host "  -> [CLEAN] Staged: $relPath ($contentSha256)" -ForegroundColor Green
        } else {
            $quarantinedCount++
            Write-Host "  -> [QUARANTINED] Blocked: $relPath ($($violations -join ', '))" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 250
        
    } catch {
        Write-Host "  -> Error fetching blob $blobSha`: $($_.Exception.Message)" -ForegroundColor DarkYellow
        $skippedCount++
    }
}

# Generate Ingest Summary Report
$ingestReport = [ordered]@{
    schema = "skill-registry.operational.github-candidate-ingest/v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    total_processed = $ingestedRecords.Count
    clean_candidates_staged = $passedCount
    quarantined_count = $quarantinedCount
    skipped_count = $skippedCount
    staged_inbox_directory = "staging/github-inlet/candidates"
    quarantine_directory = "staging/github-inlet/quarantine"
    ingested_candidates_ledger = "staging/github-inlet/ingested-candidates.jsonl"
    ingested_items = $ingestedRecords.ToArray()
}

$summaryJson = $ingestReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($reportJson, $summaryJson, $utf8NoBom)

# Generate Markdown Report
$mdList = New-Object 'System.Collections.Generic.List[string]'
[void]$mdList.Add("# Operacao 3: GitHub Candidate Ingest, Security Scan & Quarantine Report")
[void]$mdList.Add("")
[void]$mdList.Add("**Skill Registry v1.0.0 - Ingestao Pontual de Blobs & Proveniencia Imutavel**")
[void]$mdList.Add("- **Total de Candidatos Processados**: **$($ingestedRecords.Count)**")
[void]$mdList.Add("- **Candidatos Aprovados em Quarentena Limpa**: **$passedCount**")
[void]$mdList.Add("- **Candidatos Bloqueados / Quarentenados**: **$quarantinedCount**")
[void]$mdList.Add("- **Data/Hora (UTC)**: $([DateTime]::UtcNow.ToString('o'))")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 1. Resumo da Ingestao")
[void]$mdList.Add("")
[void]$mdList.Add("| Metrica | Valor |")
[void]$mdList.Add("| :--- | :--- |")
[void]$mdList.Add("| **Total de Blobs Baixados** | $($ingestedRecords.Count) |")
[void]$mdList.Add("| **Candidatos Limpos em Staging** | **$passedCount** |")
[void]$mdList.Add("| **Violacoes de Seguranca Bloqueadas** | **$quarantinedCount** |")
[void]$mdList.Add("| **Inbox de Staging** | [`staging/github-inlet/candidates/`](file:///E:/.skill-registry/staging/github-inlet/candidates/) |")
[void]$mdList.Add("| **Ledger de Proveniencia** | [`staging/github-inlet/ingested-candidates.jsonl`](file:///E:/.skill-registry/staging/github-inlet/ingested-candidates.jsonl) |")
[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 2. Inventario de Candidatos Ingeridos com Proveniencia")
[void]$mdList.Add("")
[void]$mdList.Add("| ID Candidato | Repositorio | Caminho Relativo | Classe | SHA-256 | Status |")
[void]$mdList.Add("| :--- | :--- | :--- | :--- | :--- | :--- |")

foreach ($item in $ingestedRecords) {
    $cId = [string]$item.candidate_id
    $repoName = [string]$item.repository
    $p = [string]$item.relative_path
    $cls = [string]$item.artifact_class
    $h = ([string]$item.content_sha256).Substring(0, 12) + "..."
    $st = [string]$item.quarantine_state
    
    $row = "| {0} | **{1}** | `{2}` | {3} | `{4}` | **{5}** |" -f $cId, $repoName, $p, $cls, $h, $st
    [void]$mdList.Add($row)
}

[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 3. Conformidade com os 5 Invariantes")
[void]$mdList.Add("")
[void]$mdList.Add("1. **Zero Clones**: Apenas os blobs especificamente necessarios foram baixados via API.")
[void]$mdList.Add("2. **Zero Execucao**: O conteudo recebido foi tratado estritamente como dados inertes.")
[void]$mdList.Add("3. **Zero Resolucao Automatica**: Referencias externas foram registradas sem downloads secundarios.")
[void]$mdList.Add("4. **Quarentena Fail-Closed**: Todo arquivo com padroes perigosos foi isolado em `staging/github-inlet/quarantine/`.")
[void]$mdList.Add("5. **Proveniencia Imutavel**: Cada candidato possui registro com blob SHA, commit/repo e digest SHA-256.")

[System.IO.File]::WriteAllLines($reportMd, $mdList.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " CANDIDATE INGEST COMPLETE                                  " -ForegroundColor Green
Write-Host " Clean Staged    : $passedCount" -ForegroundColor Green
Write-Host " Quarantined     : $quarantinedCount" -ForegroundColor $(if ($quarantinedCount -gt 0) { 'Yellow' } else { 'Green' })
Write-Host " Ingest Ledger   : $ingestedLedger" -ForegroundColor Green
Write-Host " Report          : $reportMd" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
