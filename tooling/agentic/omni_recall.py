# -*- coding: utf-8 -*-
"""
omni_recall.py // J.A.R.V.I.S. Sovereign Cognitive Recall & Intelligence Grounding
Pure Python 3.10+ Standard Library (Zero PIP Dependencies)

Dynamically extracts and synthesizes relevant domain intelligence from:
1. 165 Governed Skills in E:/.skill-registry/skills
2. 28,634 Curated Arsenal Repositories in D:/Program Files/jarvis-arsenal/data/arsenal_library.sqlite (FTS5)
3. 5,870+ Obsidian Notes and MOCs in the Cognitive Vault

Injects bounded, high-density context into the model's prompt so J.A.R.V.I.S.
acts with deep domain mastery over Roberto's sovereign workstation.
"""

from __future__ import annotations
import re
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

REGISTRY_ROOT = Path("E:/.skill-registry").resolve()
SKILLS_DIR = REGISTRY_ROOT / "skills"
DB_PATH_PRIMARY = Path("D:/Program Files/jarvis-arsenal/data/arsenal_library.sqlite")
DB_PATH_MIRROR = REGISTRY_ROOT / "state" / "arsenal_library.sqlite"

# Stopwords to filter out trivial query noise and generic action verbs
STOPWORDS = {
    "como", "fazer", "para", "com", "qual", "quais", "onde", "quando", "voce",
    "voce", "pode", "faca", "criar", "usar", "sobre", "esse", "esta", "estou",
    "uma", "uns", "umas", "pelo", "pela", "pelos", "pelas", "mais", "menos",
    "que", "quem", "meu", "sua", "seus", "suas", "dele", "dela", "deles",
    "qualquer", "coisa", "tudo", "nada", "muito", "pouco", "agora", "depois",
    "procure", "procurar", "busca", "buscar", "ache", "achar", "encontre",
    "encontrar", "pesquise", "pesquisar", "rastreie", "rastrear", "investigue",
    "investigar", "localize", "localizar", "olhe", "olhar", "veja", "ver",
    "mostre", "mostrar", "liste", "listar", "diga", "fale", "quero", "queria",
    "preciso", "favor", "todos", "toda", "todas", "coisas",
    "the", "and", "for", "with", "from", "that", "this", "what", "how", "make"
}

OSINT_KEYWORDS = {"osint", "recon", "investigar", "investigue", "rastrear", "rastreie", "username", "usuario", "perfil", "social", "sherlock", "blackbird", "holehe"}

def extract_search_terms(text: str, max_terms: int = 5) -> List[str]:
    """Extract clean search tokens from user prompt, with OSINT & handle detection."""
    # Check for @username handles
    handles = re.findall(r"@([a-zA-Z0-9_\-\.]+)", text)
    is_osint = bool(handles) or any(k in text.lower() for k in OSINT_KEYWORDS)

    raw_tokens = re.findall(r"[a-zA-Z0-9_\-\.]{3,}", text.lower())
    filtered = [t for t in raw_tokens if t not in STOPWORDS and not t.isdigit()]

    if is_osint and "osint" not in filtered:
        filtered.append("osint")

    return filtered[:max_terms]


