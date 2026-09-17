"""Governed admission of human-authored Obsidian evidence into J.A.R.V.I.S. memory.

Vault text is evidence, never execution authority. This module converts verified
Vault events into provenance-bearing memory candidates and routes accepted
candidates through the existing ``MemoryFabric.admit`` gate.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .memory import (
    MemoryAdmissionResult,
    MemoryFabric,
    MemoryItem,
    MemoryStatus,
    MemoryTier,
)
from .vault_events import VaultEvent
from .vault_projection import END, START, _reject_linked_path


MAX_ADMISSION_BYTES = 2 * 1024 * 1024
MAX_CLAIM_CHARS = 16_384

_AUTHORITY_PATTERNS = (
    re.compile(r'\bignore\s+(?:all\s+)?authorization\b', re.IGNORECASE),
    re.compile(r'\b(?:bypass|disable|skip)\s+(?:authorization|approval|permissions?)\b', re.IGNORECASE),
    re.compile(r'\balways\s+allow\s+(?:the\s+)?shell\b', re.IGNORECASE),
    re.compile(r'\ballow\s+shell\s+commands?\b', re.IGNORECASE),
    re.compile(r'\bgrant\s+(?:admin|administrator|root)\b', re.IGNORECASE),
    re.compile(r'\bauto[- ]?approve\b', re.IGNORECASE),
    re.compile(r'\bwithout\s+(?:approval|authorization)\b', re.IGNORECASE),
    re.compile(r'\brm\s+-rf\b', re.IGNORECASE),
    re.compile(r'\bdrop\s+database\b', re.IGNORECASE),
    re.compile(r'\bformat\s+(?:the\s+)?disk\b', re.IGNORECASE),
    re.compile(r'\bdelete\s+all\b', re.IGNORECASE),
    re.compile(r'\b(?:password|passwd|api[_ -]?key|secret|token)\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'\bbearer\s+[A-Za-z0-9._~-]+', re.IGNORECASE),
)


@dataclass
class MemoryCandidate:
    candidate_id: str
    source_event_id: str
    claim_or_summary: str
    category: str
    source_path: str
    source_hash: str
    observed_at: str
    confidence: float
    conflict_keys: list[str]
    risk_class: str
    admission_state: str


def _normalize_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or '\\' in value:
        raise ValueError('Vault admission requires a normalized relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '.' in path.parts:
        raise ValueError('Vault admission path escapes the vault')
    normalized = path.as_posix()
    if normalized != value:
        raise ValueError('Vault admission path must be canonical')
    return normalized


def _candidate_id(event: VaultEvent, claim: str, state: str) -> str:
    material = json.dumps(
        {
            'event_id': event.event_id,
            'claim': claim,
            'state': state,
        },
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    ).encode('utf-8')
    return 'vault-candidate-' + hashlib.sha256(material).hexdigest()


def _memory_id(candidate: MemoryCandidate) -> str:
    return 'vault-memory-' + hashlib.sha256(candidate.candidate_id.encode('utf-8')).hexdigest()


def _strip_managed_markdown(text: str) -> str:
    starts = text.count(START)
    ends = text.count(END)
    if starts == 0 and ends == 0:
        return text
    if starts != 1 or ends != 1:
        raise ValueError('Damaged managed projection markers')
    first = text.index(START)
    last = text.index(END)
    if last < first:
        raise ValueError('Reversed managed projection markers')
    return text[:first] + text[last + len(END):]


def _canvas_human_text(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError('Invalid Canvas JSON for admission') from exc
    if not isinstance(payload, dict):
        raise ValueError('Invalid Canvas object for admission')
    nodes = payload.get('nodes', [])
    if not isinstance(nodes, list):
        raise ValueError('Invalid Canvas nodes for admission')
    human_text: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError('Invalid Canvas node for admission')
        node_id = node.get('id')
        if isinstance(node_id, str) and node_id.startswith('jarvis:projection:'):
            continue
        value = node.get('text')
        if isinstance(value, str) and value.strip():
            human_text.append(value.strip())
    return '\n\n'.join(human_text)


def _risk_class(text: str) -> str:
    return 'HIGH_AUTHORITY' if any(pattern.search(text) for pattern in _AUTHORITY_PATTERNS) else 'LOW'


class VaultAdmissionPipeline:
    """Convert hash-verified Vault evidence into governed memory admissions."""

    def __init__(self, vault_root: Path) -> None:
        self.vault_root = Path(vault_root).absolute()
        _reject_linked_path(self.vault_root, 'Linked vault roots are not supported')

    def _path_for(self, relative_path: str) -> Path:
        normalized = _normalize_relative_path(relative_path)
        path = self.vault_root.joinpath(*PurePosixPath(normalized).parts)
        _reject_linked_path(path, 'Linked vault admission paths are not supported')
        return path

    def _read_verified_text(self, event: VaultEvent) -> str:
        if not isinstance(event.content_hash, str) or len(event.content_hash) != 64:
            raise ValueError('Vault event content hash required for admission')
        path = self._path_for(event.path)
        try:
            stat = path.stat()
            if not path.is_file() or stat.st_size > MAX_ADMISSION_BYTES:
                raise ValueError('Vault source is not an admissible file')
            payload = path.read_bytes()
        except FileNotFoundError as exc:
            raise ValueError('Vault source disappeared before admission') from exc
        actual_hash = hashlib.sha256(payload).hexdigest()
        if actual_hash != event.content_hash:
            raise ValueError('Vault source hash changed before admission')
        try:
            text = payload.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('Vault source is not UTF-8 text') from exc
        suffix = path.suffix.casefold()
        if suffix == '.md':
            return _strip_managed_markdown(text)
        if suffix == '.canvas':
            return _canvas_human_text(text)
        return ''

    def candidates_from_event(self, event: VaultEvent) -> list[MemoryCandidate]:
        if not isinstance(event, VaultEvent):
            raise TypeError('VaultEvent required')
        if event.source == 'jarvis_projection':
            return []
        if event.kind == 'deleted':
            source_hash = event.previous_hash
            if not isinstance(source_hash, str) or len(source_hash) != 64:
                raise ValueError('Deleted Vault event requires previous hash')
            path = _normalize_relative_path(event.path)
            claim = f'Vault source superseded: {path}'
            return [
                MemoryCandidate(
                    candidate_id=_candidate_id(event, claim, 'SUPERSEDED'),
                    source_event_id=event.event_id,
                    claim_or_summary=claim,
                    category='source_lifecycle',
                    source_path=path,
                    source_hash=source_hash,
                    observed_at=event.observed_at,
                    confidence=1.0,
                    conflict_keys=[f'vault:{path}'],
                    risk_class='LOW',
                    admission_state='SUPERSEDED',
                )
            ]
        if event.kind not in {'created', 'modified'}:
            return []

        path = _normalize_relative_path(event.path)
        text = self._read_verified_text(event).strip()
        if not text:
            return []
        if len(text) > MAX_CLAIM_CHARS:
            text = text[:MAX_CLAIM_CHARS].rstrip()

        risk = _risk_class(text)
        state = 'REJECTED' if risk == 'HIGH_AUTHORITY' else 'CANDIDATE'
        category = 'authority_change' if risk == 'HIGH_AUTHORITY' else (
            'canvas_context' if path.casefold().endswith('.canvas') else 'project_context'
        )
        candidate = MemoryCandidate(
            candidate_id=_candidate_id(event, text, state),
            source_event_id=event.event_id,
            claim_or_summary=text,
            category=category,
            source_path=path,
            source_hash=str(event.content_hash),
            observed_at=event.observed_at,
            confidence=0.0 if risk == 'HIGH_AUTHORITY' else 0.85,
            conflict_keys=[f'vault:{path}'],
            risk_class=risk,
            admission_state=state,
        )
        return [candidate]

    @staticmethod
    def _metadata(candidate: MemoryCandidate, admission_reason: str) -> dict[str, Any]:
        return {
            'source_path': candidate.source_path,
            'source_hash': candidate.source_hash,
            'source_event_id': candidate.source_event_id,
            'candidate_id': candidate.candidate_id,
            'risk_class': candidate.risk_class,
            'admission_reason': admission_reason,
        }

    def admit(self, candidate: MemoryCandidate, memory_fabric: MemoryFabric) -> MemoryAdmissionResult:
        if not isinstance(candidate, MemoryCandidate):
            raise TypeError('MemoryCandidate required')
        if not isinstance(memory_fabric, MemoryFabric):
            raise TypeError('MemoryFabric required')

        if candidate.admission_state == 'REJECTED' or candidate.risk_class == 'HIGH_AUTHORITY':
            return MemoryAdmissionResult(
                admitted=False,
                item_id=None,
                status=MemoryStatus.ARCHIVED,
                reason='REJECTED: VAULT_AUTHORITY_TEXT_IS_NOT_EXECUTION_AUTHORITY',
            )

        if candidate.admission_state == 'SUPERSEDED':
            item = MemoryItem(
                memory_id=_memory_id(candidate),
                tier=MemoryTier.EPISODIC,
                key=f'vault-superseded:{candidate.source_path}:{candidate.source_event_id}',
                content=candidate.claim_or_summary,
                provenance=f'vault:{candidate.source_event_id}',
                confidence=candidate.confidence,
                created_utc=candidate.observed_at,
                last_accessed_utc=candidate.observed_at,
                tags=['vault', 'obsidian', 'source_lifecycle'],
                metadata=self._metadata(candidate, 'VAULT_SOURCE_SUPERSEDED'),
                status=MemoryStatus.ACTIVE,
            )
            return memory_fabric.admit(item)

        if candidate.admission_state != 'CANDIDATE':
            return MemoryAdmissionResult(
                admitted=False,
                item_id=None,
                status=MemoryStatus.ARCHIVED,
                reason=f'REJECTED: UNSUPPORTED_VAULT_ADMISSION_STATE:{candidate.admission_state}',
            )

        item = MemoryItem(
            memory_id=_memory_id(candidate),
            tier=MemoryTier.SEMANTIC,
            key=candidate.conflict_keys[0] if candidate.conflict_keys else f'vault:{candidate.source_path}',
            content=candidate.claim_or_summary,
            provenance=f'vault:{candidate.source_event_id}',
            confidence=candidate.confidence,
            created_utc=candidate.observed_at,
            last_accessed_utc=candidate.observed_at,
            tags=['vault', 'obsidian', candidate.category],
            metadata=self._metadata(candidate, 'LOW_RISK_VAULT_CONTEXT'),
            status=MemoryStatus.ACTIVE,
        )
        result = memory_fabric.admit(item)
        if result.admitted:
            candidate.admission_state = (
                'CONFLICT' if result.status == MemoryStatus.CONFLICT_DETECTED else 'ADMITTED'
            )
        return result
