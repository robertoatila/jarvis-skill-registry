# J.A.R.V.I.S. Obsidian + Universal Remote Second Brain Implementation Plan / Master Prompt

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bidirectional, event-driven Obsidian second brain, explicit external-capability memory including ChatGPT browser skills/plugins, and universal any-device remote access to the same authoritative home-PC J.A.R.V.I.S. runtime.

**Architecture:** Keep one authoritative J.A.R.V.I.S. runtime on the home PC. Add a restart-safe Vault watcher and memory-admission pipeline around the existing `CognitiveVaultBridge`, an explicit external-capability catalog that distinguishes remembered capabilities from executable ones, and extend/consume PR #17 so paired phone/tablet/desktop browsers can reconnect to the same PC-side sessions from outside the LAN through a replaceable private/outbound transport layer.

**Tech Stack:** Python 3.12 standard library for the shipped runtime, existing agentic runtime/memory/vault modules, existing stdlib HTTP server and Remote Companion work, HTML/CSS/vanilla JS PWA for the universal client, JSON/JSONL durable state, Markdown/Obsidian Canvas.

**Spec:** `docs/superpowers/specs/2026-09-15-jarvis-obsidian-remote-second-brain-design.md`

## Global Constraints

- One authoritative PC-side planner/Governor/memory/model-router/tool-router stack.
- Do not create a second J.A.R.V.I.S. runtime on phone, tablet, browser or another PC.
- Preserve human-authored Vault content; autonomous writes use JARVIS-owned regions/notes/nodes by default.
- Obsidian text is evidence/candidate knowledge, not execution authority.
- JARVIS-generated Vault projections must not recursively re-ingest themselves.
- External capability memory is separate from capability execution.
- Do not claim ChatGPT browser skills/plugins/connectors are locally installed merely because their names are known.
- ChatGPT capability import must be explicit and provenance-bearing; do not scrape cookies, session tokens, private browser storage or credentials.
- Universal remote access must work beyond LAN without requiring direct public port-forwarding of port 8899 as the default design.
- Remote devices use individual revocable identities, not one permanent shared credential as the target architecture.
- Client disconnects must not kill PC-side missions.
- Keep shipped Python runtime standard-library-only unless a later explicitly approved change says otherwise.
- Preserve existing v0.2 runtime behavior and existing tests.
- `v0.1.0` remains immutable.
- Do not launch a separate unrelated security campaign. Respect existing repository gates and the authorization semantics already present in J.A.R.V.I.S.

---

# EXECUTION PROMPT

Você está trabalhando no repositório:

`robertoatila/jarvis-skill-registry`

Objetivo final: transformar o Obsidian em um segundo cérebro bidirecional do J.A.R.V.I.S., fazer o runtime lembrar explicitamente capacidades externas — inclusive skills/plugins/connectors expostos no ChatGPT no navegador — sem confundir “lembrar” com “conseguir executar”, e permitir conversar/operar o MESMO J.A.R.V.I.S. do PC de casa por qualquer dispositivo aprovado, de qualquer rede, com sessões retomáveis.

NÃO faça uma implementação monolítica. Execute cada slice em TDD RED -> GREEN, com commit pequeno, CI e evidência antes de iniciar o próximo.

## Fase 0 — Recupere o estado real antes de tocar no código

- [ ] Rode/inspecione o equivalente a:

```bash
git status
git log -10 --oneline --decorate
git branch -a
```

- [ ] Confirme o SHA atual de `main`.
- [ ] Inspecione PR #17 `feat: remote companion host runtime`.
- [ ] Determine se PR #17 está:

```text
MERGED
OPEN_AND_GREEN
OPEN_AND_PARTIAL
SUPERSEDED
CONFLICTING
```

- [ ] Se #17 já tiver sido mergeada, baseie o trabalho na `main` atual.
- [ ] Se #17 ainda estiver aberta e contiver a implementação remota canônica, NÃO recrie `remote_protocol`, `remote_sessions`, `remote_runtime_bridge`, `remote_http` ou `remote_host` em paralelo. Sequencie este trabalho depois dela ou use uma stacked branch claramente baseada no HEAD validado de #17.
- [ ] Inspecione, no mínimo:

