# FASE 3 — DISCOVERY: RELATÓRIO DE RECONHECIMENTO READ-ONLY (FASE 3A)

## 1. Identificação do Reconhecimento

- **Data / Hora UTC**: 2026-08-31T02:22:00.0000000Z
- **Escopo**: Reconhecimento Read-Only da arquitetura existente em `E:\.skill-registry` e `E:\.skill-registry-bootstrap`.
- **Status do Reconhecimento**: `PHASE_3_RECON_STATUS=PASS`
- **Próxima Ação**: `NEXT_ACTION=AWAITING_AUTHORIZATION` (Aguardando autorização humana antes de qualquer mutação).

---

## 2. Arquivos e Estado Analisados

| Arquivo / Diretório | Função / Observação |
| --- | --- |
| `E:\.skill-registry\config\registry.json` | Configuração principal (`mode: PERSONAL_LOCAL`, âncoras criptográficas do snapshot `20260812T165347306Z-80e0f888`). |
| `E:\.skill-registry\config\policy.json` | Política de governança fail-closed e precedência estrita de quarentena. |
| `E:\.skill-registry\governance\quarantine-link.json` | Vínculo canônico com a autoridade de quarentena (118 tombstones, 8 subárvores restritas). |
| `E:\.skill-registry\governance\trust-policy.json` | Modelo de 5 níveis de confiança (`BLOCKED` a `TRUSTED`). |
| `E:\.skill-registry\schemas\resource.schema.json` | Schema canônico de recurso já preparado para `lifecycle_state: DISCOVERED`, `trust_level: UNTRUSTED` e `content_hash: null`. |
| `E:\.skill-registry\schemas\provenance.schema.json` | Schema canônico de proveniência imutável (`prov-v1-sha256:...`). |
| `E:\.skill-registry\schemas\source.schema.json` | Schema de fontes com limites (`boundaries`) e estados de lifecycle. |
| `E:\.skill-registry\schemas\source-policy.schema.json` | Permissões granulares de fontes (`discovery_allowed`, `metadata_read_allowed`, etc.). |
| `E:\.skill-registry\tooling\RegistryCore.psm1` | Motor central com transações ACID, locks atômicos, guarda de quarentena e gerenciador de sources. |
| `E:\.skill-registry\tooling\skillctl.ps1` | CLI operacional suportando domínios `registry` e `source`. |
| `E:\.skill-registry\index\sources.jsonl` | Índice append-only com 3 sources sintéticas registradas na Fase 2. |
| `E:\.skill-registry\index\resources.jsonl` | Índice inicial de recursos (atualmente com 0 recursos indexados). |

---

## 3. Arquitetura Encontrada e Pontos de Integração

1. **Separação Rígida de Entidades**:
   - `Source`: Origem cadastrada e governada por limites e políticas.
   - `Discovery`: Processo transitório e não invasivo de descoberta de candidatos a partir de uma Source elegível.
   - `Resource`: Entidade lógica no índice (`sres-v1-sha256:...`) com estado inicial `DISCOVERED` e confiança `UNTRUSTED`.
   - `Provenance`: Registro determinístico da linhagem (`prov-v1-sha256:...`).
   - `Payload / Content`: Conteúdo físico em disco, que **NÃO é copiado, hasheado ou executado na Fase 3**.

2. **Precedência Absoluta de Quarentena**:
   - A função `Test-RegistryQuarantineGuard` em `RegistryCore.psm1` avalia deterministicamente qualquer caminho antes do registro. Se houver sobreposição com os 118 tombstones ou 8 subárvores restritas, a decisão é `FAIL-CLOSED` (`QUARANTINED` / `BLOCKED`).

3. **Mecanismo Transacional**:
   - O `Invoke-RegistryTransaction` garante que cada sessão de Discovery registre seus recursos de forma atômica no índice `index/resources.jsonl`, grave o log de auditoria em `audit/events.jsonl` e realize rollback limpo em caso de anomalia.

---

## 4. Gaps Identificados

1. **Schema de Sessão/Manifesto de Discovery**:
   - Falta um schema específico para registrar execuções de descoberta (`discovery-session.schema.json`), gravando `discovery_id`, `source_id`, status, candidatos encontrados, violações de quarentena bloqueadas e transação associada.
