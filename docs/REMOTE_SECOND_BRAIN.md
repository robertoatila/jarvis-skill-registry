# J.A.R.V.I.S. Remote Second Brain Runbook

This document describes the implemented v0.2 development-branch behavior for the bidirectional Obsidian bridge, governed durable memory, external capability catalog, and Remote Companion.

It is an operational runbook, not release evidence. Use the exact-head CI and validation gates for claims about a specific commit.

## Architecture

```text
approved browser/device
        |
        | paired device credential
        v
Remote Companion HTTP API
        |
        | local / LAN / verified Tailscale transport
        v
HOME PC — one resident JARVIS
        |
        +-- canonical authorized chat boundary
        +-- one MemoryFabric
        +-- BidirectionalVaultBridge
        +-- ExternalCapabilityCatalog
```

The remote device is a thin client. It does not own a second runtime, a second memory, provider API keys, or ChatGPT credentials.

## Start the resident host

Local-only:

```bash
python -m tooling.remote_host --port 8899
```

### Windows: start automatically when the PC user logs in

Check readiness first. If the doctor reports `SETUP_REQUIRED`, provision the Serve mapping once from a Windows **Admin terminal**; after that, install the JARVIS task from a normal user context:

```powershell
python jarvis.py remote-doctor

# One-time / elevated Windows terminal:
python jarvis.py remote-serve provision

# Read-only verification:
python jarvis.py remote-serve status

# Per-user resident host:
python jarvis.py service install --transport tailscale-serve
python jarvis.py service start
python jarvis.py service status
```

Stop or remove it with:

```powershell
python jarvis.py service stop
python jarvis.py service uninstall
```

The generated launcher restores the repository as the working directory and starts `tooling.remote_host` through `pythonw` when available. Autostart is stored in the current user's HKCU `Software\\Microsoft\\Windows\\CurrentVersion\\Run` key, so JARVIS autostart registration itself does not request administrator elevation. In `tailscale-serve` mode the resident transport is adopt-only: it verifies the exact existing `https://<tailnet-dns>` mapping to `http://127.0.0.1:8899` and never creates or modifies Serve configuration. Linux systemd-user and macOS LaunchAgent registration are not implemented in this branch.

The resident context retries an unavailable adopt-only transport during its normal reconcile loop. This covers the common Windows-logon race where the HKCU Run launcher starts before the Tailscale service has reached `Running/Online`. Missing provisioning remains `UNAVAILABLE` until `remote-serve provision` is run explicitly.

Authenticated LAN/private-network mode:

```bash
python -m tooling.remote_host --port 8899 --remote
```

Equivalent explicit LAN transport:

```bash
python -m tooling.remote_host --port 8899 --transport lan
```

Preferred Tailscale Serve mode for unrelated Wi-Fi / 4G / 5G:

```bash
python -m tooling.remote_host --port 8899 --transport tailscale-serve
```

In this mode JARVIS remains bound to `127.0.0.1:8899`. Tailscale Serve terminates HTTPS on the node's tailnet DNS name and proxies to the loopback backend. JARVIS verifies the existing Serve state, refuses to overwrite an unrelated handler on the selected HTTPS port, and remote API calls still require the paired-device credential even though the proxy reaches the backend through loopback.

The older direct-tailnet adapter remains available as `--transport tailscale`. It is read-only with respect to machine-wide VPN state and does not execute `tailscale down`.

Direct public port-forwarding of `8899` is not the design.

## PC-side provider configuration

Remote messages do not carry provider secrets. The resident adapter resolves provider/model/key/token on the home PC.

Copy the example provider config and populate only the local file:

```text
config/api_keys.example.json
-> config/api_keys.json
```

For the Remote Companion's default message path, configure at least:

```json
{
  "preferred_provider": "groq",
  "groq_model": "openai/gpt-oss-120b",
  "groq": "<LOCAL_SECRET>"
}
```

and the PC-side environment:

```text
JARVIS_CHAT_ALLOW_CLOUD=1
JARVIS_CHAT_TOKEN=<LOCAL_CHAT_GRANT>
JARVIS_CHAT_PROVIDERS=groq
```

