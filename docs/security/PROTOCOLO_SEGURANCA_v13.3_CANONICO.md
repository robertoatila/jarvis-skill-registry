🔐 PROTOCOLO SEGURANÇA v13.3

Versão: 13.3.0
Data-base: 24/09/2026
Status: CANÔNICO
Substitui: v7 · v8 · v9 · v10 · v11 · v12 · v13 · v13.1 · v13.2
Modelo: Secure by Design + Production Engineering
Gatilho: "SEGURANÇA"

«Um sistema não está pronto para produção apenas porque compila.

Um controle não existe apenas porque há código relacionado.

PASS exige implementação + evidência + teste + resultado verificável.»

---

0.0 DELTA v13 — MELHORIAS SOBRE A v12

A v13 preserva os 9 domínios e adiciona:

- RELEASE GATE separado em SECURITY + QUALITY + RELIABILITY + PRIVACY/COMPLIANCE;
- evidence freshness vinculada a commit, artefato e ambiente;
- SLSA 1.2 e verificação explícita de provenance;
- priorização de vulnerabilidades com KEV + EPSS + CVSS 4.0 + SSVC/contexto;
- controles de release safety, migrations, filas e feature flags;
- ampliação de AI/RAG/Agents/MCP com referências OWASP 2026;
- proteção explícita contra tool poisoning, rug pull, excessive agency e memory poisoning;
- orçamento e kill switch para loops/agentes;
- authorization per tool e per resource em MCP;
- critérios de blockers para cross-tenant RAG/MCP e artifact provenance mismatch;
- finding format com mapeamento a padrões e contexto de exploração;
- auditoria de insecure defaults com Trail of Bits `insecure-defaults`;
- fail-closed obrigatório para flags críticas como `REQUIRE_AUTH`;
- databases em Docker privadas por padrão, sem publicação de porta ao host quando não necessária;
- credenciais default/dev proibidas em produção e rotação obrigatória após suspeita de exposição;
- segmentação explícita entre rede de clientes/guest, aplicação, administração e dados;
- subnetting sem ACL/firewall não conta como isolamento;
- microsegmentação e service-specific connectivity para workloads críticos;
- management plane privado, sem SSH/RDP/painéis administrativos expostos diretamente à Internet;
- reverse proxy/WAF/CDN/DMZ podem reduzir exposição, mas ocultação não substitui AuthN/AuthZ;
- regras específicas para Docker/firewall, incluindo risco de portas publicadas contornarem políticas UFW;
- source maps públicos tratados como exposure control;
- `.env`, arquivos de ambiente e config dumps públicos tratados como blockers;
- preço, desconto, imposto, total e estado de pagamento validados no servidor;
- webhooks sensíveis exigem assinatura verificável e replay protection;
- checks de segurança passam a ser expressos como gates automatizáveis, não apenas checklist.
- evidência inválida quando produzida por commit/artefato diferente do que vai a produção.

Regra:

EVIDENCE FROM OLD COMMIT
≠
PASS FOR CURRENT RELEASE

RELEASE
=
SECURITY PASS
+
QUALITY PASS
+
RELIABILITY PASS
+
PRIVACY/COMPLIANCE PASS WHEN APPLICABLE

---

0. OBJETIVO

Este protocolo estabelece o baseline para:

- aplicações web;
- SaaS;
- APIs;
- backends;
- sistemas multi-tenant;
- bancos de dados;
- storage;
- sistemas empresariais;
- aplicações financeiras;
- sistemas com dados pessoais;
- cloud;
- containers;
- CI/CD;
- supply chain;
- caches;
- filas;
- WebSockets;
- webhooks;
- OAuth/OIDC;
- IA generativa;
- RAG;
- agentes;
- MCP;
- infraestrutura;
- observabilidade;
- disaster recovery;
- acessibilidade;
- documentação arquitetural.

O ciclo protegido passa a ser:

DESIGN
  ↓
IMPLEMENT
  ↓
REVIEW
  ↓
TEST
  ↓
BUILD
  ↓
DEPLOY
  ↓
OBSERVE
  ↓
RESPOND
  ↓
RECOVER
  ↓
LEARN

---

0.1 REFERÊNCIAS CANÔNICAS

Segurança de aplicações

- OWASP Top 10:2025;
- OWASP ASVS 5.0.0;
- OWASP API Security Top 10:2023;
- OWASP Cheat Sheet Series;
- OWASP Automated Threats;
- OWASP Bot Management;
- OWASP Credential Stuffing Prevention.

OWASP Top 10:2025 é a versão atual e inclui Broken Access Control, Security Misconfiguration, Software Supply Chain Failures, Cryptographic Failures, Injection, Insecure Design, Authentication Failures, Integrity Failures, Logging/Alerting Failures e Mishandling of Exceptional Conditions.

Para verificação técnica, ASVS 5.0.0 deve ter precedência sobre tratar o Top 10 como checklist, pois a própria OWASP recomenda ASVS como padrão verificável para design, code review e testes.

---

Identidade

- NIST SP 800-63-4;
- NIST SP 800-63B-4;
- RFC 8725;
- RFC 9700;
- RFC 10017.

NIST SP 800-63B-4 é final desde julho de 2025.

RFC 10017, publicado em agosto de 2026, formaliza OAuth 2.0 para aplicações em browser. O padrão BFF mantém access/refresh tokens fora do JavaScript e é fortemente recomendado para aplicações empresariais, sensíveis e que tratam dados pessoais.

---

Secure SDLC e supply chain

- NIST SP 800-218 SSDF 1.1;
- NIST SP 800-218A;
- CISA KEV;
- SBOM;
- provenance;
- artifact signing;
- SLSA 1.2;
- CVSS 4.0;
- EPSS;
- CISA SSVC.

SSDF 1.1 continua sendo a versão final; SP 800-218 Rev. 1 / SSDF 1.2 permanece draft em setembro de 2026.

SLSA 1.2 é a versão aprovada atual e adiciona/estrutura trilhas de Build e Source, provenance e propriedades verificadas.

CVSS não deve ser usado isoladamente para priorização. Combinar severidade técnica com exploração real, probabilidade de exploração, exposição, criticidade do ativo e impacto.

---

IA, agentes e MCP

- OWASP GenAI LLM Top 10 2026;
- OWASP Top 10 for Agentic Applications 2026;
- OWASP MCP Top 10;
- OWASP Practical Guide for Secure MCP Server Development;
- NIST SP 800-218A.

IA generativa, agentes e MCP são tratados como trust boundaries explícitas.

Model output, tool output, retrieved context, memory e conteúdo externo permanecem não confiáveis até validação e autorização.

---

Incident Response e continuidade

- NIST CSF 2.0;
- NIST SP 800-61 Rev. 3;
- NIST SP 800-34 Rev. 1.

NIST SP 800-61 Rev. 3 é a recomendação final atual para integração de incident response ao gerenciamento de risco.

---

Acessibilidade

Baseline:

WCAG 2.2
NÍVEL AA

WCAG 2.2 é W3C Recommendation e Level AA inclui os critérios A e AA.

---

Privacidade e compliance

Conforme aplicabilidade:

- LGPD;
- regulamentações ANPD;
- GDPR;
- HIPAA;
- PCI DSS 4.0.1.

PCI DSS 4.0.1 continua sendo a versão publicada atual em agosto de 2026.

---

0.2 OS 9 DOMÍNIOS

PARTE 1
Governança, Arquitetura e Secure SDLC

PARTE 2
Identity, AuthN, AuthZ, Sessions e Anti-Abuse

PARTE 3
Web, API, Injection e Business Logic

PARTE 4
Data, Database, RLS, Privacy e Compliance

PARTE 5
Cloud, Infrastructure, Secrets e Supply Chain

PARTE 6
Reliability, Resilience, Performance e DR

PARTE 7
Logging, Audit, Detection e Incident Response

PARTE 8
Testing, Quality Engineering e Accessibility

PARTE 9
AI, RAG, Agents e MCP

---

0.3 NÍVEIS

Nível| Aplicação
🟢 BÁSICO| qualquer aplicação com usuário real
🟡 INTERMEDIÁRIO| produção, SaaS, autenticação, PII
🔴 AVANÇADO| multi-tenant, financeiro, escala
⚫ COFRE MÁXIMO| alto impacto, regulado, crítico

Fluxo:

BÁSICO COMPLETO
      ↓
INTERMEDIÁRIO
      ↓
AVANÇADO
      ↓
COFRE MÁXIMO

---

0.4 STATUS DOS CONTROLES

Somente utilizar:

PASS
FAIL
UNKNOWN
N/A
PENDING EXTERNAL ACTION
PENDING LEGAL
ACCEPTED RISK

PASS

Exige evidência objetiva.

UNKNOWN

Não foi possível verificar.

N/A

Existe justificativa técnica de não aplicabilidade.

ACCEPTED RISK

Exige:

RISCO
JUSTIFICATIVA
OWNER
CONTROLE COMPENSATÓRIO
EXPIRAÇÃO
APROVAÇÃO

---

0.5 DEFINITION OF DONE

Um controle crítico somente recebe PASS com:

- [ ] implementação;
- [ ] teste;
- [ ] evidência;
- [ ] resultado esperado;
- [ ] resultado real;
- [ ] owner;
- [ ] data;
- [ ] regressão quando possível.

Para controles críticos, a evidência deve registrar quando aplicável:

- CONTROL ID;
- standard mapping;
- commit SHA;
- artifact digest;
- ambiente;
- comando/teste executado;
- timestamp;
- tool/version;
- resultado bruto ou referência verificável.

Evidência de outro commit, outro artefato ou outro ambiente não prova a release atual sem justificativa explícita.

Exemplo:

CONTROL:
Tenant isolation

IMPLEMENTATION:
TenantAuthorizationService

TEST:
Tenant A → resource B

EXPECTED:
403 / 404

ACTUAL:
403

EVIDENCE:
integration test

OWNER:
Backend

REGRESSION:
CI

---

0.6 SECURITY / PRODUCTION BLOCKERS

Produção deve ser bloqueada para:

- secret ativo exposto;
- credential leak;
- RCE;
- SQL Injection explorável;
- command injection;
- auth bypass;
- privilege escalation crítica;
- cross-tenant access;
- IDOR/BOLA crítico;
- mass assignment privilegiado;
- armazenamento inseguro de senha;
- banco sensível exposto;
- storage sensível público;
- vulnerabilidade crítica ativamente explorada sem mitigação;
- supply-chain compromise;
- build não validado;
- migration destrutiva sem recovery plan;
- falha crítica de autorização;
- corrupção de dados conhecida;
- DR necessário sem backup recuperável;
- release produzida a partir de artefato diferente do validado;
- provenance/signature/digest incompatível com o artefato aprovado;
- cross-tenant leak em RAG, vector DB, agent memory ou MCP;
- agente/MCP com capacidade destrutiva ampla sem autorização e controles compensatórios;
- restore obrigatório falhando ou não verificável;
- migration crítica sem rollback/roll-forward/recovery testável;
- vulnerabilidade KEV aplicável e exposta sem correção ou mitigação formal;
- auth/admin crítico sem telemetria mínima para detectar abuso conhecido;
- mecanismo de fallback que transforma falha de segurança em allow;
- banco de dados sensível publicado na interface pública sem necessidade arquitetural e sem controles compensatórios;
- PostgreSQL/Redis/MySQL/MongoDB exposto à Internet por `ports:`/host binding quando deveria ser somente interno;
- credencial padrão, exemplo, dev ou conhecida ativa em produção;
- `POSTGRES_HOST_AUTH_METHOD=trust` ou autenticação equivalente sem senha em superfície alcançável;
- flag crítica de segurança ausente resultando em estado permissivo (`REQUIRE_AUTH` ausente → auth desligada);
- `.env`, dump, config sensível ou secret file acessível publicamente;
- frontend autorizado a definir unilateralmente valor/status de pagamento;
- webhook financeiro/privilegiado processado sem verificação de autenticidade quando assinatura é suportada/obrigatória;
- source map público contendo secrets ou material sensível.

---

PARTE 1 — GOVERNANÇA, ARQUITETURA E SECURE SDLC

🟢 BÁSICO

1.1 Inventário

Mapear:

- frontend;
- backend;
- APIs;
- banco;
- cache;
- filas;
- storage;
- WebSockets;
- webhooks;
- domínios;
- subdomínios;
- cloud;
- CI/CD;
- integrações;
- terceiros;
- repositórios;
- ambientes;
- secrets;
- certificados;
- IA;
- MCP;
- owners.

---

1.2 Data Classification

PUBLIC
INTERNAL
CONFIDENTIAL
SENSITIVE
CRITICAL

Inventariar:

- PII;
- credenciais;
- tokens;
- dados financeiros;
- documentos;
- dados empresariais;
- fingerprints;
- telemetria;
- biometria;
- logs.

---

1.3 Trust Boundaries

Produzir diagrama mostrando:

INTERNET
   ↓
EDGE
   ↓
FRONTEND
   ↓
BACKEND
   ↓
DATA LAYER
   ↓
THIRD PARTIES

Fronteiras devem ser tratadas explicitamente.

---

1.4 Secure Defaults

DEFAULT DENY

- endpoints privados por padrão;
- debug desligado;
- permissões mínimas;
- storage privado;
- recursos experimentais privados;
- ações administrativas protegidas.

---

🟡 INTERMEDIÁRIO

1.5 Threat Modeling

Para features críticas:

STRIDE
+
ABUSE CASES
+
BUSINESS LOGIC
+
TRUST BOUNDARIES

Analisar:

- spoofing;
- tampering;
- repudiation;
- disclosure;
- denial of service;
- elevation of privilege.

---

1.6 Abuse Cases

Perguntar:

E se alterar o ID?

E se trocar tenant?

E se ignorar o frontend?

E se repetir a ação?

E se usar 10.000 IPs?

E se mandar duas requisições simultâneas?

