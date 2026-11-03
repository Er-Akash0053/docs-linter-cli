"""
Metadata & Frontmatter Checker Module.
Validates YAML frontmatter schemas, calculates word counts, and estimated reading time.
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional


class MetadataChecker:
    """Validates YAML frontmatter against documentation standards."""

    REQUIRED_FIELDS = ["title", "description", "author", "date", "tags"]
    WORDS_PER_MINUTE = 200

    def parse_file(self, file_path: Path) -> Tuple[Optional[Dict[str, Any]], str, List[Dict[str, Any]]]:
        """
        Parses YAML frontmatter and Markdown body.
        Returns: (frontmatter_dict, body_content, violations_list)
        """
        violations: List[Dict[str, Any]] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            violations.append({
                "file_path": str(file_path),
                "line_number": 0,
                "rule_id": "META-READ-ERROR",
                "severity": "ERROR",
                "found_text": "",
                "message": f"Failed to read file: {e}",
                "suggested_replacement": ""
            })
            return None, "", violations

        # Match frontmatter: starting at line 1 between --- and ---
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)

        if not frontmatter_match:
            violations.append({
                "file_path": str(file_path),
                "line_number": 1,
                "rule_id": "META-MISSING-FRONTMATTER",
                "severity": "ERROR",
                "found_text": "",
                "message": "Missing required YAML frontmatter header (bounded by '---').",
                "suggested_replacement": ""
            })
            return None, content, violations

        raw_yaml = frontmatter_match.group(1)
        body = frontmatter_match.group(2)

        try:
            meta = yaml.safe_load(raw_yaml)
            if not isinstance(meta, dict):
                violations.append({
                    "file_path": str(file_path),
                    "line_number": 1,
                    "rule_id": "META-INVALID-FORMAT",
                    "severity": "ERROR",
                    "found_text": raw_yaml[:30],
                    "message": "YAML frontmatter must be a key-value mapping dictionary.",
                    "suggested_replacement": ""
                })
                return None, body, violations
        except yaml.YAMLError as e:
            violations.append({
                "file_path": str(file_path),
                "line_number": 1,
                "rule_id": "META-YAML-SYNTAX",
                "severity": "ERROR",
                "found_text": "",
                "message": f"Syntax error in YAML frontmatter: {e}",
                "suggested_replacement": ""
            })
            return None, body, violations

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in meta or meta[field] is None:
                violations.append({
                    "file_path": str(file_path),
                    "line_number": 1,
                    "rule_id": f"META-MISSING-{field.upper()}",
                    "severity": "ERROR",
                    "found_text": "",
                    "message": f"Required metadata property '{field}' is missing.",
                    "suggested_replacement": ""
                })

        # Validate types
        if "tags" in meta and not isinstance(meta["tags"], list):
            violations.append({
                "file_path": str(file_path),
                "line_number": 1,
                "rule_id": "META-TAGS-NOT-LIST",
                "severity": "WARNING",
                "found_text": str(meta.get("tags")),
                "message": "Metadata 'tags' should be a YAML list of strings.",
                "suggested_replacement": ""
            })

        # Calculate word count & reading time
        words = len(re.findall(r"\w+", body))
        reading_time = round(words / self.WORDS_PER_MINUTE, 1)

        meta["word_count"] = words
        meta["reading_time_min"] = reading_time
        meta["has_valid_frontmatter"] = len(violations) == 0
        meta["file_path"] = str(file_path)

        return meta, body, violations

    def check_directory(self, dir_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Checks all Markdown files in a directory for metadata compliance."""
        all_metadata: List[Dict[str, Any]] = []
        all_violations: List[Dict[str, Any]] = []

        for md_file in dir_path.rglob("*.md"):
            meta, _, violations = self.parse_file(md_file)
            if meta:
                all_metadata.append(meta)
            all_violations.extend(violations)

        return all_metadata, all_violations
