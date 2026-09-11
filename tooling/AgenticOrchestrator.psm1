# Local source-validation bridge. No repository synthesis or maturity certification.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-AgenticAscensionPipeline {
    [CmdletBinding()]
    param(
        [string]$TargetRepository = "anthropics/anthropic-quickstarts",
        [string]$RegistryRoot = 'E:\.skill-registry',
        [int]$TargetMaturityLevel = 9,
        [string]$SourceFile
    )

    if ([string]::IsNullOrWhiteSpace($SourceFile)) {
        throw 'SourceFile is required. Repository analysis and source synthesis were not executed.'
    }
    $resolvedSource = (Get-Item -LiteralPath $SourceFile -ErrorAction Stop).FullName
    if (-not [System.IO.File]::Exists($resolvedSource)) { throw 'SourceFile must be a file.' }
    if ($resolvedSource.Contains('"') -or $RegistryRoot.Contains('"')) { throw 'Invalid argument path.' }
    $parts = $TargetRepository -split '/'
    $rawName = if ($parts.Length -ge 2) { $parts[1] } else { $TargetRepository }
    $cleanName = ($rawName -replace '[^a-zA-Z0-9_-]', '-')
    if ([string]::IsNullOrWhiteSpace($cleanName)) { throw 'A nonempty target name is required.' }

    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = 'python.exe'
    $pinfo.Arguments = "-B -m tooling.agentic.swe_orchestrator `"$cleanName`" --source `"$resolvedSource`" --registry-root `"$RegistryRoot`""
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true
    $pinfo.WorkingDirectory = $PSScriptRoot | Split-Path -Parent
    $process = [System.Diagnostics.Process]::Start($pinfo)
    try {
        $stdoutRead = $process.StandardOutput.ReadToEndAsync()
        $stderrRead = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(60000)) {
            $process.Kill()
            throw 'Local source validation exceeded its 60-second limit.'
        }
        $stdout = $stdoutRead.GetAwaiter().GetResult()
        $stderr = $stderrRead.GetAwaiter().GetResult()
        if ([string]::IsNullOrWhiteSpace($stdout)) {
            throw "Source validation returned no result (exit $($process.ExitCode)): $stderr"
        }
        $result = $stdout | ConvertFrom-Json
        if ($process.ExitCode -ne 0 -or $result.status -ne 'PASS') {
            throw "Source validation failed (exit $($process.ExitCode)): $($result.status). $stderr"
        }
        return [PSCustomObject]@{
            status = $result.status
            scope = $result.scope
            requested_level = $TargetMaturityLevel
            level_verified = $false
            composite_score = $result.composite_score
            target_repository = $TargetRepository
            source_file = $resolvedSource
            artifacts = $result.artifacts
            stages_passed = $result.passed_stages
            evidence = $result.evidence
            timestamp = (Get-Date).ToUniversalTime().ToString('o')
        }
    }
    finally { $process.Dispose() }
}
Export-ModuleMember -Function Invoke-AgenticAscensionPipeline
