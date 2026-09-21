# SECURITY_AUDIT — PROTOCOLO SEGURANÇA v13.2 / Intermediário

- Protocolo: **13.2.0 já existia na main antes desta auditoria**
- Nível alvo: **INTERMEDIÁRIO — PRODUCTION DEFENSIBLE**
- Issue: #55
- Branch: `security/55-protocol-v13-2-intermediate`
- Baseline: `0dc49677ff2136b9b02cce2e29ebaccf4d5699e0`
- Snapshot de código validado diretamente: `b2c5dbff0f01179f3ac2df5334dbb1cf4e893cec`
- Estado global: **INTERMEDIATE_PENDING_DIRECT_VALIDATION**
- Autoridade de evidência: `evidence/current.json` + gates diretos; GitHub Actions não substitui validação direta.

## Correção do estado histórico

`governance/sovereign-security-protocol-v13.json` já está em `version: 13.2.0` e `ACTIVE_SEALED`.
Portanto, o problema não era ausência do protocolo no JARVIS. O bloqueio é execução/evidência: `evidence/current.json` permanece `INCOMPLETE` e vários gates estão `DIRECT_VALIDATION_REQUIRED`.

## Findings

### JAR-SEC-001 — HIGH / P1 — FIXED_IN_BRANCH / SUPPLEMENTARY_CI_PASS

`N8nAdapter`:
- tinha segredo HMAC default conhecido;
- aceitava trigger sem assinatura;
- assinava apenas o payload, sem vincular envelope;
- não exigia timestamp/nonce nem impedia replay.

Correção:
- segredo explícito `JARVIS_N8N_WEBHOOK_SECRET`, mínimo 16 caracteres e diferente do legado;
- assinatura obrigatória;
- HMAC cobre event type, mission id, timestamp, nonce e payload;
- janela de freshness;
- nonce one-time em replay cache;
- testes para unsigned, tamper, stale e replay.

### JAR-SEC-002 — HIGH / P1 — FIXED_IN_BRANCH / SUPPLEMENTARY_CI_PASS

`FederationRouter` tratava SHA-256 sem chave como `signature_sha256`, enquanto o trust tier era apenas uma declaração.

Correção:
- nó remoto não pode ser registrado sem `JARVIS_FEDERATION_EXCHANGE_SECRET` explícito >= 32 caracteres;
- envelope usa HMAC-SHA256;
- exchange id não reutilizável;
- verificação inclui freshness e replay;
- tamper/replay têm testes negativos;
- trust tier desconhecido é rejeitado no parse;
- `UNTRUSTED_EXTERNAL` nunca é candidato a offload;
- o campo enganoso `signature_sha256` deixa de ser usado nesse caminho e vira `signature_hmac_sha256`.

## Evidência suplementar fresca do snapshot atual

No SHA `e19ac72877bcfa5f582f9fb3db490f2ddb46a8b5`:

- SSP-v13 Audit run **#601**: PASS;
- JARVIS Validation run **#602**: PASS;
- Portable Runtime Windows: PASS;
- Portable Runtime Ubuntu/Linux: PASS;
- Portable Runtime macOS: PASS;
- Legacy Registry Governance Windows: PASS;
- isolated runtime/UI regression: PASS;
- pre-publish security audit: PASS;
- repository hygiene/secret sanitization scan: PASS.

Esses resultados corrigem o antigo estado `TEST_PENDING` dos hardenings n8n/federation e provam que o branch não regrediu na matriz CI. Porém `evidence/current.json` define explicitamente `github_actions_authority: false`; portanto esses runs são **evidência suplementar**, não substituem os gates diretos.

## Evidência direta — Linux / Chromium

Runner isolado Render: `tcc-ds-backend-final-gate`, deploy `dep-dao8lqek1f9s73b3o2pg`, runner `7fe39912cfa9c0b5efef8446a27f1e634d2edc88`.

O runner clonou e fixou explicitamente o SHA `b2c5dbff0f01179f3ac2df5334dbb1cf4e893cec`; o build só prosseguiu após confirmar `git rev-parse HEAD` igual ao SHA esperado.

Gates diretos executados fora do GitHub Actions:

- `contracts` — **PASS / linux**;
- `integration` — **PASS / linux**;
- `recovery` — **PASS / linux**;
- `benchmarks-claims` — **PASS / linux**;
- `portable-runtime` — **PASS / linux**;
- `browser-ui` — **PASS / linux / Chromium**;
- `tests.test_agentic_n8n` + `tests.test_agentic_federation` — PASS;
- `python jarvis.py --full-test` — **95 suites / 596 testes / 596 PASS / 0 failed / 0 errors**;
- `tooling/audit_pre_publish_security.py` — exit 0, protocolo v13.2 homologado com 14/14 invariantes;
- deploy do runner: **live**.