def recall_relevant_skills(terms: List[str], max_skills: int = 3) -> List[Dict[str, str]]:
    """Match terms against active managed skills."""
    if not SKILLS_DIR.exists() or not terms:
        return []

    is_osint = any(t in OSINT_KEYWORDS or t == "osint" for t in terms)
    matched = []
    seen = set()

    # Prioritize blackbird-osint-recon if OSINT intent
    if is_osint:
        for preferred in ("blackbird-osint-recon", "blackbird"):
            p_dir = SKILLS_DIR / preferred
            if p_dir.exists() and preferred not in seen:
                seen.add(preferred)
                matched.append({
                    "name": preferred,
                    "score": 100,
                    "description": "Reconhecimento OSINT assíncrono e verificação de perfil multi-plataforma (500+ redes)."
                })

    for skill_path in SKILLS_DIR.iterdir():
        if not skill_path.is_dir():
            continue
        skill_name = skill_path.name.lower()

        # Score by term hits in directory name
        score = sum(2 for t in terms if t in skill_name)

        # Inspect SKILL.md description
        skill_md = skill_path / "SKILL.md"
        desc = ""
        if skill_md.exists():
            try:
                # Read first 30 lines
                with open(skill_md, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [f.readline() for _ in range(30)]
                    header_text = "".join(lines).lower()
                    for t in terms:
                        if t in header_text:
                            score += 1
                    # Extract description field
                    for l in lines:
                        if l.strip().startswith("description:"):
                            desc = l.replace("description:", "").strip().strip('"\'')
                            break
            except Exception:
                pass

        if score > 0 and skill_path.name not in seen:
            seen.add(skill_path.name)
            matched.append({
                "name": skill_path.name,
                "score": score,
                "description": desc or "Skill de engenharia pronta no IDE."
            })

    matched.sort(key=lambda x: x["score"], reverse=True)
    return matched[:max_skills]


def recall_arsenal_tools(terms: List[str], max_tools: int = 4) -> List[Dict[str, Any]]:
    """Query 28k tools in SQLite FTS5 using fast MATCH."""
    if not terms:
        return []

    db_path = DB_PATH_PRIMARY if DB_PATH_PRIMARY.exists() else DB_PATH_MIRROR
    if not db_path.exists():
        return []

    tools = []
    is_osint = any(t in OSINT_KEYWORDS or t == "osint" for t in terms)

    # If OSINT intent, directly inject top canonical OSINT tools from catalog
    if is_osint:
        osint_canonical = [
            ("sherlock-project/sherlock", "sherlock", 95220, "Python", "Cyberspace", "Hunt down social media accounts by username across social networks."),
            ("antoniaci/blackbird", "blackbird", 9466, "Python", "Cyberspace", "An OSINT tool to search for accounts by username and email across 500+ networks."),
            ("megadose/holehe", "holehe", 15134, "Python", "Neuro-Cognitive", "Checks if email or username is registered across major web platforms."),
            ("WebBreacher/WhatsMyName", "WhatsMyName", 2934, "Python", "Aegis", "Community-maintained dataset of 700+ websites for finding accounts by username.")
        ]
        for c in osint_canonical[:max_tools]:
            tools.append({
                "full_name": c[0],
                "name": c[1],
                "stars": c[2],
                "language": c[3],
                "squad": c[4],
                "description": c[5]
            })
        return tools

    clean_tokens = [re.sub(r'[^a-zA-Z0-9]', '', t) for t in terms if len(t) >= 3]
    if not clean_tokens:
        return []

    fts_query = " OR ".join(f'"{t}"*' for t in clean_tokens[:4])

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("""
            SELECT t.full_name, t.name, t.stars, t.language, t.squad_name, t.description
            FROM arsenal_fts f
            JOIN arsenal_tools t ON t.rowid = f.rowid
            WHERE arsenal_fts MATCH ?
            ORDER BY t.stars DESC
            LIMIT ?
        """, (fts_query, max_tools))

        for r in cur.fetchall():
            tools.append({
                "full_name": r[0],
                "name": r[1],
                "stars": r[2],
                "language": r[3] or "Code",
                "squad": r[4] or "Geral",
                "description": (r[5] or "")[:95]
            })
        conn.close()
    except Exception:
        pass

    return tools


def recall_vault_notes(terms: List[str], max_notes: int = 3) -> List[str]:
    """Find numbered Obsidian MOCs and notes matching query."""
    if not terms:
        return []

    matched_notes = []
    try:
        for p in REGISTRY_ROOT.glob("[0-9][0-9]*.md"):
            stem_lower = p.stem.lower()
            if any(t in stem_lower for t in terms):
                matched_notes.append(p.name)
    except Exception:
        pass

    return matched_notes[:max_notes]


def synthesize_omni_context(query: str) -> str:
    """
    Builds a high-density, concise ground-truth context block (< 300 words)
    grounded in Roberto's actual tools, code repositories, and vault notes.
    """
    terms = extract_search_terms(query)
    if not terms:
        return ""

    skills = recall_relevant_skills(terms)
    tools = recall_arsenal_tools(terms)
    notes = recall_vault_notes(terms)

    if not skills and not tools and not notes:
        return ""

    lines = [
        "### [J.A.R.V.I.S. SOVEREIGN WORKSPACE CONTEXT // CONHECIMENTO LOCAL DO QUINTAL DO ROBERTO]",
        "Você tem acesso e deve utilizar diretamente as seguintes capacidades locais do seu ambiente:"
    ]

    if skills:
        lines.append("\n• Skills Gerenciadas Prontas no IDE:")
        for s in skills:
            lines.append(f"  - `{s['name']}`: {s['description']}")

    if tools:
        lines.append("\n• Ferramentas e Repositórios no Arsenal (Drive D:):")
        for t in tools:
            lines.append(f"  - `{t['full_name']}` ({t['stars']:,} ★, {t['language']}) [{t['squad']}]: {t['description']}")

    if notes:
        lines.append("\n• Notas Estratégicas do Segundo Cérebro Obsidian:")
        for n in notes:
            lines.append(f"  - `{n}`")

    lines.append("\nInstrução: Utilize e cite com naturalidade essas capacidades do seu quintal local para formular a solução técnica precisa ao senhor Roberto.")
    return "\n".join(lines)
