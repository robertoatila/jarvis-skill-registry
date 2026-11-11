# Visual reference archive

This directory is reserved for source visual references that should remain openable after any raw design-tool export is removed.

## Current provenance

At the start of the JARVIS Experience System v2 work, the repository had **no** `design-system-export/` directory. A recursive repository inspection also found no Google Labs/Stitch `DESIGN.md`, exported reference HTML, design-system adherence lint config, nested component export, thumbnail bundle or tool manifest to migrate.

Therefore:

- imported reference HTML files: **0**;
- imported design-tool assets: **0**;
- duplicate export conflicts resolved: **0**;
- raw export directories deleted: **0**.

This record is intentional. It prevents a later maintainer or agent from inferring that a missing export was silently discarded.

If a real reference export is added later, preserve only visual-reference material here, fix its relative asset paths so each HTML file still opens independently, and keep production primitives in the parent `design-system/` directory.
