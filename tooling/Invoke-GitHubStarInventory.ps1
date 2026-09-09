# Skill Registry - Operational Tooling: GitHub Starred Repositories Inventory (Metadata-First)
# Discovers and indexes starred repositories via GitHub API with pagination, rate-limit governance, checkpointing, and zero cloning.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$Username = 'robertoatila',
    [string]$GitHubToken = $env:GITHUB_TOKEN,
    [int]$PerPage = 100,
    [int]$MaxPages = 50,
    [string]$OutputDirectory = (Join-Path $RegistryRoot 'staging\github-inlet')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
}

$inventoryJsonl = Join-Path $OutputDirectory 'starred-inventory.jsonl'
$checkpointFile = Join-Path $OutputDirectory 'starred-inventory-checkpoint.json'
$reportJson = Join-Path $RegistryRoot 'reports\operational-github-star-inventory.json'
$reportMd = Join-Path $RegistryRoot 'reports\operational-github-star-inventory.md'

# Load existing checkpoint if present
$checkpoint = $null
if (Test-Path $checkpointFile) {
    try {
        $rawCp = [System.IO.File]::ReadAllText($checkpointFile)
        $checkpoint = $rawCp | ConvertFrom-Json
    } catch {
        $checkpoint = $null
    }
}

$startPage = 1
$existingIds = New-Object 'System.Collections.Generic.HashSet[string]'

if ($null -ne $checkpoint -and $checkpoint.PSObject.Properties.Item('last_completed_page')) {
    $startPage = [int]$checkpoint.last_completed_page + 1
    Write-Host "Resuming from checkpoint page: $startPage (Total repos cataloged so far: $($checkpoint.total_cataloged))" -ForegroundColor Cyan
} else {
    if (Test-Path $inventoryJsonl) {
        Remove-Item -Path $inventoryJsonl -Force | Out-Null
    }
}

# If resuming, load existing repository IDs to prevent duplicates
if (Test-Path $inventoryJsonl) {
    $lines = [System.IO.File]::ReadAllLines($inventoryJsonl)
    foreach ($line in $lines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            try {
                $obj = $line | ConvertFrom-Json
                [void]$existingIds.Add($obj.full_name)
            } catch {}
        }
    }
}

$headers = @{
    'User-Agent' = 'SkillRegistry-Operational-Scanner/1.0.0'
    'Accept'     = 'application/vnd.github.v3+json'
}

if (-not [string]::IsNullOrWhiteSpace($GitHubToken)) {
    $headers['Authorization'] = "token $GitHubToken"
    Write-Host "Using authenticated GitHub API requests." -ForegroundColor Green
} else {
    Write-Host "Using unauthenticated GitHub API requests (60 req/hr rate limit)." -ForegroundColor Yellow
}

$page = $startPage
$totalFetched = $existingIds.Count
$hasMorePages = $true
$rateLimitRemaining = 60
$rateLimitReset = [DateTime]::UtcNow.AddHours(1)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GITHUB STARRED REPOSITORY INVENTORY SCANNER                " -ForegroundColor Cyan
Write-Host " Target User : $Username" -ForegroundColor Cyan
Write-Host " Page Size   : $PerPage" -ForegroundColor Cyan
Write-Host " Target File : $inventoryJsonl" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

