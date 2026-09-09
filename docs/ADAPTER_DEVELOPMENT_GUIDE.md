# Target Platform Adapter Development Guide

## Overview

Adapters allow the Skill Registry to translate canonical skill structures into platform-specific configurations without mutating canonical sources.

## Adapter Architecture

Each adapter lives in `adapters/<platform>/adapter.json` and adheres to `schemas/adapter.schema.json`.

```json
{
  "schema_version": "1.0.0",
  "adapter_id": "adp-custom-v1",
  "target_provider": "CUSTOM_AGENT",
  "transformation_mode": "PASSTHROUGH",
  "parameters": {
    "preserve_frontmatter": true,
    "target_extension": ".md",
    "collision_policy": "FAIL_ON_CONFLICT"
  }
}
```

## Adding an Adapter Step-by-Step

1. **Create Adapter Directory**:
   Create `adapters/<platform_id>/adapter.json`.

2. **Register Target Layout**:
   In `schemas/target-layouts.json`, register the platform's standard global and workspace skill path templates.

3. **Register Capabilities**:
   In `schemas/platform-capabilities.json`, add runtime capabilities (supported file types, instruction formats, max prompt size).

4. **Verify Lifecycle**:
   Run `Invoke-DistributionEngineTests.ps1` to ensure the adapter executes dry-run preview, atomic distribution, and clean uninstall.