E se inverter a ordem das operações?

E se comprometer uma conta?

E se comprometer um admin?

E se uma dependência externa mentir?

---

1.7 Risk Register

Cada risco:

ID
ASSET
THREAT
VULNERABILITY
LIKELIHOOD
IMPACT
OWNER
MITIGATION
RESIDUAL RISK
DEADLINE
STATUS

---

1.8 Code Review

Review deve verificar:

- correctness;
- security;
- AuthN;
- AuthZ;
- tenant isolation;
- data access;
- validation;
- concurrency;
- errors;
- observability;
- performance;
- accessibility;
- tests.

OWASP também recomenda explicitamente server-side authorization, fail-safe defaults e review de sessão/IDOR em code review.

---

1.9 CODEOWNERS

Utilizar para áreas críticas quando possível:

- authentication;
- payment;
- authorization;
- migrations;
- CI/CD;
- cloud;
- crypto;
- security configuration.

---

🔴 AVANÇADO

1.10 Architecture Review

Obrigatório para:

- auth;
- multi-tenancy;
- pagamento;
- storage;
- encryption;
- cache;
- queues;
- public APIs;
- AI/agents;
- MCP;
- network architecture.

---

1.11 Architecture Diagrams

Manter no repositório:

System Context

USERS
  ↓
SYSTEM
  ↓
EXTERNAL SYSTEMS

Containers

BROWSER
  ↓
FRONTEND
  ↓
BACKEND
  ↓
DATABASE

 ↘ CACHE
 ↘ STORAGE
 ↘ QUEUE

Deployment

Mostrar:

- cloud;
- regions;
- proxies;
- CDN;
- instances;
- database;
- storage;
- network boundaries.

Data Flow Diagram

Mostrar dados sensíveis atravessando sistemas.

Security Architecture

Mostrar:

- AuthN;
- AuthZ;
- tenant;
- secrets;
- KMS;
- audit logs;
- WAF;
- bot defense;
- backups.

---

1.12 ADR — Architecture Decision Records

Diretório recomendado:

docs/adr/

Formato:

# ADR-XXX — Decisão

## Status

## Context

## Decision

## Alternatives

## Consequences

## Security Impact

## Reliability Impact

## Data/Privacy Impact

## Rollback

ADRs para decisões importantes:

- auth;
- sessions;
- JWT;
- BFF;
- multi-tenancy;
- database;
- RLS;
- cache;
- queue;
- storage;
- encryption;
- rate limiting;
- logging;
- backup;
- AI/MCP.


---

1.13 Control Mapping

Controles críticos devem, quando aplicável, mapear para referências estáveis:

- OWASP ASVS `v5.0.0-x.y.z`;
- OWASP Top 10:2025;
- OWASP API Security Top 10:2023;
- NIST SSDF;
- NIST 800-63-4;
- PCI DSS;
- WCAG 2.2;
- OWASP GenAI / Agentic / MCP.

Não usar somente nome genérico quando existir requisito verificável versionado.

---

1.14 Security Requirements as Code / Policy

Quando viável:

REQUIREMENT
  ↓
CONTROL
  ↓
TEST
  ↓
CI GATE
  ↓
EVIDENCE

Políticas críticas repetíveis devem migrar de documentação manual para validação automatizada sem eliminar review humano.

---

1.15 Insecure Defaults Audit

Configuração ausente deve falhar para o estado seguro.

Exemplos proibidos em produção:

`REQUIRE_AUTH` ausente → autenticação desligada

`DEBUG` ausente → debug ligado

`TLS_VERIFY` ausente → verificação desligada

`SECRET_KEY` ausente → segredo de exemplo

`ADMIN_PASSWORD` ausente → senha conhecida

Regra:

MISSING SECURITY CONFIG
→ FAIL CLOSED / FAIL FAST

Não:

MISSING SECURITY CONFIG
→ CONTINUE INSECURE

Auditar:

- fallback secrets;
- default credentials;
- fail-open switches;
- weak crypto defaults;
- permissive ACL/CORS/file modes;
- debug leakage.

Para finding real, provar:

DEFAULT REACHABLE
+
INSECURE VALUE ACTIVE
+
SECURITY SINK
+
PRODUCTION REACHABILITY

---

1.16 Fail-Closed Configuration Contract

Cada configuração de segurança crítica deve declarar:

- nome;
- secure default;
- comportamento quando ausente;
- comportamento quando inválida;
- environment scope;
- owner;
- test;
- startup validation.

Para produção, preferir:

CONFIG INVALID / MISSING
→ STARTUP FAILURE

em vez de fallback silencioso.

---

⚫ COFRE MÁXIMO

- AppSec formal;
- architecture board;
- security champion;
- risk acceptance formal;
- independent audits;
- vulnerability disclosure;
- supplier governance;
- metrics executivas;
- tabletop exercises;
- separation of duties.

---

PARTE 2 — IDENTITY, AUTHENTICATION, AUTHORIZATION, SESSION E ANTI-ABUSE

🟢 BÁSICO

2.1 Password Storage

Preferir:

ARGON2ID
   ↓
SCRYPT
   ↓
BCRYPT / PBKDF2 quando justificável

OWASP recomenda Argon2id para novos sistemas; um perfil mínimo atualmente documentado é 19 MiB, duas iterações e paralelismo 1, embora a configuração deva ser calibrada ao ambiente.

Nunca:

PLAINTEXT
MD5
SHA-1
SHA-256(password)
REVERSIBLE PASSWORD ENCRYPTION

---

2.2 Password Policy

NIST SP 800-63B-4 estabelece:

SINGLE FACTOR:
mínimo 15 caracteres

PARTE DE MFA:
mínimo 8

Também:

- permitir 64+ caracteres;
- password manager;
- autofill;
- paste;
- blocklist de senhas comprometidas;
- sem composição arbitrária;
- sem troca periódica obrigatória sem comprometimento.

---

2.3 Authentication

Servidor é autoridade.

REQUEST
  ↓
CREDENTIAL / SESSION
  ↓
VALIDATION
  ↓
IDENTITY
  ↓
ACCOUNT STATE

Frontend redirect:

if (!user) ...

é UX.

Não segurança suficiente.

---

2.4 Recovery

- token aleatório;
- single-use;
- TTL;
- armazenar de forma segura;
- rate limit;
- resposta anti-enumeration;
- invalidar após uso;
- notificar alteração;
- revisar sessões;
- não confiar em "Host" arbitrário para construir link.

---

🟡 INTERMEDIÁRIO

2.5 MFA

Obrigatório conforme risco para:

- owner;
- admin;
- infraestrutura;
- cloud;
- secrets;
- funções críticas.

Preferência:

PASSKEY / WEBAUTHN
       ↓
TOTP
       ↓
FALLBACK ADEQUADO

---

2.6 Biometrics

BIOMETRIC
≠
SERVER-STORED PASSWORD

Preferir:

LOCAL BIOMETRIC
     ↓
UNLOCK PRIVATE KEY
     ↓
WEBAUTHN
     ↓
SERVER VERIFIES SIGNATURE

NIST não considera biometria isolada um autenticador e prefere verificação biométrica local associada a autenticador físico.

---

2.7 Session Lifecycle

Toda sessão possui:

CREATE
  ↓
ROTATE
  ↓
USE
  ↓
REFRESH
  ↓
EXPIRE
  ↓REVOKE
  ↓
DESTROY

Definir:

- idle timeout;
- absolute timeout;
- renewal;
- revocation;
- concurrent-session policy.

Não usar tempos universais para todos os sistemas.

---

2.8 Cookies

Quando aplicável:

Set-Cookie:
__Host-session=<random>;
Secure;
HttpOnly;
SameSite=Lax;
Path=/

"SameSite=Strict" quando compatível.

OWASP recomenda TLS durante toda a sessão e atributo "Secure" para session cookies.

---

2.9 Session Fixation

Rotacionar identificador após:

- login;
- aumento de privilégio;
- mudanças sensíveis de contexto.

---

2.10 Logout

Logout deve revogar acesso de verdade quando o mecanismo suportar.

Não apenas remover estado visual.

---

2.11 OAuth / OIDC

Preferir:

AUTHORIZATION CODE
+
PKCE

Seguir RFC 9700.

Para browser com elevada exigência:

BROWSER
 ↓ secure cookie
BFF
 ↓ token
RESOURCE SERVER

RFC 10017 descreve BFF como padrão que mantém access/refresh tokens fora do JavaScript.

Quando BFF for aplicável:

- cookie de sessão seguro;
- tokens OAuth mantidos server-side;
- CSRF considerado;
- CORS mínimo;
- session rotation;
- token revocation conforme arquitetura;
- backend continua executando AuthZ por recurso/ação.

Token-mediating backend é menos seguro que BFF porque access token ainda chega ao browser.

Browser-only OAuth client deve ser exceção arquitetural consciente e seguir Authorization Code + PKCE.


---

2.12 JWT

JWT é opção arquitetural.

Não requisito.

Se usado:

- algorithm allow-list;
- assinatura obrigatória;
- "iss";
- "aud";
- "exp";
- tipo/finalidade;
- key validation;
- replay strategy;
- token separation.

Nunca:

JWT role=ADMIN
=
AUTHORIZATION AUTOMÁTICA

---

2.13 Authorization

IDENTITY
  ↓
ROLE / ATTRIBUTES
  ↓
PERMISSIONS
  ↓
TENANT
  ↓
RESOURCE
  ↓
ACTION

---

2.14 RBAC

Papéis devem ser descobertos na aplicação.

Exemplo:

OWNER
ADMIN
MANAGER
EMPLOYEE
VIEWER

---

2.15 ABAC

Quando necessário considerar:

- tenant;
- device;
- risk;
- horário;
- localização;
- estado;
- sensitivity;
- transaction type.

---

2.16 Multi-Tenant Isolation

Toda operação responde:

WHO?
TENANT?
RESOURCE?
ACTION?
PERMISSION?

Conceitualmente:

WHERE resource_id = :resource
AND tenant_id = :authenticatedTenant

Tenant recebido no body não é fonte de autoridade.

---

2.17 Tenant Isolation deve atingir

Não somente SQL.

Também:

- database;
- cache;
- object storage;
- search indexes;
- vector DB;
- queues;
- WebSockets;
- exports;
- logs;
- reports;
- background jobs;
- analytics.

---

2.18 UUID

UUID
≠
ACCESS CONTROL

---

2.19 Mass Assignment

Allow-list explícita.

Nunca salvar indiscriminadamente:

req.body

Campos protegidos incluem:

- role;
- permissions;
- tenant;
- owner;
- admin;
- verified;
- balance;
- internalPrice;
- status privilegiado.

---

2.20 Step-Up Authentication

Exigir conforme risco para:

- trocar senha;
- mudar e-mail;
- mudar MFA;
- transferir owner;
- criar admin;
- exportar dados;
- excluir empresa;
- pagamento;
- secrets;
- impersonation.

---

2.21 Impersonation

Se suporte puder impersonar usuário:

- permissão explícita;
- motivo;
- TTL;
- banner visível;
- audit log;
- nunca esconder identidade do operador;
- operações críticas opcionalmente bloqueadas.

---

2.22 Anti-Automation

OWASP recomenda defesa em camadas e ressalta que ataques distribuídos não podem ser resolvidos apenas por IP.

Assumir atacante com:

PROXY ROTATION
RESIDENTIAL BOTNET
HEADLESS BROWSER
CAPTCHA SOLVER
LOW-AND-SLOW

---

2.23 Distributed Rate Limiting

Avaliar:

REQ / IP
REQ / SUBNET
REQ / ASN
REQ / ACCOUNT
REQ / DEVICE
REQ / SESSION
REQ / TENANT
REQ / ROUTE
REQ / ACTION

Aplicar:

- burst;
- rolling windows;
- quotas;
- velocity;
- distributed counters;
- backoff.

---

2.24 Fingerprinting

Separar:

DEVICE
CONNECTION
SESSION
BEHAVIOR

Fingerprint:

≠ IDENTITY
≠ AUTH
≠ AUTHORIZATION

---

2.25 Risk Engine

Combinar:

NETWORK
DEVICE
CONNECTION
SESSION
ACCOUNT
BEHAVIOR
VELOCITY
RESOURCE

Saída:

LOW
MEDIUM
HIGH
CRITICAL

---

2.26 Adaptive Response

LOW
→ ALLOW

MEDIUM
→ THROTTLE / CHALLENGE

HIGH
→ CAPTCHA + STEP-UP

CRITICAL
→ HOLD / DENY / REVOKE / ALERT

---

2.27 CAPTCHA

CAPTCHA:

≠ AUTHENTICATION
≠ AUTHORIZATION
≠ MFA

Preferir uso adaptativo.

OWASP destaca que CAPTCHA pode ser resolvido ou terceirizado e não deve ser o único controle.

---

2.28 Credential Stuffing

Combinar:

- breached-password blocklist;
- account limits;
- MFA;
- passkeys;
- fingerprint;
- velocity;
- adaptive challenge;
- alerting.

---

2.29 Password Spraying

Detectar:

MESMA SENHA/PADRÃO
→ MUITAS CONTAS

---

2.30 ATO — Account Takeover

Sinais:

- novo device;
- novo ASN;
- MFA removido;
- password reset;
- owner changed;
- admin granted;
- export anormal;
- sessão incompatível.

Resposta:

STEP-UP
ALERT
REVOKE
HOLD
REVIEW

---

2.31 Honeypots / Tarpits

Podem aumentar risk score.

Nunca gerar DoS contra o próprio sistema.

---

2.32 Fingerprint Privacy

- finalidade;
- minimização;
- retenção curta;
- acesso restrito;
- pseudonimização;
- documentação.


---

2.33 Recovery Assurance

RECOVERY
≠
WEAKEST AUTH PATH

Recuperação de conta não deve contornar controles equivalentes à autenticação normal.

