import math
from pathlib import Path

ROOT = Path(".")

# 1. GENERATE BIG COLORFUL GRAPH CONSTELLATION SVG (2000 x 1200)
width = 2000
height = 1200
cx, cy = 1000, 610

clusters = [
    {"name": "CYBERSPACE (SEC & OSINT)", "color": "#f43f5e", "angle": -150, "radius": 440, "nodes": ["blackbird", "burp-suite", "sqlmap", "jadx", "api-fuzzing", "owasp-top10", "sast-semgrep"]},
    {"name": "AEGIS (ACTIVE DEFENSE)", "color": "#34d399", "angle": -90, "radius": 380, "nodes": ["ssp-v13.4", "merkle-tree", "secrets-rotation", "quarantine", "token-governance", "fail-closed"]},
    {"name": "NEURO-COGNITIVE (AGENTS)", "color": "#a78bfa", "angle": -30, "radius": 440, "nodes": ["qdrant-vector", "crewai-swarm", "polars-engine", "dspy-compiler", "obsidian-vault", "hippocampus", "memory-fabric"]},
    {"name": "TACTICAL (KERNEL & OS)", "color": "#f59e0b", "angle": 30, "radius": 440, "nodes": ["pc-operator", "whisper-stt", "kokoro-tts", "tmux-multiplex", "ffmpeg-transcode", "ollama-local"]},
    {"name": "HYPERION (FULLSTACK & UI)", "color": "#3b82f6", "angle": 90, "radius": 385, "nodes": ["threejs-3d", "fastapi-pro", "nextjs-router", "gsap-react", "zod-validator", "cockpit-hud"]},
    {"name": "QUANTUM (ATLAS & BENCH)", "color": "#00e5ff", "angle": 150, "radius": 440, "nodes": ["vault-atlas", "context-budget", "graph-universe", "remote-host", "tailscale-mesh", "dag-planner"]},
]

def quad_curve(x1, y1, x2, y2, bend=0.14):
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    dx, dy = x2 - x1, y2 - y1
    qx = mx - dy * bend
    qy = my + dx * bend
    return f"M{x1:.1f} {y1:.1f} Q{qx:.1f} {qy:.1f} {x2:.1f} {y2:.1f}"

svg_elements = []

# Defs: Nebulae, Golden Core Glow, Synaptic Filter
svg_elements.append('''<defs>
  <radialGradient id="nebulaBg" cx="50%" cy="51%" r="60%">
    <stop offset="0%" stop-color="#ffd700" stop-opacity="0.11"/>
    <stop offset="28%" stop-color="#00e5ff" stop-opacity="0.08"/>
    <stop offset="68%" stop-color="#09152b" stop-opacity="0.92"/>
    <stop offset="100%" stop-color="#03060c" stop-opacity="1"/>
  </radialGradient>
  <radialGradient id="goldenCore" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#fffbeb" stop-opacity="1"/>
    <stop offset="35%" stop-color="#ffd700" stop-opacity="0.98"/>
    <stop offset="72%" stop-color="#f59e0b" stop-opacity="0.82"/>
    <stop offset="100%" stop-color="#78350f" stop-opacity="0"/>
  </radialGradient>
  <filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>''')

# Background
svg_elements.append(f'''<rect width="{width}" height="{height}" fill="#03060c" rx="18"/>''')
svg_elements.append(f'''<rect width="{width}" height="{height}" fill="url(#nebulaBg)" rx="18" stroke="#74cdff" stroke-width="1.5" stroke-opacity="0.32"/>''')

# Cosmic grid
grid_paths = []
for x in range(0, width + 1, 100):
    grid_paths.append(f"M{x} 0 V{height}")
for y in range(0, height + 1, 100):
    grid_paths.append(f"M0 {y} H{width}")
svg_elements.append(f'''<path d="{' '.join(grid_paths)}" stroke="#74cdff" stroke-width="0.6" opacity="0.065" fill="none"/>''')

