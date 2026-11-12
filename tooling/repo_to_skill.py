#!/usr/bin/env python3
"""
J.A.R.V.I.S. Arsenal Bridge: Repository-to-Skill Converter
Transforms catalogued GitHub repositories from the 73,000+ Arsenal SQLite database
into standard, high-performance canonical Agent Skills (skills/<name>/SKILL.md).
"""

import sys
import os
import json
import sqlite3
import re
import argparse
from pathlib import Path

REGISTRY_ROOT = Path(__file__).resolve().parent.parent
if str(REGISTRY_ROOT) not in sys.path:
    sys.path.insert(0, str(REGISTRY_ROOT))

from tooling.agentic.untrusted_text import (  # noqa: E402
    describe_external_repository,
    sanitize_untrusted_text,
)

SKILLS_DIR = REGISTRY_ROOT / "skills"
E_DB_PATH = REGISTRY_ROOT / "state" / "arsenal_library.sqlite"
D_DB_PATH = Path(r"D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite")

def get_db_connection():
    for p in [E_DB_PATH, D_DB_PATH]:
        if p.exists():
            conn = sqlite3.connect(str(p), timeout=5.0)
            conn.row_factory = sqlite3.Row
            return conn
    return None

def clean_description_for_frontmatter(desc: str, max_words: int = 15) -> str:
    """Return a sanitized, single-line frontmatter description of <= max_words.

    The description is third-party text: it goes through the shared untrusted
    text boundary first, and instruction-shaped content is replaced by a neutral
    placeholder instead of being copied into a SKILL.md that agents will read.
    """
    result = describe_external_repository(desc, max_words=max_words)
    if result.suspicious:
        return result.text
    if not result.text:
        return "Sovereign technical tool for agentic execution and specialized automation."
    # Strip emojis and special characters
    clean = re.sub(r'[^\w\s\-\.,/]', ' ', result.text)
    return ' '.join(clean.split())


def _safe_label(value, fallback: str, max_chars: int = 80) -> str:
    """Bounded single-line projection of a third-party label."""
    return sanitize_untrusted_text(value, max_chars=max_chars).text or fallback

def sanitize_skill_name(name: str) -> str:
    """Converts a repository name or full_name to a clean directory slug."""
    slug = name.split('/')[-1] if '/' in name else name
    slug = re.sub(r'[^a-zA-Z0-9_\-]', '-', slug).lower()
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug

def generate_skill_content(repo: dict) -> str:
    # Every catalog field below is third-party data and is sanitized before it
    # is written into a skill file.
    slug = sanitize_skill_name(str(repo.get("name") or "tool")) or "tool"
    name = _safe_label(repo.get("name"), slug)
    full_name = _safe_label(repo.get("full_name"), name, max_chars=200)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9_.-]{1,100}", full_name):
        full_name = slug
    raw_desc = repo.get("description")
    fm_desc = clean_description_for_frontmatter(raw_desc, max_words=15)
    body_result = sanitize_untrusted_text(raw_desc, max_chars=600)
    if body_result.suspicious:
        desc = fm_desc
    else:
        desc = body_result.text or "Sovereign tool for automated workflows."
    try:
        stars = max(int(repo.get("stars") or 0), 0)
    except (TypeError, ValueError):
        stars = 0
    lang = _safe_label(repo.get("language"), "Multi-language", max_chars=40)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 +#.'\-]{0,39}", lang):
        lang = "Multi-language"
    url = f"https://github.com/{full_name}" if "/" in full_name else "https://github.com/"
    squad_name = _safe_label(repo.get("squad_name"), "Hyperion", max_chars=60)
    try:
        squad_id = int(repo.get("squad_id") or 5)
    except (TypeError, ValueError):
        squad_id = 5
    
    topics_raw = repo.get("topics") or []
    if isinstance(topics_raw, str):
        try:
            topics = json.loads(topics_raw)
        except Exception:
            topics = [t.strip() for t in topics_raw.split(',') if t.strip()]
    elif isinstance(topics_raw, list):
        topics = topics_raw
    else:
        topics = []
        
    caps_raw = repo.get("capabilities") or []
    if isinstance(caps_raw, str):
        try:
            caps = json.loads(caps_raw)
        except Exception:
            caps = []
    elif isinstance(caps_raw, list):
        caps = caps_raw
    else:
        caps = []
        
    topics = [label for label in (_safe_label(t, "", max_chars=40) for t in topics[:20]) if label]
    caps = [label for label in (_safe_label(c, "", max_chars=120) for c in caps[:12]) if label]

    if not caps:
        caps = [f"Automated execution and integration for {slug}"]
        if topics:
            caps.extend([f"Domain support for {t}" for t in topics[:4]])

    caps_md = "\n".join([f"- **{c}**" for c in caps])
    topics_str = ", ".join(topics) if topics else "general, automation"

    skill_template = f"""---
name: {slug}
description: {fm_desc}
---

# {name}

## Overview
- **Repository**: [{full_name}]({url})
- **Stars**: {stars:,}
- **Primary Language**: {lang}
- **Tactical Squad**: Esquadrão {squad_id} ({squad_name})
- **Tags & Topics**: {topics_str}

{desc}

## Key Capabilities
{caps_md}

## Tactical Usage & Execution
Execute CLI commands or API invocations corresponding to `{name}`:

```bash
# Example invocation pattern
{slug} --help
```

### Integration Patterns
- **Agent Delegation**: When subagents encounter workflows requiring {slug}, dispatch tasks mapped to Esquadrão {squad_id} ({squad_name}).
- **Sovereign Evidence**: Validate execution outputs and verify exit codes prior to marking operations as resolved.
"""
    return skill_template

