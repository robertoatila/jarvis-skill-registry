import json
import tempfile
import unittest
from pathlib import Path

from tooling.audit_pre_publish_security import (
    find_host_metadata,
    is_ignored,
    should_scan_host_metadata,
    validate_security_protocol,
)


class TestPrePublishSecurityAuditor(unittest.TestCase):
    def test_detects_windows_user_path_without_literal_fixture_leak(self):
        sample = "C:" + "\\Users\\" + "Alice\\AppData\\Local"
        findings = find_host_metadata(sample)
        self.assertTrue(any(kind == "Windows user path" for kind, _ in findings))

    def test_detects_unix_home_without_literal_fixture_leak(self):
        sample = "/home/" + "alice/project"
        findings = find_host_metadata(sample)
        self.assertTrue(any(kind == "Unix/macOS user path" for kind, _ in findings))

    def test_ignores_explicit_unix_username_example(self):
        sample = "/Users/" + "username/monorepo/CLAUDE.md"
        self.assertEqual(find_host_metadata(sample), [])

    def test_ignores_only_documented_home_user_example(self):
        sample = "Examples: " + "/home/" + "user/monorepo/CLAUDE.md"
        self.assertEqual(find_host_metadata(sample), [])
        actual_home = "/home/" + "user/private"
        self.assertTrue(any(kind == "Unix/macOS user path" for kind, _ in find_host_metadata(actual_home)))

    def test_detects_windows_host_identifier_without_literal_fixture_leak(self):
        sample = "DESKTOP-" + "ABC123"
        findings = find_host_metadata(sample)
        self.assertTrue(any(kind == "Windows host identifier" for kind, _ in findings))

    def test_canonical_placeholders_are_not_flagged(self):
        sample = "$REGISTRY_ROOT/reports and %USERPROFILE%\\project"
        self.assertEqual(find_host_metadata(sample), [])

    def test_ignores_windows_placeholder_and_ci_runner(self):
        self.assertEqual(find_host_metadata("C:\\Users\\username\\project"), [])
        self.assertEqual(find_host_metadata("C:\\Users\\RUNNER~1\\AppData\\Local"), [])
        self.assertEqual(find_host_metadata("C:\\Users\\runneradmin\\project"), [])

    def test_ignores_numeric_rest_routes(self):
        self.assertEqual(find_host_metadata("GET /api/v1/users/42/orders"), [])
        self.assertEqual(find_host_metadata("curl /users/123/posts"), [])

    def test_reports_and_scripts_are_scanned_for_host_metadata(self):
        self.assertTrue(should_scan_host_metadata("reports/acceptance/windows.json"))
        self.assertTrue(should_scan_host_metadata("tooling/bootstrap.ps1"))
        self.assertFalse(should_scan_host_metadata("cache/local/probe.txt"))
        self.assertFalse(should_scan_host_metadata("staging/probe.txt"))
        self.assertFalse(should_scan_host_metadata("backups/probe.txt"))

    def test_canonical_v13_4_binding_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "governance").mkdir()
            (root / "docs" / "security").mkdir(parents=True)
            protocol = {
                "effective_canonical_version": "13.4.0",
                "canonical_source": "docs/security/PROTOCOLO_SEGURANCA_v13.4_CANONICO.md",
                "merkle_root_anchor": "a" * 64,
                "invariants": [{"id": "SSP13-INV-01"}],
            }
            (root / "governance" / "sovereign-security-protocol-v13.json").write_text(
                json.dumps(protocol),
                encoding="utf-8",
            )
            (root / "docs" / "security" / "PROTOCOLO_SEGURANCA_v13.4_CANONICO.md").write_text(
                "PROTOCOLO SEGURANÇA v13.4\n"
                "Versão: 13.4.0\n"
                "Status: CANÔNICO\n"
                "Substitui: v13.3\n",
                encoding="utf-8",
            )
            loaded, count = validate_security_protocol(root)
            self.assertEqual(loaded["effective_canonical_version"], "13.4.0")
            self.assertEqual(count, 1)

            loaded["effective_canonical_version"] = "13.2.0"
            (root / "governance" / "sovereign-security-protocol-v13.json").write_text(
                json.dumps(loaded),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "canonical v13.4"):
                validate_security_protocol(root)

            loaded["effective_canonical_version"] = "13.4.0"
            loaded["merkle_root_anchor"] = "not-a-digest"
            (root / "governance" / "sovereign-security-protocol-v13.json").write_text(
                json.dumps(loaded),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Merkle anchor"):
                validate_security_protocol(root)

    def test_remote_runtime_state_glob_is_ignored(self):
        rules = [
            "state/remote_*.json",
            "state/remote_events/",
            "state/remote_service/",
        ]
        for path in (
            "state/remote_devices.json",
            "state/remote_host.json",
            "state/remote_commands.json",
            "state/remote_tasks.json",
            "state/remote_events/session-example.jsonl",
            "state/remote_service/launcher.pyw",
        ):
            self.assertTrue(is_ignored(path, rules), path)


if __name__ == "__main__":
    unittest.main()
