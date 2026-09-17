import tempfile
import unittest
from pathlib import Path

from tooling.agentic.chatgpt_capability_manifest import ChatGPTCapabilityManifestBridge
from tooling.agentic.external_capabilities import (
    CapabilityAvailability,
    ExternalCapabilityCatalog,
)


class ChatGPTCapabilityManifestTests(unittest.TestCase):
    def _manifest(self, observed_at='2026-09-16T17:40:00+00:00', availability='KNOWN'):
        return {
            'schema_version': 1,
            'source_id': 'chatgpt-browser',
            'observed_at': observed_at,
            'source_provenance': 'explicit-user-export',
            'capabilities': [
                {
                    'capability_id': 'github',
                    'name': 'GitHub',
                    'kind': 'connector',
                    'provider': 'chatgpt',
                    'capabilities': ['repository.read'],
                    'availability': availability,
                }
            ],
        }

    def test_chatgpt_manifest_imports_as_known_not_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = 1_789_580_700.0
            catalog = ExternalCapabilityCatalog(Path(tmp), clock=lambda: now)
            bridge = ChatGPTCapabilityManifestBridge(catalog, clock=lambda: now)

            result = bridge.import_manifest(self._manifest())
            self.assertEqual(result['inserted'], 1)
            self.assertFalse(result['stale_manifest'])
            item = catalog.get('chatgpt-browser', 'github')
            self.assertEqual(item.availability_state, CapabilityAvailability.KNOWN)
            self.assertEqual(item.invocation_mode, 'catalog_only')
            self.assertIsNone(item.last_verified_at)

    def test_old_manifest_does_not_claim_current_availability(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = 1_789_580_700.0
            catalog = ExternalCapabilityCatalog(Path(tmp), clock=lambda: now)
            bridge = ChatGPTCapabilityManifestBridge(
                catalog,
                clock=lambda: now,
                max_manifest_age_seconds=300,
            )
            old = self._manifest(observed_at='2026-09-16T16:00:00+00:00', availability='KNOWN')

            result = bridge.import_manifest(old)
            self.assertTrue(result['stale_manifest'])
            item = catalog.get('chatgpt-browser', 'github')
            self.assertEqual(item.availability_state, CapabilityAvailability.UNVERIFIED)
            self.assertEqual(item.last_observed_at, old['observed_at'])

    def test_materially_future_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            now = 1_789_580_700.0
            bridge = ChatGPTCapabilityManifestBridge(
                ExternalCapabilityCatalog(Path(tmp), clock=lambda: now),
                clock=lambda: now,
            )
            future = self._manifest(observed_at='2026-09-16T18:00:00+00:00')
            with self.assertRaisesRegex(ValueError, 'future|observed_at'):
                bridge.import_manifest(future)

    def test_manifest_rejects_secret_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = ExternalCapabilityCatalog(Path(tmp))
            bridge = ChatGPTCapabilityManifestBridge(catalog)
            for field in ('cookie', 'access_token', 'session_token', 'api_key', 'authorization'):
                manifest = self._manifest()
                manifest[field] = 'must-not-enter-runtime-state'
                with self.subTest(field=field):
                    with self.assertRaisesRegex(ValueError, 'secret|field|manifest'):
                        bridge.import_manifest(manifest)

    def test_conversation_text_or_json_string_is_not_a_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = ChatGPTCapabilityManifestBridge(ExternalCapabilityCatalog(Path(tmp)))
            for text in (
                'I have the GitHub plugin installed in ChatGPT.',
                '{"schema_version":1,"source_id":"chatgpt-browser","capabilities":[]}',
            ):
                with self.subTest(text=text):
                    with self.assertRaisesRegex(TypeError, 'object|dict|manifest'):
                        bridge.import_manifest(text)

    def test_chatgpt_bridge_rejects_other_source_or_provider_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = ChatGPTCapabilityManifestBridge(ExternalCapabilityCatalog(Path(tmp)))
            wrong_source = self._manifest()
            wrong_source['source_id'] = 'random-browser'
            with self.assertRaisesRegex(ValueError, 'source_id'):
                bridge.import_manifest(wrong_source)

            wrong_provider = self._manifest()
            wrong_provider['capabilities'][0]['provider'] = 'unknown-provider'
            with self.assertRaisesRegex(ValueError, 'provider'):
                bridge.import_manifest(wrong_provider)

    def test_manifest_cannot_smuggle_executable_availability(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge = ChatGPTCapabilityManifestBridge(ExternalCapabilityCatalog(Path(tmp)))
            for state in ('AVAILABLE_LOCAL', 'AVAILABLE_DELEGATED'):
                with self.subTest(state=state):
                    with self.assertRaisesRegex(ValueError, 'availability'):
                        bridge.import_manifest(self._manifest(availability=state))


if __name__ == '__main__':
    unittest.main()
