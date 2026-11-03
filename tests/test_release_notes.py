"""
Unit tests for ReleaseNotesAssembler.
"""

import unittest
from docstool.release_notes import ReleaseNotesAssembler


class TestReleaseNotes(unittest.TestCase):

    def setUp(self):
        self.assembler = ReleaseNotesAssembler()

    def test_parse_conventional_commits(self):
        c1 = {"commit_hash": "a1b2c3d4", "subject": "feat(s3): add OIDC support", "author": "Alice", "date": "2026-11-03"}
        p1 = self.assembler.parse_commit(c1)
        self.assertEqual(p1["commit_type"], "feat")
        self.assertEqual(p1["scope"], "s3")
        self.assertEqual(p1["description"], "add OIDC support")
        self.assertFalse(p1["is_breaking"])

        c2 = {"commit_hash": "e5f6a7b8", "subject": "feat(core)!: change default repo format", "author": "Bob", "date": "2026-11-03"}
        p2 = self.assembler.parse_commit(c2)
        self.assertTrue(p2["is_breaking"])

    def test_generate_markdown_sections(self):
        parsed = [
            {"commit_hash": "111", "commit_type": "feat", "scope": "s3", "description": "add OIDC", "author": "Alice", "date": "2026-11-03", "is_breaking": False},
            {"commit_hash": "222", "commit_type": "fix", "scope": "cli", "description": "resolve memory leak", "author": "Bob", "date": "2026-11-03", "is_breaking": False},
            {"commit_hash": "333", "commit_type": "feat", "scope": "format", "description": "v2 repo required", "author": "Charlie", "date": "2026-11-03", "is_breaking": True}
        ]

        md = self.assembler.generate_markdown("v0.17.0", parsed)
        self.assertIn("# Release Notes - v0.17.0", md)
        self.assertIn("## ⚠️ BREAKING CHANGES", md)
        self.assertIn("## 🚀 Features", md)
        self.assertIn("## 🐛 Bug Fixes", md)
        self.assertIn("add OIDC", md)
        self.assertIn("resolve memory leak", md)


if __name__ == "__main__":
    unittest.main()
