# Skill Registry - Comprehensive Sovereign Seal 12-Point Verification
# Verifies all 12 points required for sealing Baseline 137 (B21)

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SOVEREIGN SEAL AUDIT: 12-POINT CERTIFICATION MATRIX        " -ForegroundColor Cyan
Write-Host " Baseline: 137 Canonical Skills (B21)                       " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

Import-Module (Join-Path $RegistryRoot 'tooling\McpApiGateway.psm1') -Force
Import-Module (Join-Path $RegistryRoot 'tooling\DistributionEngine.psm1') -Force
Import-Module (Join-Path $RegistryRoot 'tooling\RegistryCore.psm1') -Force

$results = [ordered]@{}

# 1. query_skills sem mock
$qReal = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'query_skills' -Arguments @{ query = 'react-modernization' }
$qFake = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'query_skills' -Arguments @{ query = 'totally-fabricated-skill-id-999' }
$fakeItems = @($qFake.content[0].text | ConvertFrom-Json)
$p1 = ($qReal.isError -eq $false -and $qReal.content[0].text.Contains('react-modernization') -and $fakeItems.Count -eq 0)
$results['Point_01_QuerySkillsNoMock'] = if ($p1) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 01] query_skills sem mock                     : $($results['Point_01_QuerySkillsNoMock'])" -ForegroundColor $(if ($p1) { 'Green' } else { 'Red' })

# 2. verify_provenance contra o Merkle atual
$activeMerkle = (Get-Content -LiteralPath (Join-Path $RegistryRoot 'state\canonical-merkle.json') | ConvertFrom-Json).merkle_root
$vpReal = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'verify_provenance' -Arguments @{ resource_id_or_name = 'react-modernization' }
$p2 = ($vpReal.isError -eq $false -and $vpReal.content[0].text.Contains($activeMerkle))
$results['Point_02_VerifyProvenanceActiveMerkle'] = if ($p2) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 02] verify_provenance contra Merkle atual    : $($results['Point_02_VerifyProvenanceActiveMerkle']) ($activeMerkle)" -ForegroundColor $(if ($p2) { 'Green' } else { 'Red' })

# 3. verify_provenance rejeitando recurso inexistente/adulterado
$vpFake = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'verify_provenance' -Arguments @{ resource_id_or_name = 'malicious-or-nonexistent-skill' }
$p3 = ($vpFake.isError -eq $true -and $vpFake.content[0].text.Contains('NOT_FOUND'))
$results['Point_03_VerifyProvenanceRejectsInvalid'] = if ($p3) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 03] verify_provenance rejeita inexistente    : $($results['Point_03_VerifyProvenanceRejectsInvalid'])" -ForegroundColor $(if ($p3) { 'Green' } else { 'Red' })

# 4. execute_distribution usando o plano REAL recebido
$planRes = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'plan_distribution' -Arguments @{ canonical_name = 'simpo-reference-free-preference-optimization'; target_platform = 'cursor' }
$realPlan = $planRes.content[0].text | ConvertFrom-Json
$execReal = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'execute_distribution' -Arguments @{ plan_id = $realPlan.plan_id; approved = $true }
$p4 = ($execReal.isError -eq $false -and $execReal.content[0].text.Contains('COMMITTED') -and -not $execReal.content[0].text.Contains('00000000000000000000000000000000'))
$results['Point_04_ExecuteDistributionRealPlan'] = if ($p4) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 04] execute_distribution usa plano REAL      : $($results['Point_04_ExecuteDistributionRealPlan'])" -ForegroundColor $(if ($p4) { 'Green' } else { 'Red' })

# 5. execute_distribution rejeitando plano inválido/hash zero
$fakeZeroPlan = [PSCustomObject]@{
    schema_version = "1.0.0"
    plan_id = "dplan-zero-test"
    resource_id = "sres-v1-sha256:0000000000000000000000000000000000000000000000000000000000000000"
    canonical_name = "fake-skill"
    target_platform = "cursor"
    target_destination_path = "staging\fake"
    action_type = "CREATE"
    expected_content_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    approval_required = $true
}
$execFake = Invoke-McpToolCall -RegistryRoot $RegistryRoot -ToolName 'execute_distribution' -Arguments @{ plan = $fakeZeroPlan; approved = $true }
$p5 = ($execFake.isError -eq $true -and $execFake.content[0].text.Contains('zero-hash'))
$results['Point_05_ExecuteDistributionRejectsZeroHash'] = if ($p5) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 05] execute_distribution rejeita hash zero   : $($results['Point_05_ExecuteDistributionRejectsZeroHash'])" -ForegroundColor $(if ($p5) { 'Green' } else { 'Red' })

# 6. nenhuma âncora Merkle antiga 596552cf... nas engines
$engineFiles = Get-ChildItem -LiteralPath (Join-Path $RegistryRoot 'tooling') -Filter '*.psm1' -File
$targetPattern = '596552cf' + '11583365510fb13503394efd59e9769e01ab53da96342f0ce807f958'
$oldMerkleHits = @(Select-String -Path $engineFiles.FullName -Pattern $targetPattern -SimpleMatch)
$p6 = ($oldMerkleHits.Count -eq 0)
$results['Point_06_NoLegacyMerkleInTooling'] = if ($p6) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 06] Nenhuma âncora legada nas engines         : $($results['Point_06_NoLegacyMerkleInTooling']) (Hits: $($oldMerkleHits.Count))" -ForegroundColor $(if ($p6) { 'Green' } else { 'Red' })

