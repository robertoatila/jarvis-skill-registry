$ErrorActionPreference = 'Stop'
$registryRoot = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).FullName
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$testRoot = Join-Path $tempBase ('jarvis-source-adapter-' + [guid]::NewGuid().ToString('N'))
[void][System.IO.Directory]::CreateDirectory($testRoot)
try {
    Import-Module (Join-Path $registryRoot 'tooling\AgenticOrchestrator.psm1') -Force
    $sourceFile = Join-Path $testRoot 'fixture.py'
    [System.IO.File]::WriteAllText($sourceFile, "answer = 42`n", [System.Text.UTF8Encoding]::new($false))
    $result = Invoke-AgenticAscensionPipeline -TargetRepository 'local/fixture' -RegistryRoot $testRoot -SourceFile $sourceFile
    if ($result.status -ne 'PASS' -or $result.level_verified -ne $false -or $result.scope -ne 'local_source_validation') {
        throw 'Adapter returned an unexpected result or unverified maturity claim.'
    }
    foreach ($artifact in $result.artifacts) {
        if (-not [System.IO.File]::Exists($artifact)) { throw 'Missing artifact.' }
    }
    $missingRejected = $false
    try { Invoke-AgenticAscensionPipeline -TargetRepository 'local/fixture' -RegistryRoot $testRoot }
    catch { $missingRejected = $_.Exception.Message -like '*SourceFile is required*' }
    if (-not $missingRejected) { throw 'Missing source was not rejected.' }
    [System.IO.File]::WriteAllText($sourceFile, 'def broken(:', [System.Text.UTF8Encoding]::new($false))
    $failureRejected = $false
    try { Invoke-AgenticAscensionPipeline -TargetRepository 'local/fixture' -RegistryRoot $testRoot -SourceFile $sourceFile }
    catch { $failureRejected = $_.Exception.Message -like '*Source validation failed*' }
    if (-not $failureRejected) { throw 'Adapter hid compiler failure.' }
    Write-Output 'PASS: local source, emitted artifacts, no maturity certification, missing-input rejection, failure propagation.'
}
finally {
    $resolved = [System.IO.Path]::GetFullPath($testRoot)
    if (-not $resolved.StartsWith($tempBase, [StringComparison]::OrdinalIgnoreCase) -or
        [System.IO.Path]::GetFileName($resolved) -notlike 'jarvis-source-adapter-*') {
        throw 'Cleanup target outside the created temporary test directory.'
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
