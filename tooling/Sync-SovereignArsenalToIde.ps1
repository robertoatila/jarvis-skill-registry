# ==============================================================================
# J.A.R.V.I.S. Arsenal Synchronizer -> Antigravity IDE Global Config
# Purpose: Mirror Sovereign Skills into C:\Users\Ad\.gemini\config\skills
# Enforces: Sovereign Token Governance (Description <= 25 words)
# ==============================================================================

[CmdletBinding()]
param(
    [string]$SourceVault = 'E:\.skill-registry\skills',
    [string]$TargetConfig = 'C:\Users\Ad\.gemini\config\skills',
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $SourceVault)) {
    throw "Source vault not found: $SourceVault"
}
if (-not (Test-Path $TargetConfig)) {
    New-Item -ItemType Directory -Path $TargetConfig -Force | Out-Null
}

$sourceSkills = Get-ChildItem -Path $SourceVault -Directory
Write-Host "Iniciando sincronizacao soberana..." -ForegroundColor Cyan
Write-Host "Origem : $SourceVault ($($sourceSkills.Count) skills)"
Write-Host "Destino: $TargetConfig"
Write-Host "Regra  : Token Budget Governance (<= 25 palavras na descricao)`n"

$synced = 0
$pruned = 0

foreach ($s in $sourceSkills) {
    $srcSkillMd = Join-Path $s.FullName 'SKILL.md'
    if (-not (Test-Path $srcSkillMd)) { continue }

    $targetSkillDir = Join-Path $TargetConfig $s.Name
    $targetSkillMd = Join-Path $targetSkillDir 'SKILL.md'

    if (-not (Test-Path $targetSkillDir)) {
        if (-not $WhatIf) {
            New-Item -ItemType Directory -Path $targetSkillDir -Force | Out-Null
        }
    }

    $raw = [System.IO.File]::ReadAllText($srcSkillMd)

    # Check description length and prune if needed
    if ($raw -match '(?m)^description:\s*["'']?([^"''\r\n]+)["'']?') {
        $desc = $matches[1].Trim()
        $words = $desc -split '\s+'
        if ($words.Count -gt 13) {
            $prunedDesc = ($words[0..11] -join ' ')
            if (-not $prunedDesc.EndsWith('.')) { $prunedDesc += '.' }
            $raw = $raw -replace '(?m)^description:\s*["'']?[^"''\r\n]+["'']?', "description: $prunedDesc"
            $pruned++
        }
    }

    if (-not $WhatIf) {
        [System.IO.File]::WriteAllText($targetSkillMd, $raw, [System.Text.Encoding]::UTF8)
        
        # Copy helper scripts or resources if they exist
        $subDirs = @('scripts', 'resources', 'references')
        foreach ($sub in $subDirs) {
            $subSrc = Join-Path $s.FullName $sub
            if (Test-Path $subSrc) {
                $subTarget = Join-Path $targetSkillDir $sub
                Copy-Item -Path $subSrc -Destination $subTarget -Recurse -Force
            }
        }
    }

    $synced++
}

Write-Host "=================================================" -ForegroundColor Green
Write-Host " Sincronizacao Concluida com Sucesso!" -ForegroundColor Green
Write-Host " Total de Skills Sincronizadas : $synced"
Write-Host " Skills com Poda de Descricao  : $pruned"
Write-Host " Token Budget Preservado       : SAFE (< 25 palavras)"
Write-Host "=================================================" -ForegroundColor Green
