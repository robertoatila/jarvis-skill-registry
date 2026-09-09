---
name: deckgl-geospatial-visualization
description: High-performance WebGL2 and WebGPU large-scale reactive data layer and geospatial visualization engine.
---

# Deck.gl Large-Scale WebGL2 Data Visualization

High-performance GPU-accelerated rendering of massive datasets (100k+ points, arcs, polygons, hexagons) for telemetry dashboards, autonomous agent swarm heatmaps, and spatial graphs.

## Core Visual Architecture

```text
[Raw Telemetry Data] ──► [DeckGL Instanced Buffer] ──► [WebGL2 / WebGPU Pipeline] ──► 60 FPS Canvas HUD
```

## Production Implementation: Standalone HTML/Canvas Component

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <script src="https://unpkg.com/deck.gl@latest/dist.min.js"></script>
  <style>
    body { margin: 0; background: #050a12; overflow: hidden; }
    #deck-canvas { width: 100vw; height: 100vh; position: absolute; }
  </style>
</head>
<body>
  <canvas id="deck-canvas"></canvas>
  <script>
    const { Deck, ScatterplotLayer, ArcLayer } = deck;

    const nodes = [
      { id: 'JARVIS-Core', coords: [-46.6333, -23.5505], size: 40, color: [0, 242, 254] },
      { id: 'Swarm-Cyber', coords: [-46.7000, -23.5000], size: 25, color: [244, 63, 94] },
      { id: 'Swarm-Agents', coords: [-46.5500, -23.6000], size: 30, color: [0, 245, 160] }
    ];

    const arcs = [
      { source: [-46.6333, -23.5505], target: [-46.7000, -23.5000] },
      { source: [-46.6333, -23.5505], target: [-46.5500, -23.6000] }
    ];

    new Deck({
      canvas: 'deck-canvas',
      initialViewState: { longitude: -46.6333, latitude: -23.5505, zoom: 11, pitch: 45, bearing: 0 },
      controller: true,
      layers: [
        new ScatterplotLayer({
          id: 'nodes-layer',
          data: nodes,
          getPosition: d => d.coords,
          getRadius: d => d.size * 10,
          getFillColor: d => d.color,
          pickable: true
        }),
        new ArcLayer({
          id: 'arcs-layer',
          data: arcs,
          getSourcePosition: d => d.source,
          getTargetPosition: d => d.target,
          getSourceColor: [0, 242, 254, 200],
          getTargetColor: [168, 85, 247, 200],
          getWidth: 2
        })
      ]
    });
  </script>
</body>
</html>
```
