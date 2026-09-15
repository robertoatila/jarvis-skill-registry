#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the J.A.R.V.I.S. 100k+ Star Repositories & Official Sites Catalog."""

import json
import unittest
from pathlib import Path

REGISTRY_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REGISTRY_ROOT / "index" / "repos_100k_stars.json"
OBSIDIAN_NOTE_PATH = REGISTRY_ROOT / "21 - Repositorios 100k+ Estrelas e Radar de Sites Oficiais.md"


class Test100kReposCatalog(unittest.TestCase):
    def test_catalog_file_exists_and_valid(self):
        self.assertTrue(CATALOG_PATH.exists(), "index/repos_100k_stars.json must exist")
        data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

        self.assertIn("repositories", data)
        self.assertIn("total_repos", data)
        repos = data["repositories"]
        self.assertGreaterEqual(len(repos), 40)
        self.assertEqual(len(repos), data["total_repos"])

    def test_all_repositories_meet_100k_contract(self):
        data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        repos = data["repositories"]

        names_seen = set()
        for r in repos:
            name = r.get("name")
            self.assertTrue(name, f"Repository missing name: {r}")
            self.assertNotIn(name, names_seen, f"Duplicate repository name: {name}")
            names_seen.add(name)

            full_name = r.get("full_name")
            self.assertTrue(full_name and "/" in full_name, f"Invalid full_name: {full_name}")

            stars = r.get("stars")
            self.assertIsInstance(stars, int)
            self.assertGreaterEqual(stars, 100000, f"{name} must have at least 100k stars")

            homepage = r.get("homepage_url")
            self.assertTrue(homepage, f"{name} must have a homepage_url")
            self.assertTrue(homepage.startswith("http://") or homepage.startswith("https://"),
                            f"Invalid homepage URL for {name}: {homepage}")

            docs = r.get("docs_url")
            self.assertTrue(docs, f"{name} must have a docs_url")
            self.assertTrue(docs.startswith("http://") or docs.startswith("https://"),
                            f"Invalid docs URL for {name}: {docs}")

            category = r.get("category")
            self.assertTrue(category, f"{name} must have a category")

            description = r.get("description")
            self.assertTrue(description and len(description) > 10, f"{name} must have a valid description")

    def test_obsidian_projection_note_exists(self):
        self.assertTrue(OBSIDIAN_NOTE_PATH.exists(), "Obsidian projection note must exist")
        content = OBSIDIAN_NOTE_PATH.read_text(encoding="utf-8")
        self.assertIn("Radar de Sites Oficiais", content)
        self.assertIn("freeCodeCamp", content)
        self.assertIn("AutoGPT", content)
        self.assertIn("kernel.org", content)


if __name__ == "__main__":
    unittest.main()