Para contas críticas considerar:

- reautenticação;
- proof-of-possession;
- cooldown;
- notification out-of-band;
- session revocation;
- MFA recovery controls;
- helpdesk verification;
- audit trail.

---

2.34 Phishing-Resistant Authentication

Para alto impacto, priorizar autenticadores resistentes a phishing:

PASSKEY / FIDO2 / WEBAUTHN

SMS/voice devem ser tratados como mecanismos de menor garantia e usados apenas quando o risco/compatibilidade justificar.

---

2.35 Authentication Must Fail Closed

Flags como:

- `REQUIRE_AUTH`;
- `AUTH_ENABLED`;
- `SECURITY_ENABLED`;
- `DISABLE_AUTH`;
- `ALLOW_ANONYMOUS`;

devem possuir semântica inequívoca.

Baseline de produção:

`REQUIRE_AUTH` ausente
→ AUTH REQUIRED / STARTUP FAIL

Nunca:

`REQUIRE_AUTH` ausente
→ FALSE
→ anonymous access

Validar em teste:

1. remover a variável;
2. iniciar a aplicação;
3. confirmar falha de startup ou autenticação obrigatória;
4. tentar endpoint protegido;
5. confirmar `401/403`, nunca `2xx`.

---

PARTE 3 — WEB, API, INJECTION E BUSINESS LOGIC

🟢 BÁSICO

3.1 Input Validation

Toda entrada externa é hostil:

BODY
QUERY
PARAM
HEADER
COOKIE
FILE
WEBHOOK
QUEUE
API
LLM
MCP

Validar:

- tipo;
- tamanho;
- range;
- formato;
- enum;
- cardinalidade;
- URL;
- data;
- quantidade;
- moeda;
- regras de negócio.

---

3.2 Sanitization não substitui controles corretos

VALIDATION
≠
PARAMETERIZATION
≠
OUTPUT ENCODING
≠
HTML SANITIZATION

---

3.3 SQL Injection

PREPARED STATEMENT
+
PARAMETERIZED ORM

Nunca concatenar input.

---

3.4 NoSQL Injection

- validar operadores;
- rejeitar objetos inesperados;
- restringir expressions;
- controlar regex.

---

3.5 Command Injection

Evitar shell.

Quando inevitável:

- args estruturados;
- allow-list;
- sandbox;
- least privilege;
- timeout.

---

3.6 Template Injection

Nunca tratar conteúdo externo como template executável.

---

3.7 XSS

- framework escaping;
- contextual encoding;
- sanitizer confiável para rich HTML;
- CSP;
- evitar HTML cru.

---

3.8 Security Headers

Aplicar conforme resposta.

Para browser:

X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin

CSP adequada.

"frame-ancestors" é mecanismo moderno para controle de framing; "X-Frame-Options" pode ser usado como compatibilidade.

---

3.9 CORS

CORS
≠
AUTHORIZATION

Origem "*" não é automaticamente vulnerabilidade.

Pode ser válida para recurso genuinamente público sem credentials.

Para APIs autenticadas:

- origens controladas;
- métodos mínimos;
- headers mínimos;
- credential policy explícita.

---

3.10 CSRF

Avaliar quando browser envia credenciais automaticamente.

Controles:

- SameSite;
- CSRF token;
- Origin;
- Referer complementar.

GET não deve causar mutation.

---

🟡 INTERMEDIÁRIO

3.11 API Security Top 10

Cobrir:

API1  BOLA
API2  Broken Authentication
API3  BOPLA
API4  Resource Consumption
API5  Broken Function Authorization
API6  Sensitive Business Flows
API7  SSRF
API8  Misconfiguration
API9  Inventory
API10 Unsafe Consumption

Essa é a edição publicada atual do OWASP API Security Top 10.

---

3.12 IDOR/BOLA Regression

USER A → A = ALLOW
USER B → A = DENY

Testar GET, PUT, PATCH, DELETE e ações customizadas.

---

3.13 API Output Minimization

Nunca serializar entidade inteira automaticamente.

Não retornar:

- hash;
- reset token;
- MFA secret;
- internal flags;
- private metadata;
- secrets;
- PII desnecessária.

---

3.14 Resource Consumption

Limitar:

- payload;
- pagination;
- batch;
- files;
- CPU;
- memory;
- connections;
- reports;
- AI tokens.

---

3.15 Upload Security

Validar:

- extensão;
- MIME;
- magic bytes;
- tamanho;
- quantidade;
- nome;
- path.

Aplicar:

- randomized server name;
- private storage;
- authorization;
- malware scanning quando risco justificar;
- nunca executar upload.

---

3.16 SSRF

Validar:

- scheme;
- hostname;
- DNS;
- IP resolvido;
- redirects;
- port;
- IPv4;
- IPv6.

Bloquear quando desnecessário:

- loopback;
- private networks;
- link-local;
- cloud metadata;
- internal services.

---

3.17 Path Traversal

Canonicalizar e então validar.

---

3.18 XXE

Quando XML existir:

- DTD off;
- external entities off.

---

3.19 ReDoS

- input limits;
- regex review;
- timeout;
- evitar backtracking explosivo.

---

3.20 Open Redirect

Preferir rotas relativas ou allow-list.

---

3.21 Proxy Trust

Somente confiar em:

Forwarded
X-Forwarded-For
X-Forwarded-Proto

quando enviados por proxy confiável.

---

3.22 Header Bypass

Quando não utilizados:

X-Original-URL
X-Rewrite-URL
X-Override-URL
X-HTTP-Method-Override

devem ser removidos ou rejeitados.

---

3.23 Host Header

Não construir URLs sensíveis usando "Host" arbitrário.

---

3.24 Request Smuggling

- edge/proxy/backend atualizados;
- parsing consistente;
- rejeitar ambiguity;
- testar CL/TE e TE/CL quando relevante.

---

3.25 Cache Poisoning

Validar:

- cache key;
- "Vary";
- headers;
- query params;
- auth state;
- tenant.

---

3.26 Webhooks

- signature;
- timestamp;
- replay protection;
- schema;
- idempotency;
- timeout;
- logs.

---

3.27 WebSockets

- AuthN;
- AuthZ por evento;
- tenant;
- payload schema;
- message size;
- rate limit;
- heartbeat;
- revocation.

---

3.28 GraphQL — se aplicável

- AuthZ por resolver;
- depth/complexity;
- batch limits;
- introspection policy;
- pagination;
- field-level controls.

---

3.29 Replay Protection

Utilizar conforme protocolo:

- nonce;
- timestamp;
- one-time token;
- replay cache;
- signature;
- idempotency key.

---

3.30 Business Logic

Testar:

NEGATIVE
ZERO
MAX
OVERFLOW
DUPLICATE
REPLAY
RACE
OUT-OF-ORDER
DOUBLE CLICK


---

3.31 API Inventory / Shadow APIs

Inventariar:

- routes;
- versions;
- deprecated endpoints;
- internal APIs;
- admin APIs;
- webhooks;
- GraphQL;
- mobile APIs;
- experimental endpoints.

Endpoint esquecido continua sendo superfície de ataque.

---

3.32 Background Jobs / Async Authorization

JOB
≠
TRUSTED BY DEFAULT

Job deve carregar contexto autorizado:

- actor;
- tenant;
- resource;
- action;
- permissions snapshot ou revalidação;
- correlation ID.

Nunca confiar apenas em IDs serializados na fila.

---

3.33 Content-Type / Parser Safety

Validar:

- Content-Type esperado;
- parser compatível;
- charset quando relevante;
- tamanho antes de parse;
- nesting/depth;
- decompression limits.

Evitar parser differential entre edge e backend.

---

3.34 Exposed Environment / Configuration Files

Arquivos de ambiente, configuração, dumps e artefatos de build nunca devem ser servidos publicamente.

Bloquear:

- `.env`;
- `.env.*`;
- `.git`;
- `.svn`;
- `config.*` sensível;
- backup files;
- editor swap files;
- build manifests sensíveis;
- logs exportados;
- dumps SQL;
- debug endpoints;
- framework diagnostic files.

HTTP GET público para segredo/configuração sensível:

→ BLOCKER

Controles:

- deny rules no web server;
- build packaging allow-list;
- static root mínimo;
- secret scan;
- post-deploy probe;
- artifact inspection.

Regra:

FILE EXISTS IN REPO
≠
FILE MUST BE PUBLICLY SERVED

---

3.35 Source Map Exposure

Source maps de frontend podem expor:

- nomes de arquivos;
- caminhos;
- código-fonte;- comentários;
- endpoints;
- feature flags;
- lógica interna;
- nomes de classes/funções;
- referências a serviços.

Source map público não é automaticamente vulnerabilidade crítica, mas amplia reconnaissance e pode revelar informação sensível.

Produção deve decidir explicitamente:

PUBLIC SOURCEMAP?
YES / NO

Se não necessário:

- gerar apenas para observability privada;
- remover do artefato público;
- usar upload privado para Sentry/equivalente;
- testar URLs `*.map`;
- impedir publicação acidental.

Nunca permitir secrets em source map ou bundle.

---

3.36 Payment Integrity — Server Authority

Frontend nunca é autoridade para:

- preço unitário;
- subtotal;
- desconto;
- imposto;
- frete;
- total;
- status de pagamento;
- moeda;
- quantidade final;
- produto/plan ID;
- entitlement.

Cliente pode enviar intenção ou seleção.

Servidor recalcula:

ITEMS
+
PRICE SOURCE OF TRUTH
+
DISCOUNT RULES
+
TAX RULES
+
TOTAL
+
PAYMENT STATE

Nunca aceitar:

```json
{
  "price": 1,
  "paid": true,
  "role": "premium"
}
```

como autoridade de negócio.

Para pagamentos:

FRONTEND SUCCESS SCREEN
≠
PAYMENT CONFIRMED

Confirmar por:

- provider API;
- signed webhook;
- server-to-server verification;
- idempotency;
- transaction state machine.

---

3.37 Webhook Signature Enforcement

Webhook sensível deve possuir, quando provider suportar:

SIGNATURE
+
TIMESTAMP
+
BODY CANONICALIZATION
+
REPLAY WINDOW
+
SECRET/KEY ROTATION
+
IDEMPOTENCY

Se assinatura é esperada:

MISSING / INVALID SIGNATURE
→ REJECT

Nunca:

MISSING SIGNATURE
→ PROCESS ANYWAY

Não confiar apenas em:

- source IP;
- User-Agent;
- obscurity da URL;
- header não autenticado.

---

3.38 Password Reset Security Gate

Password reset é fluxo de autenticação.

Validar:

- token forte e aleatório;
- uso único;
- TTL;
- armazenamento seguro;
- anti-enumeration;
- rate limit;
- invalidation after use;
- session review/revocation;
- notification;
- Host header safety;
- MFA/recovery interaction;
- no predictable IDs.

Teste obrigatório:

RESET TOKEN REPLAY
→ DENY

EXPIRED RESET TOKEN
→ DENY

OTHER USER TOKEN
→ DENY

---

3.39 Session Management Security Gate

Sessão fraca inclui:

- session ID previsível;
- ausência de rotação;
- timeout indefinido;
- logout apenas visual;
- revogação inexistente;
- cookie sem flags adequadas;
- sessão sobrevivendo a mudança crítica de credencial sem justificativa.

Gate deve provar:

LOGIN
→ SESSION CREATED

PRIVILEGE CHANGE
→ SESSION ROTATED / REEVALUATED

LOGOUT
→ ACCESS REVOKED

EXPIRY
→ ACCESS DENIED

---

3.40 JWT Secret / Key Exposure

JWT signing secret/private key é CRITICAL SECRET.

Nunca em:

- frontend;
- mobile bundle;
- source map;
- public repo;
- image layer;
- logs;
- example config com valor real.

Se exposto:

ASSUME COMPROMISE
→ ROTATE KEY
→ INVALIDATE AFFECTED TOKENS WHEN POSSIBLE
→ REVIEW ISSUANCE
→ REVIEW AUDIENCE/ISSUER
→ ADD REGRESSION

JWT válido criptograficamente:

≠
AUTHORIZED REQUEST

---

PARTE 4 — DATA, DATABASE, RLS, PRIVACY E COMPLIANCE

🟢 BÁSICO

4.1 Data Minimization

IF NOT NEEDED
DO NOT COLLECT

---

4.2 Database Access

Banco tradicional:

CLIENT
  ↓
BACKEND
  ↓
DATABASE

Não browser → banco administrativo.

---

4.3 BaaS / Publishable Keys

Se arquitetura suportar chave explicitamente publicável:

CLIENT
→ PUBLISHABLE KEY

pode ser correto.

Mas:

PUBLIC KEY
≠ AUTH
≠ AUTHORIZATION
≠ RLS

Secret/service/admin keys nunca no browser.

---

4.4 RLS

Quando suportado e adequado:

- default deny;
- SELECT policy;
- INSERT;
- UPDATE;
- DELETE;
- tenant;
- ownership.

RLS é defesa adicional.

Backend AuthZ continua necessária quando houver backend.

---

4.5 Cross-Tenant Tests

A → A = ALLOW
A → B = DENY
B → A = DENY
ANON → PRIVATE = DENY

---

4.6 Encryption

Senhas:

HASH

Dados recuperáveis:

ENCRYPT

Não construir criptografia própria.

---

4.7 Key Management

Separar:

DATA
KEY
MASTER KEY

- key IDs;
- versioning;
- rotation;
- access control;
- KMS quando apropriado.

---

4.8 Test Data

Não copiar produção para desenvolvimento sem:

- necessidade;
- autorização;
- masking;
- anonymization/pseudonymization;
- controles equivalentes.

Preferir dados sintéticos.

---

🟡 INTERMEDIÁRIO

4.9 Data Lifecycle

COLLECT
 ↓
PROCESS
 ↓
STORE
 ↓
SHARE
 ↓
