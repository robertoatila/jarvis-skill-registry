param(
    [string]$RegistryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'legacy-governance gate requires Windows'
}

$sourceRoot = (Resolve-Path $RegistryRoot).Path.TrimEnd('\')
$protectedLegacyRoot = 'E:\.skill-registry'
$legacyRoot = $protectedLegacyRoot
$usesTemporaryLegacyRoot = $false
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

function Invoke-ScriptChecked {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "PowerShell gate failed: $Name (exit code $LASTEXITCODE)"
    }
}

function Remove-GeneratedTemporaryRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedNamePattern
    )

    if (-not (Test-Path -LiteralPath $Path)) { return }
    $item = Get-Item -LiteralPath $Path -Force
    $resolvedPath = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd('\')
    $tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    $isTemporaryChild = $resolvedPath.StartsWith(
        $tempRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    )
    $isGeneratedName = $item.Name -match $ExpectedNamePattern
    $isDirectory = $item.PSIsContainer
    $isReparsePoint = ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0

    if ($isTemporaryChild -and $isGeneratedName -and $isDirectory -and -not $isReparsePoint) {
        Remove-Item -LiteralPath $resolvedPath -Recurse -Force
    } else {
        Write-Warning 'legacy-governance left an unexpected temporary cleanup target untouched'
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
            $legacyRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
                'jarvis-plan4-legacy-' + [Guid]::NewGuid().ToString('N')
            )
            $usesTemporaryLegacyRoot = $true
        }

        if (Test-Path $legacyRoot) {
            throw 'legacy-governance temporary workspace path already exists'
        }

        New-Item -ItemType Directory -Path $legacyRoot | Out-Null
        $createdLegacyRoot = $true

        Get-ChildItem -Path $sourceRoot -Force |
            Where-Object { $_.Name -notin @('.git', 'node_modules', 'reports', 'backups') } |
            ForEach-Object {
                Copy-Item -Path $_.FullName -Destination $legacyRoot -Recurse -Force
            }
    }

    Set-Location $legacyRoot
    New-Item -ItemType Directory -Path reports -Force | Out-Null

    Invoke-ScriptChecked 'Bootstrap' { & ./tooling/Bootstrap.ps1 -RegistryRoot $PWD }
    Invoke-ScriptChecked 'Distribution reconnaissance' {
        & ./tests/Invoke-DistributionReconTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-25-distribution-recon.json')
    }
    Invoke-ScriptChecked 'GitHub intelligence reconnaissance' {
        & ./tests/Invoke-GitHubIntelligenceReconTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-26-github-intelligence-recon.json')
    }
    Invoke-ScriptChecked 'Distribution engine' {
        & ./tests/Invoke-DistributionEngineTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-27-distribution-engine.json')
    }
    Invoke-ScriptChecked 'Resolution engine' {
        & ./tests/Invoke-ResolutionEngineTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-28-project-profiles-lockfiles.json')
    }
    Invoke-ScriptChecked 'OCI distribution' {
        & ./tests/Invoke-OciDistributionTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-29-remote-oci-distribution.json')
    }
    Invoke-ScriptChecked 'Federation' {
        & ./tests/Invoke-FederationTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-30-federation.json')
    }
    Invoke-ScriptChecked 'MCP API gateway' {
        & ./tests/Invoke-McpApiGatewayTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-31-mcp-api-gateway.json')
    }
    Invoke-ScriptChecked 'Sidecar' {
        & ./tests/Invoke-SidecarTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-32-sidecar-sync.json')
    }
    Invoke-ScriptChecked 'Public packaging' {
        & ./tests/Invoke-PackagingTests.ps1 -RegistryRoot $PWD -OutputPath (Join-Path $legacyRoot 'reports\phase-33-open-source-packaging.json')
    }

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

    if ($createdLegacyRoot -and (Test-Path -LiteralPath $legacyRoot)) {
        $item = Get-Item -LiteralPath $legacyRoot -Force
        $resolvedRoot = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd('\')
        $isDirectory = $item.PSIsContainer
        $isReparsePoint = ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
        $isExpectedRoot = if ($usesTemporaryLegacyRoot) {
            $tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
            $resolvedRoot.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
                $item.Name -match '^jarvis-plan4-legacy-[0-9a-f]{32}$'
        } else {
            $resolvedRoot -eq [System.IO.Path]::GetFullPath($protectedLegacyRoot).TrimEnd('\')
        }

        if ($isDirectory -and -not $isReparsePoint -and $isExpectedRoot) {
            Remove-Item -LiteralPath $resolvedRoot -Recurse -Force
        } else {
            Write-Warning 'legacy-governance left an unexpected cleanup target untouched'
        }
    }

    if ($createdSubst) {
        subst E: /d | Out-Null
    }

    if ($compatRoot) {
        Remove-GeneratedTemporaryRoot `
            -Path $compatRoot `
            -ExpectedNamePattern '^jarvis-plan4-[0-9a-f]{32}$'
    }
}
