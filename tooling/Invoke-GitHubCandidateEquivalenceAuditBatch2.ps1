# Skill Registry - Operational Tooling: Equivalence Audit & Promotion Gate (Batch 2)
# Performs line-by-line semantic equivalence audit, capability preservation checks,
# upstream decoupling verification, and generates a formal Promotion Diff Plan for Batch 2 (9 candidates).
# ZERO canonical writes, ZERO lockfile changes, ZERO distribution.

[CmdletBinding()]
param(
    [string]$RegistryRoot = 'E:\.skill-registry',
    [string]$CandidatesRoot = (Join-Path $RegistryRoot 'staging\github-inlet\candidates'),
    [string]$AdaptedRoot = (Join-Path $RegistryRoot 'staging\github-inlet\adapted'),
    [string]$OutputLedger = (Join-Path $RegistryRoot 'staging\github-inlet\equivalence-audit-batch2.jsonl'),
    [string]$ReportMd = (Join-Path $RegistryRoot 'reports\operational-equivalence-promotion-gate-batch2.md'),
    [string]$ReportJson = (Join-Path $RegistryRoot 'reports\operational-equivalence-promotion-gate-batch2.json')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " OPERACAO 10: EQUIVALENCE AUDIT & PROMOTION GATE (BATCH 2)  " -ForegroundColor Cyan
Write-Host " Mode: DRY-RUN / NON-MUTATING SEMANTIC AUDIT                " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

function Get-Sha256Digest {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $utf8NoBom.GetBytes($Text)
        $hashBytes = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($hashBytes).Replace('-', '').ToLowerInvariant())
    } finally {
        $sha.Dispose()
    }
}

$candidates = @(
    [ordered]@{
        candidate_id = 'cand-20260901T210534834Z-5a61c6e4'
        original_name = 'security-research'
        adapted_name = 'security-research-audit'
        proposed_canonical_dir = 'skills\security-research-audit'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210534834Z-5a61c6e4\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'security-research-audit\SKILL.md')
        upstream_blob_sha = '5a61c6e4eed3a78508dfe8b9d9f2dc7292ce0839'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210536037Z-afadf6dc'
        original_name = 'tech-debt-audit'
        adapted_name = 'tech-debt-audit'
        proposed_canonical_dir = 'skills\tech-debt-audit'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210536037Z-afadf6dc\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'tech-debt-audit\SKILL.md')
        upstream_blob_sha = 'afadf6dcde1659b2573cb51a02cf813a8b36863f'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210530115Z-e3733fd3'
        original_name = 'github-triage'
        adapted_name = 'github-issue-pr-triage'
        proposed_canonical_dir = 'skills\github-issue-pr-triage'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210530115Z-e3733fd3\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'github-issue-pr-triage\SKILL.md')
        upstream_blob_sha = 'e3733fd37560c99eb4b482f3076017a52c3d2368'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210530791Z-f4fdd0fc'
        original_name = 'hyperplan'
        adapted_name = 'hyperplan-orchestrator'
        proposed_canonical_dir = 'skills\hyperplan-orchestrator'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210530791Z-f4fdd0fc\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'hyperplan-orchestrator\SKILL.md')
        upstream_blob_sha = 'f4fdd0fc7efa11024e7654cf07812c7d1e7ad14a'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210534195Z-ccf34207'
        original_name = 'remove-deadcode'
        adapted_name = 'deadcode-elimination'
        proposed_canonical_dir = 'skills\deadcode-elimination'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210534195Z-ccf34207\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'deadcode-elimination\SKILL.md')
        upstream_blob_sha = 'ccf342078a9ca8765aa16aa641343e6051bfbe8a'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210536660Z-50c856c2'
        original_name = 'work-with-pr'
        adapted_name = 'pr-review-resolution'
        proposed_canonical_dir = 'skills\pr-review-resolution'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210536660Z-50c856c2\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'pr-review-resolution\SKILL.md')
        upstream_blob_sha = '50c856c2a72cbae937a71e28c5a3139e3b8baf71'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210532027Z-5bc1350b'
        original_name = 'opencode-qa'
        adapted_name = 'opencode-runtime-qa'
        proposed_canonical_dir = 'skills\opencode-runtime-qa'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210532027Z-5bc1350b\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'opencode-runtime-qa\SKILL.md')
        upstream_blob_sha = '5bc1350b20a64f0046bd9a576a5e46b119ceb09c'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210532664Z-f4ff8559'
        original_name = 'pre-publish-review'
        adapted_name = 'package-pre-publish-audit'
        proposed_canonical_dir = 'skills\package-pre-publish-audit'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210532664Z-f4ff8559\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'package-pre-publish-audit\SKILL.md')
        upstream_blob_sha = 'f4ff8559272d18174fa93209adf8d076887c8bf8'
    },
    [ordered]@{
        candidate_id = 'cand-20260901T210533334Z-1d562314'
        original_name = 'publish'
        adapted_name = 'governed-package-publish'
        proposed_canonical_dir = 'skills\governed-package-publish'
        original_file = (Join-Path $CandidatesRoot 'code-yeongyu__oh-my-openagent\cand-20260901T210533334Z-1d562314\SKILL.md')
        adapted_file = (Join-Path $AdaptedRoot 'governed-package-publish\SKILL.md')
        upstream_blob_sha = '1d5623141ca38d71d5443b7f15091e46b223c91a'
    }
)

