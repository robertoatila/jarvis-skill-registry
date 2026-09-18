"""Plan 4 Task 3 contracts for repository-scale context admission evidence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.repository_context_benchmark import (
    CLAIM_BOUNDARY,
    MANIFEST_PATH,
    evaluate_fixture,
    load_fixture,
    main,
)


class RepositoryContextBenchmarkTests(unittest.TestCase):
    def test_public_fixture_is_repository_scale_and_represents_required_roles(self):
        fixture = load_fixture()
        roles = {item["role"] for item in fixture["items"]}

        self.assertGreater(len(fixture["items"]), 6)
        self.assertTrue(
            {"required", "relevant", "duplicate", "stale", "irrelevant"}.issubset(roles)
        )
        by_source = {item["source"]: item for item in fixture["items"]}
        self.assertEqual(
            by_source["context-relevant.txt"]["content"],
            by_source["duplicate-context.txt"]["content"],
        )
        self.assertLess(
            by_source["stale-note.txt"]["valid_until"],
            fixture["now"],
        )

    def test_default_benchmark_reports_raw_bytes_sources_and_unknown_tokens_truthfully(self):
        result = evaluate_fixture(load_fixture(), commit_sha="fixture-sha")

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["commit_sha"], "fixture-sha")
        self.assertEqual(
            result["declared_budget"]["unit"],
            "serialized_utf8_bytes",
        )
        self.assertGreater(result["raw_source_bytes"], 0)
        self.assertGreater(
            result["naive_serialized_bytes"],
            result["bounded_serialized_bytes"],
        )
        self.assertLessEqual(
            result["bounded_serialized_bytes"],
            result["declared_budget"]["value"],
        )
        self.assertEqual(result["required_sources_missing"], [])
        self.assertTrue(
            set(result["required_sources"]).issubset(result["sources_loaded"])
        )
        self.assertTrue(
            set(result["stale_sources"]).issubset(result["sources_omitted"])
        )
        self.assertIn("duplicate-context.txt", result["sources_loaded"])
        self.assertIn("irrelevant-ui.txt", result["sources_omitted"])
        self.assertEqual(
            result["token_estimate"],
            {"status": "UNKNOWN", "value": None, "method": None},
        )
        self.assertTrue(all(result["invariants"].values()))
        self.assertIn("not provider token savings", CLAIM_BOUNDARY)

    def test_explicit_estimator_requires_and_reports_method(self):
        fixture = load_fixture()

        with self.assertRaisesRegex(ValueError, "TOKEN_ESTIMATION_METHOD_REQUIRED"):
            evaluate_fixture(
                fixture,
                commit_sha="fixture-sha",
                token_estimator=lambda text: len(text) // 4,
            )

        result = evaluate_fixture(
            fixture,
            commit_sha="fixture-sha",
            token_estimator=lambda text: len(text) // 4,
            token_estimation_method="fixture_chars_div_4",
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["token_estimate"]["status"], "ESTIMATED")
        self.assertGreater(result["token_estimate"]["value"], 0)
        self.assertEqual(
            result["token_estimate"]["method"],
            "fixture_chars_div_4",
        )

    def test_manifest_source_paths_fail_closed_on_traversal(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["items"][0]["path"] = "../outside.txt"

        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "escapes fixture directory"):
                load_fixture(manifest_path)

    def test_output_flag_writes_canonical_machine_readable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "repository-context.json"
            exit_code = main(["--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["benchmark"], "repository-context-admission-v1")
        self.assertIn("bounded_serialized_bytes", payload)
        self.assertIn("sources_loaded", payload)
        self.assertIn("sources_omitted", payload)


if __name__ == "__main__":
    unittest.main()