```text
tooling/agentic/vault.py
tooling/agentic/vault_projection.py
tooling/agentic/workspace_hub.py
tooling/agentic/memory.py
tooling/agentic/memory_core.py
tooling/Sync-ObsidianVault.ps1
tooling/jarvis_server.py
ui/index.html
ui/jarvis.js
ui/jarvis.css
ui/chat-session.js
run_tests.py
```

- [ ] Leia também os testes existentes de Vault, memória, contexto, HTTP, Remote Companion e UI antes de escolher nomes finais de APIs.
- [ ] Registre em uma nota da PR quais componentes já existiam e quais serão realmente novos.

**Gate:** nenhum código de produção antes de recuperar o estado e provar que não está duplicando trabalho de #17.

---

## Task 1 — Durable Vault Event Core

**Files:**
- Create: `tooling/agentic/vault_events.py`
- Create: `tooling/agentic/vault_watcher.py`
- Test: `tests/test_agentic_vault_watcher.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class VaultEvent:
    schema_version: int
    event_id: str
    path: str
    kind: str
    content_hash: str | None
    previous_hash: str | None
    observed_at: str
    source: str
    projection_receipt: str | None = None

class VaultCheckpointStore:
    def load(self) -> dict: ...
    def save(self, snapshot: dict) -> None: ...

class VaultWatcher:
    def scan_once(self) -> list[VaultEvent]: ...
```

### Behavior

- Observe Markdown and Canvas content deterministically.
- Use SHA-256 content hashes, not mtime alone, to determine meaningful change.
- Persist checkpoint state atomically.
- Produce `created`, `modified`, `deleted` events.
- Generate deterministic/restart-safe event identity from normalized path + previous hash + current hash + event kind.
- Ignore `.git/`, `backups/`, projection temp files, runtime temp files and default `.obsidian/` UI churn.
- Never require the Obsidian desktop app to be running.

- [ ] **Step 1: Write failing watcher tests**

Include tests equivalent to:

```python
def test_create_modify_delete_emit_once(): ...
def test_unchanged_file_emits_nothing(): ...
def test_restart_from_checkpoint_does_not_reemit_old_event(): ...
def test_mtime_only_change_without_hash_change_emits_nothing(): ...
def test_ignored_paths_do_not_emit(): ...
```

- [ ] **Step 2: Run canonical battery and prove RED**

```bash
python run_tests.py
```

Expected: existing tests stay green; new watcher suite fails because production module/behavior is absent.

- [ ] **Step 3: Implement minimal event/checkpoint core**
- [ ] **Step 4: Run targeted tests**
- [ ] **Step 5: Run `python run_tests.py`**
- [ ] **Step 6: Commit only after GREEN**

```bash
git add tooling/agentic/vault_events.py tooling/agentic/vault_watcher.py tests/test_agentic_vault_watcher.py
git commit -m "feat: add durable Obsidian vault event watcher"
```

---

## Task 2 — Projection Receipts and Self-Loop Suppression

**Files:**
- Create: `tooling/agentic/vault_projection_receipts.py`
- Create: `tooling/agentic/managed_vault_projector.py`
- Modify only if required: `tooling/agentic/vault.py`
- Reuse without weakening: `tooling/agentic/vault_projection.py`
- Test: `tests/test_agentic_vault_projection_receipts.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ProjectionReceipt:
    receipt_id: str
    path: str
    content_hash: str
    projected_at: str
    projection_kind: str

class ProjectionReceiptStore:
    def record(self, receipt: ProjectionReceipt) -> None: ...
    def find_hash(self, path: str, content_hash: str) -> ProjectionReceipt | None: ...

class ManagedVaultProjector:
    def project_markdown(self, path: Path, body: str, *, kind: str) -> ProjectionReceipt | None: ...
    def project_canvas(self, path: Path, nodes: list, edges: list, *, kind: str) -> ProjectionReceipt | None: ...
```

