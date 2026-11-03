"""
Unit tests for StyleLinter (terminology, bias, and clarity rules).
"""

import unittest
from pathlib import Path
import tempfile

from docstool.linter import StyleLinter
from docstool.rules import DEFAULT_STYLE_RULES


class TestStyleLinter(unittest.TestCase):

    def setUp(self):
        self.linter = StyleLinter(DEFAULT_STYLE_RULES)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_catches_non_inclusive_terms(self):
        """Verifies that non-inclusive terms like whitelist/blacklist are flagged."""
        file_path = Path(self.temp_dir.name) / "doc.md"
        file_path.write_text("Add the IP to the whitelist and blacklist the rest.", encoding="utf-8")

        violations = self.linter.lint_file(file_path)
        rule_ids = [v["rule_id"] for v in violations]
        self.assertIn("STYLE-INCLUSIVE-01", rule_ids)
        self.assertIn("STYLE-INCLUSIVE-02", rule_ids)

    def test_ignores_code_blocks(self):
        """Ensures fenced code blocks and inline backticks are NOT flagged."""
        file_path = Path(self.temp_dir.name) / "code.md"
        content = """# Guide

Here is valid command: `restic backup --exclude-file=whitelist.txt`

```bash
# simply run the command
git push origin master/slave
```
"""
        file_path.write_text(content, encoding="utf-8")

        violations = self.linter.lint_file(file_path)
        # Should be zero because terms are inside inline code `...` and fenced code ```...```
        self.assertEqual(len(violations), 0)

    def test_catches_filler_words(self):
        """Catches condescending filler words like simply and easily in prose."""
        file_path = Path(self.temp_dir.name) / "clarity.md"
        file_path.write_text("You can easily configure this repository.", encoding="utf-8")

        violations = self.linter.lint_file(file_path)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule_id"], "STYLE-CLARITY-01")


if __name__ == "__main__":
    unittest.main()