Essa evidência é direta e independente de GitHub Actions. Ela não cobre Windows, macOS nem o gate Legacy Registry Governance de Windows.

### JAR-EVID-001 — HIGH / P1 — OPEN

`evidence/current.json` continua globalmente `INCOMPLETE`. Após a validação direta deste ciclo, permanecem sem evidência direta:
- portable runtime **Windows**;
- portable runtime **macOS**;
- legacy governance **Windows**;
- release evidence completo.

Portable runtime Linux e browser smoke Chromium já têm PASS direto no SHA `b2c5dbff0f01179f3ac2df5334dbb1cf4e893cec`.

Nenhuma evidência histórica é promovida automaticamente para o snapshot atual.

### JAR-STACK-001 — HIGH / P1 — OPEN

PRs ativas:
- #53 — remote PC command runtime, HEAD `ab72eafc58e02ecd9ccbf1187c2def9ff0c40596`;
- #54 — Mark-LIV Holomat cockpit, HEAD `804f42e7c895e328bfc4eb72978822c045d34f33`.

Elas partem da main e **não contêm** as correções deste branch. Antes de merge, precisam incorporar o hardening aplicável e executar evidência fresca no novo HEAD.

### JAR-TRUST-001 — MEDIUM / P2 — OPEN

O audit de trust boundaries ainda lista áreas que não podem ser promovidas só pelas duas correções acima: interseção completa de permissões, secret-reference materialization, integridade/freshness de artifact reuse e authenticated evidence. Requer inspeção/execução adicional.

## 9 domínios

| Domínio | Estado | Evidência / limite |
| --- | --- | --- |
| 1. Governança / Secure SDLC | PARTIAL | v13.2 selado, issue/branch/audit; evidence corrente ainda incomplete. |
| 2. Identity / AuthN / AuthZ / Session / Anti-Abuse | PARTIAL | Policy/grants existem; identidade distribuída e permissões efetivas ainda têm open gates. |
| 3. Web / API / Injection / Business Logic | PARTIAL | n8n endurecido; browser-ui Chromium passou diretamente no SHA validado; remote/stack #53/#54 ainda exigem incorporação e rerun. |
| 4. Data / DB / RLS / Privacy | PARTIAL/N/A | Não é SaaS DB central clássico; vault/state/telemetry continuam exigindo minimização e secret handling. |
| 5. Cloud / Infra / Secrets / Supply Chain | PARTIAL | pre-publish/Merkle/quarantine existem; secret refs e evidence auth ainda incompletos. |
| 6. Reliability / Resilience / Performance / DR | PARTIAL | recovery + portable-runtime Linux passaram diretamente; Windows/macOS diretos ainda pendentes. |
| 7. Logging / Audit / Detection / IR | PARTIAL | ledgers/telemetry existem; autenticidade de evidence e sinks ainda aberta. |
| 8. Testing / Quality / Accessibility | PARTIAL | contracts/integration/benchmarks/browser-ui/portable Linux passaram diretamente; Windows/macOS/Legacy Windows e PRs #53/#54 ainda pendentes. |
| 9. AI / RAG / Agents / MCP | PARTIAL | authorization/policy robustos em partes; n8n/federation corrigidos, demais trust boundaries ainda abertos. |

## Release gates

| Gate | Estado |
| --- | --- |
| Security | **PARTIAL** — dois P1 corrigidos e verdes na matriz CI; gates diretos + demais trust boundaries pendentes |
| Quality | **PARTIAL** — gates diretos Linux/Chromium PASS; cobertura direta Windows/macOS e stack #53/#54 ainda incompleta |
| Reliability | **PARTIAL** — recovery + portable-runtime Linux diretos PASS; Windows/macOS e Legacy Windows diretos pendentes |
| Privacy/Compliance | **PARTIAL** — vault/telemetry/secret materialization ainda requer fechamento |

## Validação obrigatória antes de fechar Intermediário

```bash
python jarvis.py --doctor
python jarvis.py --full-test
python jarvis.py --test
python -m unittest tests.test_agentic_n8n tests.test_agentic_federation
python tooling/validate_v020_plan4.py --gate portable-runtime
python tooling/validate_v020_plan4.py --gate legacy-governance
npm run test:browser
```

Executar os gates de plataforma exigidos pelo repositório e registrar SHA, ambiente, artefato e timestamp.

Depois:
1. atualizar `evidence/current.json` apenas com evidência direta;
2. incorporar este hardening em #53/#54 e rerodar;
3. revisar `docs/security/TRUST_BOUNDARIES.md` com evidência do código atual;
4. manter UNKNOWN onde identidade/secret/evidence não tiver prova.

**Não está autorizado declarar Intermediário PASS neste snapshot enquanto `evidence/current.json` permanecer incompleto.**
