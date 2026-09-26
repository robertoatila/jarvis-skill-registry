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

    def test_detects_windows_host_identifier_without_literal_fixture_leak(self):
        sample = "DESKTOP-" + "ABC123"
        findings = find_host_metadata(sample)
        self.assertTrue(any(kind == "Windows host identifier" for kind, _ in findings))

    def test_canonical_placeholders_are_not_flagged(self):
        sample = "$REGISTRY_ROOT/reports and %USERPROFILE%\\project"
        self.assertEqual(find_host_metadata(sample), [])

    def test_reports_and_scripts_are_scanned_for_host_metadata(self):
        self.assertTrue(should_scan_host_metadata("reports/acceptance/windows.json"))
        self.assertTrue(should_scan_host_metadata("tooling/bootstrap.ps1"))
        self.assertFalse(should_scan_host_metadata("cache/local/probe.txt"))
        self.assertFalse(should_scan_host_metadata("staging/probe.txt"))
        self.assertFalse(should_scan_host_metadata("backups/probe.txt"))

    def test_canonical_v13_3_binding_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "governance").mkdir()
            (root / "docs" / "security").mkdir(parents=True)
            protocol = {
                "effective_canonical_version": "13.3.0",
                "canonical_source": "docs/security/PROTOCOLO_SEGURANCA_v13.3_CANONICO.md",
                "invariants": [{"id": "SSP13-INV-01"}],
            }
            (root / "governance" / "sovereign-security-protocol-v13.json").write_text(
                json.dumps(protocol),
                encoding="utf-8",
            )
            (root / "docs" / "security" / "PROTOCOLO_SEGURANCA_v13.3_CANONICO.md").write_text(
                "PROTOCOLO SEGURANÇA v13.3\n"
                "Versão: 13.3.0\n"
                "Status: CANÔNICO\n"
                "Substitui: v13.2\n",
                encoding="utf-8",
            )
            loaded, count = validate_security_protocol(root)
            self.assertEqual(loaded["effective_canonical_version"], "13.3.0")
            self.assertEqual(count, 1)

            loaded["effective_canonical_version"] = "13.2.0"
            (root / "governance" / "sovereign-security-protocol-v13.json").write_text(
                json.dumps(loaded),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "canonical v13.3"):
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