The remote adapter deliberately ignores an `apiKey` supplied by a phone/browser payload. If the PC-side authorization/provider/model configuration is missing, the canonical chat boundary returns a truthful `BLOCKED` result rather than inventing a provider.

## Vault watcher

The resident host owns one `BidirectionalVaultBridge`. By default, `ResidentHostContext` reconciles every 30 seconds.

The watcher:

- works directly on Vault files; Obsidian does not need to be open;
- observes `*.md` and `*.canvas`;
- ignores `.git`, `.obsidian`, `state`, `backups`, temporary/swap/backup projection files;
- ignores files larger than 2 MiB;
- identifies changes by SHA-256 content hash rather than modification time alone;
- persists restart-safe file state at `state/obsidian/vault_checkpoint.json`.

Each observed transition has a deterministic event identity derived from path, transition kind, previous hash and current hash.

## What can become durable memory

Human/unknown Markdown or Canvas content can become a governed semantic-memory candidate only after the event hash is re-verified against the file contents.

Accepted low-risk Vault context is admitted through the existing `MemoryFabric.admit()` path with provenance metadata including:

```text
source_path
source_hash
source_event_id
candidate_id
risk_class
admission_reason
```

Durable model-derived semantic/procedural memory remains subject to the existing verification/evidence/admission-reason requirements in `MemoryFabric`.

The following do **not** become executable authority merely because they appear in a note:

- authorization bypass instructions;
- auto-approval instructions;
- admin/root grants;
- destructive commands such as mass deletion/database destruction;
- credential/token/API-key-like text;
- other high-authority patterns recognized by `VaultAdmissionPipeline`.

Those candidates are rejected with `VAULT_AUTHORITY_TEXT_IS_NOT_EXECUTION_AUTHORITY`.

Deleting a source note creates a supersession/lifecycle episode; it does not silently erase history.

## Projection ownership and anti-loop behavior

Runtime projection is written inside managed projection markers. Human-authored text outside the managed region is preserved.

Projection receipts are stored at:

```text
state/obsidian/projection_receipts.json
```

A watcher event is considered `jarvis_projection` only when its exact path/content hash matches a one-shot projection receipt. Marker-shaped text by itself does not grant JARVIS authorship.

This prevents:

```text
runtime memory -> Obsidian projection -> watcher -> memory again
```

The managed runtime projection defaults to:

```text
JARVIS/Second Brain Runtime.md
```

## Inspect reconciliation and conflicts

One manual reconciliation from the repository root:

```python
from pathlib import Path
from tooling.agentic.bidirectional_vault import BidirectionalVaultBridge

bridge = BidirectionalVaultBridge(Path("."))
print(bridge.reconcile_once())
print(bridge.status())
```

The result reports counts for:

```text
human_events
projection_events_suppressed
candidates
admitted
rejected
conflicts
superseded
admission_errors
```

The durable memory snapshot is:

```text
state/memory/memory_snapshot.json
```

A semantic/procedural contradiction preserves the prior record in the snapshot `history` collection, marks both sides `CONFLICT_DETECTED`, and links them with `contradicted_by`. Inspect that snapshot when the reconcile result reports non-zero conflicts.

## External capability memory

The catalog is stored at:

```text
state/external_capabilities/catalog.json
```

Supported states are:

```text
KNOWN
UNVERIFIED
AVAILABLE_LOCAL
AVAILABLE_DELEGATED
UNAVAILABLE
REVOKED
```

Remembering a capability is not equivalent to owning or executing it.

- `AVAILABLE_LOCAL` requires a separately verified local adapter.
- `AVAILABLE_DELEGATED` requires a separately verified delegated/provider bridge.
- executable availability is time-bounded and degrades to `UNVERIFIED` when verification becomes stale.

The human-facing Obsidian projection is `20 - External Capability Matrix.md`.

## ChatGPT browser capability inventory

JARVIS does **not** automatically discover the skills/plugins/connectors available in a ChatGPT browser session and does not scrape cookies, browser storage, tokens, or private session state.

Import requires an explicit structured manifest with:

