import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tooling.agentic.external_capabilities import (
    CapabilityAvailability,
    ExternalCapabilityCatalog,
)
from tooling.agentic.vault import CognitiveVaultBridge
from tooling.agentic.vault_capabilities import VaultCapabilityProjector


class VaultCapabilityProjectorTests(unittest.TestCase):
    def _clock(self, text: str) -> float:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp()

    def _manifest(self, observed_at: str):
        return {
            'schema_version': 1,
            'source_id': 'chatgpt-browser',
            'observed_at': observed_at,
            'source_provenance': 'explicit-user-export',
            'capabilities': [
                {
                    'capability_id': 'local-tool',
                    'name': 'Local Tool',
                    'kind': 'tool',
                    'provider': 'chatgpt',
                    'capabilities': ['local.read'],
                    'availability': 'KNOWN',
                },
                {
                    'capability_id': 'delegated-tool',
                    'name': 'Delegated Tool',
                    'kind': 'connector',
                    'provider': 'chatgpt',
                    'capabilities': ['remote.read'],
                    'availability': 'KNOWN',
                },
                {
                    'capability_id': 'known-tool',
                    'name': 'Known Tool',
                    'kind': 'skill',
                    'provider': 'chatgpt',
                    'capabilities': ['known.read'],
                    'availability': 'KNOWN',
                },
                {
                    'capability_id': 'unverified-tool',
                    'name': 'Unverified Tool',
                    'kind': 'skill',
                    'provider': 'chatgpt',
                    'capabilities': ['unknown.read'],
                    'availability': 'UNVERIFIED',
                },
                {
                    'capability_id': 'unavailable-tool',
                    'name': 'Unavailable Tool',
                    'kind': 'connector',
                    'provider': 'chatgpt',
                    'capabilities': ['offline.read'],
                    'availability': 'KNOWN',
                },
                {
                    'capability_id': 'revoked-tool',
                    'name': 'Revoked Tool',
                    'kind': 'connector',
                    'provider': 'chatgpt',
                    'capabilities': ['revoked.read'],
                    'availability': 'KNOWN',
                },
            ],
        }

    def _catalog(self, root: Path, *, now: float) -> ExternalCapabilityCatalog:
        catalog = ExternalCapabilityCatalog(
            root / 'state',
            clock=lambda: now,
            verification_ttl_seconds=300,
        )
        observed = datetime.fromtimestamp(now, timezone.utc).isoformat()
        catalog.import_manifest(self._manifest(observed))
        catalog.mark_availability(
            'chatgpt-browser',
            'local-tool',
            CapabilityAvailability.AVAILABLE_LOCAL,
            verified_at=observed,
        )
        catalog.mark_availability(
            'chatgpt-browser',
            'delegated-tool',
            CapabilityAvailability.AVAILABLE_DELEGATED,
            verified_at=observed,
        )
        catalog.mark_availability(
            'chatgpt-browser',
            'unavailable-tool',
            CapabilityAvailability.UNAVAILABLE,
            verified_at=None,
        )
        catalog.mark_availability(
            'chatgpt-browser',
            'revoked-tool',
            CapabilityAvailability.REVOKED,
            verified_at=None,
        )
        return catalog

    def test_projects_distinct_execution_states_with_source_and_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = self._clock('2026-09-16T18:00:00+00:00')
            catalog = self._catalog(root, now=now)
            projector = VaultCapabilityProjector(root, catalog=catalog)

            result = projector.sync()
            self.assertTrue(result['changed'])
            self.assertEqual(result['capabilities'], 6)
            note = (root / '20 - External Capability Matrix.md').read_text(encoding='utf-8')

            self.assertIn('LOCAL EXECUTABLE', note)
            self.assertIn('DELEGATED / PROVIDER VERIFIED', note)
            self.assertIn('KNOWN ONLY', note)
            self.assertIn('UNVERIFIED / STALE', note)
            self.assertIn('REVOKED / UNAVAILABLE', note)
            self.assertIn('chatgpt-browser', note)
            self.assertIn('chatgpt', note)
            self.assertIn('2026-09-16T18:00:00+00:00', note)
            self.assertIn('jarvis:projection:start', note)

    def test_stale_executable_verification_is_rendered_unverified_not_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            verified_now = self._clock('2026-09-16T18:00:00+00:00')
            self._catalog(root, now=verified_now)
            stale_catalog = ExternalCapabilityCatalog(
                root / 'state',
                clock=lambda: verified_now + 301,
                verification_ttl_seconds=300,
            )
            projector = VaultCapabilityProjector(root, catalog=stale_catalog)

            projector.sync()
            note = (root / '20 - External Capability Matrix.md').read_text(encoding='utf-8')
            delegated_row = next(line for line in note.splitlines() if 'Delegated Tool' in line)
            local_row = next(line for line in note.splitlines() if 'Local Tool' in line)
            self.assertIn('UNVERIFIED / STALE', delegated_row)
            self.assertIn('UNVERIFIED / STALE', local_row)
            self.assertNotIn('PROVIDER VERIFIED', delegated_row)
            self.assertNotIn('LOCAL EXECUTABLE', local_row)

    def test_projection_preserves_human_text_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note_path = root / '20 - External Capability Matrix.md'
            human = '# Human capability notes\nKeep this paragraph.\n'
            note_path.write_text(human, encoding='utf-8')
            now = self._clock('2026-09-16T18:00:00+00:00')
            projector = VaultCapabilityProjector(root, catalog=self._catalog(root, now=now))

            first = projector.sync()
            second = projector.sync()

            self.assertTrue(first['changed'])
            self.assertFalse(second['changed'])
            self.assertTrue(note_path.read_text(encoding='utf-8').startswith(human))

    def test_projection_uses_selected_catalog_fields_and_does_not_dump_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = self._clock('2026-09-16T18:00:00+00:00')
            catalog = self._catalog(root, now=now)
            catalog_path = root / 'state' / 'external_capabilities' / 'catalog.json'
            raw = catalog_path.read_text(encoding='utf-8')
            self.assertIn('metadata_hash', raw)

            VaultCapabilityProjector(root, catalog=catalog).sync()
            note = (root / '20 - External Capability Matrix.md').read_text(encoding='utf-8')
            self.assertNotIn('metadata_hash', note)
            self.assertNotIn('invocation_mode', note)
            self.assertNotIn('catalog.json', note)

    def test_legacy_vault_bridge_exposes_managed_capability_sync(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = self._clock('2026-09-16T18:00:00+00:00')
            catalog = self._catalog(root, now=now)

            result = CognitiveVaultBridge.sync_external_capabilities(root, catalog=catalog)

            self.assertEqual(result['status'], 'SUCCESS')
            self.assertEqual(result['note'], '20 - External Capability Matrix.md')
            self.assertEqual(result['capabilities'], 6)


if __name__ == '__main__':
    unittest.main()
