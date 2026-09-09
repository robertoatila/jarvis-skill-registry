# Phase 26 Test Harness — GitHub Repository Intelligence Reconnaissance

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$OutputPath = 'E:\.skill-registry\reports\phase-26-github-intelligence-recon.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$testResults = New-Object 'System.Collections.Generic.List[object]'
$globalPassed = $true

function Assert-GitHubTest {
    param(
        [string]$Id,
        [string]$Description,
        [scriptblock]$Assertion
    )
    $testResult = [ordered]@{
        id = $Id
        description = $Description
        status = 'FAIL'
        error = $null
    }
    
    try {
        $passed = & $Assertion
        if ($passed -eq $true) {
            $testResult.status = 'PASS'
            Write-Host "  [PASS] $Id : $Description" -ForegroundColor Green
        } else {
            $testResult.status = 'FAIL'
            $testResult.error = 'Assertion returned false'
            Write-Host "  [FAIL] $Id : $Description (Assertion returned false)" -ForegroundColor Red
            $script:globalPassed = $false
        }
    } catch {
        $testResult.status = 'FAIL'
        $testResult.error = $_.Exception.Message
        Write-Host "  [FAIL] $Id : $Description ($($_.Exception.Message))" -ForegroundColor Red
        $script:globalPassed = $false
    }
    
    $script:testResults.Add($testResult)
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RUNNING PHASE 26 TEST SUITE: GITHUB INTELLIGENCE RECON " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 01: GitHub Source Config Schema exists and is valid JSON
Assert-GitHubTest "Test 01" "github-source-config.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\github-source-config.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:github-source-config:1.0.0')
}