```text
source_id = chatgpt-browser
provider = chatgpt
availability = KNOWN or UNVERIFIED
```

Example import from a Python shell:

```python
import json
from pathlib import Path
from tooling.agentic.external_capabilities import ExternalCapabilityCatalog
from tooling.agentic.chatgpt_capability_manifest import ChatGPTCapabilityManifestBridge
from tooling.agentic.vault import CognitiveVaultBridge

root = Path(".").resolve()
manifest = json.loads(Path("chatgpt-capabilities.json").read_text(encoding="utf-8"))

catalog = ExternalCapabilityCatalog(root / "state")
bridge = ChatGPTCapabilityManifestBridge(catalog)
print(bridge.import_manifest(manifest))

# Refresh the Obsidian capability matrix.
print(CognitiveVaultBridge.sync_external_capabilities(root, catalog=catalog))
```

Re-import the same `source_id` / `capability_id` with a newer `observed_at` to update catalog metadata. A ChatGPT manifest older than the configured maximum age is retained for provenance but imported as `UNVERIFIED`. A manifest cannot grant `AVAILABLE_LOCAL` or `AVAILABLE_DELEGATED`.

See `docs/CHATGPT_CAPABILITY_BRIDGE.md` and `schemas/external-capability-manifest.schema.json`.

## Pair a device

1. Start the resident host.
2. On the home PC, open the JARVIS HUD / Remote Companion.
3. Choose **Gerar link no PC**. Pairing offers are one-time and expire after 120 seconds by default.
4. Open the generated link on the phone/tablet/laptop.
5. Choose **Parear dispositivo**.
6. The client creates its own device credential and opens/resumes a durable remote session.

For Tailscale, the generated link uses the verified tailnet endpoint rather than `localhost`.

Pairing-offer creation is accepted only from loopback or the host's own verified transport IP. Another tailnet peer cannot create pairing offers.

Remote static assets are served only to loopback, private/link-local addresses, or source networks explicitly declared by the configured transport.

## Execute a command on the PC from the paired phone

The Remote Companion now has a separate command surface in addition to chat. A command never executes at the moment it is submitted.

Example commands for the Windows v0.2 gates:

```text
python tooling/validate_v020_plan4.py --gate portable-runtime
python tooling/validate_v020_plan4.py --gate legacy-governance
```

Flow:

```text
phone submits structured argv
  -> PC persists PENDING action
  -> PC returns approval_required + action_id + SHA-256 action_digest
  -> phone displays the exact command
  -> user approves that exact digest
  -> PC executes with shell=False inside the repository
  -> action_receipt returns exit code + bounded stdout/stderr
```

The same completed action is not executed again if approval is retried. If the PC restarts while a command is marked RUNNING, the persisted action becomes `UNKNOWN` and is not replayed automatically.

The first command runner is deliberately not a raw shell proxy. It accepts bounded argv for development executables such as Python, Git, Node/npm/npx and script-based PowerShell. Inline interpreter forms such as `python -c`, `node --eval` and `powershell -Command` are rejected. The working directory must remain inside the JARVIS checkout.

This path is owned by the JARVIS resident host. It does not require a Codex Remote session or ChatGPT Desktop to remain open.

## Run a natural-language software task on the PC

The Companion also exposes a separate **Tarefa autônoma** surface. This is not chat text being treated as authorization.

The canonical [remote task contract](architecture/REMOTE_TASK_CONTRACT.md) defines
wire fields, digest serialization, durable states, receipt semantics and limits.
Final validation on the physical Windows PC remains **pending**; neither this
runbook nor passing contract fixtures authorizes merge of PR #53.

Example:

```text
analise a falha de login, corrija apenas o código necessário e rode os testes focados
```

Planning is intentionally split into two inference-only passes:

```text
goal
  -> path-only repository inventory (protected paths excluded)
  -> planner selects <= 8 files
  -> PC reads only those bounded files and records their SHA-256
  -> planner returns strict JSON actions
  -> PC normalizes/rejects the plan
  -> state/remote_tasks.json stores PENDING plan + plan_digest
  -> phone receives task_plan_required with a bounded public plan view
  -> explicit approval of task_id + exact plan_digest
  -> preflight verifies write-target hashes/absence + command cwd/executable
  -> write_text / command actions execute sequentially
  -> task_receipt reports each action
```