ARCHIVE
 ↓
DELETE / ANONYMIZE

---

4.10 Retention

Política por categoria:

DATA TYPE
PURPOSE
LEGAL BASIS
RETENTION
DELETION METHOD
BACKUP BEHAVIOR
OWNER

---

4.11 Deletion

Exclusão deve considerar:

- dados ativos;
- cache;
- search;
- storage;
- replicas;
- derived data;
- backups.

Backup pode possuir ciclo separado documentado.

---

4.12 LGPD

Aplicar princípios e obrigações pertinentes da Lei 13.709/2018.

---

4.13 Incident LGPD

Quando incidente puder causar risco ou dano relevante:

ANPD / TITULAR
3 DIAS ÚTEIS

ressalvada legislação específica.

Registro de incidentes deve ser mantido por pelo menos cinco anos segundo o regulamento.

---

4.14 Direitos do Titular

Projetar mecanismos para quando aplicável:

- confirmação;
- acesso;
- correção;
- anonimização;
- bloqueio;
- eliminação;
- portabilidade;
- informações de compartilhamento;
- revogação;
- revisão de decisões automatizadas.

---

4.15 Privacy by Design

Avaliar privacy no design, não somente em documento jurídico.

Para sistemas avançados considerar privacy threat modeling, inclusive metodologias como LINDDUN quando úteis.

---

4.16 Cookies

Inventariar:

ESSENTIAL
AUTH
PREFERENCE
ANALYTICS
MARKETING

Não criar banner apenas por hábito.

Avaliar obrigação real.

---

4.17 Terms / Privacy

Sistema comercial deve possuir quando aplicável:

/termos
/privacidade

Política deve refletir comportamento real.

Não inventar empresa, DPO ou subprocessadores.

Placeholder:

[INFORMAÇÃO JURÍDICA A DEFINIR]

---

4.18 Legal Footer

© {ANO_ATUAL} Produto.
Todos os direitos reservados.

Com links acessíveis.

---

🔴 AVANÇADO

4.19 GDPR

Primeiro:

IS GDPR APPLICABLE?

Se sim, aplicar controles correspondentes.

GDPR exige princípios como lawfulness, purpose limitation e data minimisation.

---

4.20 HIPAA

Primeiro:

IS SYSTEM A
COVERED ENTITY
OR BUSINESS ASSOCIATE
PROCESSING ePHI?

HIPAA Security Rule não é requisito genérico para todo SaaS; aplica-se às entidades reguladas e ePHI.

A proposta de atualização publicada em 2025 ainda não substituiu a Security Rule vigente.

---

4.21 PCI DSS

Primeiro:

IS CARDHOLDER DATA ENVIRONMENT
IN SCOPE?

Se sim, mapear PCI DSS 4.0.1.

Evitar armazenar dados de cartão quando tokenização/PSP puder remover o sistema do escopo mais amplo.


---

4.22 Data Export Security

Exportações devem aplicar:

- AuthN;
- AuthZ;
- tenant isolation;
- step-up conforme sensibilidade;
- minimização;
- audit;
- rate/volume limits;
- expiração de links;
- private storage;
- revocation quando aplicável.

EXPORT
≠
BYPASS DE AUTORIZAÇÃO

---

4.23 Cryptographic Erasure

Quando arquiteturalmente apropriado, considerar eliminação por destruição segura de chaves para dados criptograficamente isolados.

Deve existir prova de:

- escopo;
- key ownership;
- dependências;
- backups;
- irreversibilidade esperada.

---

⚫ COFRE MÁXIMO

- KMS;
- HSM;
- envelope encryption;
- DLP;
- key ceremonies quando necessário;
- separation of duties;
- dual control;
- crypto inventory;
- crypto agility;
- post-quantum migration planning conforme vida útil dos dados e risco.

---

PARTE 5 — CLOUD, INFRASTRUCTURE, SECRETS E SUPPLY CHAIN

🟢 BÁSICO

5.1 Secrets

Nunca em:

SOURCE CODE
GIT
README
SCREENSHOT
PUBLIC ISSUE
BUILD LOG
FRONTEND BUNDLE
DOCKER IMAGE
PUBLIC PROMPT

---

5.2 ".env"

.env
.env.*
!.env.example

".env.example" contém somente placeholders.

---

5.3 Git History

Segredo versionado:

COMPROMISED

Fluxo:

REVOKE / ROTATE
 ↓
REMOVE CURRENT
 ↓
CLEAN HISTORY IF APPROPRIATE
 ↓
CHECK ARTIFACTS
 ↓
PREVENT RECURRENCE

Nunca mostrar o valor encontrado.

---

5.4 History Rewrite

Não fazer force-push destrutivo automaticamente em repo compartilhado.

Avaliar:

- branches;
- tags;
- forks;
- collaborators;
- deploys.

---

5.5 Secret Inventory

NAME
PURPOSE
OWNER
ENVIRONMENT
LOCATION
ACCESS
ROTATION METHOD
EXPIRATION
LAST ROTATION

---

🟡 INTERMEDIÁRIO

5.6 Secret Manager

Usar mecanismo apropriado:

- cloud secret manager;
- platform secrets;
- Vault;
- workload identity.

Secret manager não significa necessariamente “nenhuma env var”; o objetivo é controlar exposição e ciclo de vida.

---

5.7 Short-Lived Credentials

Preferir quando disponível:

OIDC FEDERATION
WORKLOAD IDENTITY
SHORT-LIVED TOKEN

---

5.8 Secret Rotation

Não:

ROTATE EVERYTHING EVERY 90 DAYS

como regra universal.

Rotacionar segundo:

- compromise;
- exposure;
- lifecycle;
- personnel change;
- provider requirements;
- risk;
- compliance.

---

5.9 TLS

Baseline:

TLS 1.3 DEFAULT
TLS 1.2 WHEN COMPATIBILITY REQUIRES
TLS 1.0/1.1 OFF

Isso corresponde à orientação OWASP atual.

---

5.10 Certificate Lifecycle

Cada certificado possui:

ISSUE
 ↓
DEPLOY
 ↓
MONITOR
 ↓
RENEW
 ↓
ROTATE
 ↓
REVOKE

Controlar:

- expiration;
- private key access;
- SAN/domain;
- issuer;
- renewal automation;
- revocation.

---

5.11 HSTS

Somente após HTTPS corretamente operacional.

Preload é decisão adicional, não default obrigatório.

---

5.12 IAM

LEAST PRIVILEGE

- funções específicas;
- admin separado;
- MFA;
- workload identity;
- audit;
- revocation.

---

5.13 Network

- ingress mínimo;
- egress control;
- private subnets;
- private DB;
- metadata protection;
- management interfaces restritas.

---

5.14 Cloud Metadata

Proteção contra SSRF.

Na AWS, usar IMDSv2 quando aplicável.

---

5.15 Containers

- trusted base;
- non-root;
- image scan;
- no secrets;
- read-only quando compatível;
- capabilities mínimas;
- seccomp quando adequado;
- health checks.

"Alpine" ou "distroless" não significam automaticamente seguro.

---

5.16 CI/CD

Pipeline base:

LINT
 ↓
TYPECHECK
 ↓
UNIT
 ↓
SECRET SCAN
 ↓
SAST
 ↓
SCA
 ↓
BUILD
 ↓
SBOM
 ↓
CONTAINER/IaC SCAN
 ↓
INTEGRATION
 ↓
STAGING
 ↓
DAST/API
 ↓
REGRESSION
 ↓
GATE
 ↓
PRODUCTION

---

5.17 Dependencies

Antes de adicionar pacote:

- necessidade;
- registry;
- maintainer;
- repository;
- history;
- CVEs;
- license;
- typosquatting;
- slopsquatting.

---

5.18 Lockfiles

Obrigatórios quando ecossistema suportar.

---

5.19 Vulnerability Management

Priorizar:

KEV / EXPLOITATION OBSERVED
+
EPSS / EXPLOIT LIKELIHOOD
+
EXPOSURE
+
REACHABILITY
+
IMPACT
+
ASSET CRITICALITY
+
COMPENSATING CONTROLS
+
CVSS 4.0
+
SSVC / DECISION CONTEXT

CISA KEV deve ser entrada direta porque representa vulnerabilidades conhecidamente exploradas.

EPSS estima probabilidade de exploração no horizonte de 30 dias e não substitui impacto/contexto.

CVSS descreve severidade técnica e não deve ser tratado isoladamente como prioridade de patch.

---

5.20 Patch Strategy

Cada vulnerabilidade:

CVE
AFFECTED?
REACHABLE?
EXPOSED?
EXPLOITABLE?
KEV?
EPSS?
CVSS 4.0?
SSVC/DECISION?
FIX AVAILABLE?
BREAKING CHANGE?
MITIGATION?
DEADLINE?
OWNER?

---

🔴 AVANÇADO

5.21 SBOM

Gerar:

- component;
- version;
- origin;
- hash;
- license.

Formatos:

CycloneDX
SPDX

---

5.22 Provenance

Produção deve saber:

SOURCE COMMIT
BUILD
DEPENDENCIES
ARTIFACT HASH
DEPLOYMENT

---

5.23 Artifact Signing

Avaliar:

- Sigstore/cosign;
- signed container images;
- signed releases.

---

5.24 Build Once

BUILD
 ↓
TEST SAME ARTIFACT
 ↓
DEPLOY SAME ARTIFACT

---

5.25 GitHub Actions / CI

- explicit permissions;
- least privilege;
- trusted actions;
- pinning adequado;
- protected secrets;
- PR isolation;
- revisar "pull_request_target".

---

5.26 Branch Protection

- required PR;
- required CI;
- reviewers;
- no arbitrary force push;
- CODEOWNERS quando necessário.


---

5.27 SLSA 1.2 / Provenance Verification

Para artefatos críticos, avaliar trilhas SLSA:

SOURCE
+
BUILD
+
PROVENANCE
+
VERIFICATION

Antes do deploy verificar quando disponível:

- source repository;
- source revision;
- builder identity;
- build parameters;
- artifact digest;
- provenance;
- signature/attestation;
- policy result.

ATTESTATION EXISTS
≠
ATTESTATION VERIFIED

---

5.28 IaC Drift

Infraestrutura declarada e real devem ser comparadas.

Detectar:

- manual changes;
- permissões ampliadas;
- public exposure;
- firewall drift;
- secret/config drift;
- unmanaged resources.

DRIFT CRÍTICO
→ REVIEW / RECONCILE
---

5.29 Database Network Exposure — Docker / Compose

Banco de dados de aplicação deve ser PRIVATE BY DEFAULT.

Em Docker Compose, comunicação entre serviços usa a rede interna e o nome do serviço.

Exemplo seguro:

```yaml
services:
  app:
    environment:
      DB_HOST: db
      DB_PORT: 5432
    depends_on:
      - db

  db:
    image: postgres:18
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    networks:
      - backend

networks:
  backend:
    internal: true
```

Para tráfego apenas container → container:

NÃO É NECESSÁRIO:

```yaml
ports:
  - "5432:5432"
```

`ports:` publica a porta no host.

Se acesso pelo host for realmente necessário em desenvolvimento:

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

Isso não é substituto de firewall, auth ou segredo forte.

Em produção, exposição externa do banco exige justificativa arquitetural explícita, ACL/firewall, TLS conforme cenário, autenticação forte, observabilidade e owner.

Nunca assumir:

DB PASSWORD
=
NETWORK PERIMETER

Defesa correta:

PRIVATE NETWORK
+
AUTH
+
LEAST PRIVILEGE
+
PATCHING
+
MONITORING

---

5.30 PostgreSQL Authentication Hardening

Para a imagem oficial PostgreSQL:

- `POSTGRES_PASSWORD` deve ser forte e não-padrão;
- não usar valores como `postgres`, `password`, `admin`, `example`, nome do produto ou credencial publicada em README;
- não usar `POSTGRES_HOST_AUTH_METHOD=trust` em ambiente alcançável;
- preferir autenticação moderna suportada, como `scram-sha-256`;
- app não deve conectar como superuser `postgres` quando uma role limitada for suficiente;
- separar role de migration/admin da role runtime quando justificável;
- restringir `pg_hba.conf` ao mínimo necessário;
- rotacionar senha após exposição/suspeita de comprometimento;
- lembrar que alterar `POSTGRES_PASSWORD` no Compose não necessariamente altera uma instância já inicializada.

INCIDENT RESPONSE:

PORT EXPOSED + CREDENTIAL WEAK/KNOWN
→ ASSUME CREDENTIAL COMPROMISE
→ CLOSE EXPOSURE
→ ROTATE CREDENTIAL
→ REVIEW LOGS
→ CHECK PERSISTENCE
→ PATCH
→ VERIFY FROM INTERNET
→ ADD REGRESSION

---

5.31 Database Exposure Regression

CI/review deve procurar em manifests:

- `5432:5432`;
- `0.0.0.0:5432`;
- `3306:3306`;
- `6379:6379`;
- `27017:27017`;
- `network_mode: host`;
- security groups `0.0.0.0/0`;
- `POSTGRES_HOST_AUTH_METHOD=trust`;
- credenciais de exemplo/default.

Finding depende do contexto.

Porta publicada em dev local pode ser válida.

Porta publicada em VPS/produção sem necessidade é blocker.

Teste recomendado:

EXTERNAL HOST
→ DB PORT
→ MUST BE CLOSED / FILTERED

quando o banco é designado como interno.

---

5.32 Subnetting ≠ Security Boundary

Máscara de sub-rede organiza endereçamento e roteamento.

Sozinha, não prova isolamento.

Exemplo:

CLIENTES 10.10.10.0/24
SISTEMA  10.10.20.0/24

Se o roteador permite:

10.10.10.0/24
→
10.10.20.0/24
ALLOW ANY

então existe separação lógica de endereços, mas não isolamento de segurança.

Para considerar segmentação como controle:

