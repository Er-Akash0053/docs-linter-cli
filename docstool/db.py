"""
Audit Database Module using SQLite and pure SQL.
Stores style rules, document metadata, lint violations, and git release commits.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class AuditDatabase:
    """Manages the SQLite database for documentation quality audits."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path("docs_audit.db")
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        """Initializes tables and indexes using standard SQL DDL."""
        cursor = self.conn.cursor()

        # 1. Style Rules Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS style_rules (
                rule_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                pattern TEXT NOT NULL,
                preferred_term TEXT,
                explanation TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('ERROR', 'WARNING', 'INFO'))
            );
        """)

        # 2. Audit Runs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                target_dir TEXT NOT NULL,
                files_scanned INTEGER NOT NULL,
                total_issues INTEGER NOT NULL
            );
        """)

        # 3. Lint Violations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lint_violations (
                violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                rule_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                found_text TEXT NOT NULL,
                message TEXT NOT NULL,
                suggested_replacement TEXT,
                FOREIGN KEY (run_id) REFERENCES audit_runs (run_id)
            );
        """)

        # 4. Document Metadata Inventory Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_metadata (
                file_path TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                author TEXT,
                date TEXT,
                tags TEXT,
                word_count INTEGER DEFAULT 0,
                reading_time_min REAL DEFAULT 0.0,
                has_valid_frontmatter INTEGER DEFAULT 0
            );
        """)

        # 5. Git Release Commits Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS release_commits (
                commit_hash TEXT PRIMARY KEY,
                commit_type TEXT NOT NULL,
                scope TEXT,
                description TEXT NOT NULL,
                author TEXT,
                date TEXT,
                is_breaking INTEGER NOT NULL DEFAULT 0
            );
        """)

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_run ON lint_violations(run_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_file ON lint_violations(file_path);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_type ON release_commits(commit_type);")

        self.conn.commit()

    def populate_default_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Upserts style rules into the database using SQL."""
        cursor = self.conn.cursor()
        for rule in rules:
            cursor.execute("""
                INSERT OR REPLACE INTO style_rules 
                (rule_id, category, pattern, preferred_term, explanation, severity)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (
                rule["rule_id"],
                rule["category"],
                rule["pattern"],
                rule.get("preferred_term"),
                rule["explanation"],
                rule["severity"]
            ))
        self.conn.commit()

    def get_active_rules(self) -> List[Dict[str, Any]]:
        """Queries all active style rules using SQL."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT rule_id, category, pattern, preferred_term, explanation, severity FROM style_rules;")
        return [dict(row) for row in cursor.fetchall()]

    def record_audit_run(self, target_dir: str, files_scanned: int, violations: List[Dict[str, Any]]) -> int:
        """Records an audit run and its violations in a single SQL transaction."""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        total_issues = len(violations)

        cursor.execute("""
            INSERT INTO audit_runs (timestamp, target_dir, files_scanned, total_issues)
            VALUES (?, ?, ?, ?);
        """, (timestamp, target_dir, files_scanned, total_issues))
        run_id = cursor.lastrowid

        for v in violations:
            cursor.execute("""
                INSERT INTO lint_violations 
                (run_id, file_path, line_number, rule_id, severity, found_text, message, suggested_replacement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                run_id,
                v["file_path"],
                v["line_number"],
                v["rule_id"],
                v["severity"],
                v.get("found_text", ""),
                v["message"],
                v.get("suggested_replacement", "")
            ))

        self.conn.commit()
        return run_id

    def upsert_document_metadata(self, meta: Dict[str, Any]) -> None:
        """Stores document frontmatter metadata into SQL."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO document_metadata 
            (file_path, title, description, author, date, tags, word_count, reading_time_min, has_valid_frontmatter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            meta["file_path"],
            meta.get("title"),
            meta.get("description"),
            meta.get("author"),
            meta.get("date"),
            ", ".join(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else meta.get("tags"),
            meta.get("word_count", 0),
            meta.get("reading_time_min", 0.0),
            1 if meta.get("has_valid_frontmatter") else 0
        ))
        self.conn.commit()

    def record_commit(self, commit: Dict[str, Any]) -> None:
        """Inserts a parsed git commit into SQL."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO release_commits
            (commit_hash, commit_type, scope, description, author, date, is_breaking)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            commit["commit_hash"],
            commit["commit_type"],
            commit.get("scope"),
            commit["description"],
            commit.get("author"),
            commit.get("date"),
            1 if commit.get("is_breaking") else 0
        ))
        self.conn.commit()

    # --- SQL Analytical Reporting Queries ---

    def query_top_violating_files(self, limit: int = 5) -> List[Dict[str, Any]]:
        """SQL query: Find files with the highest number of linting issues."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT file_path, COUNT(*) AS issue_count,
                   SUM(CASE WHEN severity = 'ERROR' THEN 1 ELSE 0 END) AS error_count,
                   SUM(CASE WHEN severity = 'WARNING' THEN 1 ELSE 0 END) AS warning_count
            FROM lint_violations
            GROUP BY file_path
            ORDER BY issue_count DESC
            LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def query_violations_by_category(self) -> List[Dict[str, Any]]:
        """SQL query: Breakdown of violations by rule category using an INNER JOIN."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(sr.category, 'structure') AS category, 
                   COUNT(lv.violation_id) AS total_count,
                   SUM(CASE WHEN lv.severity = 'ERROR' THEN 1 ELSE 0 END) AS errors
            FROM lint_violations lv
            LEFT JOIN style_rules sr ON lv.rule_id = sr.rule_id
            GROUP BY COALESCE(sr.category, 'structure')
            ORDER BY total_count DESC;
        """)
        return [dict(row) for row in cursor.fetchall()]

    def query_content_inventory(self) -> List[Dict[str, Any]]:
        """SQL query: Inventory of all documentation pages with word counts and reading times."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT file_path, title, word_count, reading_time_min, has_valid_frontmatter
            FROM document_metadata
            ORDER BY word_count DESC;
        """)
        return [dict(row) for row in cursor.fetchall()]

    def query_release_commits_grouped(self) -> Dict[str, List[Dict[str, Any]]]:
        """SQL query: Group commits by commit_type for release notes."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT commit_hash, commit_type, scope, description, is_breaking
            FROM release_commits
            ORDER BY commit_type, commit_hash;
        """)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            t = row_dict["commit_type"]
            grouped.setdefault(t, []).append(row_dict)
        return grouped

    def close(self) -> None:
        """Closes the SQLite database connection."""
        self.conn.close()