### Behavior

- The projector calls the existing safe `update_projection` / `update_canvas_projection` primitives.
- After a successful write, record exact resulting hash and receipt.
- `VaultWatcher` marks matching changes as `jarvis_projection` and suppresses them from human-memory admission.
- Human changes outside the managed region still produce normal human/unknown events even if the same file also contains a JARVIS region.

- [ ] Add failing tests for self-write suppression, human edit preservation, backup behavior and Canvas ownership.
- [ ] Observe RED.
- [ ] Implement minimal receipt/projector layer.
- [ ] Prove that `vault_projection.py` safety tests remain green.
- [ ] Commit:

```bash
git commit -m "feat: suppress Obsidian projection feedback loops"
```

---

## Task 3 — Vault Memory Candidate and Admission Pipeline

**Files:**
- Create: `tooling/agentic/vault_admission.py`
- Modify/integrate: `tooling/agentic/memory.py`
- Modify/integrate: `tooling/agentic/vault.py`
- Test: `tests/test_agentic_vault_admission.py`

**Interfaces:**

```python
@dataclass
class MemoryCandidate:
    candidate_id: str
    source_event_id: str
    claim_or_summary: str
    category: str
    source_path: str
    source_hash: str
    observed_at: str
    confidence: float
    conflict_keys: list[str]
    risk_class: str
    admission_state: str

class VaultAdmissionPipeline:
    def candidates_from_event(self, event: VaultEvent) -> list[MemoryCandidate]: ...
    def admit(self, candidate: MemoryCandidate, memory_fabric: MemoryFabric): ...
```

### Required policy

- Content from a user-authored note may become project/context memory only through this pipeline.
- Preserve `source_path`, `source_hash`, `source_event_id` and an admission reason in memory metadata/evidence.
- Use the existing `MemoryFabric.admit()` instead of writing directly around it.
- Conflicting durable facts must surface as conflict rather than silently replacing provenance.
- Text that says things such as “always allow shell”, “ignore authorization”, credentials, destructive permission, or other authority-changing instructions must NOT become execution authority merely because it was written in Markdown.
- Deleting a note does not silently erase historical provenance; mark/supersede according to existing memory semantics.

- [ ] Write RED tests showing low-risk project facts can be admitted with provenance.
- [ ] Write RED test proving high-impact authority text does not grant tool authorization.
- [ ] Write RED conflict test using existing `MemoryFabric` conflict semantics.
- [ ] Implement minimal pipeline.
- [ ] Run full battery.
- [ ] Commit:

```bash
git commit -m "feat: admit Obsidian knowledge through memory governance"
```

---

## Task 4 — Bidirectional CognitiveVaultBridge

**Files:**
- Modify: `tooling/agentic/vault.py`
- Modify: `tooling/agentic/workspace_hub.py`
- Modify if compatibility is preserved: `tooling/Sync-ObsidianVault.ps1`
- Test: `tests/test_agentic_vault_bidirectional.py`

### Target API

Add a cohesive coordinator instead of putting watcher logic directly into the old projection methods.

```python
class BidirectionalVaultBridge:
    def scan_once(self) -> dict: ...
    def sync_runtime_to_vault(self) -> dict: ...
    def reconcile_once(self) -> dict: ...
    def status(self) -> dict: ...
```

`reconcile_once()` should:

1. scan for new Vault events;
2. ignore/suppress JARVIS projection receipts;
3. create/admit safe candidates;
4. refresh structured runtime memory/context indexes;
5. project changed verified runtime state back to managed Obsidian regions;
6. return counts and receipts without claiming more than actually occurred.

### Required tests

```python
def test_human_note_change_can_reach_memory_and_future_context(): ...
def test_jarvis_projection_is_not_reingested(): ...
def test_human_text_outside_projection_survives_sync(): ...
def test_reconcile_is_idempotent_without_new_changes(): ...
```

