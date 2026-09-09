# Relatório de Reconhecimento Técnico — FASE 4: STRUCTURAL ANALYSIS

---

## 1. Estado Atual do Registry e Baseline Canônico

A partir da conclusão formal e selagem das Fases 0, 1, 2 e 3, o **Skill Registry** (`E:\.skill-registry`) encontra-se no seguinte estado canônico:

```text
PHASE_0_STATUS=PASS (Gate 0 PASS)
PHASE_1_STATUS=PASS (Gate 1 PASS — 12 Schemas, RegistryCore.psm1, skillctl.ps1)
PHASE_2_STATUS=PASS (Gate 2 PASS — 4 Schemas de Source, sources.jsonl)
PHASE_3_STATUS=PASS (Gate 3 PASS — discovery-session.schema.json, discoveries.jsonl, resources.jsonl, 29/29 PASS)
PHASE_4_STATUS=READY_FOR_RECON
CURRENT_GATE=GATE_4_STRUCTURAL_ANALYSIS (PENDING)

```

- **Total de Schemas Ativos**: 17 Schemas Draft 2020-12 (`additionalProperties: false`).
- **Índices Operacionais Ativos**: `index/sources.jsonl`, `index/resources.jsonl`, `index/discoveries.jsonl`.
- **Governança & Quarentena**: `governance/quarantine-link.json` vinculado ao snapshot `20260812T165347306Z-80e0f888` (118 tombstones, 8 subárvores bloqueadas, 3 arquivos permanentemente bloqueados). Precedência absoluta *fail-closed*.
- **Integridade Transacional**: Lock atômico (`state/locks/registry.lock`), journal (`transactions/journal.jsonl`) e auditoria imutável (`audit/events.jsonl`).

---

## 2. Arquitetura Existente Relevante & Interfaces Reutilizáveis