while ($hasMorePages -and $page -le $MaxPages) {
    $uri = "https://api.github.com/users/$Username/starred?per_page=$PerPage&page=$page"
    Write-Host "Fetching page $page... ($uri)" -ForegroundColor Gray
    
    try {
        $resp = Invoke-WebRequest -Uri $uri -Headers $headers -UseBasicParsing -TimeoutSec 30
        
        if ($null -ne $resp.Headers) {
            if ($resp.Headers.ContainsKey('X-RateLimit-Remaining')) {
                $rateLimitRemaining = [int]$resp.Headers['X-RateLimit-Remaining']
            }
            if ($resp.Headers.ContainsKey('X-RateLimit-Reset')) {
                $epoch = [double]$resp.Headers['X-RateLimit-Reset']
                $rateLimitReset = [DateTimeOffset]::FromUnixTimeSeconds([long]$epoch).UtcDateTime
            }
        }
        
        $repos = $resp.Content | ConvertFrom-Json
        
        if ($null -eq $repos -or $repos.Count -eq 0) {
            Write-Host "No more starred repositories found. Reached end of stream." -ForegroundColor Green
            $hasMorePages = $false
            break
        }
        
        $pageCount = 0
        $jsonlBatch = New-Object 'System.Text.StringBuilder'
        
        foreach ($repo in $repos) {
            $fullName = [string]$repo.full_name
            if ($existingIds.Contains($fullName)) { continue }
            
            [void]$existingIds.Add($fullName)
            $totalFetched++
            $pageCount++
            
            $topics = if ($repo.PSObject.Properties.Item('topics') -and $null -ne $repo.topics) { @($repo.topics) } else { @() }
            $lang = if ($repo.PSObject.Properties.Item('language') -and $null -ne $repo.language) { [string]$repo.language } else { 'Unknown' }
            $desc = if ($repo.PSObject.Properties.Item('description') -and $null -ne $repo.description) { [string]$repo.description } else { '' }
            $lic = if ($repo.PSObject.Properties.Item('license') -and $null -ne $repo.license -and $repo.license.PSObject.Properties.Item('spdx_id')) { [string]$repo.license.spdx_id } else { 'None' }
            
            $record = [ordered]@{
                schema_version = "1.0.0"
                repo_id = [string]$repo.id
                full_name = $fullName
                owner = [string]$repo.owner.login
                name = [string]$repo.name
                html_url = [string]$repo.html_url
                description = $desc
                language = $lang
                topics = $topics
                stargazers_count = [int]$repo.stargazers_count
                forks_count = if ($repo.PSObject.Properties.Item('forks_count')) { [int]$repo.forks_count } else { 0 }
                default_branch = if ($repo.PSObject.Properties.Item('default_branch')) { [string]$repo.default_branch } else { 'main' }
                is_fork = if ($repo.PSObject.Properties.Item('fork')) { [bool]$repo.fork } else { $false }
                is_archived = if ($repo.PSObject.Properties.Item('archived')) { [bool]$repo.archived } else { $false }
                license_spdx = $lic
                created_at = [string]$repo.created_at
                updated_at = [string]$repo.updated_at
                pushed_at = if ($repo.PSObject.Properties.Item('pushed_at')) { [string]$repo.pushed_at } else { [string]$repo.updated_at }
                cataloged_utc = [DateTime]::UtcNow.ToString("o")
            }
            
            $jsonStr = ($record | ConvertTo-Json -Compress)
            [void]$jsonlBatch.AppendLine($jsonStr)
        }
        
        # Append batch to JSONL file
        if ($jsonlBatch.Length -gt 0) {
            [System.IO.File]::AppendAllText($inventoryJsonl, $jsonlBatch.ToString(), $utf8NoBom)
        }
        
        Write-Host "  -> Page $page complete: Added $pageCount repos (Total cataloged: $totalFetched | RateLimit remaining: $rateLimitRemaining)" -ForegroundColor Green
        
        # Save checkpoint
        $cpData = [ordered]@{
            schema_version = "1.0.0"
            username = $Username
            last_completed_page = $page
            per_page = $PerPage
            total_cataloged = $totalFetched
            ratelimit_remaining = $rateLimitRemaining
            ratelimit_reset_utc = $rateLimitReset.ToString("o")
            updated_utc = [DateTime]::UtcNow.ToString("o")
            status = if ($repos.Count -lt $PerPage) { "COMPLETE" } else { "IN_PROGRESS" }
        }
        $cpJson = $cpData | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($checkpointFile, $cpJson, $utf8NoBom)
        
        if ($repos.Count -lt $PerPage) {
            Write-Host "Received $($repos.Count) (< $PerPage) items. Completed pagination." -ForegroundColor Green
            $hasMorePages = $false
            break
        }
        
        # Check rate limit safety threshold
        if ($rateLimitRemaining -le 2) {
            Write-Host "WARNING: GitHub API rate limit almost exhausted ($rateLimitRemaining remaining). Pausing until $rateLimitReset UTC." -ForegroundColor Yellow
            break
        }
        
        $page++
        Start-Sleep -Milliseconds 300
        
    } catch {
        Write-Host "Error fetching page $page`: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Message -match "403|rate limit") {
            Write-Host "GitHub Rate Limit Hit. Checkpoint saved. Run again once rate limit resets." -ForegroundColor Yellow
        }
        break
    }
}

# Generate Inventory Summary Report
$allRecords = if (Test-Path $inventoryJsonl) {
    [System.IO.File]::ReadAllLines($inventoryJsonl) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_ | ConvertFrom-Json }
} else { @() }

$langBreakdown = @{}
$topicCounts = @{}
$archivedCount = 0
$forkCount = 0