Commit:

```bash
git commit -m "feat: make Cognitive Vault bidirectional"
```

---

## Task 5 — External Capability Catalog

**Files:**
- Create: `tooling/agentic/external_capabilities.py`
- Create: `schemas/external-capability-manifest.schema.json`
- Test: `tests/test_agentic_external_capabilities.py`

**Interfaces:**

```python
class CapabilityAvailability(str, Enum):
    KNOWN = "KNOWN"
    UNVERIFIED = "UNVERIFIED"
    AVAILABLE_LOCAL = "AVAILABLE_LOCAL"
    AVAILABLE_DELEGATED = "AVAILABLE_DELEGATED"
    UNAVAILABLE = "UNAVAILABLE"
    REVOKED = "REVOKED"

@dataclass
class ExternalCapability:
    schema_version: int
    source_id: str
    capability_id: str
    name: str
    provider: str
    kind: str
    provenance: str
    capabilities: list[str]
    availability_state: CapabilityAvailability
    invocation_mode: str
    last_observed_at: str
    last_verified_at: str | None
    metadata_hash: str

class ExternalCapabilityCatalog:
    def import_manifest(self, manifest: dict) -> dict: ...
    def list(self, *, source_id: str | None = None) -> list[ExternalCapability]: ...
    def get(self, source_id: str, capability_id: str) -> ExternalCapability | None: ...
    def mark_availability(self, source_id: str, capability_id: str, state: CapabilityAvailability, *, verified_at: str | None) -> None: ...
```

### Required semantic distinction

The following must be impossible:

```text
manifest says ChatGPT has skill X
=> JARVIS labels X AVAILABLE_LOCAL
```

unless a separate local adapter verification proves that state.

A remembered ChatGPT browser capability normally enters as `KNOWN` or `UNVERIFIED`. It becomes `AVAILABLE_DELEGATED` only while an authenticated delegated-provider bridge/session is verified.

- [ ] Add tests for import, dedupe, provenance, stale verification, local-vs-delegated separation and revocation.
- [ ] Persist catalog atomically under ignored runtime state, e.g. `state/external_capabilities/`, unless existing repository conventions require a better location.
- [ ] Never store browser cookies/tokens in the manifest.
- [ ] Commit:

```bash
git commit -m "feat: add provenance-aware external capability catalog"
```

---

## Task 6 — ChatGPT Browser Capability Manifest Contract

**Files:**
- Create: `tooling/agentic/chatgpt_capability_manifest.py`
- Test: `tests/test_agentic_chatgpt_capability_manifest.py`
- Docs: `docs/CHATGPT_CAPABILITY_BRIDGE.md`

### Problem to solve

J.A.R.V.I.S. local NÃO consegue hoje enxergar automaticamente as skills/plugins/connectors instalados no ChatGPT no navegador.

A solução inicial NÃO é scraping. É um contrato explícito e importável.

### Manifest example

```json
{
  "schema_version": 1,
  "source_id": "chatgpt-browser",
  "observed_at": "2026-09-15T22:00:00-03:00",
  "source_provenance": "explicit-user-export",
  "capabilities": [
    {
      "capability_id": "example-skill",
      "name": "Example Skill",
      "kind": "skill",
      "provider": "chatgpt",
      "capabilities": ["example"],
      "availability": "UNVERIFIED"
    }
  ]
}
```

### Rules

- User/browser/provider-supplied manifest must be schema validated.
- Import remembers capability metadata; it does not import the implementation.
- Do not treat conversational mentions as installation proof.
- Do not infer current availability from old manifests.
- Future browser/ChatGPT connector integration may produce this same manifest automatically, so keep the contract provider-neutral and stable.
- If a later delegated ChatGPT execution bridge exists, its session verifier may upgrade an entry to `AVAILABLE_DELEGATED` temporarily.

### Required tests