1. **`Test-RegistryQuarantineGuard`** ([RegistryCore.psm1](file:///E:/.skill-registry/tooling/RegistryCore.psm1)):
   - Valida compulsoriamente caminhos físicos antes de qualquer I/O.
   - Reutilizável em nível de diretório e de arquivo individual dentro da árvore estrutural da skill.
2. **`Invoke-RegistryTransaction`**:
   - Mecanismo ACID com lock exclusivo, rollback em caso de falha e diário de transação.
   - Reutilizável para serializar a gravação de relatórios estruturais e transições de estado de recursos.
3. **`Write-RegistryAuditEvent`**:
   - Emissão de eventos imutáveis em `audit/events.jsonl` com tipo de evento, ação, recurso alvo e ID da transação.
4. **`Get-RegistryDiscoveredResources` / `Get-RegistrySource`**:
   - Interfaces para recuperar recursos no estado `DISCOVERED` elegíveis para análise estrutural.
5. **`resource.schema.json` & `lifecycle.schema.json`**:
   - Modelos formais já existentes que preveem o estado `CANDIDATE` e a manutenção de `trust_level: UNTRUSTED`.

---

## 3. Auditoria Crítica da Implementação Existente (Gaps & Inconsistências)

Após auditoria rigorosa de código e schemas, foram identificados os seguintes pontos de atenção:

1. **Ausência de Schema Dedicado de Análise Estrutural**:
   - O Registry possui 17 schemas, mas nenhum define formalmente o payload de um laudo de análise estrutural (`structural-analysis.schema.json`).
2. **Fronteira Indefinida de Hashing no Resource**:
   - `resource.schema.json` define `content_identity` com `content_hash: null`. A Análise Estrutural NÃO deve hashear os payloads de arquivos de script antes de fases posteriores de verificação estática e empacotamento, prevenindo riscos de leitura não autorizada de artefatos sob suspeita.
3. **Falta de Máquina de Transição Formal para Resources**:
   - Existe `Set-RegistrySourceState`, mas não existe ainda `Set-RegistryResourceState` em `RegistryCore.psm1` para gerenciar formalmente as transições `DISCOVERED` $\rightarrow$ `CANDIDATE` ou `DISCOVERED` $\rightarrow$ `BLOCKED`.
4. **Necessidade de Detecção Estática de Extensões Perigosas**:
   - Skills podem conter binários compilados (`.exe`, `.dll`, `.so`) ou scripts de automação (`.bat`, `.cmd`, `.vbs`, `.ps1`). A Análise Estrutural deve catalogar e sinalizar essas extensões sem nunca executá-las.

---

## 4. Definição Formal de STRUCTURAL ANALYSIS no Registry

### 4.1 O que É Structural Analysis

A **Structural Analysis (Análise Estrutural)** é a inspeção estática, determinística, não executável e orientada a metadados da árvore de arquivos e diretórios que compõem uma skill descoberta. Ela analisa:

- A hierarquia física de diretórios (`scripts/`, `references/`, `schemas/`, `examples/`, `docs/`).
- O inventário completo de arquivos (caminhos relativos, extensões, tamanhos em bytes, contagem).
- A conformidade do manifesto principal (`SKILL.md`) com a especificação canônica de frontmatter.
- A presença e integridade sintática de arquivos declarativos (`manifest.json`, `package.json`, `requirements.txt`).
- A identificação de pontos de entrada declarados (*entrypoints*).
- O mapeamento de extensões potencialmente perigosas sem executar nenhuma instrução.

### 4.2 O que NÃO É Structural Analysis

- **NÃO é Execução**: Nenhum script (`.ps1`, `.py`, `.js`, `.sh`, `.bat`) é executado ou interpretado.
- **NÃO é Importação de Módulos**: Nenhum runtime é carregado (`Import-Module`, `import`, `require` proibidos).
- **NÃO é Static Security Scan Profundo**: Não faz parsing semântico de código malicioso (escopo da Fase 10).
- **NÃO é Hashing de Payload Protegido**: Não calcula hash criptográfico de arquivos restritos.
- **NÃO é Elevação de Confiança**: O recurso permanece `UNTRUSTED`.

---

## 5. Matriz de Separação de Fronteiras

| Dimensão / Fase | Alvo Primário | I/O Permitido | Execução | Alteração de Confiança |
|---|---|---|---|---|
| **Discovery (Fase 3)** | Locator da Source | Leitura estática de `SKILL.md` | Proibida | Nenhuma (`UNTRUSTED`) |
| **Structural Analysis (Fase 4)** | Diretório da Skill | Leitura de estrutura de diretório, tamanhos, sintaxe de manifestos | Proibida | Nenhuma (`UNTRUSTED` ou `BLOCKED`) |
| **Static Scan (Fase 10/11)** | Conteúdo textual / AST | Regex/AST sobre texto de scripts | Proibida | Permite sinalização de risco |
| **Trust Evaluation (Fase 12)** | Evidências consolidadas | Avaliação de governança e proveniência | Proibida | Transição formal (`PROVISIONAL`, `REVIEWED`, `TRUSTED`) |
| **Execution (Fase 18+)** | Sandboxed Worker | Execução controlada via adapter | Permitida em sandbox | Depende de autorização prévia |

---

## 6. Informações Obtidas com Segurança (Sem Executar Código)

1. **Topologia Física**:
   - `layout_type`: `SINGLE_FILE` (somente `SKILL.md`), `STANDARD_SKILL_DIR` (`SKILL.md` + subpastas), `EXTENDED_PACKAGE`.
   - `total_files`, `total_directories`, `total_bytes`.
   - Árvore completa de arquivos relativos normalizados com ordenação ordinal.
2. **Classificação de Arquivos**:
   - Arquivos documentais (`.md`, `.txt`, `.rst`).
   - Arquivos declarativos/estruturados (`.json`, `.yaml`, `.yml`, `.toml`).
   - Scripts/código-fonte (`.ps1`, `.py`, `.js`, `.ts`, `.sh`, `.bat`).
   - Arquivos binários/executáveis (`.exe`, `.dll`, `.bin`, `.dat`).
3. **Declarações Extraídas**:
   - Nome canônico, versão semântica, descrição, autor, licença, tags.
   - Lista de capacidades declaradas (`declared_capabilities`).
   - Lista de dependências declaradas (`declared_dependencies`).
   - Entrypoints declarados (ex: `entrypoint: scripts/run.py`).
4. **Sinalizadores de Risco Estrutural**:
   - `contains_executable_binaries: boolean`
   - `contains_unsupported_extensions: boolean`
   - `has_path_traversal_references: boolean`
   - `is_quarantine_adjacent: boolean`

---

## 7. Separação Tridimensional: Declared vs Observed vs Inferred

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        STRUCTURAL EVIDENCE MODEL                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. DECLARED METADATA (O que a skill diz que é)                        │
│    - Nome: "python-refactor"                                          │
│    - Versão: "1.0.0"                                                  │
│    - Capacidades declaradas: [ "code-refactoring", "ast-analysis" ]    │
│    - Entrypoint declarado: "scripts/refactor.py"                      │
├────────────────────────────────────────────────────────────────────────┤
│ 2. OBSERVED STRUCTURE (O que a inspeção estática verificou no disco)   │
│    - Total de arquivos: 3                                              │
│    - Extensões presentes: [ ".md", ".py" ]                            │
│    - Diretórios existentes: [ "scripts" ]                             │
│    - Arquivo de script detectado: "scripts/refactor.py" (1.4 KB)       │
│    - Binários detectados: 0                                           │
├────────────────────────────────────────────────────────────────────────┤
│ 3. INFERRED METADATA (Deduções determinísticas da governança)          │
│    - Packaging Type: "STANDARD_SKILL_DIR"                             │
│    - Primary Runtime: "PYTHON"                                        │
│    - Structural Conformance: "COMPLIANT"                              │
│    - Structural Risk Score: "LOW"                                     │
└────────────────────────────────────────────────────────────────────────┘

```

---

## 8. Fluxo Operacional da Análise Estrutural (Fail-Closed)

```text
Resource (State: DISCOVERED, Trust: UNTRUSTED)
   │
   ▼
[ 1. Validação de Fronteira e Path Lexical ] ──(Inválido)──► STOP: REJECTED
   │ (Válido)
   ▼
[ 2. Consulta ao Test-RegistryQuarantineGuard ] ──(Violação)──► STATE: BLOCKED, TRUST: BLOCKED
   │ (ALLOW)
   ▼
[ 3. Leitor Estrutural Não Executável ]
   │  - Varredura de diretório (Get-ChildItem -File)
   │  - Validação contra reparse points (symlinks/junctions bloqueados)
   │  - Verificação de extensões e tamanhos
   │  - Parser estático de frontmatter / manifests (SKILL.md, JSON)
   │
   ▼
[ 4. Consolidação de Evidência Estrutural ]
   │  - Montagem do payload structural-analysis
   │  - Classificação (Declared / Observed / Inferred)
   │
   ▼
[ 5. Transação Atômica ACID ]
   │  - Gravação em index/structural-analyses.jsonl
   │  - Transição de estado: DISCOVERED ──► CANDIDATE (ou BLOCKED)
   │  - Preservação estrita de trust_level = UNTRUSTED
   │
   ▼
[ 6. Auditoria Imutável ] ──► audit/events.jsonl (STRUCTURAL_ANALYSIS_COMPLETED)

```

---

## 9. Máquina de Estados e Modelo de Confiança na Fase 4

### 9.1 Transições de Lifecycle Permitidas na Fase 4

- `DISCOVERED` $\rightarrow$ `CANDIDATE` (quando a análise estrutural comprova conformidade total).
- `DISCOVERED` $\rightarrow$ `BLOCKED` (quando há violação de quarentena, path traversal ou binário proibido).
- `CANDIDATE` $\rightarrow$ `BLOCKED` (caso detectada anomalia).
- **Proibidas**: Transições para `EVALUATED`, `VERIFIED`, `ELIGIBLE`, `STAGED` ou `ACTIVE`.

### 9.2 Invariante de Confiança (*Trust Isolation*)

- O `trust_level` de qualquer recurso sob análise estrutural **permanece estritamente `UNTRUSTED`** (ou transiciona para `BLOCKED`).
- **É expressamente vedada a elevação automática** para `PROVISIONAL`, `REVIEWED` ou `TRUSTED` na Fase 4.

---

## 10. Estratégia de Determinismo Ordinal e Compatibilidade Multi-Ambiente

1. **Ordenação Ordinal Canônica**:
   - Listas de arquivos, capacidades, extensões e chaves estruturais devem ser ordenadas compulsoriamente via `[System.StringComparer]::Ordinal.Compare()`.
2. **Normalização de Caminhos**:
   - Todos os caminhos relativos na árvore estrutural utilizam `/` como separador canônico.
3. **Invariância Cultural**:
   - Conversões de maiúsculas/minúsculas utilizam `ToLowerInvariant()` e `ToUpperInvariant()`.
   - Testado e validado sob localidades como `tr-TR` (onde `i` $\neq$ `I`), `pt-BR` e `en-US`.
4. **Compatibilidade PS5.1 / PS7.x**:
   - Utilização de construtores padrão .NET (`[ordered]@{}`, `ConvertFrom-Json`, `ConvertTo-Json -Depth 10`).
   - Evitar cmdlets exclusivos de PowerShell 7 ou chamadas nativas de SO não portáveis.

---

## 11. Tratamento de Arquivos Potencialmente Perigosos

- **Binários (`.exe`, `.dll`, `.so`, `.sys`, `.scr`)**: Catalogados por metadados de sistema de arquivos; presença gera sinalizador de alerta ou bloqueio conforme política. Zero carregamento em memória.
- **Scripts Executáveis (`.ps1`, `.bat`, `.cmd`, `.vbs`, `.sh`)**: Tratados como texto estático opaco. Nunca invocados via `&`, `Invoke-Expression`, `Start-Process` ou interpretadores externos.
- **Symlinks / Reparse Points**: Bloqueados por padrão (`allow_reparse_points: false`). Rejeição imediata se houver tentativa de apontamento externo à fronteira da source.

---

## 12. Estrutura de Artefatos Proposta para a Fase 4

### 12.1 Arquivos a Criar

1. `E:\.skill-registry\schemas\structural-analysis.schema.json` (Draft 2020-12, `additionalProperties: false`).
2. `E:\.skill-registry\index\structural-analyses.jsonl` (Índice de laudos de análise estrutural).
3. `E:\.skill-registry\tests\fixtures\mock-sources\structural-pool\` (Fixtures com skills padrão, multi-arquivo, malformadas, com binários e violadoras de quarentena).
4. `E:\.skill-registry\tests\Invoke-StructuralAnalysisTests.ps1` (Suíte de 30 testes sintéticos).
5. `E:\.skill-registry\reports\phase-4-structural-analysis.md` e `phase-4-structural-analysis.json`.

### 12.2 Arquivos a Modificar

1. `E:\.skill-registry\tooling\RegistryCore.psm1`:
   - Adicionar `New-RegistryStructuralAnalysisId`.
   - Adicionar `Invoke-RegistryStructuralAnalysis -ResourceId <id>`.
   - Adicionar `Set-RegistryResourceState -ResourceId <id> -TargetState <state>`.
   - Adicionar `Get-RegistryStructuralAnalyses`.
2. `E:\.skill-registry\tooling\skillctl.ps1`:
   - Adicionar domínio `structure` / `analysis` (`status`, `list`, `inspect`, `validate`, `doctor`).
3. `E:\.skill-registry\state\current-state.json`:
   - Atualizar contadores e fase para `PHASE_4_STRUCTURAL_ANALYSIS`.

---

## 13. Plano de Testes Sintéticos Proposto (30 Cenários)

1. `StructuralAnalysisValidSkillDir`: Análise completa de skill padrão multi-arquivo.
2. `StructuralAnalysisSingleFileSkill`: Análise de skill composta apenas por `SKILL.md`.
3. `StructuralAnalysisIneligibleResource`: Rejeição de análise em recurso que não esteja em `DISCOVERED` ou `CANDIDATE`.
4. `StructuralQuarantinePrecedence`: Bloqueio imediato de recurso com arquivo em quarentena sem I/O.
5. `MissingQuarantineLinkFailClosed`: Falha fechada sob link de quarentena ausente.
6. `StaleQuarantineLinkDetection`: Detecção de link de quarentena divergente do snapshot selado.
7. `DeterministicStructuralAnalysisId`: Identificador determinístico da análise estrutural.
8. `OrdinalFileTreeSorting`: Ordenação ordinal estrita da lista de arquivos analisados.
9. `LocaleIndependenceInStructuralAnalysis`: Invariância sob cultura turca e portuguesa.
10. `DeclaredVsObservedSeparation`: Validação da correta separação entre declarado e observado.
11. `InferredPackagingClassification`: Classificação correta de packaging (SINGLE_FILE vs STANDARD_DIR).
12. `DangerousExtensionDetection`: Detecção e sinalização de scripts e binários executáveis.
13. `BinaryFileZeroExecutionZeroLoad`: Comprovação de que arquivos binários não são lidos como texto nem executados.
14. `ReparsePointBlockedByDefault`: Bloqueio de junctions/symlinks na árvore da skill.
15. `PathTraversalInSkillReferences`: Bloqueio de referências relativas fora do diretório da skill.
16. `FrontmatterSyntaxValidation`: Detecção de erros de sintaxe no frontmatter do `SKILL.md`.
17. `MissingSkillMdDetection`: Sinalização de diretório de skill sem arquivo `SKILL.md`.
18. `LifecycleStateTransitionToCandidate`: Transição formal de `DISCOVERED` para `CANDIDATE`.
19. `LifecycleStateTransitionToBlockedOnViolation`: Transição formal para `BLOCKED` sob violação.
20. `TrustLevelImmutability`: Confirmação de que `trust_level` permanece `UNTRUSTED`.
21. `ContentHashRemainsNull`: Comprovação de que `content_hash` permanece `null` na Fase 4.
22. `TransactionAtomicCommitOnAnalysis`: Confirmação de gravação atômica em `structural-analyses.jsonl`.
23. `TransactionRollbackOnAnalysisFault`: Reversão integral do estado sob falha simulada.
24. `AuditEventEmittedOnStructuralAnalysis`: Registro do evento `STRUCTURAL_ANALYSIS_COMPLETED` em `events.jsonl`.
25. `CorruptedAnalysisIndexDetection`: Detecção de anomalia no índice de análises estruturais.
26. `PS5CompatibilityInTreeParsing`: Execução em PowerShell 5.1 sem erros.
27. `PS7CompatibilityInTreeParsing`: Execução em PowerShell 7.x com ordenação ordinal idêntica.
28. `LongPathSupportInStructuralWalk`: Suporte a caminhos longos (>260 caracteres).
29. `StructuralAnalysisSchemaValidation`: Conformidade do laudo gerado com `structural-analysis.schema.json`.
30. `DoctorVerificationAcrossIndices`: Validação do comando `skillctl` para diagnóstico de integridade.

---

## 14. Critérios Objetivos para Aprovação do Gate 4

1. `structural-analysis.schema.json` e todos os schemas do Registry 100% válidos conforme Draft 2020-12.
2. Análise comprovadamente não invasiva (zero execução, zero importação de módulo, zero hash de arquivos bloqueados).
3. Precedência de quarentena validada antes de qualquer I/O físico na árvore da skill.
4. Isolamento estrito de confiança: nenhum recurso analisado tem seu `trust_level` elevado automaticamente.
5. Separação rigorosa de metadados declarados, observados e inferidos.
6. Transacionalidade ACID e auditoria imutável comprovadas em 100% das operações.
7. Suíte de 30 testes sintéticos com aprovação integral (`30/30 PASS`).
8. Zero varredura ou acesso a `E:\.gemini` ou aos 3 artefatos permanentemente bloqueados.

---

```text
PHASE_4_RECON_STATUS=PASS
NEXT_ACTION=AWAITING_AUTHORIZATION

```
