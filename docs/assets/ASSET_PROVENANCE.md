# J.A.R.V.I.S. visual asset provenance

Created for Milestone Zero on 2026-09-11. All graphics are original programmatic SVG compositions produced during this repository task. Shapes, layout and mark are editable source; no downloaded image, stock illustration, protected character artwork, external font or image-generation service was used. The user requested programmatic SVG as an acceptable creation method.

The geometric mark uses an open J inside a hexagonal boundary. Project-name usage identifies this repository; it does not imply affiliation with a fictional character or another vendor. The artwork describes project direction, and the diagrams explicitly disclose their implementation scope.

| SVG source path (repository relative) | Dimensions | Purpose | Provenance |
| --- | --- | --- | --- |
| `.github/assets/jarvis-hero.svg` | 1400 × 560 | README banner | Original grid, core graph and typography |
| `.github/assets/jarvis-social-preview.svg` | 1200 × 630 | Social sharing card, ready for manual hosting configuration | Original simplified identity composition |
| `.github/assets/jarvis-mark.svg` | 32 × 32 | Small cyan identity mark on dark backgrounds | Original geometry; transparent background |
| `.github/assets/jarvis-mark-mono.svg` | 32 × 32 | Monochrome mark for light backgrounds | Same geometry; single graphite color |
| `docs/assets/jarvis-runtime-architecture.svg` | 1200 × 900 | Actual/partial/planned architecture | Source inspection, selected test scope and canonical roadmap |
| `docs/assets/jarvis-cognitive-loop.svg` | 1200 × 740 | Target nine-stage lifecycle | Requested lifecycle; explicitly not live telemetry |
| `docs/assets/jarvis-memory-fabric.svg` | 1200 × 870 | Planned four-level memory architecture | Requested target; current vault support is narrower |
| `docs/assets/jarvis-cognitive-vault.svg` | 1200 × 840 | Faithful existing-note navigation map | Ten actual root MOC links, listed in [vault-map-sources.json](vault-map-sources.json) |

Every SVG has a same-directory, same-basename **PNG export at the same dimensions**. The [asset manifest](asset-manifest.json) records source metadata. The [validation manifest](../../reports/milestone-zero/20260911/artifact-validation.json) records content hashes, byte sizes, raster dimensions and check results. Rendered files are portable; no machine-specific font or tool path is embedded into them.

## Reproduction

From the repository root, generate the deterministic SVG sources using Python's standard library:

```powershell
python -B tooling/design/generate_assets.py
```

Optional PNG exports use Node.js and Sharp. With Sharp already available in the local environment:

```powershell
node tooling/design/render_assets.cjs
```

Alternatively pass an absolute path to an already installed Sharp module as the first argument. The renderer does not download or install packages. Milestone Zero used the host's bundled Node/Sharp dependency runtime. SVGs remain authoritative; PNG text rasterization can vary with installed system fonts.

## Usage and visual constraints

- Palette: graphite `#080f19`, panel navy `#101e2e`, cyan `#5de0ec`, blue `#84b5ff`, primary text `#edf5ff`, secondary text `#a9bfd1`.
- Typography: Segoe UI with Arial/sans-serif fallback. No external font requests.
- Status uses words and stroke patterns: solid = validated unit scope; dash-dot = partial; dashed = planned. Color is supplemental.
- The architecture graphic's 84-test reference describes the selected eight-suite baseline, not only the graph or a whole-system certificate.
- The vault map shows existing root MOC navigation only. It is a diagram, not an Obsidian screenshot or an inference of semantic relationships. Personal-memory note bodies were not used.
- No live HUD capture was taken. No diagram or image is represented as a product screenshot.
- Hero and social-preview maturity labels must remain visible. The card has been prepared locally; no repository-hosting social-preview setting has been changed.
- Use the cyan mark on dark surfaces and the graphite monochrome variant on light surfaces. The SVG source remains legible at its native 32-pixel size.

Local render inspection, small-size checks and document-link validation are described in the [Milestone Zero report](../../reports/MILESTONE_ZERO.md). These are asset checks, not a WCAG certification of the existing HUD.
