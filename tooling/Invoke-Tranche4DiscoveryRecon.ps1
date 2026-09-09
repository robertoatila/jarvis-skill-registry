# Skill Registry - Tranche 4 Discovery Reconnaissance
[CmdletBinding()]
param(
    [string[]]$CandidateRepos = @(
        'Orchestra-Research/AI-Research-SKILLs',
        'HKUDS/nanobot',
        'Panniantong/Agent-Reach',
        'Graphify-Labs/graphify',
        'ruvnet/ruflo'
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$headers = @{
    'User-Agent' = 'SkillRegistry-Tranche4/1.0.0'
    'Accept'     = 'application/vnd.github.v3+json'
}

$rateResp = Invoke-WebRequest -Uri 'https://api.github.com/rate_limit' -Headers $headers -UseBasicParsing
$rateObj = $rateResp.Content | ConvertFrom-Json
Write-Host "GitHub Rate Limit Remaining: $($rateObj.rate.remaining)" -ForegroundColor Green

$discoveredBlobs = New-Object 'System.Collections.Generic.List[object]'

foreach ($repo in $CandidateRepos) {
    Write-Host "`nQuerying tree for $repo..." -ForegroundColor Yellow
    $treeItems = $null
    $resolvedBranch = $null
    
    foreach ($branch in @('main', 'master')) {
        $uri = "https://api.github.com/repos/$repo/git/trees/$branch`?recursive=1"
        try {
            $resp = Invoke-WebRequest -Uri $uri -Headers $headers -UseBasicParsing -TimeoutSec 15
            $json = $resp.Content | ConvertFrom-Json
            if ($null -ne $json.PSObject.Properties['tree']) {
                $treeItems = @($json.tree)
                $resolvedBranch = $branch
                break
            }
        } catch {}
    }
    
    if ($null -eq $treeItems) {
        Write-Host "  Could not fetch tree for $repo." -ForegroundColor DarkYellow
        continue
    }
    
    Write-Host "  Fetched $($treeItems.Count) items on branch '$resolvedBranch'." -ForegroundColor Green
    
    $matches = $treeItems | Where-Object {
        $p = [string]$_.path.ToLowerInvariant()
        $_.type -eq 'blob' -and ($p -match 'skill\.md$' -or $p -match 'skills/.+/skill\.md$' -or $p -match 'prompts?/.+\.md$')
    }
    
    Write-Host "  Discovered $($matches.Count) potential skill/prompt definition blobs." -ForegroundColor Cyan
    
    foreach ($m in $matches) {
        $item = [ordered]@{
            repo = $repo
            branch = $resolvedBranch
            path = $m.path
            blob_sha = $m.sha
            size_bytes = if ($m.PSObject.Properties.Item('size')) { [int]$m.size } else { 0 }
        }
        [void]$discoveredBlobs.Add($item)
        Write-Host "    - $($m.path) (SHA: $($m.sha), $($item.size_bytes) bytes)" -ForegroundColor Gray
    }
}

Write-Host "`nTotal blobs discovered in Tranche 4 recon: $($discoveredBlobs.Count)" -ForegroundColor Green
$discoveredBlobs | ConvertTo-Json -Depth 5 | Out-File -FilePath 'E:\.skill-registry\staging\github-inlet\discovered-tranche4-candidates.json' -Encoding utf8