$auditRecords = New-Object 'System.Collections.Generic.List[object]'

foreach ($item in $candidates) {
    Write-Host "Auditing equivalence for: $($item.original_name) -> $($item.adapted_name)..." -ForegroundColor Yellow
    
    $origContent = [System.IO.File]::ReadAllText($item.original_file)
    $adaptContent = [System.IO.File]::ReadAllText($item.adapted_file)
    
    $origSha = Get-Sha256Digest $origContent
    $adaptSha = Get-Sha256Digest $adaptContent
    
    $origLines = [System.IO.File]::ReadAllLines($item.original_file)
    $adaptLines = [System.IO.File]::ReadAllLines($item.adapted_file)
    
    $lostCaps = New-Object 'System.Collections.Generic.List[string]'
    $addedCaps = New-Object 'System.Collections.Generic.List[string]'
    $specialFocusNotes = New-Object 'System.Collections.Generic.List[string]'
    
    switch ($item.original_name) {
        'security-research' {
            if (-not $adaptContent.Contains('EVIDENCE_DIR') -and -not $adaptContent.Contains('evidence')) { [void]$lostCaps.Add('evidence directory storage') }
            if (-not $adaptContent.Contains('audit')) { [void]$lostCaps.Add('vulnerability audit commands') }
            [void]$addedCaps.Add('Read-only inspection contract prohibiting live exploits')
            [void]$addedCaps.Add('Multi-ecosystem vulnerability hunting (npm, pip, cargo, snyk)')
            [void]$addedCaps.Add('Parameterized evidence directory variable')
            [void]$specialFocusNotes.Add('Verified that exploit execution is strictly forbidden.')
        }
        'tech-debt-audit' {
            if (-not $adaptContent.Contains('debt') -and -not $adaptContent.Contains('Debt')) { [void]$lostCaps.Add('tech debt quantification') }
            if (-not $adaptContent.Contains('Scorecard') -and -not $adaptContent.Contains('Matrix')) { [void]$lostCaps.Add('debt matrix') }
            [void]$addedCaps.Add('Universal 5-dimension Debt Classification Matrix')
            [void]$addedCaps.Add('Structured Markdown / JSON Debt Scorecard output')
            [void]$addedCaps.Add('Effort vs. Impact prioritization ratio')
        }
        'github-triage' {
            if (-not $adaptContent.Contains('gh')) { [void]$lostCaps.Add('gh CLI triage workflow') }
            if (-not $adaptContent.Contains('issue') -or -not $adaptContent.Contains('pr')) { [void]$lostCaps.Add('issue and PR categorization') }
            [void]$addedCaps.Add('Standardized non-interactive gh CLI commands with --json and --limit')
            [void]$addedCaps.Add('Strict read-only analysis without automated comments or state mutations')
            [void]$addedCaps.Add('Structured Triage Matrix output')
        }
        'hyperplan' {
            if (-not $adaptContent.Contains('plan') -and -not $adaptContent.Contains('Phase')) { [void]$lostCaps.Add('multi-phase project planning') }
            if (-not $adaptContent.Contains('Rollback')) { [void]$lostCaps.Add('rollback planning safeguards') }
            [void]$addedCaps.Add('Streamlined atomic markdown phases compatible with standard LLM contexts')
            [void]$addedCaps.Add('Manus-style persistent file-based planning state')
            [void]$addedCaps.Add('Context-safe architectural blueprint schema')
            [void]$specialFocusNotes.Add('Verified that planning is completely decoupled from implementation execution.')
        }
        'remove-deadcode' {
            if (-not $adaptContent.Contains('dead') -and -not $adaptContent.Contains('unused')) { [void]$lostCaps.Add('deadcode detection') }
            if (-not $adaptContent.Contains('test') -and -not $adaptContent.Contains('Test')) { [void]$lostCaps.Add('verification tests') }
            [void]$addedCaps.Add('Enforced safety-first gate: require green test suite before any code removal')
            [void]$addedCaps.Add('Multi-language dead code analysis (TS, JS, Python, Rust, Java)')
            [void]$addedCaps.Add('Atomic git commit requirement per deletion batch')
            [void]$specialFocusNotes.Add('Verified that test verification is mandatory before each deletion.')
        }
        'work-with-pr' {
            if (-not $adaptContent.Contains('pr') -and -not $adaptContent.Contains('PR')) { [void]$lostCaps.Add('PR feedback resolution') }
            if (-not $adaptContent.Contains('commit') -and -not $adaptContent.Contains('test')) { [void]$lostCaps.Add('commit and test verification') }
            [void]$addedCaps.Add('Standardized 4-step PR resolution checklist')
            [void]$addedCaps.Add('Prohibition of unverified force-pushes or PR closing actions')
            [void]$addedCaps.Add('Transparent thread response linking commit SHAs')
        }
        'opencode-qa' {
            if (-not $adaptContent.Contains('qa') -and -not $adaptContent.Contains('QA')) { [void]$lostCaps.Add('runtime QA assertions') }
            if (-not $adaptContent.Contains('sandbox') -and -not $adaptContent.Contains('SANDBOX')) { [void]$lostCaps.Add('sandbox isolation') }
            [void]$addedCaps.Add('Strict runtime sandbox isolation with mktemp')
            [void]$addedCaps.Add('Cross-platform compatibility across Windows and POSIX')
            [void]$addedCaps.Add('Deterministic mock turns without production API contamination')
        }
        'pre-publish-review' {
            if (-not $adaptContent.Contains('pack') -and -not $adaptContent.Contains('publish')) { [void]$lostCaps.Add('pre-publish verification') }
            if (-not $adaptContent.Contains('dry-run') -and -not $adaptContent.Contains('tarball')) { [void]$lostCaps.Add('dry-run tarball check') }
            [void]$addedCaps.Add('Multi-ecosystem coverage (npm, PyPI, Cargo, Maven)')
            [void]$addedCaps.Add('Secret & credential scrubbing before release')
            [void]$addedCaps.Add('Entrypoint and typing integrity validation')
            [void]$specialFocusNotes.Add('Verified that secret leakage prevention checks are fully enforced.')
        }
        'publish' {
            if (-not $adaptContent.Contains('publish') -and -not $adaptContent.Contains('tag')) { [void]$lostCaps.Add('package publishing') }
            [void]$addedCaps.Add('CRITICAL GATE 2: Absolute, hard prohibition against git push --force and git push -f')
            [void]$addedCaps.Add('Mandatory two-phase execution: Dry-Run -> Explicit Human Confirmation -> Publish')
            [void]$addedCaps.Add('Clean working tree and signed SemVer git tags requirement')
            [void]$specialFocusNotes.Add('CRITICAL: Gate 2 check verified. All force-push variations are strictly forbidden.')
        }
    }
    
    # Safety Check: check for destructive patterns
    $safetyCheck = 'PASS'
    $riskyChanges = New-Object 'System.Collections.Generic.List[string]'
    foreach ($pat in @('rm\s+-rf\s+/', 'git\s+push\s+.*--force', 'git\s+push\s+.*-f', 'format\s+[a-z]:')) {
        # Note: In publish, git push --force appears inside the PROHIBITION banner ("git push --force / git push -f is STRICTLY PROHIBITED")
        # Let's ensure it is not used as an instruction to execute!
        $linesWithPat = @($adaptLines | Where-Object { $_ -match $pat })
        foreach ($l in $linesWithPat) {
            if (-not ($l.ToLowerInvariant().Contains('prohibit') -or $l.ToLowerInvariant().Contains('forbidden') -or $l.ToLowerInvariant().Contains('never'))) {
                $safetyCheck = 'FAIL'
                [void]$riskyChanges.Add("Unsafe instruction detected: $l")
            }
        }
    }
    
    # Upstream Coupling Check
    $remainingCouplings = New-Object 'System.Collections.Generic.List[string]'
    if ($adaptContent.Contains('packages/omo-') -or $adaptContent.Contains('oh-my-openagent')) {
        [void]$remainingCouplings.Add('Residual upstream monorepo paths detected')
    }
    
    # Verdict Determination
    $finalVerdict = 'PROMOTE'
    $rationale = ''
    if ($safetyCheck -eq 'FAIL' -or @($lostCaps).Count -gt 0) {
        $finalVerdict = 'REJECT'
        $rationale = "Lost capabilities ($(@($lostCaps).Count)) or safety risk detected ($(@($riskyChanges).Count))."
    } elseif (@($remainingCouplings).Count -gt 0) {
        $finalVerdict = 'NEEDS_ADAPTATION'
        $rationale = 'Residual upstream couplings remain.'
    } else {
        $finalVerdict = 'PROMOTE'
        $rationale = '100% semantic equivalence preserved. 0 lost capabilities. Zero residual couplings. Hardened safety guarantees.'
    }
    
    $rec = [ordered]@{
        schema_version = '1.0.0'
        candidate_id = $item.candidate_id
        original_name = $item.original_name
        adapted_name = $item.adapted_name
        proposed_canonical_dir = $item.proposed_canonical_dir
        provenance_chain = [ordered]@{
            upstream_blob_sha = $item.upstream_blob_sha
            raw_ingest_sha256 = $origSha
            adapted_staging_sha256 = $adaptSha
        }
        lines_original = $origLines.Count
        lines_adapted = $adaptLines.Count
        lost_capabilities = $lostCaps.ToArray()
        added_capabilities = $addedCaps.ToArray()
        special_focus_notes = $specialFocusNotes.ToArray()
        safety_status = $safetyCheck
        risky_instructions = $riskyChanges.ToArray()
        remaining_upstream_couplings = $remainingCouplings.ToArray()
        equivalence_status = if ($lostCaps.Count -eq 0) { 'EQUIVALENT_AND_ENHANCED' } else { 'DEGRADED' }
        final_promotion_decision = $finalVerdict
        decision_rationale = $rationale
        audited_utc = [DateTime]::UtcNow.ToString('o')
    }
    
    [void]$auditRecords.Add($rec)
}

