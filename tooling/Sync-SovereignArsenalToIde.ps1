# ==============================================================================
# J.A.R.V.I.S. Arsenal Synchronizer -> Antigravity IDE & Agent Workspaces
# Purpose: Maintain parity across:
#   - E:\.skill-registry\skills (Sovereign Canonical Vault)
#   - C:\Users\Ad\.gemini\config\skills (Antigravity Global IDE Config)
#   - C:\Users\Ad\.agents\skills (Coding Agents Workspace)
# Enforces: Sovereign Token Governance (Description <= 20 words)
# ==============================================================================

[CmdletBinding()]
param(
    [string]$SourceVault = 'E:\.skill-registry\skills',
    [string]$GeminiConfig = 'C:\Users\Ad\.gemini\config\skills',
    [string]$AgentsWorkspace = 'C:\Users\Ad\.agents\skills',
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $SourceVault)) {
    throw "Source vault not found: $SourceVault"
}
if (-not (Test-Path $GeminiConfig)) {
    New-Item -ItemType Directory -Path $GeminiConfig -Force | Out-Null
}

$sourceSkills = Get-ChildItem -Path $SourceVault -Directory
Write-Host "Iniciando sincronizacao soberana J.A.R.V.I.S. Arsenal..." -ForegroundColor Cyan
Write-Host "Cofre Soberano : $SourceVault ($($sourceSkills.Count) skills)"
Write-Host "Destino IDE    : $GeminiConfig"
Write-Host "Destino Agentes: $AgentsWorkspace"
Write-Host "Regra de Ouro  : Token Budget Governance (<= 20 palavras na descricao)`n"

$synced = 0
$pruned = 0

foreach ($s in $sourceSkills) {
    $srcSkillMd = Join-Path $s.FullName 'SKILL.md'
    if (-not (Test-Path $srcSkillMd)) { continue }

    $raw = [System.IO.File]::ReadAllText($srcSkillMd)

    # Check description length and prune if needed
    if ($raw -match '(?m)^description:\s*["'']?([^"''\r\n]+)["'']?') {
        $desc = $matches[1].Trim()
        $words = $desc -split '\s+'
        if ($words.Count -gt 20) {
            $prunedDesc = ($words[0..17] -join ' ')
            if (-not $prunedDesc.EndsWith('.')) { $prunedDesc += '.' }
            $raw = $raw -replace '(?m)^description:\s*["'']?[^"''\r\n]+["'']?', "description: $prunedDesc"
            $pruned++
            if (-not $WhatIf) {
                [System.IO.File]::WriteAllText($srcSkillMd, $raw, [System.Text.Encoding]::UTF8)
            }
        }
    }

    # Mirror to Gemini Config
    $geminiSkillDir = Join-Path $GeminiConfig $s.Name
    $geminiSkillMd = Join-Path $geminiSkillDir 'SKILL.md'
    if (-not (Test-Path $geminiSkillDir) -and -not $WhatIf) {
        New-Item -ItemType Directory -Path $geminiSkillDir -Force | Out-Null
    }
    if (-not $WhatIf) {
        [System.IO.File]::WriteAllText($geminiSkillMd, $raw, [System.Text.Encoding]::UTF8)
        $subDirs = @('scripts', 'resources', 'references')
        foreach ($sub in $subDirs) {
            $subSrc = Join-Path $s.FullName $sub
            if (Test-Path $subSrc) {
                $subTarget = Join-Path $geminiSkillDir $sub
                Copy-Item -Path $subSrc -Destination $subTarget -Recurse -Force
            }
        }
    }

    # Mirror to Agents Workspace if present
    if (Test-Path $AgentsWorkspace) {
        $agentSkillDir = Join-Path $AgentsWorkspace $s.Name
        if (Test-Path $agentSkillDir) {
            $agentSkillMd = Join-Path $agentSkillDir 'SKILL.md'
            if (-not $WhatIf) {
                [System.IO.File]::WriteAllText($agentSkillMd, $raw, [System.Text.Encoding]::UTF8)
            }
        }
    }

    $synced++
}

Write-Host "=================================================" -ForegroundColor Green
Write-Host " Sincronizacao Concluida com Sucesso!" -ForegroundColor Green
Write-Host " Total de Skills Sincronizadas : $synced"
Write-Host " Skills com Poda de Descricao  : $pruned"
Write-Host " Token Budget Preservado       : SAFE (<= 20 palavras)"
Write-Host "=================================================" -ForegroundColor Green

