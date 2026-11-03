"""
Unit tests for MetadataChecker (frontmatter schemas and word counts).
"""

import unittest
from pathlib import Path
import tempfile

from docstool.metadata_checker import MetadataChecker


class TestMetadataChecker(unittest.TestCase):

    def setUp(self):
        self.checker = MetadataChecker()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_frontmatter_parsing(self):
        doc = Path(self.temp_dir.name) / "valid.md"
        content = """---
title: Test Title
description: Test Description
author: Technical Writer
date: 2026-11-03
tags:
  - backup
  - storage
---

This is a test document with twelve words written to calculate proper word count.
"""
        doc.write_text(content, encoding="utf-8")

        meta, body, violations = self.checker.parse_file(doc)
        self.assertEqual(len(violations), 0)
        self.assertIsNotNone(meta)
        self.assertEqual(meta["title"], "Test Title")
        self.assertEqual(len(meta["tags"]), 2)
        self.assertTrue(meta["word_count"] > 10)
        self.assertTrue(meta["has_valid_frontmatter"])

    def test_missing_frontmatter_fails(self):
        doc = Path(self.temp_dir.name) / "no_meta.md"
        doc.write_text("# Hello World\n\nNo frontmatter here.", encoding="utf-8")

        meta, body, violations = self.checker.parse_file(doc)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule_id"], "META-MISSING-FRONTMATTER")

    def test_missing_required_property_fails(self):
        doc = Path(self.temp_dir.name) / "missing_field.md"
        content = """---
title: Only Title
---
Content here.
"""
        doc.write_text(content, encoding="utf-8")

        meta, body, violations = self.checker.parse_file(doc)
        rule_ids = [v["rule_id"] for v in violations]
        self.assertIn("META-MISSING-DESCRIPTION", rule_ids)
        self.assertIn("META-MISSING-AUTHOR", rule_ids)


if __name__ == "__main__":
    unittest.main()