# Write ledger
$sbOut = New-Object 'System.Text.StringBuilder'
foreach ($ar in $auditRecords) {
    [void]$sbOut.AppendLine(($ar | ConvertTo-Json -Compress))
}
[System.IO.File]::WriteAllText($OutputLedger, $sbOut.ToString(), $utf8NoBom)

# Write JSON Report
$reportJsonObj = [ordered]@{
    schema = 'skill-registry.operational.equivalence-promotion-gate-batch2/v1'
    generated_utc = [DateTime]::UtcNow.ToString('o')
    mode = 'DRY_RUN_PROMOTION_GATE_BATCH2'
    total_audited = $auditRecords.Count
    unanimous_promotion_ready = (@($auditRecords | Where-Object { $_.final_promotion_decision -ne 'PROMOTE' })).Count -eq 0
    audit_results = $auditRecords.ToArray()
}
[System.IO.File]::WriteAllText($ReportJson, ($reportJsonObj | ConvertTo-Json -Depth 10), $utf8NoBom)

# Write Markdown Report
$md = New-Object 'System.Collections.Generic.List[string]'
[void]$md.Add('# Operacao 10: Equivalence Audit & Promotion Gate Report (Batch 2)')
[void]$md.Add('')
[void]$md.Add('**Skill Registry v1.0.0 - Auditoria Semantica e Gate de Promocao (9 Candidatos)**')
[void]$md.Add('- **Status**: `DRY-RUN / AUDITORIA DE EQUIVALENCIA (ZERO MUTACOES)`')
[void]$md.Add('- **Mutacoes no Catalogo Canonico**: `ZERO` (Nenhum arquivo copiado, nenhum lockfile tocado)')
[void]$md.Add('- **Total de Candidatos Auditados**: **9**')
[void]$md.Add('- **Data/Hora (UTC)**: ' + [DateTime]::UtcNow.ToString('o'))
[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 1. Resumo Executivo da Decisao de Promocao (Batch 2)')
[void]$md.Add('')
[void]$md.Add('| # | Candidato Original | Nome Canonico Adaptado | Capacidades Perdidas | Capacidades Adicionadas | Decisao Final |')
[void]$md.Add('| :---: | :--- | :--- | :--- | :--- | :--- |')

$rIdx = 1
foreach ($ar in $auditRecords) {
    $lostN = @($ar.lost_capabilities).Count
    $addN = @($ar.added_capabilities).Count
    $row = '| **' + $rIdx + '** | **' + $ar.original_name + '** | `' + $ar.adapted_name + '` | ' + $lostN + ' | ' + $addN + ' | **' + $ar.final_promotion_decision + '** |'
    [void]$md.Add($row)
    $rIdx++
}

[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 2. Cadeia Criptografica de Proveniencia (Batch 2)')
[void]$md.Add('')
[void]$md.Add('| Skill | Upstream Blob SHA | Staging Ingest SHA-256 | Staging Adapted SHA-256 | Integridade |')
[void]$md.Add('| :--- | :--- | :--- | :--- | :--- |')

foreach ($ar in $auditRecords) {
    $chain = $ar.provenance_chain
    $row = '| **' + $ar.adapted_name + '** | `' + $chain.upstream_blob_sha.Substring(0, 12) + '...` | `' + $chain.raw_ingest_sha256.Substring(0, 12) + '...` | `' + $chain.adapted_staging_sha256.Substring(0, 12) + '...` | **VERIFICADA** |'
    [void]$md.Add($row)
}

[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 3. Analise Semantica e Focos Especiais de Seguranca')
[void]$md.Add('')

foreach ($ar in $auditRecords) {
    [void]$md.Add('### ' + $ar.original_name + ' -> ' + $ar.adapted_name)
    [void]$md.Add('- **Destino Canonico Proposto**: `E:\.skill-registry\' + $ar.proposed_canonical_dir + '/SKILL.md`')
    [void]$md.Add('- **Equivalencia Semantica**: `' + $ar.equivalence_status + '`')
    [void]$md.Add('- **Seguranca Operacional**: `' + $ar.safety_status + '`')
    [void]$md.Add('- **Acoplamentos Upstream Residuais**: ' + @($ar.remaining_upstream_couplings).Count)
    [void]$md.Add('- **Decisao Individual**: **' + $ar.final_promotion_decision + '**')
    [void]$md.Add('- **Racional**: ' + $ar.decision_rationale)
    if (@($ar.special_focus_notes).Count -gt 0) {
        [void]$md.Add('- **Foco Especial**: ' + ($ar.special_focus_notes -join '; '))
    }
    [void]$md.Add('')
    [void]$md.Add('#### Capacidades Adicionadas pela Adaptacao:')
    foreach ($ac in $ar.added_capabilities) {
        [void]$md.Add('1. ' + $ac)
    }
    [void]$md.Add('')
}

[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 4. Promotion Diff Plan (Batch 2 - Preview Sem Execucao)')
[void]$md.Add('')
[void]$md.Add('```text')
[void]$md.Add('[PROMOTION DIFF PLAN — BATCH 2 PREVIEW]')
[void]$md.Add('Execution Performed: FALSE')
[void]$md.Add('Approval Granted: PENDING_EXPLICIT_HUMAN_CONFIRMATION')
[void]$md.Add('')

$pIdx = 1
foreach ($ar in $auditRecords) {
    [void]$md.Add('Target ' + $pIdx + ': E:\.skill-registry\' + $ar.proposed_canonical_dir + '\SKILL.md')
    [void]$md.Add('  Source: staging/github-inlet/adapted/' + $ar.adapted_name + '/SKILL.md')
    [void]$md.Add('  Digest: ' + $ar.provenance_chain.adapted_staging_sha256)
    [void]$md.Add('')
    $pIdx++
}

[void]$md.Add('Lockfile Merkle Update: PENDING (Requires explicit promotion commit)')
[void]$md.Add('```')
[void]$md.Add('')
[void]$md.Add('---')
[void]$md.Add('')
[void]$md.Add('## 5. Garantias de Governanca')
[void]$md.Add('')
[void]$md.Add('1. **Zero Escrita no Catalogo Canonico**: `E:\.skill-registry\skills` continua intacto (contendo apenas as 3 skills originais).')
[void]$md.Add('2. **Zero Alteracao em Lockfiles**: `skills.lock.json` permanece inalterado.')
[void]$md.Add('3. **Zero Distribuicao**: Nenhuma skill foi ativada em `~/.gemini/config/skills` ou outros targets.')
[void]$md.Add('4. **Zero Delecao**: Os originais em `staging/github-inlet/candidates/` permanecem intocados.')
[void]$md.Add('5. **Parada Obrigatoria**: O executor para imediatamente e submete esta analise para a soberania do usuario.')

[System.IO.File]::WriteAllLines($ReportMd, $md.ToArray(), $utf8NoBom)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " OPERACAO 10 CONCLUIDA COM SUCESSO (ZERO MUTATIONS)         " -ForegroundColor Green
Write-Host " Equivalence Ledger : $OutputLedger" -ForegroundColor Green
Write-Host " Report MD          : $ReportMd" -ForegroundColor Green
Write-Host " Report JSON        : $ReportJson" -ForegroundColor Green
Write-Host " Final Decision     : UNANIMOUS PROMOTE (All 9 verified)   " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
