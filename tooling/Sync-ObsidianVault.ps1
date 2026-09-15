# Compatibility entry point: the existing vault bridge owns every projection.
[CmdletBinding()]
param([string]$RegistryRoot = 'E:\.skill-registry')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
try {
    & python -m tooling.agentic.workspace_hub --root $RegistryRoot --sync-obsidian
    if ($LASTEXITCODE -ne 0) { throw 'Obsidian synchronization failed; inspect the reported error.' }
} finally {
    Pop-Location
}
