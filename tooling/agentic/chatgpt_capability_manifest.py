"""Explicit ChatGPT browser capability manifest bridge.

The local JARVIS runtime cannot infer ChatGPT browser plugins, skills, or
connectors from conversation text or browser state. This bridge accepts only an
explicit structured manifest, validates ChatGPT source identity, degrades stale
observations to UNVERIFIED, and delegates persistence to ExternalCapabilityCatalog.
It never imports implementation code, browser cookies, session tokens, or
execution authority.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import math
import time
from typing import Any, Callable

from .external_capabilities import CapabilityAvailability, ExternalCapabilityCatalog


DEFAULT_MAX_MANIFEST_AGE_SECONDS = 24 * 60 * 60
MAX_FUTURE_SKEW_SECONDS = 60
CHATGPT_SOURCE_ID = 'chatgpt-browser'
CHATGPT_PROVIDER = 'chatgpt'


class ChatGPTCapabilityManifestBridge:
    """Validate and import explicit ChatGPT browser capability observations."""

    def __init__(
        self,
        catalog: ExternalCapabilityCatalog,
        *,
        clock: Callable[[], float] | None = None,
        max_manifest_age_seconds: float = DEFAULT_MAX_MANIFEST_AGE_SECONDS,
    ) -> None:
        if not isinstance(catalog, ExternalCapabilityCatalog):
            raise TypeError('ExternalCapabilityCatalog required')
        if isinstance(max_manifest_age_seconds, bool) or not isinstance(max_manifest_age_seconds, (int, float)):
            raise ValueError('Invalid max manifest age')
        age = float(max_manifest_age_seconds)
        if not math.isfinite(age) or age <= 0:
            raise ValueError('Invalid max manifest age')
        self.catalog = catalog
        self.clock = clock or time.time
        self.max_manifest_age_seconds = age

    @staticmethod
    def _observed_timestamp(value: Any) -> float:
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Invalid observed_at')
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError as exc:
            raise ValueError('Invalid observed_at') from exc
        if parsed.tzinfo is None:
            raise ValueError('observed_at requires timezone')
        timestamp = parsed.timestamp()
        if not math.isfinite(timestamp):
            raise ValueError('Invalid observed_at')
        return timestamp

    @staticmethod
    def _validate_chatgpt_identity(manifest: dict[str, Any]) -> None:
        if manifest.get('source_id') != CHATGPT_SOURCE_ID:
            raise ValueError('ChatGPT capability manifest source_id must be chatgpt-browser')
        capabilities = manifest.get('capabilities')
        if not isinstance(capabilities, list):
            # The generic catalog will provide the detailed schema error after
            # ChatGPT identity has been established for structurally valid lists.
            return
        for raw in capabilities:
            if not isinstance(raw, dict):
                continue
            if raw.get('provider') != CHATGPT_PROVIDER:
                raise ValueError('ChatGPT capability manifest provider must be chatgpt')
            try:
                availability = CapabilityAvailability(raw.get('availability', 'UNVERIFIED'))
            except (TypeError, ValueError) as exc:
                raise ValueError('Invalid ChatGPT capability manifest availability') from exc
            if availability not in {
                CapabilityAvailability.KNOWN,
                CapabilityAvailability.UNVERIFIED,
            }:
                raise ValueError('ChatGPT capability manifest availability cannot claim executable capability')

    def normalize(self, manifest: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Return a non-mutating normalized manifest plus its stale flag."""
        if not isinstance(manifest, dict):
            raise TypeError('ChatGPT capability manifest must be an object/dict')

        # Validate identity and authority-bearing fields before applying stale
        # normalization. Otherwise an old malicious manifest could have an
        # executable availability claim silently rewritten to UNVERIFIED and
        # escape the catalog's rejection path.
        self._validate_chatgpt_identity(manifest)
        observed_ts = self._observed_timestamp(manifest.get('observed_at'))
        now = float(self.clock())
        if not math.isfinite(now):
            raise ValueError('Invalid runtime clock')
        age = now - observed_ts
        if age < -MAX_FUTURE_SKEW_SECONDS:
            raise ValueError('ChatGPT capability manifest observed_at is materially in the future')
        stale = age > self.max_manifest_age_seconds

        normalized = deepcopy(manifest)
        if stale:
            raw_capabilities = normalized.get('capabilities')
            if isinstance(raw_capabilities, list):
                for raw in raw_capabilities:
                    if isinstance(raw, dict):
                        raw['availability'] = 'UNVERIFIED'
        return normalized, stale

    def import_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        """Import explicit browser metadata without granting executable capability."""
        normalized, stale = self.normalize(manifest)
        result = self.catalog.import_manifest(normalized)
        return {
            **result,
            'source_id': CHATGPT_SOURCE_ID,
            'stale_manifest': stale,
        }
