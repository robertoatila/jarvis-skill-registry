# Skill Registry — Cross-Platform Bootstrap & Self-Test Initialization

[CmdletBinding()]
param(
    [string]$RegistryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BOOTSTRAPPING SKILL REGISTRY ENVIRONMENT                   " -ForegroundColor Cyan
Write-Host " Root: $RegistryRoot" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Directory structure validation
$requiredDirs = @('schemas', 'tooling', 'tests', 'reports', 'staging', 'adapters', 'docs')
foreach ($d in $requiredDirs) {
    $dirPath = Join-Path $RegistryRoot $d
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Write-Host "  [INIT] Created missing directory: $d" -ForegroundColor Yellow
    } else {
        Write-Host "  [OK] Verified directory: $d" -ForegroundColor Green
    }
}

# 2. Schema Integrity Verification
$schemas = @(Get-ChildItem -Path (Join-Path $RegistryRoot 'schemas') -Filter '*.schema.json')
Write-Host "  [INFO] Validating $($schemas.Count) JSON schemas..." -ForegroundColor Cyan
foreach ($s in $schemas) {
    try {
        $content = [System.IO.File]::ReadAllText($s.FullName)
        $null = $content | ConvertFrom-Json
    } catch {
        Write-Error "Invalid JSON in schema: $($s.Name) ($($_.Exception.Message))"
        exit 1
    }
}
Write-Host "  [OK] All $($schemas.Count) schemas parsed successfully." -ForegroundColor Green

# 3. Core Engine Import Verification
$modules = @(Get-ChildItem -Path (Join-Path $RegistryRoot 'tooling') -Filter '*.psm1')
Write-Host "  [INFO] Loading $($modules.Count) PowerShell engine modules..." -ForegroundColor Cyan
foreach ($m in $modules) {
    try {
        Import-Module $m.FullName -Force
        Write-Host "  [OK] Loaded module: $($m.Name)" -ForegroundColor Green
    } catch {
        Write-Error "Failed to load module: $($m.Name) ($($_.Exception.Message))"
        exit 1
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BOOTSTRAP COMPLETE: REGISTRY IS OPERATIONAL AND SEALED     " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