```python
def test_chatgpt_manifest_imports_as_known_not_local(): ...
def test_old_manifest_does_not_claim_current_availability(): ...
def test_manifest_rejects_secret_fields(): ...
def test_conversation_text_is_not_a_manifest(): ...
```

Commit:

```bash
git commit -m "feat: define ChatGPT browser capability import contract"
```

---

## Task 7 — Obsidian Capability MOC

**Files:**
- Create: `tooling/agentic/vault_capabilities.py`
- Modify: `tooling/agentic/vault.py`
- Create or update managed note: `20 - External Capability Matrix.md` only through managed projection semantics
- Test: `tests/test_agentic_vault_capabilities.py`

### Projection must distinguish

```text
LOCAL EXECUTABLE
DELEGATED / PROVIDER VERIFIED
KNOWN ONLY
UNVERIFIED / STALE
REVOKED / UNAVAILABLE
```

Each row must expose provider/source and last verification time where present.

Do not print secrets or provider credentials.

Commit:

```bash
git commit -m "feat: project external capability state into Obsidian"
```

---

## Task 8 — Consume/Finish PR #17 Remote Foundation

Before editing remote code, re-check #17 state.

If already merged, use the merged modules. If still open, either finish/merge it under its own validated scope or stack explicitly on its current validated head. Do not copy-and-diverge.

Required remote primitives before continuing:

```text
versioned protocol
durable sessions
request_id idempotency for completed requests
event cursor replay
RemoteRuntimeBridge
/api/remote/v1/*
truthful resident-host liveness
```

Run the full battery and record exact SHA before Task 9.

---

## Task 9 — Per-Device Identity, Pairing and Revocation

**Expected files after reconciling with #17 naming:**
- Create: `tooling/remote_devices.py`
- Extend remote HTTP/session modules from #17 rather than replacing them
- Test: `tests/test_agentic_remote_devices.py`

**Interfaces:**

```python
@dataclass
class RemoteDevice:
    device_id: str
    label: str
    status: str
    paired_at: str
    last_seen_at: str | None
    credential_fingerprint: str

class RemoteDeviceRegistry:
    def create_pairing_offer(self, *, label_hint: str | None = None) -> dict: ...
    def complete_pairing(self, offer_id: str, proof: dict) -> RemoteDevice: ...
    def authenticate(self, device_id: str, proof: dict) -> bool: ...
    def revoke(self, device_id: str) -> RemoteDevice: ...
```

### Required semantics

- Pairing offer is short-lived and one-time.
- Every device has its own identity/credential.
- Revoke one device without rotating all others.
- Device identity is bound to remote sessions.
- Phone, tablet and another PC use the same protocol.
- Pairing transport never creates a second JARVIS brain.

### Tests

```python
def test_pairing_offer_is_one_time(): ...
def test_two_devices_have_independent_credentials(): ...
def test_revoking_one_device_does_not_break_other(): ...
def test_wrong_device_cannot_resume_other_session(): ...
```

Commit:

```bash
git commit -m "feat: add revocable remote device identities"
```

---

## Task 10 — Beyond-LAN Remote Transport Abstraction

**Files:**
- Create: `tooling/remote_transport.py`
- Create: `tooling/remote_transport_local.py`
- Add provider adapters only when there is a concrete supported mechanism in the environment
- Test: `tests/test_agentic_remote_transport.py`

**Interface:**

```python
@dataclass(frozen=True)
class RemoteTransportStatus:
    transport_id: str
    state: str
    public_or_private_endpoint: str | None
    last_verified_at: str | None
    detail: str

class RemoteTransport:
    def start(self) -> RemoteTransportStatus: ...
    def status(self) -> RemoteTransportStatus: ...
    def stop(self) -> RemoteTransportStatus: ...
```

### Requirements

- Local/LAN mode remains available for compatibility.
- Add a provider-neutral path for private overlay/outbound tunnel connectivity.
- It must allow a paired device on 4G/5G or unrelated Wi-Fi to reach the home host.
- Do not make direct public `0.0.0.0:8899` port-forwarding the default answer.
- Host UI/status must identify which transport is active and whether its endpoint was actually verified.
- If external transport is unavailable, report it truthfully; do not pretend remote-anywhere works.