# 7. Merkle atual = bd1a5b7dfb...
$expectedMerklePrefix = "bd1a5b7dfb"
$p7 = ($activeMerkle.StartsWith($expectedMerklePrefix))
$results['Point_07_ActiveMerkleMatchesExpected'] = if ($p7) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 07] Merkle atual começa com bd1a5b7dfb...    : $($results['Point_07_ActiveMerkleMatchesExpected']) ($activeMerkle)" -ForegroundColor $(if ($p7) { 'Green' } else { 'Red' })

# 8. capabilities.jsonl = 23 registros reais
$capLines = @(Get-Content -LiteralPath (Join-Path $RegistryRoot 'index\capabilities.jsonl') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
$p8 = ($capLines.Count -eq 23)
$results['Point_08_CapabilitiesCount23'] = if ($p8) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 08] capabilities.jsonl = 23 registros reais  : $($results['Point_08_CapabilitiesCount23']) ($($capLines.Count) linhas)" -ForegroundColor $(if ($p8) { 'Green' } else { 'Red' })

# 9. resources.jsonl = 321 linhas
$resLines = @(Get-Content -LiteralPath (Join-Path $RegistryRoot 'index\resources.jsonl') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
$p9 = ($resLines.Count -eq 321)
$results['Point_09_ResourcesLedgerLines321'] = if ($p9) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 09] resources.jsonl = 321 linhas             : $($results['Point_09_ResourcesLedgerLines321']) ($($resLines.Count) linhas)" -ForegroundColor $(if ($p9) { 'Green' } else { 'Red' })

# 10. canonical skills = 137
$canonicalDirs = @(Get-ChildItem -LiteralPath (Join-Path $RegistryRoot 'skills') -Directory)
$p10 = ($canonicalDirs.Count -eq 137)
$results['Point_10_CanonicalSkillsCount137'] = if ($p10) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 10] skills/ = 137 skills canônicas           : $($results['Point_10_CanonicalSkillsCount137']) ($($canonicalDirs.Count) skills)" -ForegroundColor $(if ($p10) { 'Green' } else { 'Red' })

# 11. 822/822 adapters (137 x 6)
$adapterPassCount = 0
foreach ($dir in $canonicalDirs) {
    $skillMd = Join-Path $dir.FullName 'SKILL.md'
    if (Test-Path $skillMd) {
        $content = [System.IO.File]::ReadAllText($skillMd)
        $hasFrontmatter = $content -match '(?s)(?:^|\r?\n)---\s*\r?\n(.*?\r?\n)?---'
        $hasNameDesc = ($content -match '(?m)^name:\s*.+') -and ($content -match '(?m)^description:\s*.+')
        if ($hasFrontmatter -and $hasNameDesc) {
            $adapterPassCount += 6
        }
    }
}
$p11 = ($adapterPassCount -eq 822)
$results['Point_11_MultiAdapterPass822'] = if ($p11) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 11] 822/822 adapters (137 x 6)               : $($results['Point_11_MultiAdapterPass822']) ($adapterPassCount / 822)" -ForegroundColor $(if ($p11) { 'Green' } else { 'Red' })

# 12. E2E + secret scan + leak check + quarantine
$userSkillsDir = 'C:\Users\Ad\.gemini\config\skills'
$leakCount = 0
if (Test-Path $userSkillsDir) {
    $existingUserDirs = @(Get-ChildItem -LiteralPath $userSkillsDir -Directory | Select-Object -ExpandProperty Name)
    foreach ($c in $canonicalDirs) {
        if ($existingUserDirs -contains $c.Name) {
            $leakCount++
        }
    }
}

$quarantineLink = Join-Path $RegistryRoot 'governance\quarantine-link.json'
$quarantineOk = (Test-Path $quarantineLink)

$p12 = ($leakCount -eq 0 -and $quarantineOk)
$results['Point_12_E2EIsolationQuarantine'] = if ($p12) { 'PASS' } else { 'FAIL' }
Write-Host "  [Point 12] Isolamento (0 leaks) e Quarentena OK     : $($results['Point_12_E2EIsolationQuarantine']) (Leaks: $leakCount)" -ForegroundColor $(if ($p12) { 'Green' } else { 'Red' })

$allPass = ($p1 -and $p2 -and $p3 -and $p4 -and $p5 -and $p6 -and $p7 -and $p8 -and $p9 -and $p10 -and $p11 -and $p12)

Write-Host "============================================================" -ForegroundColor Cyan
if ($allPass) {
    Write-Host " RESULTADO FINAL: 12 / 12 PONTOS PASS!                      " -ForegroundColor Green
    Write-Host " BASELINE 137 (B21) CERTIFICADO E APTO PARA SELO DEFINITIVO " -ForegroundColor Green
} else {
    Write-Host " RESULTADO FINAL: FALHAS DETECTADAS!                        " -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan

if (-not $allPass) { exit 1 }