foreach ($r in $allRecords) {
    $l = [string]$r.language
    if (-not $langBreakdown.ContainsKey($l)) { $langBreakdown[$l] = 0 }
    $langBreakdown[$l]++
    
    if ($r.is_archived) { $archivedCount++ }
    if ($r.is_fork) { $forkCount++ }
    
    if ($null -ne $r.topics) {
        foreach ($t in $r.topics) {
            $tStr = [string]$t
            if (-not $topicCounts.ContainsKey($tStr)) { $topicCounts[$tStr] = 0 }
            $topicCounts[$tStr]++
        }
    }
}

$summaryReport = [ordered]@{
    schema = "skill-registry.operational.github-star-inventory/v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    target_username = $Username
    total_starred_cataloged = $allRecords.Count
    inventory_ledger = "staging/github-inlet/starred-inventory.jsonl"
    active_repositories = ($allRecords.Count - $archivedCount)
    archived_repositories = $archivedCount
    forked_repositories = $forkCount
    languages_count = $langBreakdown.Keys.Count
    top_languages = @($langBreakdown.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 15 | ForEach-Object { [ordered]@{ language = $_.Key; count = $_.Value } })
    top_topics = @($topicCounts.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 20 | ForEach-Object { [ordered]@{ topic = $_.Key; count = $_.Value } })
}

$summaryJson = $summaryReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($reportJson, $summaryJson, $utf8NoBom)

# Generate Markdown Report
$activeCount = $allRecords.Count - $archivedCount
$totalCount = $allRecords.Count
$langCount = $langBreakdown.Keys.Count
$nowUtc = [DateTime]::UtcNow.ToString('o')

$mdLines = @(
    "# Operacao 1: GitHub Star Inventory Report",
    "",
    "**Skill Registry v1.0.0 - Operacao Governamental de Descoberta**",
    "- **Usuario Alvo**: $Username",
    "- **Total de Repositorios Catalogados**: $totalCount",
    "- **Modo**: METADATA-FIRST (Zero Clones / Zero Auto-Promocao)",
    "- **Data/Hora (UTC)**: $nowUtc",
    "",
    "---",
    "",
    "## 1. Resumo Executivo da Catalogacao",
    "",
    "| Metrica | Valor |",
    "| :--- | :--- |",
    "| **Total de Repositorios Catalogados** | $totalCount |",
    "| **Repositorios Ativos** | $activeCount |",
    "| **Repositorios Arquivados** | $archivedCount |",
    "| **Forks** | $forkCount |",
    "| **Diversidade de Linguagens** | $langCount |",
    "| **Ledger de Metadados** | staging/github-inlet/starred-inventory.jsonl |",
    "",
    "---",
    "",
    "## 2. Top Linguagens nos Repositorios Favoritos",
    "",
    "| Linguagem | Quantidade de Repositorios |",
    "| :--- | :--- |"
)

$mdList = New-Object 'System.Collections.Generic.List[string]'
foreach ($l in $mdLines) { [void]$mdList.Add($l) }

foreach ($topL in $summaryReport.top_languages) {
    [void]$mdList.Add("| " + [string]$topL.language + " | " + [string]$topL.count + " |")
}

[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 3. Top Topicos / Tags Descobertos")
[void]$mdList.Add("")
[void]$mdList.Add("| Topico / Tag | Ocorrencias |")
[void]$mdList.Add("| :--- | :--- |")

foreach ($topT in $summaryReport.top_topics) {
    [void]$mdList.Add("| " + [string]$topT.topic + " | " + [string]$topT.count + " |")
}

[void]$mdList.Add("")
[void]$mdList.Add("---")
[void]$mdList.Add("")
[void]$mdList.Add("## 4. Proximo Passo Operacional")
[void]$mdList.Add("")
[void]$mdList.Add("Com o inventario de metadados concluido e registrado em ledger imutavel, a **Operacao 2 - Deep Triage & Classification** pode filtrar e priorizar repositorios por topicos de interesse (`skills`, `ai-agent`, `mcp`, `prompts`, `automation`, `tools`), inspecionar unicamente as arvores de arquivos relevantes e submeter eventuais candidatos a quarentena e proveniencia sem clonar a totalidade dos repositorios.")

[System.IO.File]::WriteAllLines($reportMd, $mdList.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " INVENTORY COMPLETE: $totalCount REPOSITORIES CATALOGED " -ForegroundColor Green
Write-Host " Ledger : $inventoryJsonl" -ForegroundColor Green
Write-Host " Report : $reportMd" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