SUBNET / VLAN / VRF
+
ROUTING CONTROL
+
ACL / FIREWALL
+
DEFAULT DENY
+
LOGGING
+
TEST

Regra:

DIFFERENT SUBNET
≠
DENIED CONNECTIVITY

---

5.33 Network Security Zones

Separar conforme arquitetura real.

Modelo para academia/empresa:

INTERNET
  ↓
EDGE / CDN / WAF
  ↓
DMZ / REVERSE PROXY
  ↓
APPLICATION ZONE
  ↓
DATA ZONE

CLIENT / GUEST WIFI
  ↛ MANAGEMENT
  ↛ DATABASE
  ↛ INTERNAL SERVICES

STAFF / CORPORATE
  → somente serviços necessários

MANAGEMENT ZONE
  → administração autorizada

DATA ZONE
  ← somente application/migration paths autorizados

Quando aplicável, separar também:

- IoT;
- catracas;
- câmeras/CCTV;
- impressoras;
- pagamentos;
- backups;
- observabilidade;
- CI/CD runners;
- fornecedores/terceiros.

Não colocar clientes e infraestrutura crítica no mesmo domínio de confiança.

---

5.34 Inter-Zone Policy

Princípio:

DENY ALL
+
ALLOW REQUIRED FLOWS

Cada fluxo permitido deve declarar:

SOURCE
DESTINATION
PROTOCOL
PORT
PURPOSE
OWNER

Exemplo:

GUEST VLAN
→ INTERNET 443
ALLOW

GUEST VLAN
→ APP PUBLIC 443
ALLOW quando necessário

GUEST VLAN
→ APP ADMIN
DENY

GUEST VLAN
→ POSTGRES 5432
DENY

GUEST VLAN
→ SSH 22
DENY

APP
→ POSTGRES 5432
ALLOW

ADMIN ZONE
→ MANAGEMENT
ALLOW conforme identidade/política

Evitar:

ANY
→ ANY
ALLOW

---

5.35 Client / Guest Isolation

Em redes de clientes/visitantes:

- VLAN/SSID próprios;
- client isolation quando suportado;
- private VLAN/PVLAN quando apropriado;
- bloquear east-west desnecessário;
- bloquear acesso a RFC1918/internal ranges quando aplicável;
- liberar apenas Internet e serviços explicitamente necessários;
- DNS e DHCP controlados;
- registrar negações relevantes;
- impedir acesso à management plane.

Objetivo:

CLIENT A
↛
CLIENT B

quando comunicação peer-to-peer não for necessária.

E:

CLIENT
↛
INTERNAL ADMIN / DB / INFRA

---

5.36 Management Plane Isolation

Administração não deve depender de painel público aberto à Internet.

Preferir:

TRUSTED ADMIN DEVICE
  ↓
VPN / ZTNA / BASTION
  ↓
MANAGEMENT ZONE
  ↓
SSH / RDP / HYPERVISOR / DB ADMIN / CONTROL PANEL

Controles:

- MFA/passkey;
- device posture quando disponível;
- source restriction;
- short-lived access;
- JIT/JEA quando disponível;
- audit;
- session timeout;
- no shared admin accounts.

Não gerenciar infraestrutura diretamente da rede guest.

Não expor SSH/RDP/painel somente porque existe senha forte.

---

5.37 Reduce Origin Exposure

"Ocultar" não é controle primário.

Mas reduzir reachability é defesa válida.

Para aplicações públicas considerar:

INTERNET
  ↓
CDN / REVERSE PROXY / WAF
  ↓
ORIGIN RESTRICTED

Origin deve, quando viável:

- aceitar tráfego apenas do proxy/CDN/LB;
- não publicar banco/cache/filas;
- não expor admin endpoints;
- possuir firewall/provider security group;
- aplicar TLS;
- rate limiting;
- observabilidade;
- patching.

Outras técnicas:

- private endpoints;
- private DNS / split-horizon DNS;
- VPN/ZTNA para administração;
- bastion para acesso operacional;
- egress filtering;
- mTLS entre serviços quando risco justificar;
- service identity;
- microsegmentation;
- separate management network.

Princípio:

HIDDEN
≠
SECURE

Mas:

NOT REACHABLE
<
SMALLER ATTACK SURFACE

---

5.38 Zero Trust Beyond Network Location

Estar em VLAN interna não concede confiança automática.

Decisão de acesso deve considerar:

IDENTITY
+
DEVICE
+
RESOURCE
+
ACTION
+
CONTEXT
+
POLICY

Aplicação continua executando AuthN/AuthZ mesmo quando:

- origem é LAN;
- origem é VPN;
- origem é subnet interna;
- serviço está em Docker/Kubernetes;
- comunicação ocorre entre workloads.

NETWORK LOCATION
≠
AUTHORIZATION

Para cloud-native/microservices considerar service identities e autorização service-to-service.

---

5.39 Docker Firewall Interaction

Docker pode criar regras próprias de iptables/nftables para bridge networks e portas publicadas.

Port publishing:

```text
-p 8080:80
```

sem host IP específico normalmente publica em todas as interfaces do host.

Em Linux, não assumir que:

UFW DENY
=
DOCKER PORT DENIED

porque tráfego publicado pelo Docker pode ser processado antes das chains usadas pelo UFW.

Baseline:

- evitar publicar o que não precisa;
- bind em loopback quando apenas host local precisar;
- usar firewall compatível com o backend Docker;
- revisar iptables/nftables/firewalld;
- testar externamente a reachability real;
- manter Docker atualizado;
- não desabilitar arbitrariamente o gerenciamento de firewall do Docker sem política substituta completa.

PASS exige teste de fora da VPS/rede:

EXPECTED CLOSED
+
ACTUAL CLOSED/FILTERED

---

5.40 Network Segmentation Regression Matrix

Testar explicitamente:

GUEST
→ INTERNET
ALLOW

GUEST
→ PUBLIC APP
ALLOW conforme produto

GUEST
→ ADMIN
DENY

GUEST
→ DB
DENY

GUEST
→ SSH/RDP
DENY

GUEST A
→ GUEST B
DENY quando client isolation exigido

APP
→ DB
ALLOW somente porta/protocolo necessário

DB
→ INTERNET
DENY ou egress mínimo conforme necessidade

MANAGEMENT
→ ADMIN TARGETS
ALLOW somente identidade/dispositivo autorizado

INTERNET
→ ORIGIN
DENY quando origin deve aceitar somente proxy/CDN

INTERNET
→ DB/CACHE/QUEUE
DENY

Qualquer caminho inesperado:

FAIL
→ FINDING
→ FIX
→ REGRESSION

---

⚫ COFRE MÁXIMO

- policy-as-code;
- admission control;
- immutable infrastructure;
- signed provenance;
- hardened runners;
- private registry;
- runtime detection;
- network segmentation;
- PAM;
- zero long-lived CI credentials quando viável.

---

PARTE 6 — RELIABILITY, RESILIENCE, PERFORMANCE E DISASTER RECOVERY

🟢 BÁSICO

6.1 Timeouts

Toda chamada externa deve ter timeout explícito:

- HTTP;
- DB;
- cache;
- queue;
- AI;
- storage.

Nunca deixar chamadas aguardarem indefinidamente.

---

6.2 Error Classification

Separar:

VALIDATION ERROR
AUTH ERROR
BUSINESS ERROR
TRANSIENT ERROR
DEPENDENCY ERROR
INTERNAL ERROR

---

6.3 Graceful Failure

Falha opcional não deve necessariamente derrubar fluxo crítico.

Exemplo:

ANALYTICS DOWN
≠
LOGIN DOWN

---

🟡 INTERMEDIÁRIO

6.4 Criticality Map

Classificar dependências:

CRITICAL
IMPORTANT
OPTIONAL

---

6.5 Retry

Retry somente quando semanticamente seguro.

Utilizar:

EXPONENTIAL BACKOFF
+
JITTER
+
MAX ATTEMPTS
+
RETRY BUDGET

---

6.6 Retry não deve duplicar efeitos

Operações não idempotentes exigem proteção antes de retry.

---

6.7 Idempotency

Aplicar quando necessário:

- payment;
- invoice;
- order;
- stock;
- webhook;
- import;
- financial action.

---

6.8 Circuit Breaker

Estados:

CLOSED
  ↓
OPEN
  ↓
HALF-OPEN
  ↓
CLOSED

Evitar cascata de falhas.

---

6.9 Fallback

Fallback nunca pode reduzir controle de segurança.

Proibido:

AUTH SERVICE DOWN
→ ALLOW USER

Correto:

AUTH SERVICE DOWN
→ FAIL CLOSED

para decisões de autorização.

---

6.10 Bulkheads

Isolar recursos para evitar que uma dependência consuma toda:

- thread pool;
- connection pool;
- queue;
- CPU;
- worker capacity.

---

6.11 Concurrency

Proteger contra:

- lost updates;
- duplicate submit;
- overselling;
- negative inventory;
- double billing;
- TOCTOU;
- simultaneous role changes.

Controles:

TRANSACTION
UNIQUE CONSTRAINT
OPTIMISTIC LOCK
PESSIMISTIC LOCK
ATOMIC UPDATE
IDEMPOTENCY KEY
VERSION

---

6.12 Cache Strategy

Todo cache documenta:

WHAT?
KEY?
TTL?
INVALIDATION?
TENANT?
PII?
OWNER?

---

6.13 Cache Isolation

Cache específico deve incluir contexto adequado.

Exemplo:

tenant:{tenantId}:invoice:{invoiceId}

quando necessário.

---

6.14 Cache Invalidation

Definir:

- write-through;
- write-behind;
- cache-aside;
- explicit purge;
- TTL.

Evitar estado eterno.

---

6.15 Cache Stampede

Mitigar quando aplicável:

- locking;
- request coalescing;
- jittered TTL;
- stale-while-revalidate.

---

6.16 Health

Separar:

LIVENESS
READINESS
DEPENDENCY HEALTH

Endpoint público não deve vazar detalhes internos.

---

6.17 SLI / SLO

Definir para serviços críticos:

- availability;
- latency;
- error rate;
- throughput;
- saturation.

Não prometer 100% uptime.

---

6.18 Load Testing

Testar:

EXPECTED
PEAK
BURST
SUSTAINED

Medir:

- p50;
- p95;
- p99;
- error rate;
- throughput;
- CPU;
- RAM;
- DB pool;
- queue depth.

---

6.19 Stress Testing

Determinar:

BREAKING POINT
+
FAILURE MODE
+
RECOVERY

---

6.20 Soak Testing

Avaliar longo período para detectar:

- leaks;
- connection exhaustion;
- queue growth;
- degradation.

---

6.21 RTO / RPO

Por serviço.

RTO
=
tempo máximo aceitável de recuperação

RPO
=
perda máxima aceitável de dados

Não inventar números.

Derivar do impacto de negócio.

---

6.22 BIA

Business Impact Analysis deve identificar:

- processos críticos;
- dependências;
- impacto;
- recovery priority;
- RTO;
- RPO.

NIST SP 800-34 trata BIA, recovery strategies, plano, testes e manutenção como componentes da contingency planning.

---

6.23 Backups

- automáticos;
- protegidos;
- criptografados quando necessário;
- separados;
- monitorados;
- retenção definida.

---

6.24 Restore Testing

BACKUP EXISTS
≠
RECOVERY PROVEN

PASS em restore exige teste real.

---

🔴 AVANÇADO

6.25 Disaster Recovery Plan

Documentar:

INCIDENT
 ↓
DECLARE DR
 ↓
FAILOVER / RESTORE
 ↓
VERIFY
 ↓
RESTORE TRAFFIC
 ↓
MONITOR

---

6.26 DR Plan

Incluir:

- owner;
- contacts;
- credentials;
- DNS;
- infrastructure;
- databases;
- storage;
- providers;
- recovery order;
- verification;
- rollback;
- communication.

---

6.27 Chaos Engineering

Somente controlado.

Testes possíveis:

DB DOWN
CACHE DOWN
API DOWN
LATENCY
PACKET LOSS
QUEUE FAILURE
INSTANCE LOSS
DISK FULL
CERT FAILURE

Requer:

- blast radius;
- stop condition;
- monitoring;
- recovery plan.


---

6.28 Release Safety

Para mudanças de risco:

- canary;
- blue/green;
- staged rollout;
- feature flag;
- kill switch;
- automatic rollback criteria;
- observability before full rollout.

DEPLOY SUCCESS
≠
RELEASE HEALTHY

---

6.29 Database Migration Safety

Preferir:

EXPAND
  ↓
MIGRATE
  ↓
VERIFY
  ↓
CONTRACT

Para migrations críticas:

- backup/restore path;
- lock impact;
- execution time;
- rollback ou roll-forward;
- backward compatibility;
- data validation;
- failure recovery.

---

6.30 Queue Safety

Filas devem considerar:

- idempotency;
- retry budget;
- DLQ;
- poison message;
- max attempts;
- ordering;
- deduplication;
- tenant context;
- message size;
- schema/version;
- replay safety.

---

6.31 Feature Flags

Flags críticas devem possuir:

- owner;- default seguro;
- environment scope;
- audit;
- expiry/removal plan;
- fail-safe behavior.

Feature flag não substitui AuthZ.

---

6.32 Error Budget

Para serviços com SLO:

ERROR BUDGET CONSUMED
→ REDUCE CHANGE RISK

Usar error budget como sinal de confiabilidade, não como licença para ignorar incidentes de segurança.

---

⚫ COFRE MÁXIMO

- multi-region quando business case exigir;
- automated failover;
- immutable/offline backups;
- DR exercises;
- dependency fault injection;
- capacity models;
- recovery automation.

---

PARTE 7 — LOGGING, AUDIT, DETECTION E INCIDENT RESPONSE

🟢 BÁSICO

7.1 Security Logging

Registrar:

- login;
- logout;
- failure;
- reset;
- admin actions;
- critical errors.

