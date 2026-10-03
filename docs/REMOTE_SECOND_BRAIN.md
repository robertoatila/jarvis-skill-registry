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

Authenticated LAN/private-network mode:

```bash
python -m tooling.remote_host --port 8899 --remote
```

Equivalent explicit LAN transport:

```bash
python -m tooling.remote_host --port 8899 --transport lan
```

Verified Tailscale mode for unrelated Wi-Fi / 4G / 5G:

```bash
python jarvis.py host --transport tailscale
```

For the preferred HTTPS phone path, provision Tailscale Serve once from an elevated Windows terminal, verify it, then run the resident host in adopt-only mode:

```bash
python jarvis.py remote-serve provision
python jarvis.py remote-serve status
python jarvis.py host --transport tailscale-serve
```

Before relying on persistent remote access, run:

```bash
python jarvis.py remote-doctor
```

The ordinary Tailscale adapter is read-only with respect to machine-wide VPN state. Tailscale Serve provisioning is explicit and separately verified; the resident host will not silently create the HTTPS mapping when started in adopt-only mode. Stopping JARVIS does not execute `tailscale down`.

Direct public port-forwarding of `8899` is not the default design.

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

Projection receipts for managed Vault projections are stored at:

```text
state/obsidian/projection_receipts.json
```

A watcher event is considered `jarvis_projection` only when its exact path/content hash matches a one-shot projection receipt. Marker-shaped text by itself does not grant JARVIS authorship.

The private runtime-memory note is under `state/`, which the watcher excludes. This prevents:

```text
runtime memory -> Obsidian projection -> watcher -> memory again
```

The managed runtime projection contains admitted semantic memory and therefore defaults to an ignored local path:

```text
state/memory/Second Brain Runtime.md
```

Do not move that projection into tracked/public Vault notes. The public Note 19 contains instructions only; local profile and fact records use ignored `state/jarvis_memory.local.json`. The tracked `state/jarvis_memory.json` is an empty compatibility template. Existing legacy local data can be read as a fallback, while new writes go to the ignored local file.

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

## Device credential storage

The server persists only the credential fingerprint in:

```text
state/remote_devices.json
```

The browser keeps the raw device credential in `sessionStorage`, not persistent `localStorage`. Device ID, session ID and replay cursor may be retained in local storage, but the raw credential is intentionally page/session-lifetime only.

As a consequence, completely ending the browser session may require pairing the device again. This is a current security/UX trade-off.

## List and revoke devices

Use the dedicated CLI:

```bash
python jarvis.py remote-devices list
python jarvis.py remote-devices revoke --device-id "<DEVICE_ID>"
```

A revoked device fails authentication and cannot continue using its existing remote session.

## Connect from another network

For access from unrelated Wi-Fi or mobile data:

1. Install/configure Tailscale on the home PC and remote device.
2. Confirm both devices are in the intended tailnet.
3. Prefer the verified HTTPS path: provision Tailscale Serve, then start JARVIS with `python jarvis.py host --transport tailscale-serve`.
4. Generate a one-time pairing link with `python jarvis.py remote-pair --label "Galaxy"` or from the home-PC HUD.
5. Open the generated HTTPS Remote Companion link on the approved device.
6. Pair and connect.

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

- Per-user Windows resident-service management is implemented; macOS/Linux autostart remains a separate platform concern.
- Tailscale Serve HTTPS provisioning is explicit and requires an elevated Windows terminal for provisioning; normal host startup adopts an already verified mapping.
- Raw browser device credentials are session-lifetime only; a completely ended browser session may require re-pairing.
- Device listing/revocation has a dedicated CLI; ChatGPT capability-manifest import remains a canonical Python/API workflow.
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

Also require fresh direct evidence on the exact candidate SHA: portable runtime on Windows/Linux/macOS, Windows legacy-governance, the focused remote suites, browser/Remote Companion acceptance, and the repository security audit. GitHub Actions are not release authority.