### Provider rule

Do not hardwire architecture to one vendor. A first concrete adapter may target whichever supported transport is already present/approved in the repository/environment, but the `RemoteTransport` interface must make replacement possible.

Commit:

```bash
git commit -m "feat: add provider-neutral remote transport layer"
```

---

## Task 11 — Universal Browser/PWA Companion

**Files:**
- Modify: `ui/index.html`
- Modify carefully: `ui/jarvis.js`
- Modify carefully: `ui/jarvis.css`
- Reuse/extend: `ui/chat-session.js`
- Create: `ui/manifest.webmanifest`
- Create: `ui/service-worker.js`
- Add tests following current UI test conventions

The current `ui/jarvis.js` and `ui/index.html` are already large. Do not dump the entire new remote client into those files. Extract a focused module such as:

```text
ui/remote-companion.js
ui/remote-companion.css
```

if that matches existing test/loading conventions.

### Required UI states

```text
HOST OFFLINE
HOST ONLINE
PAIR DEVICE
DEVICE TRUSTED
DEVICE REVOKED
CONNECTING
CONNECTED
RECONNECTING
SESSION RESUMED
MISSION RUNNING
MISSION WAITING
ERROR
```

### Device-neutral behavior

- responsive phone layout;
- usable tablet layout;
- usable desktop browser layout;
- installable PWA metadata;
- no assumption of Android-only or iPhone-only APIs;
- cursor-based session resume;
- no authoritative memory stored client-side;
- minimal local persistence limited to non-secret client/session metadata required for reconnect, following the chosen pairing design.

### Required test cases

- narrow viewport chat/session controls remain usable;
- host offline state blocks fake send success;
- reconnect fetches events after last cursor;
- revoked device transitions to re-pair state;
- desktop local HUD routes continue to work.

Commit:

```bash
git commit -m "feat: add universal PWA remote companion"
```

---

## Task 12 — Resident Background Reconciliation Loop

Integrate Vault reconciliation and remote host lifecycle without creating multiple runtimes.

**Expected integration point:** resident-host/service work from PR #17.

Target loop:

```text
host starts
-> one cognitive runtime starts
-> remote host state becomes truthful ONLINE only after readiness
-> Vault watcher/reconciliation scheduler starts
-> remote transport starts/validates if configured
-> clients may connect
-> periodic Vault reconcile runs in the host process/service
-> shutdown flushes checkpoint/journal and marks host OFFLINE
```

### Constraints

- Do not spawn one cognitive runtime per remote session.
- Do not spawn one memory fabric per device.
- Obsidian watcher and remote API must share the same process-level authoritative runtime context or a clearly bounded host-owned service context.
- Reconciliation exceptions must not crash the entire host; emit explicit degraded/error state and preserve last valid checkpoint.

Tests must cover start/stop, restart checkpoint recovery and no duplicate runtime construction.

Commit:

```bash
git commit -m "feat: run Vault reconciliation in resident JARVIS host"
```

---

## Task 13 — End-to-End Cross-System Scenario

Create a deterministic integration test that proves the complete architecture without external Internet dependency.

Scenario:

1. Start isolated JARVIS host fixture.
2. Pair `phone-1`.
3. Open remote session.
4. Create/edit an admitted Obsidian test note.
5. Run Vault reconciliation.
6. Verify structured memory contains provenance-bearing admitted knowledge.
7. Send remote prompt referencing that knowledge.
8. Verify the same PC-side runtime/context can retrieve it.
9. Project verified runtime state back into a managed Vault region.
10. Rescan and verify no self-ingestion loop.
11. Import a synthetic ChatGPT manifest containing `skill-x`.
12. Verify `skill-x` is remembered as `KNOWN`/`UNVERIFIED`, not `AVAILABLE_LOCAL`.
13. Mark a synthetic delegated-provider verification and verify it becomes `AVAILABLE_DELEGATED` only under that evidence.
14. Disconnect `phone-1`.
15. Continue/retain mission/event state PC-side.
16. Reconnect with cursor and verify replay/resume.
17. Revoke `phone-1` and verify subsequent authentication fails.

