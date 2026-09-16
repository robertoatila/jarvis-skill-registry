import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tooling.agentic.external_capabilities import (
    CapabilityAvailability,
    ExternalCapabilityCatalog,
)


class ExternalCapabilityCatalogTests(unittest.TestCase):
    def _manifest(self, *, availability='KNOWN', name='GitHub Connector'):
        return {
            'schema_version': 1,
            'source_id': 'chatgpt-browser',
            'observed_at': '2026-09-16T17:00:00+00:00',
            'source_provenance': 'explicit-user-export',
            'capabilities': [
                {
                    'capability_id': 'github-connector',
                    'name': name,
                    'provider': 'chatgpt',
                    'kind': 'connector',
                    'capabilities': ['repository.read', 'pull_request.read'],
                    'availability': availability,
                }
            ],
        }

    def test_manifest_imports_as_known_and_never_implies_local_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = ExternalCapabilityCatalog(Path(tmp), clock=lambda: 1_789_577_400.0)
            result = catalog.import_manifest(self._manifest())
            self.assertEqual(result['inserted'], 1)
            self.assertEqual(result['updated'], 0)

            item = catalog.get('chatgpt-browser', 'github-connector')
            self.assertIsNotNone(item)
            self.assertEqual(item.availability_state, CapabilityAvailability.KNOWN)
            self.assertEqual(item.invocation_mode, 'catalog_only')
            self.assertIsNone(item.last_verified_at)
            self.assertEqual(item.provenance, 'explicit-user-export')

    def test_manifest_cannot_claim_available_local_or_delegated(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = ExternalCapabilityCatalog(Path(tmp))
            for state in ('AVAILABLE_LOCAL', 'AVAILABLE_DELEGATED'):
                with self.subTest(state=state):
                    with self.assertRaisesRegex(ValueError, 'availability'):
                        catalog.import_manifest(self._manifest(availability=state))

    def test_reimport_deduplicates_and_preserves_structured_provenance_across_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            catalog = ExternalCapabilityCatalog(state)
            first = catalog.import_manifest(self._manifest())
            first_item = catalog.get('chatgpt-browser', 'github-connector')
            second = catalog.import_manifest(self._manifest(name='GitHub'))
            second_item = catalog.get('chatgpt-browser', 'github-connector')

            self.assertEqual(first['inserted'], 1)
            self.assertEqual(second['inserted'], 0)
            self.assertEqual(second['updated'], 1)
            self.assertEqual(len(catalog.list()), 1)
            self.assertNotEqual(first_item.metadata_hash, second_item.metadata_hash)
            self.assertEqual(second_item.provenance, 'explicit-user-export')
            self.assertEqual(second_item.last_observed_at, '2026-09-16T17:00:00+00:00')

            restarted = ExternalCapabilityCatalog(state)
            restored = restarted.get('chatgpt-browser', 'github-connector')
            self.assertEqual(restored.name, 'GitHub')
            self.assertEqual(restored.metadata_hash, second_item.metadata_hash)

    def test_fresh_delegated_verification_expires_to_unverified_without_erasing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = 1_789_577_400.0
            catalog = ExternalCapabilityCatalog(
                Path(tmp),
                clock=lambda: now,
                verification_ttl_seconds=300,
            )
            catalog.import_manifest(self._manifest())
            verified_at = datetime.fromtimestamp(now, timezone.utc).isoformat()
            catalog.mark_availability(
                'chatgpt-browser',
                'github-connector',
                CapabilityAvailability.AVAILABLE_DELEGATED,
                verified_at=verified_at,
            )
            fresh = catalog.get('chatgpt-browser', 'github-connector')
            self.assertEqual(fresh.availability_state, CapabilityAvailability.AVAILABLE_DELEGATED)
            self.assertEqual(fresh.invocation_mode, 'delegated')

            now += 301
            stale = catalog.get('chatgpt-browser', 'github-connector')
            self.assertEqual(stale.availability_state, CapabilityAvailability.UNVERIFIED)
            self.assertEqual(stale.invocation_mode, 'catalog_only')
            self.assertEqual(stale.last_verified_at, verified_at)

    def test_available_local_requires_separate_fresh_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = 1_789_577_400.0
            catalog = ExternalCapabilityCatalog(Path(tmp), clock=lambda: now)
            catalog.import_manifest(self._manifest())
            with self.assertRaisesRegex(ValueError, 'verified_at'):
                catalog.mark_availability(
                    'chatgpt-browser',
                    'github-connector',
                    CapabilityAvailability.AVAILABLE_LOCAL,
                    verified_at=None,
                )

            verified_at = datetime.fromtimestamp(now, timezone.utc).isoformat()
            catalog.mark_availability(
                'chatgpt-browser',
                'github-connector',
                CapabilityAvailability.AVAILABLE_LOCAL,
                verified_at=verified_at,
            )
            item = catalog.get('chatgpt-browser', 'github-connector')
            self.assertEqual(item.availability_state, CapabilityAvailability.AVAILABLE_LOCAL)
            self.assertEqual(item.invocation_mode, 'local_adapter')

    def test_revocation_is_sticky_across_manifest_reimport_until_explicitly_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = ExternalCapabilityCatalog(Path(tmp))
            catalog.import_manifest(self._manifest())
            catalog.mark_availability(
                'chatgpt-browser',
                'github-connector',
                CapabilityAvailability.REVOKED,
                verified_at=None,
            )
            catalog.import_manifest(self._manifest(name='GitHub Re-observed'))
            item = catalog.get('chatgpt-browser', 'github-connector')
            self.assertEqual(item.name, 'GitHub Re-observed')
            self.assertEqual(item.availability_state, CapabilityAvailability.REVOKED)
            self.assertEqual(item.invocation_mode, 'disabled')

    def test_manifest_rejects_secret_and_session_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = ExternalCapabilityCatalog(Path(tmp))
            for field in ('cookie', 'access_token', 'refresh_token', 'session_token', 'api_key', 'password', 'authorization'):
                manifest = self._manifest()
                manifest['capabilities'][0][field] = 'must-not-persist'
                with self.subTest(field=field):
                    with self.assertRaisesRegex(ValueError, 'secret|field|manifest'):
                        catalog.import_manifest(manifest)

    def test_catalog_schema_exists_and_is_closed_to_unknown_fields(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / 'schemas' / 'external-capability-manifest.schema.json').read_text(encoding='utf-8'))
        self.assertEqual(schema['properties']['schema_version']['const'], 1)
        self.assertFalse(schema['additionalProperties'])
        capability = schema['properties']['capabilities']['items']
        self.assertFalse(capability['additionalProperties'])
        self.assertEqual(
            set(capability['properties']['availability']['enum']),
            {'KNOWN', 'UNVERIFIED'},
        )


if __name__ == '__main__':
    unittest.main()
