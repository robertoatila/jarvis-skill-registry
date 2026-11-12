"""Deterministic sanitization of third-party text before it reaches agent context.

Repository descriptions, topics and README excerpts harvested from external
sources are *data*, never instructions.  This module is the single boundary
that turns such text into a bounded, single-line, markup-free value and reports
what it had to remove.

Scope and limits (stated so the guarantee is not overread):

- The structural guarantees are exact: the result is one line, contains no
  control/format characters, no markup delimiters and is bounded in length, so
  it cannot terminate a YAML frontmatter block, forge a Markdown heading or
  smuggle invisible characters.
- The ``instruction_like_content`` flag is a deterministic *heuristic* over a
  fixed pattern list.  A missing flag is not proof that text is benign; callers
  must keep treating the value as untrusted data.  A present flag is a reason
  to stop (fail closed), not something to "clean up" and continue.

Pure Python standard library; no network, filesystem or model calls.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Tuple

DEFAULT_MAX_CHARS = 240
NEUTRAL_PLACEHOLDER = "Third-party description withheld pending human review."

# Flags are stable identifiers; tests and callers may match on them.
FLAG_NOT_TEXT = "not_text"
FLAG_CONTROL = "control_characters_removed"
FLAG_INVISIBLE = "invisible_characters_removed"
FLAG_MARKUP = "markup_removed"
FLAG_MULTILINE = "multiline_collapsed"
FLAG_TRUNCATED = "truncated"
FLAG_INSTRUCTION = "instruction_like_content"

_HTML_COMMENT = re.compile(r"<!--.*?(?:-->|$)", re.DOTALL)
_TAG = re.compile(r"</?[A-Za-z!?|][^<>]{0,200}>")
_CHAT_TOKEN = re.compile(r"<\|[^<>|]{0,40}\|>|\[/?INST\]|<<\s*/?SYS\s*>>", re.IGNORECASE)
_MD_IMAGE = re.compile(r"!\[([^\]\[]{0,200})\]\([^()\s]{0,400}\)")
_MD_LINK = re.compile(r"\[([^\]\[]{0,200})\]\([^()\s]{0,400}\)")
_WIKILINK = re.compile(r"\[\[([^\]\[|]{0,200})(?:\|[^\]\[]{0,200})?\]\]")
_STRUCTURAL = re.compile(r"[`<>{}\[\]|\\]")
_FRONTMATTER_FENCE = re.compile(r"(?:^|\s)-{3,}(?=\s|$)")
_WHITESPACE = re.compile(r"\s+")

# Instruction-shaped phrases in English and Portuguese.  Patterns are written
# for precision: they require an imperative aimed at the reader's instructions,
# identity or secrets, because ordinary descriptions legitimately mention words
# such as "prompt", "ignore", "token" or "bash".  Matching is done on a
# case-folded, whitespace-collapsed copy so spacing tricks do not bypass it.
_QUALIFIER = r"(?:previous|prior|above|earlier|preceding|system|safety|original|initial|existing)"
_DIRECTIVE = r"(?:instructions?|prompts?|rules?|guidelines?|directives?|polic(?:y|ies)|context|messages?|constraints?)"
_PT_DIRECTIVE = r"(?:instru[cç][oõ]es|regras|diretrizes|orienta[cç][oõ]es|restri[cç][oõ]es)"
_SECRET = r"(?:api[ _-]?keys?|secrets?|passwords?|credentials?|private keys?|ssh keys?|access tokens?|environment variables|\.env)"
_PT_SECRET = r"(?:chaves?(?: de api)?|segredos?|senhas?|credenciais|credencial|tokens? de acesso)"
_INSTRUCTION_PATTERNS: Tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        # "ignore all previous instructions", "disregard the system prompt"
        rf"\b(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+|any\s+|the\s+|your\s+|these\s+|those\s+|of\s+)*{_QUALIFIER}\s+(?:\w+\s+){{0,2}}{_DIRECTIVE}\b",
        r"\b(?:ignore|disregard|forget)\s+(?:all|any|every)\s+(?:of\s+)?(?:the\s+|your\s+)?(?:instructions?|prompts?|guidelines|directives)\b",
        rf"\b(?:ignore|desconsidere|esque[cç]a|desrespeite|sobrescreva)\s+(?:todas\s+)?(?:as\s+|suas\s+|essas\s+)?{_PT_DIRECTIVE}\b",
        # identity reassignment
        r"\byou are now (?:a|an|the|in|my|dan|free|no longer|unrestricted)\b",
        r"\bvoc[eê] agora [eé]\b",
        r"\bfrom now on,? (?:you|act|respond|answer|behave)\b",
        r"\ba partir de agora,? (?:voc[eê]|aja|responda)\b",
        r"\bdo anything now\b",
        # replacement instructions
        r"\b(?:your|the) (?:new|real|actual|updated|true) (?:system )?(?:instructions?|prompt|task|goal)\b",
        r"\b(?:reveal|print|repeat|output|leak|disclose)\b.{0,30}\b(?:system|hidden|initial) (?:prompt|instructions?)\b",
        r"\b(?:revele|repita|mostre|vaze)\b.{0,30}\bprompt (?:de|do) sistema\b",
        # secret exfiltration
        rf"\b(?:reveal|leak|exfiltrate|steal|send|upload|post|email|forward)\s+(?:me\s+)?(?:your|the user'?s?|all|any|every)\s+(?:\w+\s+){{0,2}}{_SECRET}",
        rf"\b(?:revele|envie|exfiltre|vaze|roube)\s+(?:todas\s+|todos\s+)?(?:as\s+|os\s+|suas\s+|seus\s+)?{_PT_SECRET}\b",
        # concealment from the operator
        r"\b(?:do not|don't|never) (?:tell|inform|notify|mention to|reveal to|alert)\s+(?:the\s+)?(?:user|operator|human|owner)\b",
        r"\bn[aã]o (?:conte|informe|avise|mencione)\s+(?:a[o]?\s+|para o\s+)?(?:usu[aá]rio|operador|dono)\b",
        r"\bwithout (?:telling|informing|notifying|asking)\s+(?:the\s+)?(?:user|operator|human)\b",
        # remote code execution one-liners
        r"\b(?:curl|wget|iwr|invoke-webrequest)\b.{0,160}\|\s*(?:sudo\s+)?(?:ba|z|k)?sh\b",
        r"\b(?:invoke-expression|iex)\b.{0,60}\b(?:downloadstring|iwr|invoke-webrequest|irm|invoke-restmethod)\b",
        r"\brm\s+-(?:rf|fr)\s+[/~$]",
    )
)

# Role markers only count at the start of a line in the *original* text, where
# they imitate a chat transcript; "Operating system: Linux" must not match.
_ROLE_LINE = re.compile(r"(?im)^\s*(?:#+\s*)?(?:system|assistant|developer|tool)\s*:\s*\S")
_HEADING_ROLE_LINE = re.compile(r"(?im)^\s*#+\s*(?:system|instructions?|important)\b")


@dataclass(frozen=True)
class SanitizedText:
    """Result of sanitizing one untrusted value."""

    text: str
    flags: Tuple[str, ...]

    @property
    def suspicious(self) -> bool:
        """True when instruction-shaped content was detected (fail closed)."""
        return FLAG_INSTRUCTION in self.flags

    @property
    def modified(self) -> bool:
        return bool(self.flags)

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "flags": list(self.flags), "suspicious": self.suspicious}


def _strip_unsafe_characters(value: str, flags: list[str]) -> str:
    kept: list[str] = []
    for char in value:
        category = unicodedata.category(char)
        if char in "\r\n\u2028\u2029\u0085\x0b\x0c":
            if FLAG_MULTILINE not in flags:
                flags.append(FLAG_MULTILINE)
            kept.append(" ")
        elif char == "\t":
            kept.append(" ")
        elif category == "Cc":
            if FLAG_CONTROL not in flags:
                flags.append(FLAG_CONTROL)
        elif category in ("Cf", "Co", "Cs", "Cn"):
            # Zero-width, bidi overrides, tag characters, private use, lone
            # surrogates and unassigned code points carry no visible meaning.
            if FLAG_INVISIBLE not in flags:
                flags.append(FLAG_INVISIBLE)
        else:
            kept.append(char)
    return "".join(kept)


def looks_like_instruction(value: str) -> bool:
    """Heuristically detect instruction-shaped text in an already plain string."""
    probe = _WHITESPACE.sub(" ", unicodedata.normalize("NFKC", value)).casefold()
    return any(pattern.search(probe) for pattern in _INSTRUCTION_PATTERNS)


def sanitize_untrusted_text(
    value: Any,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_words: int | None = None,
) -> SanitizedText:
    """Return a bounded single-line plain-text projection of ``value``.

    The function never raises for hostile input and is idempotent: sanitizing
    its own output with the same bounds returns the same text.
    """
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if max_words is not None and max_words < 1:
        raise ValueError("max_words must be positive")

    flags: list[str] = []
    if not isinstance(value, str):
        if value is not None:
            flags.append(FLAG_NOT_TEXT)
        return SanitizedText("", tuple(flags))

    normalized = unicodedata.normalize("NFKC", value)
    multiline = any(char in normalized for char in "\r\n\u2028\u2029\u0085")
    text = _strip_unsafe_characters(normalized, flags)

    # Detection runs before markup removal (to see chat-template tokens and
    # transcript-style role lines) and again afterwards (to see phrases that
    # markup or invisible characters were splitting).
    suspicious = (
        bool(_CHAT_TOKEN.search(text))
        or bool(_ROLE_LINE.search(normalized))
        or (multiline and bool(_HEADING_ROLE_LINE.search(normalized)))
        or looks_like_instruction(text)
    )

    before_markup = text
    text = _HTML_COMMENT.sub(" ", text)
    text = _CHAT_TOKEN.sub(" ", text)
    text = _TAG.sub(" ", text)
    text = _MD_IMAGE.sub(r"\1", text)
    text = _MD_LINK.sub(r"\1", text)
    text = _WIKILINK.sub(r"\1", text)
    text = _STRUCTURAL.sub(" ", text)
    text = _FRONTMATTER_FENCE.sub(" ", text)
    if text != before_markup:
        flags.append(FLAG_MARKUP)

    text = _WHITESPACE.sub(" ", text).strip()
    # Leading Markdown/YAML indicators would change how the line is parsed.
    stripped = text.lstrip("#>-*+=~!&%@?:,'\" ").strip()
    if stripped != text and FLAG_MARKUP not in flags:
        flags.append(FLAG_MARKUP)
    text = stripped

    suspicious = suspicious or looks_like_instruction(text)

    truncated = False
    if max_words is not None:
        words = text.split(" ")
        if len(words) > max_words:
            text = " ".join(words[:max_words])
            truncated = True
    if len(text) > max_chars:
        text = text[:max_chars].rstrip()
        truncated = True
    if truncated:
        flags.append(FLAG_TRUNCATED)
    if suspicious:
        flags.append(FLAG_INSTRUCTION)

    return SanitizedText(text, tuple(flags))


def frontmatter_scalar(value: str) -> str:
    """Make already-sanitized text safe as a YAML *plain* scalar on one line.

    Repository skills use unquoted ``description:`` values, so the generated
    value must not contain a mapping indicator (``: ``), a comment indicator
    (`` #``) or a leading YAML indicator.
    """
    text = _WHITESPACE.sub(" ", value).strip()
    text = re.sub(r":(?=\s|$)", " -", text)
    text = re.sub(r"\s#", " ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text.lstrip("#>-*+=~!&%@?:,'\"|[]{} ").strip()


def describe_external_repository(
    value: Any,
    *,
    max_words: int = 15,
    max_chars: int = 160,
    placeholder: str = NEUTRAL_PLACEHOLDER,
) -> SanitizedText:
    """Sanitize a third-party repository description for skill frontmatter.

    Instruction-shaped descriptions are replaced by a neutral placeholder; the
    flags still report why, so callers can quarantine instead of promoting.
    """
    result = sanitize_untrusted_text(value, max_chars=max_chars, max_words=max_words)
    if result.suspicious:
        return SanitizedText(placeholder, result.flags)
    text = frontmatter_scalar(result.text)
    return SanitizedText(text, result.flags)
