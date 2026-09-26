param(
    [string]$RegistryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'legacy-governance gate requires Windows'
}

$sourceRoot = (Resolve-Path $RegistryRoot).Path.TrimEnd('\')
$legacyRoot = 'E:\.skill-registry'
$createdSubst = $false
$createdLegacyRoot = $false
$compatRoot = $null
$originalLocation = (Get-Location).Path

function Invoke-ExternalChecked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "External command failed with exit code $LASTEXITCODE"
    }
}

try {
    if (-not (Test-Path 'E:\')) {
        $compatRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
            'jarvis-plan4-' + [Guid]::NewGuid().ToString('N')
        )
        New-Item -ItemType Directory -Path $compatRoot -Force | Out-Null
        subst E: $compatRoot
        if ($LASTEXITCODE -ne 0) {
            throw 'Unable to create temporary E: compatibility drive'
        }
        $createdSubst = $true
    }

    if ($sourceRoot -ine $legacyRoot.TrimEnd('\')) {
        if (Test-Path $legacyRoot) {
            throw (
                'legacy-governance refused to overwrite existing E:\.skill-registry; ' +
                'run from that checkout or provide a Windows runner with a free legacy path'
            )
        }

        New-Item -ItemType Directory -Path $legacyRoot -Force | Out-Null
        $createdLegacyRoot = $true

        Get-ChildItem -Path $sourceRoot -Force |
            Where-Object { $_.Name -notin @('.git', 'node_modules', 'reports', 'backups') } |
            ForEach-Object {
                Copy-Item -Path $_.FullName -Destination $legacyRoot -Recurse -Force
            }
    }

    Set-Location $legacyRoot

    & ./tooling/Bootstrap.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-DistributionReconTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-GitHubIntelligenceReconTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-DistributionEngineTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-ResolutionEngineTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-OciDistributionTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-FederationTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-McpApiGatewayTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-SidecarTests.ps1 -RegistryRoot $PWD
    & ./tests/Invoke-PackagingTests.ps1 -RegistryRoot $PWD

    New-Item -ItemType Directory -Path reports -Force | Out-Null
    Invoke-ExternalChecked { python -B tooling/validate_isolated.py --report reports/direct-runtime.json }
    Invoke-ExternalChecked { node --check ui/jarvis.js }
    Invoke-ExternalChecked { python -B tooling/audit_pre_publish_security.py }

    $forbiddenPatterns = @(
        'ghp_[A-Za-z0-9_]{36}',
        'github_pat_[A-Za-z0-9_]{82}',
        'BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY',
        'AKIA[0-9A-Z]{16}'
    )

    $files = Get-ChildItem -Path . -Recurse -File |
        Where-Object {
            $_.FullName -notmatch '\\.git\\' -and
            $_.FullName -notmatch '\\node_modules\\' -and
            $_.FullName -notmatch '\\reports\\' -and
            $_.FullName -notmatch '\\backups\\' -and
            $_.FullName -notmatch '\\__pycache__\\' -and
            $_.Extension -notin @('.pyc', '.pyo')
        }

    foreach ($file in $files) {
        $content = [System.IO.File]::ReadAllText($file.FullName)
        foreach ($pattern in $forbiddenPatterns) {
            if ($content -match $pattern) {
                throw "Secret-shaped pattern found in $($file.FullName)"
            }
        }
    }

    Write-Host 'legacy-governance: PASS'
}
finally {
    Set-Location $originalLocation

    if ($createdLegacyRoot -and (Test-Path $legacyRoot)) {
        Remove-Item -Path $legacyRoot -Recurse -Force
    }

    if ($createdSubst) {
        subst E: /d | Out-Null
    }

    if ($compatRoot -and (Test-Path $compatRoot)) {
        Remove-Item -Path $compatRoot -Recurse -Force
    }
}
