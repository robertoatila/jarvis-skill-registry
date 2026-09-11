"""
test_agentic_quality.py // Unit tests for Quality Review (Phase 25)
"""

import unittest
from tooling.agentic.quality_review import QualityReviewAuditor


class TestQualityReview(unittest.TestCase):

    def setUp(self):
        self.auditor = QualityReviewAuditor()

    def test_01_python_compilation_all_modules(self):
        res = self.auditor.audit_python_compilation()
        self.assertEqual(res["status"], "PASS")
        self.assertGreater(res["total_files"], 20)
        self.assertEqual(len(res["errors"]), 0)

    def test_02_ast_and_zero_placeholders(self):
        res = self.auditor.audit_ast_and_placeholders()
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(res["syntax_clean"])
        self.assertEqual(len(res["placeholders_found"]), 0)

    def test_03_zero_secret_leakage(self):
        res = self.auditor.audit_secret_leakage()
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(len(res["leaks_found"]), 0)

    def test_04_json_schemas_structural_validity(self):
        res = self.auditor.audit_json_schemas()
        self.assertEqual(res["status"], "PASS")
        self.assertGreater(res["total_schemas"], 100)
        self.assertEqual(len(res["invalid_schemas"]), 0)

    def test_05_full_quality_audit(self):
        res = self.auditor.run_full_quality_audit()
        self.assertEqual(res["overall_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