# Outer star dust halo (deterministic golden-angle constellation dust)
for s in range(180):
    ang = s * 2.399963
    rad_s = 170 + ((s * 37) % 410)
    sx = cx + rad_s * 1.45 * math.cos(ang)
    sy = cy + rad_s * 0.92 * math.sin(ang)
    if 60 < sx < width - 60 and 165 < sy < height - 80:
        col = clusters[s % len(clusters)]["color"] if s % 3 else "#ffd700"
        op = 0.22 + (s % 5) * 0.08
        r_dot = 1.1 + (s % 3) * 0.6
        svg_elements.append(f'''<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r_dot:.1f}" fill="{col}" opacity="{op:.2f}"/>''')

# Concentric orbit rings
for idx_r, r in enumerate([165, 290, 410, 520]):
    col_r = "#ffd700" if idx_r == 0 else "#74cdff"
    op_r = "0.26" if idx_r == 0 else "0.14"
    svg_elements.append(f'''<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col_r}" stroke-width="1.1" stroke-dasharray="4 10" opacity="{op_r}"/>''')

# Connecting curved synaptic filaments between adjacent and opposite clusters
for i in range(len(clusters)):
    for step in (1, 2):
        c1 = clusters[i]
        c2 = clusters[(i + step) % len(clusters)]
        rad1 = math.radians(c1["angle"])
        x1 = cx + c1["radius"] * 1.32 * math.cos(rad1)
        y1 = cy + c1["radius"] * 0.92 * math.sin(rad1)
        rad2 = math.radians(c2["angle"])
        x2 = cx + c2["radius"] * 1.32 * math.cos(rad2)
        y2 = cy + c2["radius"] * 0.92 * math.sin(rad2)
        d_arc = quad_curve(x1, y1, x2, y2, bend=0.16 if step == 1 else -0.22)
        svg_elements.append(f'''<path d="{d_arc}" fill="none" stroke="#74cdff" stroke-width="1.1" stroke-opacity="0.22" stroke-dasharray="5 7"/>''')

# Curved glowing trunks from Center to Clusters
for idx_c, c in enumerate(clusters):
    rad = math.radians(c["angle"])
    x = cx + c["radius"] * 1.32 * math.cos(rad)
    y = cy + c["radius"] * 0.92 * math.sin(rad)
    d_trunk = quad_curve(cx, cy, x, y, bend=0.11 if idx_c % 2 == 0 else -0.11)
    svg_elements.append(f'''<path d="{d_trunk}" fill="none" stroke="{c['color']}" stroke-width="2.2" stroke-opacity="0.58"/>''')

# Cluster subnodes & labels
for c in clusters:
    rad = math.radians(c["angle"])
    cluster_x = cx + c["radius"] * 1.32 * math.cos(rad)
    cluster_y = cy + c["radius"] * 0.92 * math.sin(rad)
    color = c["color"]

    # Big Cluster Hub
    svg_elements.append(f'''<circle cx="{cluster_x:.1f}" cy="{cluster_y:.1f}" r="42" fill="rgba(7, 14, 28, 0.92)" stroke="{color}" stroke-width="3" filter="url(#softGlow)"/>''')
    svg_elements.append(f'''<circle cx="{cluster_x:.1f}" cy="{cluster_y:.1f}" r="25" fill="{color}" fill-opacity="0.24"/>''')
    svg_elements.append(f'''<circle cx="{cluster_x:.1f}" cy="{cluster_y:.1f}" r="9" fill="{color}"/>''')

    # Cluster Label
    svg_elements.append(f'''<text x="{cluster_x:.1f}" y="{cluster_y + 62:.1f}" font-size="14" fill="{color}" font-weight="900" text-anchor="middle" letter-spacing="1.2">{c['name']}</text>''')

    # Subnodes radiating outwards with curved filaments
    num_nodes = len(c["nodes"])
    for j, node_name in enumerate(c["nodes"]):
        offset_angle = rad + math.radians((j - (num_nodes - 1) / 2) * 24)
        sub_dist = 122 if j % 2 == 0 else 152
        sx = cluster_x + sub_dist * math.cos(offset_angle)
        sy = cluster_y + sub_dist * math.sin(offset_angle)

        d_sub = quad_curve(cluster_x, cluster_y, sx, sy, bend=0.18 if j % 2 == 0 else -0.18)
        svg_elements.append(f'''<path d="{d_sub}" fill="none" stroke="{color}" stroke-width="1.15" stroke-opacity="0.45"/>''')
        svg_elements.append(f'''<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7.5" fill="{color}" stroke="#ffffff" stroke-width="1.4"/>''')
        svg_elements.append(f'''<rect x="{sx - 50:.1f}" y="{sy + 11:.1f}" width="100" height="19" rx="4" fill="rgba(5, 11, 22, 0.9)" stroke="{color}" stroke-width="0.65" stroke-opacity="0.75"/>''')
        svg_elements.append(f'''<text x="{sx:.1f}" y="{sy + 24:.1f}" font-size="9.5" fill="#f8fafc" font-family="monospace" text-anchor="middle">{node_name}</text>''')