Nunca logar secrets.

---

7.2 Safe Errors

Cliente:

SAFE MESSAGE

Servidor:

DIAGNOSTIC CONTEXT

Nunca expor:

- stack;
- SQL;
- filesystem;
- credentials;
- internal URLs;
- tokens.

---

🟡 INTERMEDIÁRIO

7.3 Structured Logs

Exemplo:

{
  "timestamp": "...",
  "level": "WARN",
  "requestId": "...",
  "userId": "...",
  "tenantId": "...",
  "action": "...",
  "resource": "...",
  "result": "DENIED"
}

---

7.4 Correlation

Utilizar:

- request ID;
- trace ID;
- span ID quando tracing existir.

---

7.5 Audit Trail

Eventos relevantes:

- permission change;
- owner change;
- data export;
- financial action;
- impersonation;
- security setting;
- delete;
- admin actions.

---

7.6 Audit Event Schema

WHO
WHEN
TENANT
ACTION
RESOURCE
RESULT
SOURCE
REQUEST_ID

Quando necessário:

BEFORE
AFTER

com redaction.

---

7.7 Tamper Evidence

"append-only JSON" sozinho não garante integridade.

Em maior risco:

- remote log sink;
- immutable storage;
- restricted delete;
- WORM;
- hash chaining;
- digital signature;
- independent retention controls.

---

7.8 Alerts

Alertar:

- ATO;
- brute force;
- password spray;
- credential stuffing;
- privilege escalation;
- tenant violation;
- new admin;
- MFA removal;
- anomalous exports;
- secret leak;
- critical CVE;
- high 5xx;
- session anomalies.

---

🔴 AVANÇADO

7.9 SIEM

Quando escala justificar:

- Wazuh;
- Elastic Security;
- Splunk;
- equivalente.

---

7.10 Detection Engineering

THREAT
LOG SOURCE
DETECTION
ALERT
RUNBOOK
OWNER
TEST

---

7.11 Incident Response

Fluxo:

DETECT
 ↓
TRIAGE
 ↓
CONTAIN
 ↓
ERADICATE
 ↓
RECOVER
 ↓
LEARN

NIST SP 800-61 Rev. 3 integra essas capacidades ao gerenciamento contínuo de risco.

---

7.12 Severity

SEV-1 CRITICAL
SEV-2 HIGH
SEV-3 MODERATE
SEV-4 INFORMATIONAL

---

7.13 SEV-1 Runbook

- declare;
- timestamp;
- incident commander;
- preserve evidence;
- contain;
- rotate credentials;
- identify vector;
- identify data;
- fix;
- recover;
- monitor;
- legal/privacy assessment;
- RCA.

---

7.14 Evidence Preservation

Preservar:

- logs;
- traces;
- requests;
- hashes;
- snapshots;
- commits;
- artifacts;
- configs;
- deploy IDs.

---

7.15 RCA

Perguntar:

WHAT HAPPENED?
WHY?
WHICH CONTROL FAILED?
WHY DID TESTING MISS IT?
WHY DID DETECTION MISS IT?
HOW DO WE PREVENT RECURRENCE?

Não encerrar em:

HUMAN ERROR

sem causa sistêmica.

---

7.16 Pentest

Periodicidade baseada em risco e mudanças relevantes.

Acionar após:

- nova auth;
- novo tenant model;
- pagamentos;
- grande arquitetura;
- incidente;
- exposição relevante.

---

7.17 DAST

Usar onde útil.

Exemplo:

OWASP ZAP

Não substitui review ou business logic testing.


---

7.18 Detection Validation

ALERT CONFIGURED
≠
DETECTION PROVEN

Testar detections com eventos controlados.

Registrar:

- test case;
- expected alert;
- actual alert;
- latency;
- routing;
- owner response.

---

7.19 Log Privacy / Redaction

Logs devem minimizar:

- passwords;
- tokens;
- session IDs reutilizáveis;
- authorization headers;
- card data;
- sensitive PII;
- prompt secrets;
- raw documents.

Quando identificadores pessoais forem necessários, considerar pseudonimização/tokenização.

---

7.20 Incident Communications

Runbook deve definir:

- technical channel;
- executive escalation;
- legal/privacy;
- customer communication;
- regulator communication;
- status cadence;
- approval authority.

Não especular externamente antes de fatos mínimos verificados.

---

⚫ COFRE MÁXIMO

- SOC;
- EDR;
- UEBA;
- threat intelligence;
- immutable logs;
- forensic readiness;
- threat hunting;
- Red Team;
- Purple Team;
- bug bounty;
- crisis exercises.

---

PARTE 8 — TESTING, QUALITY ENGINEERING E ACCESSIBILITY

🟢 BÁSICO

8.1 Test Pyramid

O projeto deve combinar:

STATIC
+
UNIT
+
INTEGRATION
+
E2E
+
SECURITY

---

8.2 Unit Tests

Cobrir:

- business rules;
- validation;
- permission logic;
- calculations;
- edge cases.

---

8.3 Integration Tests

Cobrir:

- DB;
- cache;
- storage;
- queues;
- auth;
- third parties.

---

8.4 E2E

Jornadas críticas:

REGISTER
LOGIN
RECOVERY
MAIN BUSINESS FLOW
ADMIN
LOGOUT

---

8.5 Negative Testing

Obrigatório.

Exemplos:

UNAUTHORIZED
FORBIDDEN
INVALID
EXPIRED
CROSS-TENANT
DUPLICATE
OUT-OF-RANGE

---

🟡 INTERMEDIÁRIO

8.6 Regression Tests

Bug ou vulnerabilidade corrigida:

BUG
 ↓
FIX
 ↓
REGRESSION TEST
 ↓
CI

Sempre que tecnicamente viável.

---

8.7 Coverage Gates

Não usar:

80% = QUALITY

como dogma.

Definir thresholds baseados em criticidade.

Código crítico:

- authentication;
- authorization;
- tenant isolation;
- payments;
- accounting;
- inventory integrity;

deve possuir cobertura forte.

---

8.8 Differential Coverage

Alterações novas não devem reduzir qualidade sem justificativa.

Avaliar coverage de linhas alteradas.

---

8.9 Branch Coverage

Para lógica crítica, branch coverage costuma ser mais informativo que somente line coverage.

---

8.10 Contract Tests

Quando houver serviços/API consumidores:

- request schemas;
- response schemas;
- compatibility;
- versioning.

---

8.11 Flaky Tests

Não simplesmente reexecutar até passar.

Flaky test é dívida técnica.

---

8.12 Static Gates

CI:

LINT
TYPECHECK
SAST
SECRET SCAN

---

8.13 Code Review Standard

PR crítica exige:

CORRECTNESS
SECURITY
DATA
CONCURRENCY
ERRORS
PERFORMANCE
TESTS
ACCESSIBILITY
OBSERVABILITY

---

8.14 Accessibility Baseline

WCAG 2.2 AA

W3C recomenda WCAG 2.2 para maior aplicabilidade futura.

---

8.15 Accessibility Tests

Testar:

- keyboard navigation;
- focus;
- focus order;
- focus not obscured;
- contrast;
- semantic HTML;
- headings;
- labels;
- errors;
- accessible names;
- screen reader;
- responsive reflow;
- zoom;
- target size;
- reduced motion;
- status messages.

WCAG 2.2 adiciona inclusive Focus Not Obscured, Target Size e Accessible Authentication.

---

8.16 Accessible Authentication

CAPTCHA ou login não deve criar barreira cognitiva sem alternativa apropriada.

Isso deve ser considerado junto ao anti-bot.

---

8.17 Automation não basta

Automated accessibility scanner:

≠
WCAG CONFORMANCE PROVEN

Combinar automação com testes manuais.

---

🔴 AVANÇADO

8.18 Performance Regression

Adicionar baseline para:

- API latency;
- DB query latency;
- bundle size;
- memory;
- throughput.

---

8.19 Load Tests no CI/CD

Não precisam rodar em todo commit.

Executar conforme:

- release;
- arquitetura;
- performance-sensitive change.

---

8.20 Security Regression Suite

Manter testes para vulnerabilidades históricas.

---

8.21 Mutation Testing

Avaliar para lógica crítica.

Ajuda a identificar testes que executam código sem realmente verificar comportamento.

---

8.22 Property-Based Testing

Aplicável para:

- parsers;
- calculations;
- business invariants;
- validation;
- serialization.

---

8.23 Fuzzing

Utilizar para superfícies de alto risco:

- parsers;
- file processing;
- protocol handlers;
- APIs complexas.


---

8.24 Control-to-Test Traceability

Controle crítico deve apontar para teste verificável.

CONTROL
→ TEST ID
→ CI RUN
→ RESULT
→ EVIDENCE

Isso evita PASS baseado apenas em documentação.

---

8.25 Test Environment Fidelity

Diferenças entre staging e produção devem ser conhecidas.

Mapear:

- auth provider;
- network;
- proxy;
- TLS;
- DB engine/version;
- storage;
- cache;
- queues;
- feature flags;
- secrets mechanism.

STAGING PASS
≠
PRODUCTION PROVEN

quando diferenças materiais alteram o comportamento do controle.

---

8.26 Migration Tests

Testar quando relevante:

- forward migration;
- rollback/roll-forward;
- old app + new schema;
- new app + transitional schema;
- constraints;
- data conversion;
- large dataset behavior.

---

⚫ COFRE MÁXIMO

- continuous performance baselines;
- advanced fault injection;
- formal security regression suites;
- accessibility testing matrix;
- device/browser compatibility;
- adversarial testing;
- release qualification.

---

PARTE 9 — AI, RAG, AGENTS E MCP

OWASP publicou o GenAI LLM Top 10 2026, o Top 10 for Agentic Applications 2026, o MCP Top 10 e orientação prática para desenvolvimento seguro de servidores MCP.

---

🟢 BÁSICO

9.1 AI-generated Code

Nunca:

AI GENERATED
→ DIRECT PRODUCTION

Obrigatório:

AI
 ↓
HUMAN REVIEW
 ↓
TEST
 ↓
SECURITY
 ↓
PR

---

9.2 Secrets

Nunca enviar a modelo externo:

- prod ".env";
- private keys;
- DB passwords;
- customer secrets;
- tokens reais;
- sensitive dumps.

---

9.3 Dependency Hallucination

Pacote sugerido por IA:

VERIFY REGISTRY
VERIFY OWNER
VERIFY REPO
VERIFY SECURITY

antes de instalar.

---

🟡 INTERMEDIÁRIO

9.4 Prompt Injection

Todo conteúdo externo:

UNTRUSTED

Inclui:

- user;
- page;
- PDF;
- mail;
- RAG;
- search;
- database;
- MCP;
- tool response.

---

9.5 Instruction Boundaries

Separar:

SYSTEM
DEVELOPER
TOOL
USER
EXTERNAL DATA

---

9.6 Output Validation

LLM output continua não confiável antes de:

- executar shell;
- SQL;
- HTML;
- API call;
- e-mail;
- DB change;
- file write.

---

9.7 Tool Least Privilege

Separar:

READ
WRITE
DELETE
EXECUTE
ADMIN

---

9.8 Human Approval

Obrigatório para alto impacto:

- money;
- delete;
- admin;
- ownership;
- production deploy;
- secrets;
- mass communication;
- destructive command.

---

9.9 RAG Security

- source authorization;
- tenant filter;
- provenance;
- poisoning defenses;
- output validation;
- document ACLs.

Nunca recuperar documento de outro tenant.

---

🔴 AVANÇADO

9.10 Agent Identity

AGENT ID
+
SCOPED TOKEN
+
TENANT
+
SHORT TTL

Nunca:

AGENT = GLOBAL ADMIN

---

9.11 Delegation Chain

Registrar:

USER
 ↓
AGENT
 ↓
TOOL
 ↓
ACTION

---

9.12 Memory

Memória persistente deve ter:

- source;
- author;
- timestamp;
- tenant;
- scope;
- integrity;
- deletion.

---

9.13 Memory Poisoning

Conteúdo externo nunca deve automaticamente tornar-se política confiável.

---

9.14 MCP

MCP é trust boundary.

Servidor MCP:

- AuthN;
- AuthZ;
- schema;
- validation;
- output validation;
- rate limit;
- session isolation;
- logging;
- least privilege.

A orientação OWASP de 2026 enfatiza autenticação/autorização, validação rigorosa, isolamento de sessão e deployment hardened.

---

9.15 Third-Party MCP

Antes de conectar:

- owner;
- source;
- tools;
- scopes;
- filesystem;
- network;
- secrets;
- update mechanism;
- reputation/history.

---

9.16 MCP Filesystem

ALLOW-LIST

Não liberar raiz inteira sem necessidade.

---

9.17 MCP Shell

OFF BY DEFAULT

Quando necessário:

- sandbox;
- allow-list;
- approval;
- timeout;
- logging;
- limited network;
- limited filesystem.

---

9.18 MCP Network

Não conceder automaticamente:

- localhost;
- LAN;
- cloud metadata;
- DB;
- internal APIs;
- full internet.

---
9.19 Confused Deputy

Validar:

WHO REQUESTED?
WHO AUTHORIZED?
WHICH AGENT?
WHICH TENANT?
WHICH RESOURCE?
WHICH ACTION?

---

9.20 AI Inventory

Inventariar:

- provider;
- model;
- version;
- prompt;
- embeddings;
- vector DB;
- tools;
- agents;
- MCP;
- datasets.

---

9.21 AI Red Team

Testar:

- direct injection;
- indirect injection;
- data exfiltration;
- prompt leakage;
- tool abuse;
- cross-tenant RAG;
- memory poisoning;
- resource exhaustion;
- agent loops;
- privilege escalation.


---

9.22 OWASP GenAI 2026 Baseline

Threat model deve considerar conforme aplicabilidade:

