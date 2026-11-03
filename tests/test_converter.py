"""
Unit tests for FormatConverter (HTML, JSON AST, plain text).
"""

import unittest
from pathlib import Path
import tempfile

from docstool.converter import FormatConverter


class TestFormatConverter(unittest.TestCase):

    def test_strip_frontmatter_and_plain_text(self):
        md = """---
title: Sample
---
# Welcome

Visit [Google](https://google.com) and run `restic check`.
"""
        plain = FormatConverter.to_plain_text(md)
        self.assertNotIn("---", plain)
        self.assertNotIn("[Google]", plain)
        self.assertIn("Google", plain)
        self.assertIn("restic check", plain)

    def test_to_html(self):
        md = "## Quick Start\n\nRun **restic init** to create a repo."
        html = FormatConverter.to_html(md, title="Test")
        self.assertIn("<h2>Quick Start</h2>", html)
        self.assertIn("<strong>restic init</strong>", html)
        self.assertIn("<!DOCTYPE html>", html)

    def test_to_json_ast(self):
        temp_dir = tempfile.TemporaryDirectory()
        doc = Path(temp_dir.name) / "doc.md"
        doc.write_text("""---
title: Doc Title
description: Desc
author: Author
date: 2026-11-03
tags: [tag1]
---
# Main Section

Paragraph 1

```bash
echo hello
```
""", encoding="utf-8")

        with open(doc, "r", encoding="utf-8") as f:
            content = f.read()

        ast = FormatConverter.to_json_ast(doc, content)
        self.assertEqual(ast["metadata"]["title"], "Doc Title")
        self.assertTrue(len(ast["sections"]) > 0)
        temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
