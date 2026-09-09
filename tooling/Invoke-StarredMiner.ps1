# ==============================================================================
# J.A.R.V.I.S. // GitHub Starred Repositories Miner & Classifier
# Paginated Mining of Roberto Átila's 2,168 Starred Repositories
# Generates Obsidian Index and Prepares Autonomous Ingestion Pipeline
# ==============================================================================

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [int]$MaxPages = 3,         # 3 pages * 100 = 300 repos per run by default (or set higher)
    [int]$PerPage = 100
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. // GITHUB STARRED REPOSITORIES MINER" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Resolve Token
$token = $env:GITHUB_PERSONAL_ACCESS_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    $mcpConfigPath = 'C:\Users\Ad\.gemini\config\mcp_config.json'
    if (Test-Path $mcpConfigPath) {
        $mcpRaw = [System.IO.File]::ReadAllText($mcpConfigPath) | ConvertFrom-Json
        if ($mcpRaw.mcpServers -and $mcpRaw.mcpServers.'github-mcp-server' -and $mcpRaw.mcpServers.'github-mcp-server'.env -and $mcpRaw.mcpServers.'github-mcp-server'.env.GITHUB_PERSONAL_ACCESS_TOKEN) {
            $token = $mcpRaw.mcpServers.'github-mcp-server'.env.GITHUB_PERSONAL_ACCESS_TOKEN
        }
    }
}

if ([string]::IsNullOrWhiteSpace($token)) {
    throw "GitHub Personal Access Token not found in environment or mcp_config.json!"
}

$headers = @{
    "Authorization" = "Bearer $token"
    "User-Agent" = "JARVIS-Starred-Miner"
    "Accept" = "application/vnd.github.v3+json"
}

# 2. Get User Info and Total Starred Count
$userResp = Invoke-WebRequest -Uri 'https://api.github.com/user/starred?per_page=1' -Headers $headers -UseBasicParsing -TimeoutSec 10
$linkHeader = $userResp.Headers["Link"]
$totalKnownStarred = 2168
if ($linkHeader -match 'page=(\d+)>; rel="last"') {
    $totalKnownStarred = [int]$matches[1]
}

Write-Host "Authenticated GitHub User : robertoatila" -ForegroundColor White
Write-Host "Total Starred no Perfil   : $totalKnownStarred repositorios" -ForegroundColor Yellow
Write-Host "Minerando paginas (1 ate $MaxPages, $PerPage por pagina)..." -ForegroundColor Cyan

$allStarred = New-Object 'System.Collections.Generic.List[object]'

for ($page = 1; $page -le $MaxPages; $page++) {
    Write-Host " -> Buscando pagina $page..." -ForegroundColor DarkGray
    try {
        $uri = "https://api.github.com/user/starred?per_page=$PerPage&page=$page"
        $pageItems = Invoke-RestMethod -Uri $uri -Headers $headers -TimeoutSec 15
        if ($null -eq $pageItems -or $pageItems.Count -eq 0) { break }
        
        foreach ($item in $pageItems) {
            [void]$allStarred.Add([PSCustomObject]@{
                name = $item.name
                full_name = $item.full_name
                html_url = $item.html_url
                description = if ($item.description) { $item.description } else { "" }
                stars = $item.stargazers_count
                language = if ($item.language) { $item.language } else { "Unknown" }
                topics = if ($item.topics) { @($item.topics) } else { @() }
            })
        }
    } catch {
        Write-Warning "Falha na pagina $page : $($_.Exception.Message)"
        break
    }
}

Write-Host "Mineracao concluida: $($allStarred.Count) repositorios extraidos com sucesso!" -ForegroundColor Green

# 3. Save Cache to cache/starred_catalog.json
$cacheDir = Join-Path $RegistryRoot 'cache'
if (-not (Test-Path $cacheDir)) { [void](New-Item -ItemType Directory -Path $cacheDir -Force) }
$cachePath = Join-Path $cacheDir 'starred_catalog.json'

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$cacheJson = ($allStarred | ConvertTo-Json -Depth 5)
[System.IO.File]::WriteAllText($cachePath, $cacheJson, $utf8NoBom)
Write-Host "[OK] Cache gravado em: cache/starred_catalog.json" -ForegroundColor Green

# 4. Classify Repositories into Cognitive Categories
$classified = [ordered]@{
    "Ciberseguranca, Pentest & Evasao" = New-Object 'System.Collections.Generic.List[object]'
    "Hardening, Defesa & Privacidade" = New-Object 'System.Collections.Generic.List[object]'
    "Agentes de IA, RAG & LLMs" = New-Object 'System.Collections.Generic.List[object]'
    "Redes, Proxies & Kernel / XDP" = New-Object 'System.Collections.Generic.List[object]'
    "DevTools, Compiladores & Linguagens" = New-Object 'System.Collections.Generic.List[object]'
}

