"""
Unit tests for the SQLite Database & SQL Queries.
"""

import unittest
from pathlib import Path
import tempfile
import sqlite3

from docstool.db import AuditDatabase


class TestAuditDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_audit.db"
        self.db = AuditDatabase(self.db_path)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_schema_creation(self):
        """Verifies that all 5 SQL tables are initialized."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        self.assertIn("style_rules", tables)
        self.assertIn("audit_runs", tables)
        self.assertIn("lint_violations", tables)
        self.assertIn("document_metadata", tables)
        self.assertIn("release_commits", tables)

    def test_record_audit_and_sql_aggregation(self):
        """Tests inserting violations and querying SQL aggregations."""
        violations = [
            {
                "file_path": "docs/test.md",
                "line_number": 10,
                "rule_id": "STYLE-INCLUSIVE-01",
                "severity": "ERROR",
                "found_text": "whitelist",
                "message": "Use allowlist",
                "suggested_replacement": "allowlist"
            },
            {
                "file_path": "docs/test.md",
                "line_number": 20,
                "rule_id": "STYLE-CLARITY-01",
                "severity": "WARNING",
                "found_text": "simply",
                "message": "Avoid simply",
                "suggested_replacement": ""
            }
        ]
        run_id = self.db.record_audit_run("docs", 1, violations)
        self.assertEqual(run_id, 1)

        top_files = self.db.query_top_violating_files(limit=5)
        self.assertEqual(len(top_files), 1)
        self.assertEqual(top_files[0]["file_path"], "docs/test.md")
        self.assertEqual(top_files[0]["issue_count"], 2)
        self.assertEqual(top_files[0]["error_count"], 1)
        self.assertEqual(top_files[0]["warning_count"], 1)

    def test_document_metadata_inventory(self):
        """Tests upserting and querying document metadata."""
        self.db.upsert_document_metadata({
            "file_path": "docs/intro.md",
            "title": "Introduction",
            "description": "Intro guide",
            "author": "Tech Writer",
            "date": "2026-11-03",
            "tags": ["guide", "intro"],
            "word_count": 450,
            "reading_time_min": 2.2,
            "has_valid_frontmatter": True
        })

        inventory = self.db.query_content_inventory()
        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0]["title"], "Introduction")
        self.assertEqual(inventory[0]["word_count"], 450)
        self.assertEqual(inventory[0]["has_valid_frontmatter"], 1)


if __name__ == "__main__":
    unittest.main()