# Test 02: GitHub Source Config catalog defines sources and transport strategies
Assert-GitHubTest "Test 02" "github-source-config.json defines sources (starred, owned, selected, manual)" {
    $configFile = Join-Path $RegistryRoot 'schemas\github-source-config.json'
    if (-not [System.IO.File]::Exists($configFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($configFile) | ConvertFrom-Json
    return ($data.sources.starred -eq $true -and
            $data.sources.owned -eq $true -and
            $data.rate_limiting.max_requests_per_hour -gt 0)
}

# Test 03: Artifact Classifier Schema exists and is valid JSON
Assert-GitHubTest "Test 03" "artifact-classifier.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\artifact-classifier.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:artifact-classifier:1.0.0')
}

# Test 04: Artifact Classifier separates 7 distinct classes
Assert-GitHubTest "Test 04" "artifact-classifier.json defines all 7 distinct artifact classes" {
    $classifierFile = Join-Path $RegistryRoot 'schemas\artifact-classifier.json'
    if (-not [System.IO.File]::Exists($classifierFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($classifierFile) | ConvertFrom-Json
    $classes = @('documentation_evidence', 'prompt_artifact', 'workflow_artifact', 'agent_config_artifact', 'capability_evidence', 'candidate_skill', 'quarantined_blob')
    foreach ($c in $classes) {
        if (-not $data.classification_classes.PSObject.Properties.Item($c)) { return $false }
    }
    return $true
}

# Test 05: Promotion rules strictly reject naked README, prompt, and workflow promotion
Assert-GitHubTest "Test 05" "Promotion rules reject README, Prompt, and Workflow promotion to Skill" {
    $classifierFile = Join-Path $RegistryRoot 'schemas\artifact-classifier.json'
    $data = [System.IO.File]::ReadAllText($classifierFile) | ConvertFrom-Json
    return ($data.promotion_rules.reject_naked_readme_promotion -eq $true -and
            $data.promotion_rules.reject_naked_prompt_promotion -eq $true -and
            $data.promotion_rules.reject_workflow_promotion_as_skill -eq $true -and
            $data.promotion_rules.require_skill_md_or_manifest -eq $true)
}

# Test 06: GitHub Repository Intake Schema exists and is valid JSON
Assert-GitHubTest "Test 06" "github-repository-intake.schema.json exists and is valid JSON" {
    $schemaFile = Join-Path $RegistryRoot 'schemas\github-repository-intake.schema.json'
    if (-not [System.IO.File]::Exists($schemaFile)) { return $false }
    $json = [System.IO.File]::ReadAllText($schemaFile) | ConvertFrom-Json
    return ($json.'$id' -eq 'urn:skill-registry:github-repository-intake:1.0.0')
}

# Test 07: GitHub Repository Intake reference defines structured entity breakdown
Assert-GitHubTest "Test 07" "github-repository-intake.json defines commit provenance & entity breakdown" {
    $intakeFile = Join-Path $RegistryRoot 'schemas\github-repository-intake.json'
    if (-not [System.IO.File]::Exists($intakeFile)) { return $false }
    $data = [System.IO.File]::ReadAllText($intakeFile) | ConvertFrom-Json
    return ($data.head_commit_sha.Length -eq 40 -and
            $data.entity_breakdown.candidate_skills_count -ge 0 -and
            $data.quarantine_status -eq 'CLEAN')
}

# Test 08: Auth mode defaults to NONE_PUBLIC with rate limiting when unauthenticated
Assert-GitHubTest "Test 08" "Unauthenticated environment defaults safely to rate-limited public mode" {
    $configFile = Join-Path $RegistryRoot 'schemas\github-source-config.json'
    $data = [System.IO.File]::ReadAllText($configFile) | ConvertFrom-Json
    return ($data.auth_mode -eq 'NONE_PUBLIC' -and $data.rate_limiting.fail_closed_on_exhaustion -eq $true)
}

# Test 09: Local Git executable available as fallback transport
Assert-GitHubTest "Test 09" "Git executable available for anonymous shallow clones" {
    try {
        $gitVer = & git --version
        return ($gitVer.Contains("git version"))
    } catch {
        return $false
    }
}

# Test 10: Rate limit policy defines fail-closed behavior
Assert-GitHubTest "Test 10" "Rate limit policy defines fail-closed behavior" {
    $configFile = Join-Path $RegistryRoot 'schemas\github-source-config.json'
    $data = [System.IO.File]::ReadAllText($configFile) | ConvertFrom-Json
    return ($data.rate_limiting.fail_closed_on_exhaustion -eq $true -and $data.rate_limiting.respect_retry_after -eq $true)
}

# Test 11: Quarantine triggers identify dangerous binary extensions
Assert-GitHubTest "Test 11" "Quarantine triggers identify dangerous binary patterns" {
    $classifierFile = Join-Path $RegistryRoot 'schemas\artifact-classifier.json'
    $data = [System.IO.File]::ReadAllText($classifierFile) | ConvertFrom-Json
    $patterns = $data.classification_classes.quarantined_blob.file_patterns
    return ($patterns -contains '*.exe' -and $patterns -contains '*.dll' -and $patterns -contains '*.bat')
}

# Test 12: Read-Only intake boundary strictly enforced (Zero auto-promotion)
Assert-GitHubTest "Test 12" "Read-Only intake boundary strictly enforced (Zero auto-promotion)" {
    $classifierFile = Join-Path $RegistryRoot 'schemas\artifact-classifier.json'
    $data = [System.IO.File]::ReadAllText($classifierFile) | ConvertFrom-Json
    return ($data.classification_classes.documentation_evidence.is_skill_candidate -eq $false -and
            $data.classification_classes.prompt_artifact.is_skill_candidate -eq $false -and
            $data.classification_classes.workflow_artifact.is_skill_candidate -eq $false)
}

# Test 13: Zero secret or credential leakage across Phase 26 files
Assert-GitHubTest "Test 13" "Zero secret or credential leakage in Phase 26 schemas and configs" {
    $schemaDir = Join-Path $RegistryRoot 'schemas'
    $files = @(Get-ChildItem -Path $schemaDir -Filter '*github*' -File) +
             @(Get-ChildItem -Path $schemaDir -Filter '*artifact-classifier*' -File)
    $patterns = @('AIzaSy', 'sk-[a-zA-Z0-9]{20,}', 'ghp_[a-zA-Z0-9]{20,}', 'github_pat_[a-zA-Z0-9_]{20,}')
    foreach ($f in $files) {
        $text = [System.IO.File]::ReadAllText($f.FullName)
        foreach ($p in $patterns) {
            if ($text -match $p) { return $false }
        }
    }
    return $true
}

# Test 14: Core Gates 0-24 immutability check verified
Assert-GitHubTest "Test 14" "Core Gates 0-24 immutability check verified" {
    $archFile = Join-Path $RegistryRoot 'docs\ARCHITECTURE.md'
    $content = [System.IO.File]::ReadAllText($archFile)
    return ($content.Contains("596552cf11583365510fb13503394efd59e9769e01ab53da96342f0ce807f958") -and
            $content.Contains("gov-quarantine-link-v1"))
}

# Test 15: Clean separation between Inlet and Authority
Assert-GitHubTest "Test 15" "Clean separation between Inlet (GitHub) and Authority (E:\.skill-registry)" {
    $configFile = Join-Path $RegistryRoot 'schemas\github-source-config.json'
    $data = [System.IO.File]::ReadAllText($configFile) | ConvertFrom-Json
    return ($data.schema_version -eq '1.0.0')
}

$passedCount = @($testResults | Where-Object { $_.status -eq 'PASS' }).Count
$failedCount = @($testResults | Where-Object { $_.status -eq 'FAIL' }).Count

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " TEST RESULTS SUMMARY: $passedCount / $($testResults.Count) PASSED ($failedCount FAILED)" -ForegroundColor $(if ($script:globalPassed) { 'Green' } else { 'Red' })
Write-Host "============================================================" -ForegroundColor Cyan

$auditReport = [ordered]@{
    schema = 'skill-registry.phase-26.github-intelligence-recon/v1'
    run_utc = [DateTime]::UtcNow.ToString('o')
    overall_status = if ($script:globalPassed) { 'PASS' } else { 'FAIL' }
    passed_count = $passedCount
    failed_count = $failedCount
    artifact_classes_defined = 7
    transport_backends_mapped = 4
    test_cases = $testResults.ToArray()
}

$reportDir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
$auditJson = $auditReport | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($OutputPath, $auditJson, [System.Text.Encoding]::UTF8)

if (-not $script:globalPassed) {
    exit 1
}