The public plan shown on the phone includes the summary, selected paths, write purposes, the complete bounded unified diff, replacement-content SHA-256/byte count, command argv/cwd/timeouts and the overall `plan_digest`. A write whose diff would exceed 6,000 characters is rejected and must be split into smaller reviewable actions. Full replacement file contents remain on the PC-side plan state and are not copied into the approval event.

### Write rules

- Writes use the existing `LocalActionAdapter`, not a shell redirect.
- An existing file can be overwritten only if it was inspected in the same plan.
- The exact observed SHA-256 becomes `expected_before_sha256`.
- If any planned target changes before approval/execution, preflight rejects the plan before the first write.
- `.git/`, `state/`, `backups/`, `config/`, `.env*`, virtual environments, `node_modules/`, private-key-like paths and other protected surfaces are excluded.
- A plan may write each path at most once.
- Writes are full-file replacements; arbitrary model-generated shell patches are not used.

### Autonomous command rules

Manual commands and autonomous commands have different ceilings. The autonomous planner is narrower:

- Git is limited to read-only inspection such as `status`, `diff`, `log`, `show`, `grep`, `ls-files` and `rev-parse`.
- `npx` is rejected.
- npm is limited to `test` / `run`, with deployment/publishing script names rejected.
- Python inline code is rejected; `python -m` is limited to bounded verification modules and direct scripts must be repository-relative.
- Node and PowerShell scripts must be repository-relative.
- Commands continue to execute with `shell=False`.

These checks constrain command selection; they are not an OS sandbox for approved
scripts or their dependencies. Scripts run with the PC user's permissions.

If one action fails, later actions are not started. Re-approving a task already marked `COMPLETED` or `FAILED` returns the persisted result instead of repeating effects. A task that was `RUNNING` when the host restarted becomes `UNKNOWN` and is not silently replayed.

Earlier successful actions are not automatically rolled back. `COMPLETED` means
all action receipts reported `PASS`, not that the user's objective was independently
verified. Inspect the verification output. Remote plan approval fails closed when a
write cannot be represented by a complete diff within the review bound.

### Planner configuration and source disclosure

Natural-language task planning uses the same PC-side inference boundary as authenticated JARVIS chat. The phone never receives provider keys.

Run:

```powershell
python jarvis.py remote-doctor
```

The `task_planner` check reports only readiness metadata: cloud enabled, token presence, allowed provider names, preferred provider, model configured and provider-key presence. It never prints the token/key values.

The second planning pass sends the selected source file contents to the configured inference provider. Selection is bounded to 8 files, 32 KiB per file and 64 KiB total source content. The serialized planning prompt is capped at 120 KiB inside a planner-only 128 KiB inference envelope; ordinary chat remains on its smaller existing budget. Protected credential/state paths are excluded. If that source disclosure is not desired, use chat/manual command mode instead of autonomous task planning.

## Device credential storage

The server persists only the credential fingerprint in:

```text
state/remote_devices.json
```

The Remote Companion offers **Manter este celular pareado**. When enabled, the raw device credential is retained in browser persistent storage so the installed PWA can reconnect after being closed; when disabled, it remains session-only. Revoking the device on the PC invalidates either form.

## Pair, list and revoke devices from the PC CLI

With the resident host already running, generate a one-time pairing URL from the PC:

```powershell
python jarvis.py remote-pair --label "Galaxy"
```

The command talks only to the loopback host, which creates the one-time offer and returns the verified remote endpoint when the active transport has one. With `tailscale-serve`, the resulting URL uses the HTTPS tailnet hostname and the dedicated `/remote` shell. The one-time offer ID and pairing secret are placed in the URL fragment (`#...`), not the query string, so they are not sent in the HTTP request path to the host/proxy. The secret is printed only as part of this one-time local result and is not persisted in plaintext by the device registry.

List paired devices:

```powershell
python jarvis.py remote-devices list
```

Selectively revoke one device:

```powershell
python jarvis.py remote-devices revoke --device-id <device-id>
```

Revocation invalidates that device credential without rotating unrelated devices.

A revoked device fails authentication and cannot continue using its existing remote session.

## Connect from another network

For access from unrelated Wi-Fi or mobile data:

1. Install/configure Tailscale on the home PC and remote device.
2. Confirm both devices are in the intended tailnet.
3. Provision the HTTPS mapping once with `python jarvis.py remote-serve provision` from an Admin terminal, then verify it with `python jarvis.py remote-serve status`.
4. Start JARVIS with `--transport tailscale-serve` or the installed resident service.
5. Generate the pairing link on the home host with `python jarvis.py remote-pair --label "Galaxy"`.
6. Open the generated `https://<pc>.<tailnet>.ts.net/remote?remote=1#offer=...&pairing_secret=...` link on the approved device. The fragment is consumed client-side and immediately removed from browser history.
7. Pair and connect.

The Remote Companion uses the same resident JARVIS runtime and MemoryFabric as the home PC.

## Inspect active transport

After pairing, the client reads:

```text
GET /api/remote/v1/host
```

The response includes `transport_status` when a transport is configured:

```json
{
  "transport_id": "tailscale",
  "state": "ACTIVE",
  "public_or_private_endpoint": "http://100.x.x.x:8899",
  "last_verified_at": "...",
  "detail": "verified active tailnet endpoint"
}
```

Do not treat an old `state/remote_host.json` record as liveness proof. `RemoteHostController.status()` verifies the recorded PID; stale processes are reported `OFFLINE / STALE_PID`.

## Disconnect, reconnect and host restart

Client **Desanexar** does not close the server-side session. The PC-side mission/event journal may continue.

On reconnect, the client asks for events strictly after its stored cursor and acknowledges the newest cursor. This provides deterministic replay of missed events.

After a host restart:

- Vault observation resumes from `state/obsidian/vault_checkpoint.json`;
- governed memory reloads from `state/memory/memory_snapshot.json`;
- remote device registry remains in `state/remote_devices.json`;
- durable remote session/event state remains on disk;
- projection-loop protection resumes from `state/obsidian/projection_receipts.json`.

A browser that still has its device credential can resume its durable session. A browser session that lost the raw credential must pair again.

## Stop remote access

For a foreground resident host, stop the JARVIS host process (for example with `Ctrl+C`). The host publishes an explicit `OFFLINE / STOPPED` state and stops the JARVIS-owned transport adapter.

In Tailscale mode, stopping JARVIS does not disable the machine-wide Tailscale service.

Selective access removal should use device revocation rather than rotating unrelated devices.

## Known limitations

- Windows per-user autostart/login integration is implemented through `jarvis.py service ...`. Linux systemd-user and macOS LaunchAgent integration are still pending.
- The preferred Tailscale Serve mode requires Serve/HTTPS to be enabled in the tailnet. On Windows, one-time Serve provisioning must be performed explicitly from an Admin terminal and may require Tailscale account consent; the limited resident service never provisions it.
- Remembered browser device credentials are persistent on that phone/browser until cleared or revoked; session-only pairing is available when persistence is not desired.
- Device pairing/list/revocation has a CLI; ChatGPT manifest import still exposes a canonical Python API rather than a dedicated CLI/HUD management screen.
- The catalog remembers explicit ChatGPT capability observations; it does not automatically inventory the user's ChatGPT account.
- Remembered capabilities do not become executable without separately verified local/delegated adapters.
- Completed-request replay is durable, but the system does not claim exactly-once semantics for arbitrary external mutable effects across a crash between the effect and durable completion.

## Validation

Before calling this feature complete, use the repository gates on the exact head:

```bash
python run_tests.py
python jarvis.py --doctor
python jarvis.py --test
python benchmarks/context_budget_benchmark.py
python tooling/audit_pre_publish_security.py
```

Also require the normal portable Ubuntu/Windows/macOS and Legacy regression jobs, plus the repository security audit, to complete successfully on that same commit.