2. **Motor de Descoberta Estática em `RegistryCore.psm1`**:
   - Necessidade de implementar `Invoke-RegistrySourceDiscovery` e `Get-RegistryDiscoveryStatus` com parsing estático de metadados estruturais (ex: extração pura de YAML frontmatter sem execução de código) e validação estrita de boundaries.
3. **Comandos de Discovery no `skillctl`**:
   - Necessidade de adicionar o domínio `discovery` no CLI: `skillctl discovery status`, `list`, `inspect`, `validate`, `doctor`.

---

## 5. Riscos e Mitigações

| Risco | Impacto | Mitigação Arquitetural |
| --- | --- | --- |
| Leitura ou hashing acidental de arquivos sob quarentena durante a varredura | Crítico | Verificação obrigatória contra `Test-RegistryQuarantineGuard` *antes* de qualquer inspeção de arquivo. Se bloqueado, zero I/O no payload. |
| Execução acidental de código contido em skills (PowerShell, Python, scripts) | Crítico | A descoberta é estritamente baseada em parsing de texto e expressões regulares nos metadados declarados (`SKILL.md`). Nenhuma invocação de runtime é permitida. |
| Atribuição inadequada de confiança aos recursos descobertos | Alto | Todo recurso descoberto recebe compulsoriamente `trust_level: UNTRUSTED` e `lifecycle_state: DISCOVERED`. |
| Duplicação de recursos por variações de maiúsculas/minúsculas ou caminhos relativos | Médio | Geração de `resource_id` e `provenance_id` determinística com normalização lexical estrita e ordenação ordinal (`StringComparer.Ordinal`). |
| Escape de fronteira através de junctions / symlinks | Médio | Política `allow_reparse_points: false` padrão com validação estrita de contenção de caminho. |

---

## 6. Proposta de Implementação (Para Fases Subsequentes)

### 6.1 Arquivos a Criar

1. `E:\.skill-registry\schemas\discovery-session.schema.json`: Schema Draft 2020-12 para histórico e auditoria de sessões de descoberta.
2. `E:\.skill-registry\index\discoveries.jsonl`: Índice append-only de sessões de descoberta.
3. `E:\.skill-registry\tests\fixtures\discovery-fixtures.json`: Fixtures sintéticos e estruturas isoladas de teste.
4. `E:\.skill-registry\tests\Invoke-DiscoveryTests.ps1`: Suíte com no mínimo 29 cenários sintéticos.
5. `E:\.skill-registry\reports\phase-3-discovery.md` e `phase-3-discovery.json`: Relatórios formais de conclusão.

### 6.2 Arquivos a Modificar

1. `E:\.skill-registry\tooling\RegistryCore.psm1`:
   - Adicionar `Invoke-RegistrySourceDiscovery`, `Get-RegistryDiscoveredResources`, `Get-RegistryDiscoverySessions`.
2. `E:\.skill-registry\tooling\skillctl.ps1`:
   - Adicionar o domínio `discovery`: `status`, `list`, `inspect`, `validate`, `doctor`.
3. `E:\.skill-registry\state\current-state.json`:
   - Atualizar contadores de recursos descobertos.

---

## 7. Critérios de Aprovação do Gate 3

1. **Schemas Válidos**: `discovery-session.schema.json` e todos os schemas do Registry validados em 100%.
2. **Determinismo e Decoupling**: Recursos descobertos geram `resource_id` e `provenance_id` determinísticos, com `trust_level = UNTRUSTED` e `content_hash = null`.
3. **Precedência de Quarentena Comprovada**: Bloqueio total de qualquer tentativa de descoberta sobre os 118 tombstones ou 8 subárvores restritas.
4. **Zero Execução e Zero Cópia**: Nenhuma skill é executada, importada ou copiada.
5. **Transacionalidade e Auditoria**: Toda sessão de descoberta gera transação em `journal.jsonl` e eventos em `events.jsonl`.
6. **Suíte de Testes 100% PASS**: Mínimo de 29 testes sintéticos aprovados em PowerShell 5.1 e 7.x.
7. **Nenhum Acesso a `E:\.gemini`**: Zero varredura real não autorizada.

---

```text
PHASE_3_RECON_STATUS=PASS
NEXT_ACTION=AWAITING_AUTHORIZATION

```
