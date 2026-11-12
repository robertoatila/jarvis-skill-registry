"""Regenerate ``site/index.html`` from the template embedded below.

The tracked ``site/index.html`` has been edited by hand since this template was
written, so the two differ: running this script replaces the published page
with the older template.  It therefore writes only when run as a script and
only with ``--force``; importing the module has no effect.
"""
import sys
from pathlib import Path

SITE_INDEX = Path(__file__).resolve().parent.parent / "site" / "index.html"

html_content = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>J.A.R.V.I.S. — Sovereign Cognitive Runtime & Skill Registry for AI Agents</title>
  <meta name="description" content="Open-source local-first cognitive runtime for AI agents. 394 governed canonical skills, 42,872 repository radar in SQLite FTS5, Mark-LIV Quantum Cockpit, dual-layer episodic memory, and fail-closed cryptographic verification.">
  <meta name="theme-color" content="#05080e">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
  <meta name="author" content="Roberto Atila">
  <meta name="google-site-verification" content="zfVWOjLaEXH4FctU_rMp5X1qZIhtZF4rbd8TyR5dVsI">
  <link rel="canonical" href="https://jarvis-skill-registry.vercel.app/">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="/site.webmanifest">
  <meta property="og:title" content="J.A.R.V.I.S. — Sovereign Cognitive Runtime for AI Agents">
  <meta property="og:description" content="Make agents prove what worked. 394 governed skills, 42,872 repository radar, Mark-LIV Cockpit, episodic graph memory, and Merkle-verified execution: 100% local first.">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="J.A.R.V.I.S. Skill Registry">
  <meta property="og:url" content="https://jarvis-skill-registry.vercel.app/">
  <meta property="og:image" content="https://raw.githubusercontent.com/robertoatila/jarvis-skill-registry/main/.github/assets/jarvis-social-preview.png">
  <meta property="og:image:alt" content="J.A.R.V.I.S. Sovereign Cognitive Runtime: evidence-first AI agent infrastructure">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="J.A.R.V.I.S. — Sovereign Cognitive Runtime for AI Agents">
  <meta name="twitter:description" content="Local-first cognitive runtime with 394 skills, 42,872 repo radar, Mark-LIV cockpit and cryptographic evidence gates.">
  <meta name="twitter:image" content="https://raw.githubusercontent.com/robertoatila/jarvis-skill-registry/main/.github/assets/jarvis-social-preview.png">

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "J.A.R.V.I.S. Skill Registry & Cognitive Runtime",
    "alternateName": "J.A.R.V.I.S. Cognitive Runtime",
    "url": "https://jarvis-skill-registry.vercel.app/",
    "codeRepository": "https://github.com/robertoatila/jarvis-skill-registry",
    "downloadUrl": "https://github.com/robertoatila/jarvis-skill-registry/releases",
    "description": "A local-first sovereign cognitive runtime for AI agents with 394 governed skills, 42,872 repository radar matrix across 5 tactical squadrons, Mark-LIV Quantum Cockpit, dual-layer episodic memory, and fail-closed cryptographic verification.",
    "version": "0.2.0-rc",
    "programmingLanguage": ["Python", "JavaScript", "HTML5", "CSS3", "PowerShell"],
    "license": "https://www.apache.org/licenses/LICENSE-2.0",
    "runtimePlatform": ["Windows", "Linux", "macOS"],
    "keywords": "AI agents, agentic cognitive runtime, local-first AI, context engineering, tool routing, model routing, persistent memory, Obsidian cognitive vault, MCP gateway, verified execution",
    "sameAs": ["https://github.com/robertoatila/jarvis-skill-registry"]
  }
  </script>

  <style>
    :root {
      color-scheme: dark;
      --bg: #05080e;
      --bg2: #08101a;
      --panel: rgba(10, 18, 30, 0.78);
      --panel-hover: rgba(14, 25, 42, 0.92);
      --panel2: rgba(13, 23, 38, 0.96);
      --line: rgba(0, 242, 254, 0.16);
      --line2: rgba(0, 242, 254, 0.38);
      --text: #f8fafc;
      --muted: #94a3b8;
      --cyan: #00f2fe;
      --cyan-glow: rgba(0, 242, 254, 0.28);
      --blue: #3b82f6;
      --green: #10b981;
      --amber: #f59e0b;
      --purple: #a855f7;
      --red: #ef4444;
      --max: 1220px;
      --radius: 14px;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: radial-gradient(circle at 50% -10%, rgba(0, 242, 254, 0.16), transparent 38rem),
                  radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.1), transparent 28rem),
                  linear-gradient(180deg, var(--bg2), var(--bg) 40%, #030508);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
    }

    a { color: inherit; text-decoration: none; }
    a:focus-visible { outline: 2px solid var(--cyan); outline-offset: 4px; }
    .wrap { width: min(calc(100% - 48px), var(--max)); margin: auto; }

    /* Top Announcement Bar */
    .announcement {
      border-bottom: 1px solid var(--line);
      background: rgba(3, 8, 15, 0.88);
      backdrop-filter: blur(8px);
      color: #e2e8f0;
      font-size: 0.86rem;
      text-align: center;
      padding: 10px 16px;
    }
    .announcement a {
      color: var(--cyan);
      font-weight: 700;
      margin-left: 6px;
    }
    .announcement a:hover { text-decoration: underline; }

    /* Navigation */
    nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 22px 0;
      gap: 24px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      letter-spacing: 0.18em;
      font-weight: 900;
      font-size: 1.05rem;
      color: var(--text);
    }
    .brand .reactor-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--cyan);
      box-shadow: 0 0 10px var(--cyan);
      animation: pulse 2s infinite ease-in-out;
    }
    @keyframes pulse {
      0%, 100% { opacity: 0.6; transform: scale(0.9); }
      50% { opacity: 1; transform: scale(1.2); box-shadow: 0 0 16px var(--cyan); }
    }
    .navlinks {
      display: flex;
      gap: 22px;
      color: var(--muted);
      font-size: 0.92rem;
      font-weight: 500;
    }
    .navlinks a:hover { color: var(--cyan); }

    /* Hero Section */
    .hero {
      padding: 72px 0 54px;
      text-align: center;
    }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--cyan);
      letter-spacing: 0.16em;
      text-transform: uppercase;
      font-size: 0.78rem;
      font-weight: 800;
      padding: 6px 14px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(0, 242, 254, 0.06);
      margin-bottom: 24px;
    }
    h1 {
      font-size: clamp(2.75rem, 5.5vw, 4.5rem);
      line-height: 1.05;
      letter-spacing: -0.035em;
      margin: 0 auto 20px;
      max-width: 980px;
      font-weight: 900;
      text-wrap: balance;
    }
    .gradient {
      background: linear-gradient(110deg, #ffffff 15%, var(--cyan) 60%, #93c5fd 95%);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
    .lead {
      max-width: 68ch;
      margin: auto;
      color: var(--muted);
      font-size: clamp(1.05rem, 1.8vw, 1.25rem);
      line-height: 1.7;
      text-wrap: pretty;
    }
    .actions {
      display: flex;
      gap: 14px;
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 34px;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--line);
      background: var(--panel);
      padding: 13px 22px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 0.95rem;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      backdrop-filter: blur(8px);
    }
    .btn:hover {
      transform: translateY(-2px);
      border-color: var(--line2);
      background: var(--panel-hover);
      box-shadow: 0 8px 24px rgba(0, 242, 254, 0.12);
    }
    .btn.primary {
      background: linear-gradient(135deg, var(--cyan), var(--blue));
      color: #030b14;
      border: 0;
      box-shadow: 0 4px 18px var(--cyan-glow);
    }
    .btn.primary:hover {
      box-shadow: 0 8px 28px rgba(0, 242, 254, 0.45);
    }

    /* Trust / Verification Badges */
    .trustline {
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 12px 24px;
      margin-top: 28px;
      color: var(--muted);
      font-size: 0.9rem;
    }
    .trustline span {
      display: inline-flex;
      align-items: center;
      gap: 7px;
    }
    .trustline span:before {
      content: "•";
      color: var(--cyan);
      font-weight: 900;
      font-size: 1.2rem;
    }

    /* Interactive Terminal */
    .terminal-container {
      margin: 44px auto 0;
      max-width: 860px;
      text-align: left;
      border: 1px solid var(--line2);
      background: rgba(4, 9, 16, 0.95);
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: 0 35px 100px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 242, 254, 0.08);
      position: relative;
    }
    .terminal-header {
      padding: 12px 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(8, 16, 28, 0.9);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .terminal-tabs {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .tab-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--muted);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.82rem;
      cursor: pointer;
      font-family: var(--font-mono);
      font-weight: 600;
      transition: all 0.15s ease;
    }
    .tab-btn.active, .tab-btn:hover {
      background: rgba(0, 242, 254, 0.08);
      border-color: var(--line);
      color: var(--cyan);
    }
    .terminal-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .copy-btn {
      background: rgba(0, 242, 254, 0.08);
      border: 1px solid var(--line);
      color: var(--cyan);
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 0.78rem;
      font-family: var(--font-mono);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .copy-btn:hover {
      background: rgba(0, 242, 254, 0.16);
      border-color: var(--cyan);
    }
    .terminal-badge {
      font-size: 0.76rem;
      color: var(--green);
      font-family: var(--font-mono);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .terminal-badge:before {
      content: "";
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 6px var(--green);
    }
    .terminal-body {
      padding: 24px;
      font-family: var(--font-mono);
      font-size: 0.92rem;
      line-height: 1.7;
      color: #d8ecff;
      overflow-x: auto;
    }
    .terminal-body pre { margin: 0; }
    .cmd-comment { color: #5a7594; }
    .cmd-prompt { color: var(--cyan); user-select: none; }
    .cmd-param { color: var(--amber); }

    /* Key Numbers Grid */
    .metric-ribbon {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin: 60px auto 0;
    }
    .metric-card {
      border: 1px solid var(--line);
      background: var(--panel2);
      padding: 22px;
      border-radius: var(--radius);
      text-align: center;
      backdrop-filter: blur(8px);
    }
    .metric-card strong {
      display: block;
      font-size: clamp(2rem, 3.2vw, 2.75rem);
      letter-spacing: -0.035em;
      font-weight: 900;
      color: #ffffff;
      background: linear-gradient(135deg, #ffffff, var(--cyan));
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
    .metric-card span {
      display: block;
      color: var(--muted);
      font-size: 0.88rem;
      margin-top: 4px;
    }

    /* Sections */
    section { padding: 84px 0; }
    .section-kicker {
      color: var(--cyan);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-weight: 800;
      display: block;
      margin-bottom: 12px;
    }
    .section-title {
      font-size: clamp(2.1rem, 4vw, 3.4rem);
      letter-spacing: -0.035em;
      line-height: 1.1;
      margin: 0 0 18px;
      font-weight: 900;
      text-wrap: balance;
    }
    .section-lead {
      color: var(--muted);
      max-width: 68ch;
      font-size: 1.12rem;
      line-height: 1.7;
      margin: 0 0 40px;
      text-wrap: pretty;
    }

    /* Interactive Radar Search Box */
    .radar-box {
      border: 1px solid var(--line2);
      background: var(--panel2);
      border-radius: var(--radius);
      padding: 28px;
      margin-bottom: 40px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
    }
    .radar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }
    .radar-search-input {
      width: 100%;
      background: rgba(4, 9, 16, 0.9);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 1rem;
      color: var(--text);
      font-family: inherit;
      transition: all 0.2s ease;
    }
    .radar-search-input:focus {
      outline: none;
      border-color: var(--cyan);
      box-shadow: 0 0 16px var(--cyan-glow);
    }
    .radar-chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    .chip {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 5px 12px;
      border-radius: 999px;
      font-size: 0.82rem;
      cursor: pointer;
      color: var(--muted);
      transition: all 0.15s ease;
    }
    .chip:hover, .chip.active {
      background: rgba(0, 242, 254, 0.12);
      border-color: var(--cyan);
      color: var(--cyan);
    }
    .radar-results {
      margin-top: 20px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 12px;
      max-height: 280px;
      overflow-y: auto;
      padding-right: 6px;
    }
    .radar-item {
      padding: 12px 14px;
      background: rgba(6, 12, 22, 0.8);
      border: 1px solid var(--line);
      border-radius: 8px;
      font-size: 0.88rem;
      transition: all 0.15s ease;
    }
    .radar-item:hover {
      border-color: var(--cyan);
      background: rgba(10, 20, 36, 0.95);
    }
    .radar-item strong {
      display: block;
      color: var(--cyan);
      font-family: var(--font-mono);
      font-size: 0.86rem;
      margin-bottom: 4px;
    }
    .radar-item span {
      color: var(--muted);
      font-size: 0.8rem;
      display: block;
      line-height: 1.4;
    }

    /* 5 Squadrons Grid */
    .squadron-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 20px;
    }
    .squadron-card {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: var(--radius);
      padding: 28px;
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }
    .squadron-card:hover {
      border-color: var(--line2);
      transform: translateY(-3px);
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 242, 254, 0.08);
    }
    .squadron-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.76rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      padding: 4px 10px;
      border-radius: 6px;
      margin-bottom: 16px;
    }
    .sq-cyber { background: rgba(255, 85, 85, 0.12); color: #ff6b6b; border: 1px solid rgba(255, 85, 85, 0.25); }
    .sq-aegis { background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.25); }
    .sq-neuro { background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.25); }
    .sq-tactical { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.25); }
    .sq-hyperion { background: rgba(0, 242, 254, 0.12); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.25); }

    .squadron-card h3 {
      font-size: 1.3rem;
      margin: 0 0 12px;
      letter-spacing: -0.02em;
    }
    .squadron-card p {
      color: var(--muted);
      margin: 0 0 18px;
      font-size: 0.94rem;
      line-height: 1.65;
    }
    .squadron-tools {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .tool-tag {
      font-size: 0.78rem;
      font-family: var(--font-mono);
      padding: 3px 8px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #cbd5e1;
    }

    /* Core Architectural Highlights */
    .feature-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 36px;
      align-items: center;
      margin-bottom: 72px;
    }
    .feature-content h3 {
      font-size: 2rem;
      letter-spacing: -0.03em;
      margin: 0 0 16px;
      line-height: 1.2;
      text-wrap: balance;
    }
    .feature-content p {
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.75;
      margin: 0 0 24px;
      text-wrap: pretty;
    }
    .feature-box {
      border: 1px solid var(--line);
      background: var(--panel2);
      border-radius: var(--radius);
      padding: 32px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }

    /* HUD Visual Preview */
    .hud-preview {
      border: 1px solid var(--line2);
      background: rgba(5, 10, 18, 0.95);
      border-radius: var(--radius);
      padding: 24px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), inset 0 0 30px rgba(0, 242, 254, 0.05);
      font-family: var(--font-mono);
      font-size: 0.85rem;
    }
    .hud-titlebar {
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid var(--line);
      padding-bottom: 12px;
      margin-bottom: 16px;
      color: var(--cyan);
      font-weight: 800;
    }
    .hud-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .hud-cell {
      background: rgba(0, 242, 254, 0.04);
      border: 1px solid var(--line);
      padding: 10px 14px;
      border-radius: 8px;
    }
    .hud-cell-label {
      color: var(--muted);
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .hud-cell-val {
      color: #ffffff;
      font-weight: 700;
      font-size: 0.94rem;
      margin-top: 4px;
    }

    .checklist {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .checklist li {
      padding: 10px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: #cbd5e1;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      font-size: 0.96rem;
    }
    .checklist li:last-child { border-bottom: 0; }
    .checklist li:before {
      content: "✓";
      color: var(--green);
      font-weight: 800;
    }

    /* Lifecycle Banner */
    .flow-banner {
      border: 1px solid var(--line);
      background: linear-gradient(145deg, rgba(10, 20, 36, 0.9), rgba(5, 10, 18, 0.95));
      border-radius: var(--radius);
      padding: 34px 24px;
      text-align: center;
      margin: 40px 0;
      overflow-x: auto;
    }
    .flow-steps {
      display: inline-flex;
      align-items: center;
      gap: 14px;
      font-family: var(--font-mono);
      font-size: 0.9rem;
      font-weight: 700;
      white-space: nowrap;
    }
    .flow-step {
      padding: 8px 16px;
      border-radius: 8px;
      background: rgba(0, 242, 254, 0.08);
      border: 1px solid var(--line);
      color: var(--cyan);
    }
    .flow-arrow { color: var(--muted); }

    /* CTA Section */
    .cta-card {
      border: 1px solid var(--line2);
      border-radius: 20px;
      padding: clamp(36px, 6vw, 64px);
      background: radial-gradient(circle at 50% 0%, rgba(0, 242, 254, 0.15), transparent 70%),
                  linear-gradient(145deg, rgba(16, 32, 54, 0.6), rgba(6, 12, 22, 0.95));
      text-align: center;
      box-shadow: 0 30px 90px rgba(0, 0, 0, 0.4);
    }
    .cta-card h2 {
      font-size: clamp(2.2rem, 5vw, 3.6rem);
      letter-spacing: -0.035em;
      margin: 0 0 16px;
      font-weight: 900;
      text-wrap: balance;
    }
    .cta-card p {
      color: var(--muted);
      max-width: 68ch;
      margin: auto;
      font-size: 1.15rem;
      line-height: 1.72;
      text-wrap: pretty;
    }

    /* Footer */
    footer {
      border-top: 1px solid var(--line);
      color: var(--muted);
      padding: 44px 0 60px;
      font-size: 0.9rem;
    }
    .footer-row {
      display: flex;
      justify-content: space-between;
      gap: 24px;
      flex-wrap: wrap;
      align-items: center;
    }
    .footer-links {
      display: flex;
      gap: 20px;
    }
    .footer-links a:hover { color: var(--cyan); }

    @media (max-width: 900px) {
      .metric-ribbon { grid-template-columns: repeat(2, 1fr); }
      .feature-row { grid-template-columns: 1fr; }
      .hud-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 780px) {
      .navlinks { display: none; }
      .hero { padding-top: 48px; }
      .metric-ribbon { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="announcement">
    🚀 <strong>J.A.R.V.I.S. v0.2.0 Active Program:</strong> 394 Governed Skills · 42,872 Tactical Repositories · Mark-LIV Holographic Cockpit · Obsidian Second Brain · 
    <a href="https://github.com/robertoatila/jarvis-skill-registry" target="_blank" rel="noopener noreferrer">Explore on GitHub ↗</a>
  </div>

  <div class="wrap">
    <nav aria-label="Primary navigation">
      <a class="brand" href="/" aria-label="J.A.R.V.I.S. Home">
        <span class="reactor-dot"></span>
        J.A.R.V.I.S.
      </a>
      <div class="navlinks">
        <a href="#squadrons">The 5 Squadrons</a>
        <a href="#radar">Arsenal Radar</a>
        <a href="#cockpit">Mark-LIV Cockpit</a>
        <a href="#memory">Hippocampus Memory</a>
        <a href="#governance">SSP-v13.4 Governance</a>
        <a href="https://github.com/robertoatila/jarvis-skill-registry" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
      </div>
    </nav>

    <main>
      <!-- Hero -->
      <header class="hero">
        <div class="eyebrow">
          <span>⚡</span> Sovereign Local-First Cognitive Runtime
        </div>
        <h1>Make agents <span class="gradient">prove what worked.</span></h1>
        <p class="lead">
          A sovereign, local-first execution control plane for AI agents: 394 governed canonical skills, 42,872 curated repositories indexed in SQLite FTS5, episodic graph memory across 5,870+ Obsidian notes, neural voice synthesis, and fail-closed cryptographic verification.
        </p>

        <div class="actions">
          <a class="btn primary" href="https://github.com/robertoatila/jarvis-skill-registry" target="_blank" rel="noopener noreferrer">★ Star on GitHub ↗</a>
          <a class="btn" href="https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0" target="_blank" rel="noopener noreferrer">Download Release v0.1.0 ↗</a>
          <a class="btn" href="https://github.com/robertoatila/jarvis-skill-registry/blob/main/QUICKSTART.md" target="_blank" rel="noopener noreferrer">Read Quickstart Guide ↗</a>
        </div>

        <div class="trustline">
          <span>100% Local-First / Zero Cloud Lock-in</span>
          <span>798 Tests Passing (111 Suites)</span>
          <span>Sovereign Security Protocol SSP-v13.4</span>
          <span>Apache-2.0 License</span>
        </div>

        <!-- Interactive Terminal -->
        <div class="terminal-container" aria-label="Interactive Quickstart Terminal">
          <div class="terminal-header">
            <div class="terminal-tabs" role="tablist">
              <button class="tab-btn active" role="tab" aria-selected="true" data-tab="quickstart">1. Quickstart</button>
              <button class="tab-btn" role="tab" aria-selected="false" data-tab="remote">2. Mobile Companion</button>
              <button class="tab-btn" role="tab" aria-selected="false" data-tab="mcp">3. Sovereign MCP</button>
              <button class="tab-btn" role="tab" aria-selected="false" data-tab="doctor">4. Doctor Check</button>
            </div>
            <div class="terminal-actions">
              <button class="copy-btn" id="copy-cmd-btn" aria-label="Copy shell command to clipboard">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                <span id="copy-btn-text">Copy</span>
              </button>
              <div class="terminal-badge">Python 3.10+ Stdlib (Zero PIP Deps)</div>
            </div>
          </div>
          <div class="terminal-body" id="term-content">
            <pre><span class="cmd-comment"># Launch Mark-LIV Tactical Cockpit HUD with Neural Voice on port 8899</span>
<span class="cmd-prompt">$</span> git clone https://github.com/robertoatila/jarvis-skill-registry.git
<span class="cmd-prompt">$</span> cd jarvis-skill-registry
<span class="cmd-prompt">$</span> python jarvis.py</pre>
          </div>
        </div>

        <!-- Metric Ribbon -->
        <div class="metric-ribbon">
          <div class="metric-card">
            <strong>394</strong>
            <span>Governed Canonical Skills</span>
          </div>
          <div class="metric-card">
            <strong>42,872</strong>
            <span>Curated Repositories in SQLite FTS5</span>
          </div>
          <div class="metric-card">
            <strong>5,870+</strong>
            <span>Cognitive Vault Notes in Obsidian</span>
          </div>
          <div class="metric-card">
            <strong>&lt; 20 ms</strong>
            <span>Local SQLite FTS5 Search Latency</span>
          </div>
        </div>
      </header>

      <!-- The 5 Tactical Squadrons -->
      <section id="squadrons">
        <span class="section-kicker">The Alexandria Library of AI Engineering</span>
        <h2 class="section-title">The 5 Tactical Squadrons</h2>
        <p class="section-lead">
          All 394 skills and 42,872 curated repositories are deterministically cataloged into 5 specialized software and AI engineering squadrons:
        </p>

        <div class="squadron-grid">
          <!-- 01 Cyberspace -->
          <article class="squadron-card">
            <span class="squadron-badge sq-cyber">🦅 01 Cyberspace</span>
            <h3>Offensive Security & Pentest</h3>
            <p>BOLA/IDOR auditing, advanced SQL injection testing, DOM XSS scanning, binary reverse engineering, and multi-platform OSINT reconnaissance.</p>
            <div class="squadron-tools">
              <span class="tool-tag">burp-suite-testing</span>
              <span class="tool-tag">blackbird-osint</span>
              <span class="tool-tag">jadx</span>
              <span class="tool-tag">api-fuzzing</span>
              <span class="tool-tag">sqlmap</span>
            </div>
          </article>

          <!-- 02 Aegis -->
          <article class="squadron-card">
            <span class="squadron-badge sq-aegis">🛡️ 02 Aegis</span>
            <h3>Active Defense & Cryptographic Integrity</h3>
            <p>Merkle Root anchor validation, automated secrets rotation, OAuth2/OIDC boundaries, fail-closed quarantine isolation, and pre-publish hygiene audits.</p>
            <div class="squadron-tools">
              <span class="tool-tag">ssp-v13.4</span>
              <span class="tool-tag">merkle-tree</span>
              <span class="tool-tag">secrets-rotation</span>
              <span class="tool-tag">codebase-audit</span>
            </div>
          </article>

          <!-- 03 Neuro-Cognitive -->
          <article class="squadron-card">
            <span class="squadron-badge sq-neuro">🧠 03 Neuro-Cognitive</span>
            <h3>Autonomous Agents & Knowledge RAG</h3>
            <p>Multi-agent DAG task decomposition, in-memory vector search, hybrid retrieval, and knowledge graph associative linking via Obsidian notes.</p>
            <div class="squadron-tools">
              <span class="tool-tag">qdrant-vector</span>
              <span class="tool-tag">crewai</span>
              <span class="tool-tag">polars-engine</span>
              <span class="tool-tag">dspy</span>
              <span class="tool-tag">autogen</span>
            </div>
          </article>

          <!-- 04 Tactical -->
          <article class="squadron-card">
            <span class="squadron-badge sq-tactical">⚡ 04 Tactical</span>
            <h3>Systems, Kernel & Low-Level Automation</h3>
            <p>eBPF telemetry, high-throughput proxies, terminal multiplexing, media transcoding, audio synthesis, and native Windows automation.</p>
            <div class="squadron-tools">
              <span class="tool-tag">tmux-session</span>
              <span class="tool-tag">zellij</span>
              <span class="tool-tag">ffmpeg</span>
              <span class="tool-tag">aria2</span>
              <span class="tool-tag">edge-tts</span>
            </div>
          </article>

          <!-- 05 Hyperion -->
          <article class="squadron-card">
            <span class="squadron-badge sq-hyperion">🪐 05 Hyperion</span>
            <h3>Clean Architecture & Modern DevTools</h3>
            <p>High-conversion interface engineering, 60 FPS animations (Three.js & GSAP), Tailwind CSS tokens, strict Zod validation, and async APIs.</p>
            <div class="squadron-tools">
              <span class="tool-tag">threejs-animation</span>
              <span class="tool-tag">gsap-react</span>
              <span class="tool-tag">image-to-code</span>
              <span class="tool-tag">fastapi-pro</span>
              <span class="tool-tag">nextjs-router</span>
            </div>
          </article>
        </div>
      </section>

      <!-- Interactive Arsenal Radar Search Demo -->
      <section id="radar">
        <span class="section-kicker">Instant Local Search Benchmark</span>
        <h2 class="section-title">Tactical Arsenal Live Radar</h2>
        <p class="section-lead">
          Test the deterministic indexing speed locally. Filter canonical skills and high-impact repositories in under 5 milliseconds:
        </p>

        <div class="radar-box">
          <input type="text" id="radar-search" class="radar-search-input" placeholder="Search weapons by keyword, CVE, squadron, or category (e.g. osint, whisper, qdrant, sqlmap, fastapi)..." aria-label="Search arsenal radar">
          
          <div class="radar-chips">
            <button class="chip active" data-filter="all">All (394 Skills)</button>
            <button class="chip" data-filter="cyber">🦅 Cyberspace (Sec)</button>
            <button class="chip" data-filter="aegis">🛡️ Aegis (Defense)</button>
            <button class="chip" data-filter="neuro">🧠 Neuro-Cognitive (AI/RAG)</button>
            <button class="chip" data-filter="tactical">⚡ Tactical (Kernel/OS)</button>
            <button class="chip" data-filter="hyperion">🪐 Hyperion (Fullstack)</button>
          </div>

          <div class="radar-results" id="radar-results">
            <!-- Populated via JavaScript -->
          </div>
        </div>
      </section>

      <!-- The Mark-LIV Quantum Cockpit -->
      <section id="cockpit">
        <div class="feature-row">
          <div class="feature-content">
            <span class="section-kicker">Tactical Operations Center</span>
            <h3>Mark-LIV Cockpit & 3D Holographic Core</h3>
            <p>
              Designed under the Stark system command philosophy: pure HTML5 and ES Modules served locally at <code>http://127.0.0.1:8899</code> with real-time telemetry, memory monitoring, interactive 3D rotating holographic sphere at 60 FPS, and neural audio synthesis.
            </p>
            <div class="actions" style="justify-content: flex-start; margin-top: 0;">
              <a class="btn primary" href="https://github.com/robertoatila/jarvis-skill-registry/blob/main/docs/launch/DEMO_90S_EVIDENCE.md" target="_blank" rel="noopener noreferrer">View 82s Demo Receipt ↗</a>
            </div>
          </div>
          <div class="hud-preview" aria-label="Mark-LIV Quantum Cockpit Telemetry Display">
            <div class="hud-titlebar">
              <span>MARK-LIV TACTICAL HUD</span>
              <span>PORT 8899 • ONLINE</span>
            </div>
            <div class="hud-grid">
              <div class="hud-cell">
                <div class="hud-cell-label">Inference Router</div>
                <div class="hud-cell-val">Groq LPU (280ms)</div>
              </div>
              <div class="hud-cell">
                <div class="hud-cell-label">Offline Fallback</div>
                <div class="hud-cell-val">Ollama Local (0.00$)</div>
              </div>
              <div class="hud-cell">
                <div class="hud-cell-label">Neural TTS</div>
                <div class="hud-cell-val">Kokoro / Edge Stream</div>
              </div>
              <div class="hud-cell">
                <div class="hud-cell-label">Hippocampus Memory</div>
                <div class="hud-cell-val">5,870 Obsidian Nodes</div>
              </div>
            </div>
            <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); color: var(--muted); font-size: 0.78rem;">
              <span>Cryptographic Receipt: <code>SHA-256 e096cd3... MERKLE_VERIFIED</code></span>
            </div>
          </div>
        </div>
      </section>

      <!-- Episodic Memory & Cognitive Vault -->
      <section id="memory">
        <div class="feature-row" style="direction: rtl;">
          <div class="feature-content" style="direction: ltr;">
            <span class="section-kicker">Hippocampus Memory Architecture</span>
            <h3>Dual-Layer Memory & Obsidian Cognitive Vault</h3>
            <p>
              While most agents discard conversation context after each turn, J.A.R.V.I.S. maintains persistent, provenance-tracked memory through a dual-layer structure: an immutable cryptographic receipt ledger anchored with Merkle root, and an associative knowledge graph with over 5,870 notes in Obsidian.
            </p>
            <div class="actions" style="justify-content: flex-start; margin-top: 0;">
              <a class="btn" href="https://github.com/robertoatila/jarvis-skill-registry/blob/main/docs/vault/COGNITIVE_ATLAS.md" target="_blank" rel="noopener noreferrer">Explore the Cognitive Atlas ↗</a>
            </div>
          </div>
          <div class="feature-box" style="direction: ltr;">
            <ul class="checklist">
              <li><strong>33 Structural Maps of Content (MOCs):</strong> Curated blueprints for agent architectures, forensic audits, and tool registries.</li>
              <li><strong>5,870+ Atomic Notes:</strong> Interconnected markdown nodes that evolve after every completed mission.</li>
              <li><strong>Re-Ingestion Prevention:</strong> SHA-256 receipt tracking prevents recursive ingestion loops and data duplication.</li>
              <li><strong>Native Interactive Graph View:</strong> Real-time visualization of semantic clusters and wikilinks.</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Sovereign Security Protocol SSP-v13.4 -->
      <section id="governance">
        <span class="section-kicker">Fail-Closed Security Assurance</span>
        <h2 class="section-title">Sovereign Security Protocol (SSP-v13.4)</h2>
        <p class="section-lead">
          No tool execution or network dispatch is authorized without prior mathematical verification. Policies operate strictly in fail-closed mode.
        </p>

        <div class="flow-banner">
          <div class="flow-steps">
            <span class="flow-step">1. OBSERVE</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">2. PLAN</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">3. RESOLVE</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">4. EXECUTE</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">5. VERIFY</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">6. MEASURE</span>
            <span class="flow-arrow">→</span>
            <span class="flow-step">7. LEARN</span>
          </div>
        </div>

        <div class="squadron-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
          <div class="squadron-card">
            <h3>Quarantine Link (118 Tombstones)</h3>
            <p>8 subtrees and 118 cryptographic hashes of malicious or unstable artifacts blocked deterministically at the root.</p>
          </div>
          <div class="squadron-card">
            <h3>Pre-Publish Hygiene Gates</h3>
            <p>Over 3,070 files automatically audited with Shannon entropy scanning for zero credential leakage.</p>
          </div>
          <div class="squadron-card">
            <h3>Context Budget Governance</h3>
            <p>Strict byte-bounded context admission via <code>compile_context()</code> preventing token window exhaustion.</p>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section>
        <div class="cta-card">
          <span class="eyebrow" style="margin-bottom: 16px;">Sovereignty · Determinism · Verified Evidence</span>
          <h2>Launch J.A.R.V.I.S. on Your Workstation</h2>
          <p>
            Clone the repository, run the self-test, and launch the local Cockpit HUD in under 10 seconds. Zero complex package installation, pure Python Standard Library.
          </p>
          <div class="actions" style="margin-top: 32px;">
            <a class="btn primary" href="https://github.com/robertoatila/jarvis-skill-registry" target="_blank" rel="noopener noreferrer">★ Star on GitHub ↗</a>
            <a class="btn" href="https://github.com/robertoatila/jarvis-skill-registry/releases/tag/v0.1.0" target="_blank" rel="noopener noreferrer">Download Release v0.1.0 ↗</a>
            <a class="btn" href="https://github.com/robertoatila/jarvis-skill-registry/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener noreferrer">Read Contributing Guide ↗</a>
          </div>
        </div>
      </section>
    </main>

    <footer>
      <div class="footer-row">
        <span>J.A.R.V.I.S. Skill Registry & Cognitive Runtime · Apache-2.0 License · Cataloged projects retain their respective licenses.</span>
        <div class="footer-links">
          <a href="https://github.com/robertoatila/jarvis-skill-registry" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
          <a href="https://github.com/robertoatila/jarvis-skill-registry/releases" target="_blank" rel="noopener noreferrer">Releases ↗</a>
          <a href="/llms.txt" target="_blank" rel="noopener noreferrer">llms.txt</a>
        </div>
      </div>
    </footer>
  </div>

  <script>
    // Tab Data definitions
    const tabData = {
      quickstart: {
        cmd: "git clone https://github.com/robertoatila/jarvis-skill-registry.git\\ncd jarvis-skill-registry\\npython jarvis.py",
        html: `<pre><span class="cmd-comment"># Launch Mark-LIV Tactical Cockpit HUD with Neural Voice on port 8899</span>
<span class="cmd-prompt">$</span> git clone https://github.com/robertoatila/jarvis-skill-registry.git
<span class="cmd-prompt">$</span> cd jarvis-skill-registry
<span class="cmd-prompt">$</span> python jarvis.py</pre>`
      },
      remote: {
        cmd: "python jarvis.py --remote",
        html: `<pre><span class="cmd-comment"># Start server with secure Mobile Companion over Wi-Fi / LAN</span>
<span class="cmd-prompt">$</span> python jarvis.py <span class="cmd-param">--remote</span>
<span class="cmd-comment"># Terminal displays authenticated QR Code for instant smartphone camera pairing</span></pre>`
      },
      mcp: {
        cmd: "python tooling/jarvis_mcp_server.py",
        html: `<pre><span class="cmd-comment"># Register J.A.R.V.I.S. as a native Model Context Protocol (MCP) server</span>
<span class="cmd-prompt">$</span> python tooling/jarvis_mcp_server.py
<span class="cmd-comment"># Exposes 8 deterministic tools: query_arsenal, radar_search, verify_integrity</span></pre>`
      },
      doctor: {
        cmd: "python jarvis.py --doctor",
        html: `<pre><span class="cmd-comment"># Validate local prerequisites without making any network calls (&lt; 1s)</span>
<span class="cmd-prompt">$</span> python jarvis.py <span class="cmd-param">--doctor</span>
<span class="cmd-comment"># Returns runtime PASS status across Python, tooling, UI, and configs</span></pre>`
      }
    };

    let currentTab = 'quickstart';

    // Interactive Terminal Tab Switcher
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        currentTab = btn.getAttribute('data-tab');
        document.getElementById('term-content').innerHTML = tabData[currentTab].html;
      });
    });

    // Copy to Clipboard
    const copyBtn = document.getElementById('copy-cmd-btn');
    const copyBtnText = document.getElementById('copy-btn-text');
    copyBtn.addEventListener('click', async () => {
      const textToCopy = tabData[currentTab].cmd;
      try {
        await navigator.clipboard.writeText(textToCopy);
        copyBtnText.textContent = "Copied!";
        copyBtn.style.borderColor = "var(--green)";
        copyBtn.style.color = "var(--green)";
        setTimeout(() => {
          copyBtnText.textContent = "Copy";
          copyBtn.style.borderColor = "var(--line)";
          copyBtn.style.color = "var(--cyan)";
        }, 2000);
      } catch (err) {
        copyBtnText.textContent = "Failed";
      }
    });

    // Curated Arsenal Samples for Live Radar
    const arsenalData = [
      { name: "blackbird-osint", sq: "cyber", cat: "OSINT Reconnaissance", desc: "Fast OSINT search across 570+ social networks and public profiles." },
      { name: "burp-suite-testing", sq: "cyber", cat: "Web Pentest", desc: "Automated HTTP proxy and security testing for modern web apps." },
      { name: "sqlmap-database-pentest", sq: "cyber", cat: "SQL Injection", desc: "Automatic SQL injection detection and database takeover assessment." },
      { name: "jadx-decompiler", sq: "cyber", cat: "Reverse Engineering", desc: "Dex-to-Java decompiler for command-line Android APK analysis." },
      { name: "api-fuzzing-suite", sq: "cyber", cat: "API Security", desc: "Fuzzing engine for REST, SOAP, and GraphQL vulnerability discovery." },

      { name: "merkle-root-verifier", sq: "aegis", cat: "Cryptographic Anchor", desc: "SHA-256 Merkle root verification ensuring zero runtime tampering." },
      { name: "ssp-v13.4-governor", sq: "aegis", cat: "Security Protocol", desc: "Fail-closed execution barrier requiring math verification before dispatch." },
      { name: "secrets-rotator", sq: "aegis", cat: "Credentials", desc: "Zero-downtime secrets rotation and entropy leakage prevention." },
      { name: "quarantine-tombstone", sq: "aegis", cat: "Supply Chain", desc: "Blocks 118 malicious hashes and vulnerable subtrees at repo root." },

      { name: "qdrant-vector-hnsw", sq: "neuro", cat: "Vector Database", desc: "HNSW indexed dense vector retrieval with hybrid payload filtering." },
      { name: "obsidian-vault-curator", sq: "neuro", cat: "Cognitive Memory", desc: "Associative wikilink traversal across 5,870+ atomic markdown notes." },
      { name: "crewai-swarm-runner", sq: "neuro", cat: "Multi-Agent DAG", desc: "Orchestration engine for multi-agent autonomous mission delegation." },
      { name: "polars-lazy-engine", sq: "neuro", cat: "Streaming Data", desc: "Lightning fast DataFrame queries via Apache Arrow memory format." },
      { name: "dspy-prompt-optimizer", sq: "neuro", cat: "Prompt Optimization", desc: "Algorithmic prompt compilation and continuous metric evaluation." },

      { name: "whisper-speech-stt", sq: "tactical", cat: "Audio Recognition", desc: "Local multilingual speech recognition running offline on GPU/CPU." },
      { name: "kokoro-neural-tts", sq: "tactical", cat: "Neural Voice", desc: "82M parameter high-speed lightweight voice synthesis engine." },
      { name: "ffmpeg-transcoder", sq: "tactical", cat: "Media Engine", desc: "Hardware accelerated video/audio encoding and streaming pipelines." },
      { name: "tmux-session-operator", sq: "tactical", cat: "Terminal Multiplexer", desc: "Persistent terminal session management and command multiplexing." },
      { name: "pc-operator-automation", sq: "tactical", cat: "Windows Control", desc: "PowerShell and Win32 hardware telemetry and background daemon runtime." },

      { name: "threejs-holographic-core", sq: "hyperion", cat: "3D Visuals", desc: "Fibonacci 160-particle holographic sphere rotating at 60 FPS." },
      { name: "fastapi-pro-runtime", sq: "hyperion", cat: "High-Perf API", desc: "Asynchronous Python REST API with Pydantic v2 strict schema models." },
      { name: "nextjs-app-router", sq: "hyperion", cat: "React Shell", desc: "Modern App Router architecture with streaming and Server Components." },
      { name: "gsap-react-timelines", sq: "hyperion", cat: "Smooth Motion", desc: "Hardware accelerated reactive physics and timeline orchestration." },
      { name: "zod-runtime-validator", sq: "hyperion", cat: "Type Boundaries", desc: "Strict schema boundary parser preventing corrupted JSON injection." }
    ];

    function renderRadar(items) {
      const container = document.getElementById('radar-results');
      if (items.length === 0) {
        container.innerHTML = '<div style="grid-column: 1/-1; color: var(--muted); padding: 18px; text-align: center;">No matching weapons or repositories found. Try another keyword.</div>';
        return;
      }
      container.innerHTML = items.map(item => `
        <div class="radar-item">
          <strong>${item.name}</strong>
          <span>${item.desc}</span>
        </div>
      `).join('');
    }

    renderRadar(arsenalData);

    const searchInput = document.getElementById('radar-search');
    const chips = document.querySelectorAll('.chip');
    let activeFilter = 'all';

    function filterRadar() {
      const query = searchInput.value.toLowerCase().trim();
      const filtered = arsenalData.filter(item => {
        const matchesFilter = activeFilter === 'all' || item.sq === activeFilter;
        const matchesQuery = query === '' || 
          item.name.toLowerCase().includes(query) || 
          item.cat.toLowerCase().includes(query) || 
          item.desc.toLowerCase().includes(query);
        return matchesFilter && matchesQuery;
      });
      renderRadar(filtered);
    }

    searchInput.addEventListener('input', filterRadar);

    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        activeFilter = chip.getAttribute('data-filter');
        filterRadar();
      });
    });
  </script>
</body>
</html>
'''


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    current = SITE_INDEX.read_text(encoding="utf-8") if SITE_INDEX.is_file() else None
    if current == html_content:
        print("site/index.html already matches the embedded template")
        return 0
    if "--force" not in args:
        print(
            "site/index.html differs from the embedded template; nothing written.\n"
            "Pass --force to replace the tracked page with the template.",
            file=sys.stderr,
        )
        return 1
    SITE_INDEX.write_text(html_content, encoding="utf-8")
    print(f"Generated site/index.html successfully ({len(html_content)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