# Central Master Core (00 MOC / Animal Logic Golden Consciousness Sphere)
svg_elements.append(f'''<circle cx="{cx}" cy="{cy}" r="118" fill="url(#goldenCore)" opacity="0.55"/>''')
svg_elements.append(f'''<circle cx="{cx}" cy="{cy}" r="88" fill="rgba(8, 14, 28, 0.92)" stroke="#ffd700" stroke-width="2.6" filter="url(#softGlow)"/>''')
svg_elements.append(f'''<circle cx="{cx}" cy="{cy}" r="106" fill="none" stroke="#74cdff" stroke-width="1.3" stroke-dasharray="5 9" opacity="0.65"/>''')
svg_elements.append(f'''<circle cx="{cx}" cy="{cy}" r="52" fill="rgba(255, 215, 0, 0.22)" stroke="#f59e0b" stroke-width="1.2"/>''')
svg_elements.append(f'''<circle cx="{cx}" cy="{cy}" r="22" fill="#ffd700" filter="url(#softGlow)"/>''')
svg_elements.append(f'''<circle cx="{cx}" cy="{cy}" r="10" fill="#fffbeb"/>''')
svg_elements.append(f'''<text x="{cx}" y="{cy + 128}" font-size="16" fill="#ffd700" font-weight="900" text-anchor="middle" letter-spacing="2.2">00 COGNITIVE VAULT MOC</text>''')
svg_elements.append(f'''<text x="{cx}" y="{cy + 148}" font-size="12" fill="#cbd5e1" text-anchor="middle">5,870+ Markdown Nodes • Synaptic Constellation • Merkle Anchored</text>''')

# Top Banner Header
svg_elements.append(f'''<rect x="60" y="42" width="460" height="34" rx="17" fill="rgba(255, 215, 0, 0.08)" stroke="#ffd700" stroke-width="1" stroke-opacity="0.45"/>''')
svg_elements.append(f'''<circle cx="80" cy="59" r="5" fill="#ffd700"/>''')
svg_elements.append(f'''<text x="96" y="64" font-size="12" fill="#ffd700" font-weight="800" letter-spacing="2">J.A.R.V.I.S. // OBSIDIAN SECOND BRAIN GRAPH</text>''')
svg_elements.append(f'''<text x="60" y="114" font-size="38" fill="#f8fafc" font-weight="900" letter-spacing="-0.8">Cognitive Vault Visual Constellation</text>''')
svg_elements.append(f'''<text x="60" y="142" font-size="15" fill="#94a3b8">Curved associative topology linking governed skills, 42,872 tactical repositories, autonomous squadrons, and persistent episodic memory.</text>''')

# Bottom Telemetry Bar
svg_elements.append(f'''<rect x="60" y="1126" width="1880" height="44" rx="9" fill="rgba(8, 15, 28, 0.88)" stroke="#74cdff" stroke-width="1" stroke-opacity="0.32"/>''')
svg_elements.append(f'''<circle cx="84" cy="1148" r="5" fill="#34d399"/>''')
svg_elements.append(f'''<text x="102" y="1152" font-size="12.5" fill="#f8fafc" font-weight="700">GRAPH STATUS: 6 QUANTUM CONSTELLATIONS CLUSTERED • CURVED SYNAPTIC FILAMENTS • ZERO CIRCULAR DEPENDENCIES • MERKLE VERIFIED</text>''')

