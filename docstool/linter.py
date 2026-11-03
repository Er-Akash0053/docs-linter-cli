"""
Style & Terminology Linter Module.
Validates Markdown content against style rules while smartly ignoring code blocks.
"""

import re
from pathlib import Path
from typing import List, Dict, Any


class StyleLinter:
    """Scans Markdown files for terminology, clarity, and style guide violations."""

    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = rules
        # Compile regex patterns for performance
        self.compiled_rules = []
        for rule in self.rules:
            self.compiled_rules.append({
                "rule_id": rule["rule_id"],
                "category": rule["category"],
                "pattern": re.compile(rule["pattern"], re.IGNORECASE),
                "preferred_term": rule.get("preferred_term"),
                "explanation": rule["explanation"],
                "severity": rule["severity"]
            })

    def lint_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Lints a single Markdown file line by line."""
        violations: List[Dict[str, Any]] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            violations.append({
                "file_path": str(file_path),
                "line_number": 0,
                "rule_id": "FILE-READ-ERROR",
                "severity": "ERROR",
                "found_text": "",
                "message": f"Failed to read file: {e}",
                "suggested_replacement": ""
            })
            return violations

        in_fenced_code = False

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track fenced code blocks (``` or ~~~)
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fenced_code = not in_fenced_code
                continue

            # Skip checking inside fenced code blocks
            if in_fenced_code:
                continue

            # Strip inline code (`...`) to prevent false positives in CLI commands
            clean_line = re.sub(r"`[^`]*`", "", line)

            # Check each compiled rule
            for rule in self.compiled_rules:
                matches = list(rule["pattern"].finditer(clean_line))
                for match in matches:
                    found_text = match.group(0)
                    violations.append({
                        "file_path": str(file_path),
                        "line_number": idx,
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "found_text": found_text,
                        "message": f"{rule['explanation']} Found '{found_text}'",
                        "suggested_replacement": rule.get("preferred_term", "")
                    })

        return violations

    def lint_directory(self, dir_path: Path) -> List[Dict[str, Any]]:
        """Lints all Markdown files (.md) within a directory recursively."""
        all_violations: List[Dict[str, Any]] = []
        md_files = list(dir_path.rglob("*.md"))

        for md_file in md_files:
            violations = self.lint_file(md_file)
            all_violations.extend(violations)

        return all_violations
