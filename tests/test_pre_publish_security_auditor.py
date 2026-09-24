import unittest

from tooling.audit_pre_publish_security import find_host_metadata, is_ignored


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

    def test_remote_runtime_state_glob_is_ignored(self):
        rules = ["state/remote_*.json"]
        for path in (
            "state/remote_devices.json",
            "state/remote_host.json",
            "state/remote_commands.json",
            "state/remote_tasks.json",
        ):
            self.assertTrue(is_ignored(path, rules), path)


if __name__ == "__main__":
    unittest.main()