graph_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<g font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
{' '.join(svg_elements)}
</g>
</svg>'''

(ROOT / "docs" / "assets" / "cognitive-vault-graph-map.svg").write_text(graph_svg, encoding="utf-8")
print("Generated docs/assets/cognitive-vault-graph-map.svg successfully (2000x1200).")

# 2. GENERATE VIBRANT SOCIAL PREVIEW SVG (1200 x 630)
social_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
  <title id="title">J.A.R.V.I.S. — Sovereign Cognitive Runtime</title>
  <desc id="desc">Local-first autonomous cognitive runtime and sovereign skill registry for AI agents.</desc>
  <g font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
    <rect width="1200" height="630" fill="#05080e" rx="14" stroke="#74cdff" stroke-width="1.5" stroke-opacity="0.4"/>

    <!-- Fine Grid Background -->
    <g opacity="0.12">
      <path d="M0 0 V630 M60 0 V630 M120 0 V630 M180 0 V630 M240 0 V630 M300 0 V630 M360 0 V630 M420 0 V630 M480 0 V630 M540 0 V630 M600 0 V630 M660 0 V630 M720 0 V630 M780 0 V630 M840 0 V630 M900 0 V630 M960 0 V630 M1020 0 V630 M1080 0 V630 M1140 0 V630" fill="none" stroke="#74cdff" stroke-width="1"/>
      <path d="M0 0 H1200 M0 60 H1200 M0 120 H1200 M0 180 H1200 M0 240 H1200 M0 300 H1200 M0 360 H1200 M0 420 H1200 M0 480 H1200 M0 540 H1200 M0 600 H1200" fill="none" stroke="#74cdff" stroke-width="1"/>
    </g>

    <!-- Header Badge -->
    <rect x="56" y="50" width="320" height="30" rx="15" fill="rgba(0, 242, 254, 0.08)" stroke="#74cdff" stroke-width="1" stroke-opacity="0.4"/>
    <circle cx="72" cy="65" r="4" fill="#74cdff"/>
    <text x="86" y="70" font-size="11" fill="#74cdff" font-weight="800" letter-spacing="2">SOVEREIGN COGNITIVE RUNTIME</text>

    <!-- Project Title -->
    <text x="56" y="185" font-size="94" fill="#f8fafc" font-weight="900" letter-spacing="-2">J.A.R.V.I.S.</text>
    <text x="58" y="235" font-size="22" fill="#74cdff" font-weight="800" letter-spacing="3">AUTONOMOUS COGNITIVE RUNTIME // V0.2.0 TRACK</text>
    <text x="58" y="280" font-size="17" fill="#94a3b8" font-weight="400">Bounded Context Admission • Persistent Episodic Memory • Mathematical Verification</text>

    <!-- 5 Squadron Color Pills -->
    <g transform="translate(58, 320)">
      <rect x="0" y="0" width="170" height="36" rx="8" fill="rgba(255, 59, 92, 0.12)" stroke="#f43f5e" stroke-width="1"/>
      <circle cx="16" cy="18" r="4" fill="#f43f5e"/>
      <text x="28" y="23" font-size="11" fill="#f43f5e" font-weight="800">01 CYBERSPACE</text>

      <rect x="180" y="0" width="140" height="36" rx="8" fill="rgba(16, 185, 129, 0.12)" stroke="#34d399" stroke-width="1"/>
      <circle cx="196" cy="18" r="4" fill="#34d399"/>
      <text x="208" y="23" font-size="11" fill="#34d399" font-weight="800">02 AEGIS</text>

      <rect x="330" y="0" width="150" height="36" rx="8" fill="rgba(192, 132, 252, 0.12)" stroke="#a78bfa" stroke-width="1"/>
      <circle cx="346" cy="18" r="4" fill="#a78bfa"/>
      <text x="358" y="23" font-size="11" fill="#a78bfa" font-weight="800">03 NEURO</text>

      <rect x="490" y="0" width="150" height="36" rx="8" fill="rgba(251, 191, 36, 0.12)" stroke="#fbbf24" stroke-width="1"/>
      <circle cx="506" cy="18" r="4" fill="#fbbf24"/>
      <text x="518" y="23" font-size="11" fill="#fbbf24" font-weight="800">04 TACTICAL</text>

      <rect x="650" y="0" width="150" height="36" rx="8" fill="rgba(56, 189, 248, 0.12)" stroke="#3b82f6" stroke-width="1"/>
      <circle cx="666" cy="18" r="4" fill="#3b82f6"/>
      <text x="678" y="23" font-size="11" fill="#3b82f6" font-weight="800">05 HYPERION</text>
    </g>

    <!-- Key Metrics Cards Row -->
    <g transform="translate(58, 385)">
      <rect x="0" y="0" width="180" height="85" rx="10" fill="rgba(10, 18, 30, 0.85)" stroke="#74cdff" stroke-width="1" stroke-opacity="0.3"/>
      <text x="18" y="38" font-size="28" fill="#ffffff" font-weight="800">394</text>
      <text x="18" y="64" font-size="12" fill="#94a3b8" font-weight="600">Governed Skills</text>

      <rect x="195" y="0" width="200" height="85" rx="10" fill="rgba(10, 18, 30, 0.85)" stroke="#74cdff" stroke-width="1" stroke-opacity="0.3"/>
      <text x="213" y="38" font-size="28" fill="#74cdff" font-weight="800">42,872</text>
      <text x="213" y="64" font-size="12" fill="#94a3b8" font-weight="600">Repos (SQLite FTS5)</text>

      <rect x="410" y="0" width="180" height="85" rx="10" fill="rgba(10, 18, 30, 0.85)" stroke="#74cdff" stroke-width="1" stroke-opacity="0.3"/>
      <text x="428" y="38" font-size="28" fill="#34d399" font-weight="800">5,870+</text>
      <text x="428" y="64" font-size="12" fill="#94a3b8" font-weight="600">Obsidian Nodes</text>

      <rect x="605" y="0" width="195" height="85" rx="10" fill="rgba(10, 18, 30, 0.85)" stroke="#74cdff" stroke-width="1" stroke-opacity="0.3"/>
      <text x="623" y="38" font-size="28" fill="#3b82f6" font-weight="800">798 PASS</text>
      <text x="623" y="64" font-size="12" fill="#94a3b8" font-weight="600">111 Master Suites</text>
    </g>

    <!-- Bottom Contract Text -->
    <text x="58" y="525" font-size="12" fill="#64748b" font-weight="600" letter-spacing="1">ZERO PIP DEPENDENCIES ON LAUNCHER • STARK MARK-LIV COCKPIT (:8899) • SHA-256 MERKLE ANCHORED</text>
    <text x="58" y="565" font-size="14" fill="#74cdff" font-weight="700">HTTPS://JARVIS-SKILL-REGISTRY.VERCEL.APP</text>

    <!-- Right Side Holographic Reactor Sphere -->
    <g transform="translate(1030, 310)">
      <circle cx="0" cy="0" r="140" fill="rgba(10, 18, 30, 0.9)" stroke="#74cdff" stroke-width="2" stroke-opacity="0.6"/>
      <circle cx="0" cy="0" r="170" fill="none" stroke="#3b82f6" stroke-width="1" stroke-opacity="0.3" stroke-dasharray="4 8"/>
      <circle cx="0" cy="0" r="100" fill="none" stroke="#74cdff" stroke-width="1" stroke-opacity="0.5"/>
      
      <circle cx="0" cy="0" r="22" fill="#74cdff" opacity="0.85"/>
      <circle cx="0" cy="0" r="10" fill="#ffffff"/>

      <circle cx="70" cy="-40" r="5" fill="#3b82f6"/>
      <line x1="0" y1="0" x2="70" y2="-40" stroke="#3b82f6" stroke-width="1" opacity="0.6"/>

      <circle cx="-80" cy="45" r="5" fill="#34d399"/>
      <line x1="0" y1="0" x2="-80" y2="45" stroke="#34d399" stroke-width="1" opacity="0.6"/>

      <circle cx="50" cy="80" r="5" fill="#fbbf24"/>
      <line x1="0" y1="0" x2="50" y2="80" stroke="#fbbf24" stroke-width="1" opacity="0.6"/>

      <circle cx="-65" cy="-65" r="5" fill="#a78bfa"/>
      <line x1="0" y1="0" x2="-65" y2="-65" stroke="#a78bfa" stroke-width="1" opacity="0.6"/>
    </g>
  </g>
</svg>'''

(ROOT / ".github" / "assets" / "jarvis-social-preview.svg").write_text(social_svg, encoding="utf-8")
print("Generated .github/assets/jarvis-social-preview.svg successfully (1200x630).")
