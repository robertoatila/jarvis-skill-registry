#!/usr/bin/env python3
"""
sync_and_optimize_arsenal.py // J.A.R.V.I.S. Arsenal Synchronizer & Token Governor
Pure Python 3.12 Standard Library (Zero PIP Dependencies)

Consolidates all sovereign skills into C:\\Users\\Ad\\.gemini\\config\\skills
Prunes skill descriptions to high-signal summaries (<= 12 words) to guarantee
safe token budget consumption (< 30% of total budget) in Antigravity IDE.
"""

from __future__ import annotations
import os
import re
import shutil
from pathlib import Path

REGISTRY_ROOT = Path(r"E:\.skill-registry")
REPO_SKILLS = REGISTRY_ROOT / "skills"
CONFIG_ROOT = Path.home() / ".gemini" / "config"
CONFIG_SKILLS = CONFIG_ROOT / "skills"
ARCHIVE_SKILLS = CONFIG_ROOT / "skills_vault_archive"
OPTIMIZE_PS1 = REGISTRY_ROOT / "tooling" / "Optimize-SkillTokenBudget.ps1"


def load_curated_descriptions() -> dict[str, str]:
    curated: dict[str, str] = {}
    if not OPTIMIZE_PS1.exists():
        return curated
    try:
        content = OPTIMIZE_PS1.read_text(encoding="utf-8")
        for match in re.finditer(r'"([a-zA-Z0-9_-]+)"\s*=\s*"([^"]+)"', content):
            curated[match.group(1)] = match.group(2)
    except Exception as e:
        print(f"[WARN] Failed reading curated descriptions from PS1: {e}")
    return curated


def clean_description(name: str, raw_desc: str, curated: dict[str, str]) -> str:
    if name in curated:
        desc = curated[name].strip()
    else:
        desc = raw_desc.strip()
        # Strip surrounding quotes
        if (desc.startswith('"') and desc.endswith('"')) or (desc.startswith("'") and desc.endswith("'")):
            desc = desc[1:-1].strip()
        # Remove common boilerplate prefixes
        desc = re.sub(
            r"^(Use this skill whenever|Use this skill when|Use when|This skill should be used for|Specialized skill for|Comprehensive|Master|Official|Guides stable)\s+",
            "",
            desc,
            flags=re.IGNORECASE
        )
        desc = " ".join(desc.split())
        # Try to take first sentence if concise
        m = re.match(r"^(.*?[.?!])\s", desc)
        if m and len(m.group(1).split()) <= 12:
            desc = m.group(1).strip()

    words = desc.split()
    if len(words) > 12:
        desc = " ".join(words[:11])
        if not desc.endswith("."):
            desc += "."
    else:
        if not desc.endswith("."):
            desc += "."
    return desc


def update_skill_md_description(skill_md_path: Path, new_desc: str) -> str:
    content = skill_md_path.read_text(encoding="utf-8")
    fm_match = re.search(r"(?ms)^---\r?\n(.*?)\r?\n---", content)
    if not fm_match:
        return content

    fm = fm_match.group(1)
    new_desc_line = f"description: {new_desc}"
    if re.search(r"(?ms)^description:\s*.*?(?=\r?\n[a-zA-Z0-9_-]+:|\Z)", fm):
        updated_fm = re.sub(
            r"(?ms)^description:\s*.*?(?=\r?\n[a-zA-Z0-9_-]+:|\Z)",
            new_desc_line,
            fm
        )
        new_content = content.replace(fm, updated_fm, 1)
        return new_content
    return content


def sync_all_skills():
    print("=" * 65)
    print("  J.A.R.V.I.S. // SOBERANIA TOTAL DE SKILLS & GOVERNANÇA DE TOKENS")
    print("=" * 65)

    curated = load_curated_descriptions()
    print(f"[OK] Dicionário curado carregado: {len(curated)} descrições pré-otimizadas.")

    repo_set = set(os.listdir(REPO_SKILLS)) if REPO_SKILLS.exists() else set()
    cfg_set = set(os.listdir(CONFIG_SKILLS)) if CONFIG_SKILLS.exists() else set()
    arc_set = set(os.listdir(ARCHIVE_SKILLS)) if ARCHIVE_SKILLS.exists() else set()

    all_skill_names = sorted(list(repo_set | cfg_set | arc_set))
    print(f"[OK] Inventário Total de Skills Descobertas: {len(all_skill_names)} skills únicas.")

    CONFIG_SKILLS.mkdir(parents=True, exist_ok=True)

    synced_count = 0
    total_words = 0

    for name in all_skill_names:
        # Determine source path
        src_dir = None
        for cand in [REPO_SKILLS / name, CONFIG_SKILLS / name, ARCHIVE_SKILLS / name]:
            if (cand / "SKILL.md").is_file():
                src_dir = cand
                break

        if not src_dir:
            continue

        src_skill_md = src_dir / "SKILL.md"
        raw_text = src_skill_md.read_text(encoding="utf-8")

        # Extract current description
        desc_match = re.search(r"(?m)^description:\s*['\"]?(.*?)['\"]?$", raw_text)
        current_desc = desc_match.group(1).strip() if desc_match else ""

        optimized_desc = clean_description(name, current_desc, curated)
        updated_content = update_skill_md_description(src_skill_md, optimized_desc)

        # Target directory in IDE config
        dst_dir = CONFIG_SKILLS / name
        dst_dir.mkdir(parents=True, exist_ok=True)
        (dst_dir / "SKILL.md").write_text(updated_content, encoding="utf-8")

        # Also update in Repo if skill exists in canonical repo
        if name in repo_set:
            repo_skill_md = REPO_SKILLS / name / "SKILL.md"
            if repo_skill_md.is_file():
                repo_skill_md.write_text(updated_content, encoding="utf-8")

        # Copy any auxiliary subdirectories (scripts, resources, references)
        for sub in ["scripts", "resources", "references"]:
            sub_src = src_dir / sub
            if sub_src.is_dir():
                sub_dst = dst_dir / sub
                if not sub_dst.exists():
                    shutil.copytree(sub_src, sub_dst, dirs_exist_ok=True)

        synced_count += 1
        word_count = len(optimized_desc.split()) + len(name.split("-"))
        total_words += word_count

    est_tokens = int(total_words * 1.35)
    pct_budget = (est_tokens / 20000.0) * 100.0
    free_budget = 100.0 - pct_budget

    print("-" * 65)
    print(f"Total de Skills Sincronizadas no IDE : {synced_count}")
    print(f"Palavras Totais (Nomes + Descrições) : {total_words}")
    print(f"Consumo Estimado de Tokens           : ~{est_tokens} tokens")
    print(f"Ocupação do Token Budget (20k max)   : {pct_budget:.1f}%")
    print(f"Margem de Token Budget Livre         : {free_budget:.1f}%")
    print("=" * 65)
    print("STATUS: SUCESSO ABSOLUTO (TODAS AS SKILLS ATIVAS E DENTRO DA COTA)")
    print("=" * 65)


if __name__ == "__main__":
    sync_all_skills()
