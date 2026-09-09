# ==============================================================================
# J.A.R.V.I.S. // Backup-SovereignProfile.ps1
# Pre-Migration Snapshot of Antigravity Configurations, Skills, and MCPs
# ==============================================================================

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$BackupDir = 'E:\.skill-registry\backups'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  J.A.R.V.I.S. // BACKUP SOBERANO DO PERFIL ANTIGRAVITY" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan

if (-not (Test-Path $BackupDir)) {
    [void](New-Item -ItemType Directory -Path $BackupDir -Force)
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$tempStageDir = Join-Path $BackupDir "stage_$timestamp"
$zipFile = Join-Path $BackupDir "antigravity_backup_$timestamp.zip"

try {
    [void](New-Item -ItemType Directory -Path $tempStageDir -Force)
    
    # 1. Backup Global Config Directory (GEMINI.md, mcp_config.json, and config skills)
    $globalConfigSource = 'C:\Users\Ad\.gemini\config'
    if (Test-Path $globalConfigSource) {
        Write-Host " [+] Copiando diretorio global C:\Users\Ad\.gemini\config..." -ForegroundColor White
        $stageConfigDir = Join-Path $tempStageDir 'global_config'
        Copy-Item -Path $globalConfigSource -Destination $stageConfigDir -Recurse -Force
    }

    # 2. Backup User Skills Directory
    $userSkillsSource = 'C:\Users\Ad\.gemini\skills'
    if (Test-Path $userSkillsSource) {
        $skillCount = (Get-ChildItem -Path $userSkillsSource -Directory).Count
        Write-Host " [+] Copiando $skillCount skills locais de C:\Users\Ad\.gemini\skills..." -ForegroundColor White
        $stageSkillsDir = Join-Path $tempStageDir 'user_skills'
        Copy-Item -Path $userSkillsSource -Destination $stageSkillsDir -Recurse -Force
    }
    
    # 3. Backup State & Manifest
    $stateSource = Join-Path $RegistryRoot 'state\current-state.json'
    if (Test-Path $stateSource) {
        Write-Host " [+] Copiando current-state.json..." -ForegroundColor White
        Copy-Item -Path $stateSource -Destination (Join-Path $tempStageDir 'current-state.json') -Force
    }
    
    $manifestSource = Join-Path $RegistryRoot 'releases\v1.0.0\manifest-v1.0.0.json'
    if (Test-Path $manifestSource) {
        Write-Host " [+] Copiando manifesto Hyperion v1.0.0..." -ForegroundColor White
        Copy-Item -Path $manifestSource -Destination (Join-Path $tempStageDir 'manifest-v1.0.0.json') -Force
    }
    
    # 4. Create Metadata
    $meta = [ordered]@{
        backup_created_utc = (Get-Date).ToUniversalTime().ToString('o')
        windows_user = $env:USERNAME
        registry_root = $RegistryRoot
        backup_type = "PRE_GOOGLE_ACCOUNT_MIGRATION"
        note = "Armazena estado soberano para prevencao contra reset acidental na troca de conta Google"
    }
    $metaJson = $meta | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText((Join-Path $tempStageDir 'backup_metadata.json'), $metaJson, [System.Text.Encoding]::UTF8)
    
    # 5. Compress to Zip
    Write-Host " [+] Compactando arquivo de backup..." -ForegroundColor Cyan
    Add-Type -AssemblyName 'System.IO.Compression.FileSystem'
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempStageDir, $zipFile)
    
    # 6. Compute SHA-256
    $sha256 = (Get-FileHash -Path $zipFile -Algorithm SHA256).Hash.ToLowerInvariant()
    $shaFile = "$zipFile.sha256"
    [System.IO.File]::WriteAllText($shaFile, "$sha256 *$([System.IO.Path]::GetFileName($zipFile))`n", [System.Text.Encoding]::UTF8)
    
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "  BACKUP CRIADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "Arquivo ZIP : $zipFile" -ForegroundColor White
    Write-Host "Tamanho     : $((Get-Item $zipFile).Length / 1MB | ForEach-Object { '{0:N2} MB' -f $_ })" -ForegroundColor White
    Write-Host "SHA-256     : $sha256" -ForegroundColor Yellow
    Write-Host "=================================================================" -ForegroundColor Green
}
finally {
    if (Test-Path $tempStageDir) {
        Remove-Item -Path $tempStageDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
