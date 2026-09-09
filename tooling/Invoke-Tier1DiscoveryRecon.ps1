# Skill Registry - Discovery Tranche Reconnaissance (Tier 1 Repositories)
[CmdletBinding()]
param(
    [string[]]$TargetRepos = @(
        'addyosmani/agent-skills',
        'ComposioHQ/awesome-claude-skills',
        'Leonxlnx/taste-skill',
        'K-Dense-AI/scientific-agent-skills',
        'Donchitos/Claude-Code-Game-Studios'
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$headers = @{
    'User-Agent' = 'SkillRegistry-Discovery/1.0.0'
    'Accept'     = 'application/vnd.github.v3+json'
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DISCOVERY TRANCHE RECONNAISSANCE: TIER 1 REPOSITORIES       " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$discoveredCandidates = New-Object 'System.Collections.Generic.List[object]'

foreach ($repo in $TargetRepos) {
    Write-Host "`nScanning repository: $repo..." -ForegroundColor Yellow
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
        } catch {
            # Try next branch
        }
    }
    
    if ($null -eq $treeItems) {
        Write-Host "  Could not fetch tree for $repo (tried main & master)." -ForegroundColor DarkYellow
        continue
    }
    
    Write-Host "  Tree fetched successfully on branch '$resolvedBranch' ($($treeItems.Count) items)." -ForegroundColor Green
    
    $skills = $treeItems | Where-Object { 
        $pathLower = $_.path.ToLowerInvariant()
        $_.type -eq 'blob' -and ($pathLower -match 'skill\.md$' -or $pathLower -match 'skills/.+/skill\.md$')
    }
    
    Write-Host "  Found $($skills.Count) skill definition blobs." -ForegroundColor Cyan
    
    foreach ($s in $skills) {
        $cand = [ordered]@{
            repo = $repo
            branch = $resolvedBranch
            path = $s.path
            blob_sha = $s.sha
            size_bytes = if ($s.PSObject.Properties.Item('size')) { [int]$s.size } else { 0 }
        }
        [void]$discoveredCandidates.Add($cand)
        Write-Host "    - $($s.path) (SHA: $($s.sha), Size: $($cand.size_bytes) bytes)" -ForegroundColor Gray
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " DISCOVERY SUMMARY: $($discoveredCandidates.Count) CANDIDATES FOUND" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

$discoveredCandidates | ConvertTo-Json -Depth 5 | Out-File -FilePath 'E:\.skill-registry\staging\github-inlet\discovered-tier1-candidates.json' -Encoding utf8