- prompt injection;
- sensitive information disclosure;
- supply-chain risk;
- data/model poisoning;
- improper output handling;
- excessive agency;
- vector/embedding weaknesses;
- misinformation/integrity impact;
- unbounded consumption;
- agent/tool misuse.

Não usar lista Top 10 como substituto de threat modeling.

---

9.23 Agentic Threats

Testar explicitamente:

GOAL HIJACK
TOOL MISUSE
IDENTITY / PRIVILEGE ABUSE
MEMORY POISONING
INTER-AGENT TRUST FAILURE
RESOURCE EXHAUSTION
CASCADE FAILURE
UNEXPECTED AUTONOMY

Toda decisão de alto impacto deve possuir boundary de autorização fora do LLM.

---

9.24 Tool Poisoning / Rug Pull

Tool metadata, descriptions e schemas são entrada não confiável.

Antes de confiar:

- source;
- publisher;
- version;
- hash/signature quando disponível;
- permissions;
- behavior;
- update channel.

Mudança silenciosa de tool/plugin/MCP exige reavaliação.

---

9.25 Authorization per Tool / Resource

AUTORIZAR AGENTE
≠
AUTORIZAR TODA TOOL

Cada chamada deve considerar:

WHO
AGENT
TENANT
TOOL
RESOURCE
ACTION
SCOPE
RISK

---

9.26 Agent Budgets

Definir limites:

- steps;
- tokens;
- tool calls;
- money;
- wall-clock time;
- retries;
- recursion depth;
- spawned agents.

Loop sem limite é reliability e security risk.

---

9.27 Kill Switch

Agente de alto impacto deve possuir mecanismo para:

STOP
REVOKE
ISOLATE
DISABLE TOOL
DISABLE EGRESS

Kill switch deve ser testado.

---

9.28 MCP Session / Context Isolation

Nunca compartilhar estado entre usuários/tenants sem desenho explícito.

Isolar:

- session;
- auth context;
- tool results;
- filesystem;
- memory;
- caches;
- temporary files.

---

9.29 MCP OAuth / Scope Discipline

Quando MCP usar OAuth/OIDC:

- authorization code + PKCE quando aplicável;
- audience/resource validation;
- scopes mínimos;
- token expiry;
- revocation;
- no token forwarding indiscriminado;
- per-tool/per-resource authorization.

---

9.30 AI Data Egress

Antes de enviar dados a provider/model/tool:

CLASSIFY
  ↓
MINIMIZE
  ↓
AUTHORIZE
  ↓
REDACT
  ↓
SEND

Controlar:

- prompt;
- attachments;
- RAG context;
- tool output;
- memory;
- logs.

---

9.31 Model / Provider Change Management

Trocar modelo/provider pode alterar:

- security behavior;
- tool calling;
- output format;
- latency;
- refusal behavior;
- data handling;
- retention;
- region;
- compliance.

Mudança material exige regressão e revalidação.

---

⚫ COFRE MÁXIMO

- strong sandbox;
- policy engine;
- agent kill switch;
- egress control;
- per-tool AuthZ;
- signed/verified components quando possível;
- anomaly detection;
- adversarial testing;
- AI incident response;
- AI governance.

---

10. TEST MATRIX

Authentication

- [ ] nonexistent user;
- [ ] wrong password;
- [ ] expired session;
- [ ] invalid token;
- [ ] logout;
- [ ] reset replay;
- [ ] MFA bypass.

Authorization

- [ ] horizontal escalation;
- [ ] vertical escalation;
- [ ] IDOR/BOLA;
- [ ] tenant escape;
- [ ] property authorization.

Injection

- [ ] SQLi;
- [ ] NoSQLi;
- [ ] XSS;
- [ ] command injection;
- [ ] template injection.

Protocol

- [ ] CSRF;
- [ ] SSRF;
- [ ] traversal;
- [ ] redirect;
- [ ] upload bypass;
- [ ] unsigned/invalid webhook;
- [ ] exposed `.env`/config;
- [ ] exposed source maps;
- [ ] header attacks.

Anti-Abuse

- [ ] IP rotation;
- [ ] ASN rotation;
- [ ] low-and-slow;
- [ ] password spraying;
- [ ] credential stuffing;
- [ ] challenge replay;
- [ ] bot automation.

Business

- [ ] negative;
- [ ] zero;
- [ ] max;
- [ ] overflow;
- [ ] duplicate;
- [ ] replay;
- [ ] race;
- [ ] client-side price tampering;
- [ ] client-side discount/tax tampering;
- [ ] forged payment success;
- [ ] server-side total recomputation.

Reliability

- [ ] dependency timeout;
- [ ] retry;
- [ ] circuit breaker;
- [ ] cache failure;
- [ ] DB failure;
- [ ] recovery.

Accessibility

- [ ] keyboard;
- [ ] focus;
- [ ] screen reader;
- [ ] forms;
- [ ] contrast;
- [ ] authentication.

AI/MCP

- [ ] prompt injection;
- [ ] indirect injection;
- [ ] tool abuse;
- [ ] tool poisoning;
- [ ] rug pull/update change;
- [ ] excessive agency;
- [ ] tenant leak;
- [ ] cross-tenant RAG;
- [ ] filesystem;
- [ ] network;
- [ ] memory poisoning;
- [ ] session/context isolation;
- [ ] agent budget exhaustion;
- [ ] kill switch;
- [ ] per-tool/per-resource AuthZ.

---

11. CANONICAL CI/CD PIPELINE

LOCAL / PRE-COMMIT
   │
SECRET SCAN
   │
ENV/CONFIG EXPOSURE CHECK
   │
SOURCE MAP POLICY CHECK
   │
COMMIT
   │
   ▼
LINT
   │
TYPECHECK
   │
UNIT TESTS
   │
SECRET SCAN
   │
SAST
   │
SCA
   │
BUILD
   │
SBOM
   │
PROVENANCE / ATTESTATION
   │
SIGN / VERIFY WHEN APPLICABLE
   │
CONTAINER / IaC SCAN
   │
INTEGRATION TESTS
   │
CONTRACT TESTS
   │
STAGING
   │
E2E
   │
DAST / API SECURITY
   │
AUTHORIZATION REGRESSION
   │
ACCESSIBILITY
   │
PERFORMANCE CHECK
   │
SECURITY GATE
   │
QUALITY GATE
   │
RELIABILITY GATE
   │
PRIVACY / COMPLIANCE GATE WHEN APPLICABLE
   │
ARTIFACT / PROVENANCE VERIFY
   │
PRODUCTION
   │
POST-DEPLOY VERIFY

Nem todos os testes caros precisam rodar em cada commit.

Eles devem ser posicionados conforme custo e risco.

---

11.1 Security Checks as Gates

Checklist informa.

Gate impede avanço.

Para controles automatizáveis:

CHECK
→ EXPECTED RESULT
→ FAIL CONDITION
→ CI/PRE-COMMIT
→ EVIDENCE

Exemplos:

SECRET FOUND
→ FAIL

PUBLIC `.env`
→ FAIL

UNSIGNED REQUIRED WEBHOOK
→ FAIL

SOURCE MAP PUBLIC WHEN POLICY=PRIVATE
→ FAIL

AUTHZ REGRESSION
→ FAIL

CROSS-TENANT ACCESS
→ FAIL

PAYMENT TOTAL TRUSTS CLIENT
→ FAIL

DEFAULT CREDENTIAL
→ FAIL

UNKNOWN em controle crítico:
→ FAIL RELEASE / REQUIRE REVIEW

Automação não substitui análise humana de business logic, AuthZ e architecture.

---

12. CANONICAL GATE v13.3

GOVERNANCE               PASS/FAIL/UNKNOWN
ARCHITECTURE              PASS/FAIL
THREAT MODEL              PASS/FAIL
ADRs                      PASS/FAIL/N/A

INPUT VALIDATION          PASS/FAIL
INJECTION                 PASS/FAIL
AUTHENTICATION            PASS/FAIL
AUTHORIZATION             PASS/FAIL
ROLES/PERMISSIONS         PASS/FAIL
TENANT ISOLATION          PASS/FAIL/N/A
RLS                       PASS/FAIL/N/A

SESSION LIFECYCLE         PASS/FAIL
MFA                       PASS/FAIL/N/A
ANTI-ABUSE                PASS/FAIL
CAPTCHA/CHALLENGE         PASS/FAIL/N/A
ATO                       PASS/FAIL/N/A

SECRETS                   PASS/FAIL
GIT HISTORY               PASS/FAIL
TLS                       PASS/FAIL
CERT LIFECYCLE            PASS/FAIL
ENCRYPTION                PASS/FAIL/N/A

API MINIMIZATION          PASS/FAIL
CORS                      PASS/FAIL
CSRF                      PASS/FAIL/N/A
UPLOAD                    PASS/FAIL/N/A
SSRF                      PASS/FAIL/N/A
WEBHOOK                   PASS/FAIL/N/A
WEBHOOK SIGNATURE         PASS/FAIL/N/A
WEBSOCKET                 PASS/FAIL/N/A
SOURCE MAP EXPOSURE       PASS/FAIL/N/A
ENV/CONFIG EXPOSURE       PASS/FAIL
PAYMENT SERVER AUTHORITY  PASS/FAIL/N/A

DEPENDENCIES              PASS/FAIL
SBOM                      PASS/FAIL/N/A
SUPPLY CHAIN              PASS/FAIL
CI/CD                     PASS/FAIL

ERROR HANDLING            PASS/FAIL
RETRY                     PASS/FAIL/N/A
IDEMPOTENCY               PASS/FAIL/N/A
CIRCUIT BREAKER           PASS/FAIL/N/A
CONCURRENCY               PASS/FAIL
CACHE                     PASS/FAIL/N/A

LOAD/STRESS               PASS/FAIL/N/A
RTO/RPO                   PASS/FAIL
BACKUP                    PASS/FAIL
RESTORE                   PASS/FAIL/UNKNOWN
DR PLAN                   PASS/FAIL
CHAOS                     PASS/FAIL/N/A

LOGGING                   PASS/FAIL
AUDIT TRAIL               PASS/FAIL
TAMPER EVIDENCE           PASS/FAIL/N/A
ALERTING                  PASS/FAIL
INCIDENT RESPONSE         PASS/FAIL

UNIT TESTS                PASS/FAIL
INTEGRATION TESTS         PASS/FAIL
E2E                       PASS/FAIL
REGRESSION                PASS/FAIL
COVERAGE GATE             PASS/FAIL
CODE REVIEW               PASS/FAIL

ACCESSIBILITY             PASS/FAIL

LGPD                      PASS/FAIL/N/A
GDPR                      PASS/FAIL/N/A
HIPAA                     PASS/FAIL/N/A
PCI DSS                   PASS/FAIL/N/A

TERMS                     PASS/FAIL/PENDING LEGAL
PRIVACY POLICY            PASS/FAIL/PENDING LEGAL

AI/RAG                    PASS/FAIL/N/A
AGENTS                    PASS/FAIL/N/A
MCP                       PASS/FAIL/N/A

LINT                      PASS/FAIL
TYPECHECK                 PASS/FAIL
TEST                      PASS/FAIL
BUILD                     PASS/FAIL


---

12.1 RELEASE GATE v13.3

Uma release não recebe READY apenas porque o SECURITY GATE passou.

SECURITY GATE
- access control;
- AuthN/AuthZ;
- tenant isolation;
- injection;
- secrets;
- supply chain;
- critical vulnerabilities;
- AI/MCP when applicable.

QUALITY GATE
- lint/typecheck;
- tests;
- regression;
- code review;
- build;
- accessibility baseline.

RELIABILITY GATE
- timeouts;
- retries/idempotency;
- migrations;
- backup/restore;
- health;
- SLO impact;
- rollback;
- critical dependency behavior.

PRIVACY / COMPLIANCE GATE
- LGPD/privacy;
- retention;
- data minimization;
- legal artifacts;
- PCI/GDPR/HIPAA when applicable.

FINAL:

READY
=
ALL APPLICABLE GATES PASS
+
NO BLOCKER
+
ARTIFACT VERIFIED
+
RESIDUAL RISK ACCEPTED WHEN NECESSARY

UNKNOWN em controle crítico impede READY.

---

13. EVIDENCE RULES

AUTHORIZATION PASS
=
SERVER CONTROL
+
NEGATIVE TEST

TENANT PASS
=
ISOLATION IMPLEMENTATION
+
CROSS-TENANT TEST

RLS PASS
=
POLICY
+
MIGRATION
+
TEST

RATE LIMIT PASS
=
IMPLEMENTATION
+
OBSERVED ENFORCEMENT

BUILD PASS
=
COMMAND EXECUTED
+
EXIT CODE 0

RESTORE PASS
=
RESTORE ACTUALLY PERFORMED

ACCESSIBILITY PASS
≠
ONLY AXE/LIGHTHOUSE PASSED


EVIDENCE FRESHNESS

PASS exige evidência aplicável à release avaliada.

Preferir vínculo com:

COMMIT SHA
+
ARTIFACT DIGEST
+
ENVIRONMENT
+
TEST RUN
+
TIMESTAMP

STALE EVIDENCE
→ UNKNOWN / REVALIDATE


---

14. SECURITY_AUDIT.md

Toda auditoria completa deve produzir:

SECURITY_AUDIT.md

Estrutura:

1. Executive Summary;
2. Scope;
3. Detected Stack;
4. Architecture;
5. Threat Model;
6. Data Classification;
7. Findings;
8. Severity Matrix;
9. AuthN;
10. AuthZ;
11. Multi-Tenancy;
12. Anti-Abuse;
13. Web/API;
14. Database/RLS;
15. Privacy;
16. Secrets;
17. Git History;
18. Cloud;
19. Supply Chain;
20. Reliability;
21. Cache;
22. Performance;
23. DR;
24. Logging;
25. Incident Response;
26. Testing;
27. Accessibility;
28. AI/MCP;
29. Legal;
30. Gate;
31. Commands;
32. Evidence;
33. External Actions;
34. Residual Risks;
35. Standard Mappings;
36. Artifact/Provenance;
37. Release Gate Decision;
38. Limitations / Unknowns.

