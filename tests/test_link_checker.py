"""
Unit tests for LinkChecker (internal links and anchors).
"""

import unittest
from pathlib import Path
import tempfile

from docstool.link_checker import LinkChecker, slugify_heading


class TestLinkChecker(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_slugify_heading(self):
        self.assertEqual(slugify_heading("Step 1: Install Restic"), "step-1-install-restic")
        self.assertEqual(slugify_heading("What is `restic check`?"), "what-is-restic-check")

    def test_detects_broken_relative_file_link(self):
        source = self.root / "index.md"
        source.write_text("See [architecture](concepts/architecture.md) for details.", encoding="utf-8")

        checker = LinkChecker(self.root)
        violations = checker.check_file(source)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule_id"], "LINK-BROKEN-FILE")

    def test_validates_existing_file_and_heading_anchor(self):
        concepts_dir = self.root / "concepts"
        concepts_dir.mkdir()
        target = concepts_dir / "arch.md"
        target.write_text("# System Architecture\n\n## Data Flow\n\nContent", encoding="utf-8")

        source = self.root / "index.md"
        source.write_text("Check [Flow](concepts/arch.md#data-flow)", encoding="utf-8")

        checker = LinkChecker(self.root)
        violations = checker.check_file(source)

        # Should be valid (0 violations)
        self.assertEqual(len(violations), 0)

    def test_detects_broken_anchor_in_existing_file(self):
        concepts_dir = self.root / "concepts"
        concepts_dir.mkdir()
        target = concepts_dir / "arch.md"
        target.write_text("# System Architecture\n\n## Real Heading\n", encoding="utf-8")

        source = self.root / "index.md"
        source.write_text("Check [Nonexistent](concepts/arch.md#fake-heading)", encoding="utf-8")

        checker = LinkChecker(self.root)
        violations = checker.check_file(source)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule_id"], "LINK-BROKEN-ANCHOR")


if __name__ == "__main__":
    unittest.main()