def promote_repo_to_skill(repo_identifier: str, overwrite: bool = False) -> dict:
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database not reachable"}

    # Search by full_name or name
    row = conn.execute(
        "SELECT * FROM arsenal_tools WHERE LOWER(full_name) = ? OR LOWER(name) = ? LIMIT 1",
        (repo_identifier.lower(), repo_identifier.lower())
    ).fetchone()

    if not row:
        # Search via LIKE
        row = conn.execute(
            "SELECT * FROM arsenal_tools WHERE LOWER(full_name) LIKE ? OR LOWER(name) LIKE ? ORDER BY stars DESC LIMIT 1",
            (f"%{repo_identifier.lower()}%", f"%{repo_identifier.lower()}%")
        ).fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": f"Repository '{repo_identifier}' not found in Arsenal DB."}

    repo = dict(row)
    conn.close()

    slug = sanitize_skill_name(str(repo["name"] or ""))
    if not slug:
        # An empty slug would resolve to skills/ itself and write skills/SKILL.md.
        return {"success": False, "error": "Repository name does not yield a valid skill directory name."}
    target_dir = SKILLS_DIR / slug
    target_file = target_dir / "SKILL.md"
    if target_dir.is_symlink() or target_file.is_symlink():
        return {"success": False, "error": f"Refusing to write through a linked skill path: {slug}"}
    existed = target_file.exists()

    if existed and not overwrite:
        return {
            "success": True,
            "status": "already_exists",
            "skill_name": slug,
            "path": str(target_file),
            "repo": repo["full_name"],
            "stars": repo["stars"]
        }

    target_dir.mkdir(parents=True, exist_ok=True)
    content = generate_skill_content(repo)
    target_file.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "status": "overwritten" if existed else "created",
        "skill_name": slug,
        "path": str(target_file),
        "repo": repo["full_name"],
        "stars": repo["stars"]
    }

def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Repo-to-Skill Converter")
    parser.add_argument("--repo", help="Repository full_name or name (e.g. firecrawl/firecrawl)")
    parser.add_argument("--search", help="Search query to find and promote top matches")
    parser.add_argument("--top", type=int, default=1, help="Number of top repos to convert")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing skill files")

    args = parser.parse_args()

    if args.repo:
        res = promote_repo_to_skill(args.repo, overwrite=args.overwrite)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("success") else 1)

    if args.search:
        conn = get_db_connection()
        if not conn:
            print(json.dumps({"error": "DB unreachable"}))
            sys.exit(1)
        cur = conn.cursor()
        clean_q = re.sub(r'[^\w\s\-\.]', ' ', args.search).strip()
        fts_query = f"{clean_q}*"
        try:
            cur.execute("""
                SELECT t.full_name, t.name, t.stars FROM arsenal_fts f
                JOIN arsenal_tools t ON f.rowid = t.rowid
                WHERE arsenal_fts MATCH ?
                ORDER BY t.stars DESC LIMIT ?
            """, (fts_query, args.top))
            rows = cur.fetchall()
        except Exception:
            cur.execute("""
                SELECT full_name, name, stars FROM arsenal_tools
                WHERE full_name LIKE ? OR description LIKE ?
                ORDER BY stars DESC LIMIT ?
            """, (f"%{clean_q}%", f"%{clean_q}%", args.top))
            rows = cur.fetchall()
        conn.close()

        results = []
        for r in rows:
            res = promote_repo_to_skill(r[0], overwrite=args.overwrite)
            results.append(res)
        print(json.dumps(results, indent=2))
        sys.exit(0)

    parser.print_help()

if __name__ == "__main__":
    main()
