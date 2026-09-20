#!/usr/bin/env python3
"""
fix_markdown_lint.py // J.A.R.V.I.S. Markdown Lint Fixer
Fixes MD022, MD031, MD032, MD058, MD034, MD009, MD028 across repo markdown files.
"""

from __future__ import annotations
import re
from pathlib import Path

REGISTRY_ROOT = Path(r"E:\.skill-registry")


def fix_file_06():
    path = REGISTRY_ROOT / "06 - GitHub Starred Repositories.md"
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")

    # 1. Blank line after heading 20
    content = re.sub(
        r"(## [^\r\n]*Como Ingerir Qualquer um Desses Repositorios:[^\r\n]*)\r?\n(```)",
        r"\1\n\n\2",
        content
    )

    # 2. Blank line between headings and tables
    content = re.sub(
        r"(## [^\r\n]+)\r?\n(\| Repositorio \|)",
        r"\1\n\n\2",
        content
    )

    # 3. Bare URLs in table cells: wrap in <https://...>
    # Match bare URL in table lines that isn't preceded by [ or ( or ` or <
    def wrap_bare_url(match):
        prefix = match.group(1)
        url = match.group(2)
        return f"{prefix}<{url}>"

    # Only in lines starting with |
    lines = content.split("\n")
    fixed_lines = []
    for line in lines:
        if line.startswith("|") and not line.startswith("| :---"):
            # Replace bare URLs
            line = re.sub(r"([\s—→])(https?://[^\s<>`|)]+)", wrap_bare_url, line)
        fixed_lines.append(line)

    content = "\n".join(fixed_lines)
    path.write_text(content, encoding="utf-8")
    print("[OK] Fixed 06 - GitHub Starred Repositories.md")


def fix_file_21():
    path = REGISTRY_ROOT / "21 - Repositorios 100k+ Estrelas e Radar de Sites Oficiais.md"
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    content = re.sub(
        r"(O radar de 100k\+ estrelas está integrado diretamente nas interfaces do J\.A\.R\.V\.I\.S\.:)\r?\n(1\.)",
        r"\1\n\n\2",
        content
    )
    path.write_text(content, encoding="utf-8")
    print("[OK] Fixed 21 - Repositorios 100k+ Estrelas e Radar de Sites Oficiais.md")


def fix_agentic_runtime_architecture():
    path = REGISTRY_ROOT / "docs" / "AGENTIC_RUNTIME_ARCHITECTURE.md"
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")

    # Ensure blank line below ### headings
    content = re.sub(r"(### 2\.\d [^\r\n]+)\r?\n([^\r\n\s])", r"\1\n\n\2", content)
    # Ensure blank line before 1. lists
    content = re.sub(r"(Resolves capability requests[^\r\n]+)\r?\n(1\.)", r"\1\n\n\2", content)
    content = re.sub(r"(Concrete implementations[^\r\n]+)\r?\n(1\.)", r"\1\n\n\2", content)
    # Ensure blank line before fenced code block at line 147
    content = re.sub(r"(\*\*Strict State Invariants\*\*:\s*)\r?\n(```)", r"\1\n\n\2", content)
    # Ensure blank line after promotion lifecycle inline code before list
    content = re.sub(r"(`DISCOVERED → [^\r\n]+`)\r?\n(- )", r"\1\n\n\2", content)

    path.write_text(content, encoding="utf-8")
    print("[OK] Fixed docs/AGENTIC_RUNTIME_ARCHITECTURE.md")


def fix_cli_reference():
    path = REGISTRY_ROOT / "docs" / "CLI_REFERENCE.md"
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")

    # Blank lines below headings
    content = re.sub(r"(### \d+\. `[^`]+`)\r?\n([^\r\n\s])", r"\1\n\n\2", content)
    # Blank lines before lists
    content = re.sub(r"(\*\*Output Fields:\*\*|\*\*Options:\*\*)\r?\n(- )", r"\1\n\n\2", content)
    # Blank lines before and after code fences
    content = re.sub(r"(\*\*Example:\*\*)\r?\n(```)", r"\1\n\n\2", content)
    # Generic fence spacing
    content = re.sub(r"([^\r\n\s])\r?\n(```(?:bash|powershell|text|json|python)?)", r"\1\n\n\2", content)

    path.write_text(content, encoding="utf-8")
    print("[OK] Fixed docs/CLI_REFERENCE.md")


def fix_general_markdown(path: Path):
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    orig = content

    # MD009: Strip trailing whitespace
    lines = [line.rstrip() for line in content.split("\n")]
    content = "\n".join(lines)

    # MD022: Headings surrounded by blank lines
    # Ensure blank line below headings if followed immediately by text
    content = re.sub(r"(^(?:#{1,6})\s+[^\r\n]+)\r?\n([^\r\n#\s])", r"\1\n\n\2", content, flags=re.MULTILINE)
    # Ensure blank line above headings if preceded by text (unless line 1 or right after frontmatter ---)
    content = re.sub(r"([^\r\n\s])\r?\n(^(?:#{1,6})\s+[^\r\n]+)", r"\1\n\n\2", content, flags=re.MULTILINE)

    # MD031: Fenced code blocks surrounded by blank lines
    content = re.sub(r"([^\r\n\s])\r?\n(```[a-zA-Z0-9_-]*)", r"\1\n\n\2", content)
    content = re.sub(r"(```)\r?\n([^\r\n\s])", r"\1\n\n\2", content)

    # MD032: Lists surrounded by blank lines
    content = re.sub(r"([^\r\n\s:>])\r?\n([*-]\s+[^\r\n]+)", r"\1\n\n\2", content)
    content = re.sub(r"([^\r\n\s:>])\r?\n(\d+\.\s+[^\r\n]+)", r"\1\n\n\2", content)

    # MD028: No blank lines between blockquotes
    content = re.sub(r"(>\s*[^\r\n]*)\r?\n\r?\n(>\s*[^\r\n]*)", r"\1\n>\n\2", content)

    if content != orig:
        path.write_text(content, encoding="utf-8")
        print(f"[OK] Fixed {path.relative_to(REGISTRY_ROOT)}")


def main():
    fix_file_06()
    fix_file_21()
    fix_agentic_runtime_architecture()
    fix_cli_reference()

    target_docs = [
        REGISTRY_ROOT / "docs" / "architecture" / "JARVIS_ARCHITECTURE_REASSESSMENT.md",
        REGISTRY_ROOT / "docs" / "architecture" / "RUNTIME_EXECUTION_CONTRACT.md",
        REGISTRY_ROOT / "docs" / "roadmap" / "JARVIS_AUTONOMOUS_INTELLIGENCE_PLAN.md",
        REGISTRY_ROOT / "docs" / "security" / "JARVIS_THREAT_MODEL.md",
        REGISTRY_ROOT / "docs" / "SPECIFICATION.md",
        REGISTRY_ROOT / "examples" / "README.md",
        REGISTRY_ROOT / "README.md",
        REGISTRY_ROOT / "releases" / "v2.0.0" / "RELEASE_NOTES.md",
    ]
    for doc in target_docs:
        fix_general_markdown(doc)

    # Reports
    reports_dir = REGISTRY_ROOT / "reports"
    if reports_dir.is_dir():
        for r in reports_dir.glob("*.md"):
            fix_general_markdown(r)


if __name__ == "__main__":
    main()