foreach ($r in $allStarred) {
    $textSearch = "$($r.name) $($r.description) $($r.topics -join ' ')".ToLower()
    
    if ($textSearch -match 'obfus|hook|evasion|antivm|debugger|inject|rootkit|payload|bypass|exploit|killer|malware|offensive|pentest|reversing|ghidra|ida') {
        [void]$classified["Ciberseguranca, Pentest & Evasao"].Add($r)
    } elseif ($textSearch -match 'adblock|hblock|firewall|hardening|security|privacy|audit|shield|guard|antivirus|cleaner|defense') {
        [void]$classified["Hardening, Defesa & Privacidade"].Add($r)
    } elseif ($textSearch -match 'agent|ai|llm|rag|gpt|claude|langchain|autogen|crewai|vllm|dspy|prompt|embeddings|qdrant') {
        [void]$classified["Agentes de IA, RAG & LLMs"].Add($r)
    } elseif ($textSearch -match 'bgp|xdp|ebpf|network|socket|packet|router|vpn|wireguard|proxy|tunnel|dns|pcap') {
        [void]$classified["Redes, Proxies & Kernel / XDP"].Add($r)
    } else {
        [void]$classified["DevTools, Compiladores & Linguagens"].Add($r)
    }
}

# 5. Generate 06 - GitHub Starred Repositories (2.1k Arsenal Pipeline).md in Obsidian
$docPath = Join-Path $RegistryRoot '06 - GitHub Starred Repositories.md'
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("---")
[void]$sb.AppendLine("title: 06 - GitHub Starred Repositories (Pipeline de Expansao)")
[void]$sb.AppendLine("type: starred-catalog")
[void]$sb.AppendLine("total_github_starred: $totalKnownStarred")
[void]$sb.AppendLine("mined_in_cache: $($allStarred.Count)")
[void]$sb.AppendLine("user: robertoatila")
[void]$sb.AppendLine("tags:")
[void]$sb.AppendLine("  - github-starred")
[void]$sb.AppendLine("  - candidate-pipeline")
[void]$sb.AppendLine("  - sovereign-miner")
[void]$sb.AppendLine("---`n")

[void]$sb.AppendLine("# Catalogo de Repositorios Favoritados no GitHub ($totalKnownStarred Total)`n")
[void]$sb.AppendLine("> [!TIP] Tesouro Bruto do Arsenal")
[void]$sb.AppendLine("> O usuario possui **$totalKnownStarred repositorios favoritados** no GitHub. Este indice lista os **$($allStarred.Count) repositorios minerados** nesta rodada, categorizados automaticamente para analise e proposta via J.A.R.V.I.S.`n")
[void]$sb.AppendLine("[[00 - J.A.R.V.I.S. Cognitive Vault|Voltar ao Painel Mestre]]`n")

[void]$sb.AppendLine("## ⚡ Como Ingerir Qualquer um Desses Repositorios:")
[void]$sb.AppendLine('```powershell')
[void]$sb.AppendLine("# Exemplo para ingerir o KiExitDispatcher/GoDefender:")
[void]$sb.AppendLine("skillctl ingest KiExitDispatcher/GoDefender")
[void]$sb.AppendLine("")
[void]$sb.AppendLine("# Ou abra o J.A.R.V.I.S. Command Center no navegador:")
[void]$sb.AppendLine("skillctl jarvis")
[void]$sb.AppendLine('```')
[void]$sb.AppendLine("")

foreach ($cat in $classified.Keys) {
    $cList = $classified[$cat]
    [void]$sb.AppendLine("## $cat ($($cList.Count) repositorios)")
    [void]$sb.AppendLine("| Repositorio | Estrelas | Linguagem | Descricao | Acao J.A.R.V.I.S. |")
    [void]$sb.AppendLine("| :--- | :---: | :---: | :--- | :--- |")
    
    foreach ($cr in ($cList | Sort-Object -Property stars -Descending)) {
        $descTrunc = if ($cr.description.Length -gt 75) { $cr.description.Substring(0, 72) + "..." } else { $cr.description }
        $descClean = $descTrunc.Replace("|", "/")
        [void]$sb.AppendLine("| [$($cr.full_name)]($($cr.html_url)) | $($cr.stars) | $($cr.language) | $descClean | `skillctl ingest $($cr.full_name)` |")
    }
    [void]$sb.AppendLine("")
}

[System.IO.File]::WriteAllText($docPath, $sb.ToString(), $utf8NoBom)
Write-Host "[OK] Created: 06 - GitHub Starred Repositories.md in Obsidian Vault!" -ForegroundColor Green

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  MINERACAO CONCLUIDA COM SUCESSO!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
