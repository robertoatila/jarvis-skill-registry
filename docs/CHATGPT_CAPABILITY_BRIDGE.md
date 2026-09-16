# ChatGPT Capability Bridge

## Purpose

J.A.R.V.I.S. cannot truthfully infer which skills, plugins, connectors, models, or tools are currently exposed inside ChatGPT from conversation text, a repository name, or browser presence alone.

The ChatGPT Capability Bridge therefore uses an **explicit structured manifest**. It remembers capability metadata and provenance without importing implementation code, browser credentials, cookies, or session state.

This bridge is an observation/catalog boundary, not an execution-authority boundary.

## Manifest contract

Example:

```json
{
  "schema_version": 1,
  "source_id": "chatgpt-browser",
  "observed_at": "2026-09-16T17:40:00+00:00",
  "source_provenance": "explicit-user-export",
  "capabilities": [
    {
      "capability_id": "github",
      "name": "GitHub",
      "kind": "connector",
      "provider": "chatgpt",
      "capabilities": ["repository.read"],
      "availability": "KNOWN"
    }
  ]
}
```

The generic schema lives at `schemas/external-capability-manifest.schema.json`.

For this bridge:

- `source_id` must be `chatgpt-browser`;
- each entry must have provider `chatgpt`;
- manifest availability may only be `KNOWN` or `UNVERIFIED`;
- a manifest must be supplied as a structured object/dict;
- natural-language conversation and JSON-looking strings are not accepted as manifests.

## Availability semantics

`KNOWN` means J.A.R.V.I.S. remembers that an explicit source reported the capability.

`UNVERIFIED` means the capability is cataloged but current availability is not established.

`AVAILABLE_LOCAL` is never granted by a ChatGPT browser manifest. It requires separate, fresh verification of a local J.A.R.V.I.S. adapter.

`AVAILABLE_DELEGATED` is never granted by a manifest either. A future authenticated provider/session bridge may establish it temporarily through the external capability catalog's separate verification path.

`UNAVAILABLE` and `REVOKED` are runtime/catalog states, not claims that a browser manifest can use to create execution authority.

## Freshness

The bridge compares `observed_at` with the current runtime clock.

- A fresh manifest keeps its catalog-only `KNOWN`/`UNVERIFIED` state.
- A manifest older than the configured maximum age is still retained for provenance but its entries are imported as `UNVERIFIED`.
- A timestamp materially in the future is rejected rather than treated as fresh.
- Freshness of the manifest is distinct from executable availability. Even a just-created manifest does not prove a local or delegated invocation path.

## Secrets and browser state

The manifest must not contain browser/session secrets. Closed-field validation rejects fields such as:

- cookies;
- access or refresh tokens;
- session tokens;
- API keys;
- passwords;
- authorization headers;
- client secrets.

The bridge does not scrape browser cookies, private browser storage, authentication state, or ChatGPT session data.

## Import versus execution

The intended flow is:

```text
explicit capability export
-> ChatGPTCapabilityManifestBridge
-> validate source/provider/freshness
-> ExternalCapabilityCatalog
-> KNOWN / UNVERIFIED
```

Execution is a separate flow:

```text
verified local adapter
-> ExternalCapabilityCatalog.mark_availability(... AVAILABLE_LOCAL ...)

or

authenticated delegated provider/session
-> ExternalCapabilityCatalog.mark_availability(... AVAILABLE_DELEGATED ...)
```

Both executable states are time-bounded and require a separate verification timestamp. Remembering a ChatGPT capability must never silently make it executable inside the local J.A.R.V.I.S. runtime.

## Future integrations

A browser companion, ChatGPT connector, or another authenticated exporter may eventually generate the same manifest automatically. The stable contract should remain provider-observation metadata only so future transport changes do not weaken the distinction between **known capability** and **verified executable capability**.