This test is the acceptance proof that Obsidian, memory, external capabilities and remote access are parts of one architecture instead of disconnected demos.

Commit:

```bash
git commit -m "test: prove remote second-brain end-to-end flow"
```

---

## Task 14 — Final Documentation and Operational Surface

Update documentation only after implementation behavior is proven.

Document:

```text
How the Vault watcher works
What can and cannot become durable memory
How projection ownership works
How to inspect conflicts
How external capability memory works
Why ChatGPT skills are not automatically local skills
How to import/update a ChatGPT capability manifest
How to pair/revoke devices
How to connect from phone/tablet/another PC
How to inspect active remote transport
How to recover after host restart
How to stop remote access
```

Update `00 - J.A.R.V.I.S. Cognitive Vault.md` through managed projection where appropriate; do not rewrite historical human-authored sections as if they were current telemetry.

---

# Verification Gates

Before marking the implementation complete, run and record exact commit SHA for:

```bash
python run_tests.py
python jarvis.py --doctor
python jarvis.py --test
python benchmarks/context_budget_benchmark.py
python tooling/audit_pre_publish_security.py
```

Also require all repository CI jobs that normally gate the branch to complete successfully on that exact head, including supported portable OS and legacy regression jobs when present.

Do not report a task COMPLETE while an exact-head gate is still queued/in progress.

# Required Final Report

Return a compact but exact report containing:

```text
Branch
PR
Base SHA
Final HEAD SHA
Tasks completed
Tests: suites / tests / pass / fail / error
Ubuntu status
Windows status
macOS status
Legacy status
Existing audit/gate status
Obsidian watcher status
Memory admission status
ChatGPT capability catalog status
Universal remote status
Transport actually implemented
Pairing/revocation status
Known limitations
```

# Non-Negotiable Semantic Answer About ChatGPT Skills

If asked “o JARVIS lembra das skills que coloquei no ChatGPT no navegador?”, answer according to evidence:

- **Today, before this feature:** not automatically. The local JARVIS has no truthful automatic inventory of ChatGPT browser-installed capabilities.
- **After the catalog/import feature:** JARVIS can remember an explicitly imported/verified capability inventory with provenance and freshness.
- Remembering a capability does **not** mean JARVIS owns its implementation.
- `AVAILABLE_LOCAL` requires a verified local implementation/adapter.
- `AVAILABLE_DELEGATED` requires a currently verified provider/session bridge.
- Never upgrade capability state from conversational memory alone.

# Final Architectural Outcome

The finished system should behave like this:

```text
                         ANY APPROVED DEVICE
               phone | tablet | laptop | desktop
                              |
                    paired remote session
                              |
                    private/outbound transport
                              |
                              v
+-----------------------------------------------------------------+
|                         HOME PC                                 |
|                                                                 |
|                  ONE RESIDENT JARVIS                            |
|          Governor / Memory / Routers / Tools                    |
|               |                      |                          |
|               |                      +--> External Capability   |
|               |                           Catalog               |
|               |                           |                     |
|               |                           +-- ChatGPT Browser   |
|               |                           +-- Local Skills      |
|               |                           +-- Delegated Tools   |
|               |                                                 |
|               v                                                 |
|       Bidirectional Cognitive Vault                             |
|        watcher -> admission -> memory                           |
|        memory  -> managed projection                            |
+-----------------------+-----------------------------------------+
                        |
                        v
                  OBSIDIAN SECOND BRAIN
```

There must still be only **one J.A.R.V.I.S. brain**. Obsidian is its visual/human knowledge interface. Remote devices are its clients. ChatGPT browser skills are external capabilities that can be remembered and, only when separately verified, delegated to — never silently conflated with local runtime skills.