---

15. FINDING FORMAT

ID:
SEC-XXX

SEVERITY:
CRITICAL / HIGH / MEDIUM / LOW / INFO

PRIORITY:
P0 / P1 / P2 / P3

DOMAIN:
...


STANDARD_MAPPING:
ASVS / OWASP / NIST / PCI / WCAG / GENAI / MCP / OTHER

ASSET:
...

ATTACK_PATH:
...

CWE/CVE:
...

CVSS:
...

KEV:
YES / NO / N/A

EPSS:
...

CONTROL_ID:
...


FILE:
...

LINE:
...

PROBLEM:
...

IMPACT:
...

EVIDENCE:
...

EXPLOITABILITY:
...

FIX:
...

TEST:
...

OWNER:
...

STATUS:
OPEN / FIXED / MITIGATED / ACCEPTED

---

16. EXTERNAL ACTIONS

Nunca marcar como concluído sem execução.

Exemplos:

[ ] ROTATE PROVIDER SECRET

[ ] ENABLE BRANCH PROTECTION

[ ] CONFIGURE DNS

[ ] ENABLE TLS

[ ] EXECUTE REAL RESTORE

[ ] LEGAL REVIEW

[ ] ENABLE MFA IN CLOUD CONSOLE

---

17. REPOSITORY EXECUTION ORDER

1. INSPECT
2. DETECT STACK
3. MAP ARCHITECTURE
4. MAP DATA
5. MAP TRUST BOUNDARIES
6. THREAT MODEL
7. SECRET SCAN
8. GIT HISTORY SCAN
9. FINDINGS
10. CLASSIFY
11. FIX P0
12. FIX P1
13. FIX P2
14. FIX RELEVANT P3
15. ADD TESTS
16. ADD REGRESSIONS
17. RUN STATIC ANALYSIS
18. RUN SECURITY SCANS
19. RUN LINT
20. RUN TYPECHECK
21. RUN UNIT
22. RUN INTEGRATION
23. RUN E2E
24. BUILD
25. PERFORMANCE/RESILIENCE CHECKS
26. ACCESSIBILITY CHECKS
27. REVIEW DIFF
28. VERIFY ARTIFACT / PROVENANCE
29. SECURITY GATE
30. QUALITY GATE
31. RELIABILITY GATE
32. PRIVACY/COMPLIANCE GATE WHEN APPLICABLE
33. POST-DEPLOY / RELEASE CHECK PLAN
34. SECURITY_AUDIT.md
35. FINAL AUDIT

---

18. AGENT RULES

Agent executando este protocolo deve:

- descobrir stack antes de alterar;
- preservar arquitetura quando adequada;
- alterar o mínimo necessário;
- testar depois;
- não falsificar resultado;
- não revelar segredo;
- não inventar compliance;
- não destruir histórico Git automaticamente;
- não atacar terceiros;
- não fazer pentest destrutivo em produção;
- não enfraquecer controle para fazer teste passar;
- não marcar PASS com evidência de release diferente;
- não instalar dependência sugerida por IA sem verificação;
- não ampliar scope/token/tool permission para contornar falha;
- não executar ação destrutiva sem autorização apropriada;
- preservar rastreabilidade entre source, build, artifact e deploy.

---

19. NEW THREAT WORKFLOW

Toda nova vulnerabilidade ou defesa:

DISCOVER
 ↓
VERIFY SOURCE / REPRODUCIBILITY
 ↓
CLASSIFY
 ↓
MAP DOMAIN
 ↓
DESIGN CONTROL
 ↓
IMPLEMENT
 ↓
CREATE TEST
 ↓
ADD REGRESSION
 ↓
UPDATE PROTOCOL

---

20. EXCEPTION PROCESS

CONTROL:
...

REASON:
...

RISK:
...

COMPENSATING CONTROL:
...

OWNER:
...

EXPIRY:
...

APPROVAL:
...

Exceção sem expiração vira dívida permanente.

---

21. PRINCÍPIOS CANÔNICOS

DEFAULT DENY

LEAST PRIVILEGE

DEFENSE IN DEPTH

SECURE BY DESIGN

SECURE BY DEFAULT

FAIL SECURE

ASSUME BREACH

VERIFY EXPLICITLY

MINIMIZE DATA

MINIMIZE ATTACK SURFACE

SERVER IS AUTHORITY

CLIENT INPUT IS UNTRUSTED

TENANT INPUT IS UNTRUSTED

EXTERNAL DATA IS UNTRUSTED

AI OUTPUT IS UNTRUSTED

IDENTITY ≠ AUTHORIZATION

UUID ≠ ACCESS CONTROL

JWT ≠ AUTHORIZATION

FINGERPRINT ≠ IDENTITY

CAPTCHA ≠ AUTHENTICATION

IP ≠ USER

CORS ≠ AUTHORIZATION

WAF ≠ FIX

CACHE ≠ SOURCE OF TRUTH

RETRY ≠ ALWAYS SAFE

BACKUP ≠ RECOVERY UNTIL TESTED

COVERAGE ≠ QUALITY

SCANNER PASS ≠ SECURE

CODE ≠ CONTROL UNTIL VERIFIED

DOCUMENTATION ≠ IMPLEMENTATION

COMPLIANCE ≠ SECURITY

CVSS ≠ PRIORITY

ATTESTATION ≠ VERIFICATION

STAGING PASS ≠ PRODUCTION PROVEN
DEPLOY SUCCESS ≠ RELEASE HEALTHY

AGENT ≠ AUTHORITY

TOOL DESCRIPTION ≠ TRUST

MISSING CONFIG ≠ PERMISSION TO FAIL OPEN

DB PASSWORD ≠ NETWORK PERIMETER

PUBLISHED PORT ≠ REQUIRED CONNECTIVITY

FRONTEND VALUE ≠ BUSINESS AUTHORITY

PAYMENT UI ≠ PAYMENT CONFIRMATION

WEBHOOK URL ≠ WEBHOOK AUTHENTICATION

SOURCE MAP ≠ HARMLESS BY DEFAULT

DEFAULT CREDENTIAL ≠ SAFE DEVELOPMENT SHORTCUT

SUBNET ≠ SECURITY BOUNDARY

VLAN ≠ AUTHORIZATION

VPN ≠ TRUST

HIDDEN ≠ SECURE

PRIVATE NETWORK ≠ AUTHORIZATION

MEMORY ≠ POLICY

SECURITY ≠ RELIABILITY

BUT PRODUCTION REQUIRES BOTH

---

22. GATILHO

Ao receber:

SEGURANÇA

aplicar:

PROTOCOLO SEGURANÇA v13

e, havendo acesso ao repositório:

INSPECT
→ FIND
→ FIX
→ TEST
→ VERIFY
→ DOCUMENT

Não parar apenas em recomendações quando correções puderem ser executadas.

---

23. MATURIDADE FINAL

🟢 BÁSICO

NO OBVIOUS FAILURES

🟡 INTERMEDIÁRIO

PRODUCTION DEFENSIBLE

🔴 AVANÇADO

RESILIENT AGAINST
REAL ATTACKS
AND REAL FAILURES

⚫ COFRE MÁXIMO

PREVENT
DETECT
CONTAIN
RECOVER
PROVE
ADAPT

---

24. EQUAÇÃO FINAL

PRODUCTION READINESS
=
SECURITY
+
CORRECTNESS
+
RELIABILITY
+
RESILIENCE
+
PERFORMANCE
+
PRIVACY
+
ACCESSIBILITY
+
OBSERVABILITY
+
TESTABILITY
+
RECOVERABILITY
+
DOCUMENTATION
+
SUPPLY CHAIN INTEGRITY
+
GOVERNANCE
+
CONTINUOUS IMPROVEMENT


---

25. TOOLING — INSECURE DEFAULTS / TRAIL OF BITS

Requisito:

- Codex CLI;
- repositório próprio ou explicitamente autorizado.

Marketplace:

```bash
codex plugin marketplace add trailofbits/skills
codex plugin list
codex plugin add insecure-defaults@trailofbits
```

Executar no chat Codex:

```text
/insecure-defaults:audit
```

Escopo específico:

```text
/insecure-defaults:audit src/
```

Ou arquivo:

```text
/insecure-defaults:audit src/config/app.py
```

Resultado esperado por finding:

- categoria;
- arquivo/linha;
- default alcançável;
- valor inseguro realmente ativo;
- security sink;
- reachability;
- severidade;
- correção;
- coverage gap quando houver.

Regra de validação para autenticação:

SEM `REQUIRE_AUTH`
→ APLICAÇÃO DEVE FALHAR FECHADA

Aceitável:

STARTUP FAIL

ou

AUTH CONTINUA REQUIRED

Não aceitável:

AUTH DISABLED BY DEFAULT

O plugin deve complementar, não substituir:

- secret scan;
- Semgrep;
- SAST;
- SCA;
- review manual;
- testes negativos.

---

26. REFERÊNCIAS VERIFICADAS — 09/09/2026

Aplicação:
- OWASP Top 10:2025 — versão atual;
- OWASP ASVS 5.0.0 — latest stable;
- OWASP API Security Top 10:2023.

Identidade:
- NIST SP 800-63-4 — final, julho de 2025;
- NIST SP 800-63B-4 — final, julho de 2025;
- RFC 9700;
- RFC 10017 — Best Current Practice, agosto de 2026.

Secure SDLC / Supply Chain:
- Trail of Bits Skills — `insecure-defaults`;
- Docker Compose Networking — service-to-service via internal/default network;
- Docker Official Image — PostgreSQL (`POSTGRES_PASSWORD`, `POSTGRES_HOST_AUTH_METHOD`);
- Docker Engine Networking / Port Publishing / Packet Filtering;
- NIST SP 800-207 — Zero Trust Architecture;
- NIST SP 800-207A — Zero Trust for Cloud-Native Applications;
- CISA Zero Trust Maturity Model v2;
- CISA network segmentation/hardening guidance;
- NIST SP 800-218 SSDF 1.1 — final;
- SP 800-218 Rev. 1 / SSDF 1.2 — draft;
- NIST SP 800-218A — final;
- SLSA 1.2 — Approved;
- CISA KEV;
- CISA SSVC;
- FIRST CVSS 4.0;
- FIRST EPSS.

Incident Response:
- NIST CSF 2.0;
- NIST SP 800-61 Rev. 3 — final, abril de 2025;
- NIST SP 800-34 Rev. 1.

Privacidade:
- LGPD;
- Resolução CD/ANPD nº 15/2024 — Comunicação de Incidente de Segurança;
- comunicação à ANPD/titular conforme aplicabilidade: 3 dias úteis;
- registro de incidentes: mínimo de 5 anos.

Acessibilidade:
- WCAG 2.2;
- baseline recomendado: nível AA.

Pagamentos:
- PCI DSS 4.0.1 — versão publicada atual.

IA / Agentes / MCP:
- OWASP GenAI LLM Top 10 2026;
- OWASP Top 10 for Agentic Applications 2026;
- OWASP MCP Top 10;
- OWASP Practical Guide for Secure MCP Server Development.

---

27. CHECK DE CONSISTÊNCIA v13.3

Antes de declarar auditoria concluída:

[ ] versão do protocolo = v13
[ ] stack detectada
[ ] escopo documentado
[ ] trust boundaries mapeadas
[ ] blockers verificados
[ ] P0/P1 tratados
[ ] testes negativos executados
[ ] tenant tests executados quando aplicável
[ ] secrets/history verificados
[ ] insecure defaults auditados
[ ] flags críticas falham fechadas quando ausentes
[ ] database ports privadas por padrão
[ ] rede guest/client isolada da management/data zone
[ ] subnet/VLAN possui ACL/firewall explícito quando usada como boundary
[ ] management plane não está diretamente exposto à Internet
[ ] Docker published ports foram testadas externamente
[ ] nenhuma credencial default/dev ativa em produção
[ ] PostgreSQL `trust` ausente em superfície alcançável
[ ] `.env`/config/dumps não estão publicamente alcançáveis
[ ] source map policy validada
[ ] pagamentos recalculados/confirmados no servidor
[ ] webhooks sensíveis autenticados e replay-protected
[ ] KEV/EPSS/contexto considerados
[ ] build reproduzido
[ ] artifact digest registrado
[ ] provenance verificada quando disponível
[ ] restore realmente testado quando obrigatório
[ ] accessibility não baseada apenas em scanner
[ ] AI/MCP testado quando aplicável
[ ] security gate PASS
[ ] quality gate PASS
[ ] reliability gate PASS
[ ] privacy/compliance gate PASS/N/A/PENDING LEGAL adequado
[ ] unknowns explícitos
[ ] residual risks explícitos
[ ] SECURITY_AUDIT.md produzido

---

28. DECISÃO FINAL

Somente usar:

READY
NOT READY
READY WITH ACCEPTED RISK

READY exige:

NO CRITICAL BLOCKER
+
ALL APPLICABLE GATES PASS
+
ARTIFACT VERIFIED
+
EVIDENCE CURRENT

READY WITH ACCEPTED RISK exige:

RISK
+
OWNER
+
JUSTIFICATION
+
COMPENSATING CONTROL
+
EXPIRY
+
APPROVAL

Não usar:

"PROBABLY SAFE"
"LOOKS SECURE"
"SCANNER PASSED"
"BUILD PASSED"

como decisão de produção.


---

FIM — PROTOCOLO SEGURANÇA v13.3

BUILD SECURE.

BUILD RELIABLE.

VERIFY EVERYTHING.

FAIL SAFELY.

RECOVER BY DESIGN.

PROVE CRITICAL CONTROLS.

ADAPT CONTINUOUSLY.