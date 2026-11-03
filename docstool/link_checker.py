"""
Link Checker Module.
Scans Markdown files for broken relative links, non-existent target files, and broken heading anchors.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Set


def slugify_heading(heading_text: str) -> str:
    """Converts a Markdown heading into an anchor slug matching standard Markdown parsers."""
    text = heading_text.lower().strip()
    # Remove markdown formatting like bold, links, code ticks
    text = re.sub(r"[`*_\[\]]", "", text)
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def extract_headings(file_path: Path) -> Set[str]:
    """Extracts all heading anchor slugs from a Markdown file."""
    slugs = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r"^#{1,6}\s+(.+)$", line.strip())
                if match:
                    raw_title = match.group(1).strip()
                    # Also handle explicit attribute list IDs like {#custom-id}
                    attr_match = re.search(r"\{#([a-zA-Z0-9_-]+)\}", raw_title)
                    if attr_match:
                        slugs.add(attr_match.group(1))
                    slug = slugify_heading(raw_title)
                    slugs.add(slug)
    except Exception:
        pass
    return slugs


class LinkChecker:
    """Validates internal relative links and anchor fragments across documentation."""

    # Regex matches standard Markdown links: [text](target)
    # Excludes images ![alt](url) by negative lookbehind (?<!\!)
    LINK_REGEX = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.heading_cache: Dict[Path, Set[str]] = {}

    def get_headings_for_file(self, path: Path) -> Set[str]:
        resolved = path.resolve()
        if resolved not in self.heading_cache:
            self.heading_cache[resolved] = extract_headings(resolved)
        return self.heading_cache[resolved]

    def check_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validates all links within a single Markdown file."""
        violations: List[Dict[str, Any]] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            violations.append({
                "file_path": str(file_path),
                "line_number": 0,
                "rule_id": "LINK-READ-ERROR",
                "severity": "ERROR",
                "found_text": "",
                "message": f"Could not read file for link checking: {e}",
                "suggested_replacement": ""
            })
            return violations

        in_fenced_code = False

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fenced_code = not in_fenced_code
                continue
            if in_fenced_code:
                continue

            for match in self.LINK_REGEX.finditer(line):
                link_text = match.group(1)
                raw_target = match.group(2).strip()

                # Clean potential title attributes: [text](url "title")
                target = raw_target.split()[0].replace('"', "").replace("'", "")

                # Skip external links and email links
                if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
                    continue

                # Case A: Same-page anchor link (e.g., #prerequisites)
                if target.startswith("#"):
                    anchor = target.lstrip("#")
                    valid_headings = self.get_headings_for_file(file_path)
                    if anchor not in valid_headings:
                        violations.append({
                            "file_path": str(file_path),
                            "line_number": idx,
                            "rule_id": "LINK-BROKEN-ANCHOR",
                            "severity": "WARNING",
                            "found_text": target,
                            "message": f"Anchor '{target}' does not match any heading in the current document.",
                            "suggested_replacement": ""
                        })
                    continue

                # Case B: Relative link to another file (e.g., ../concepts/architecture.md#heading)
                parts = target.split("#")
                rel_file_path = parts[0]
                target_anchor = parts[1] if len(parts) > 1 else None

                # Resolve target file path relative to current file's parent folder
                target_file = (file_path.parent / rel_file_path).resolve()

                if not target_file.exists():
                    violations.append({
                        "file_path": str(file_path),
                        "line_number": idx,
                        "rule_id": "LINK-BROKEN-FILE",
                        "severity": "ERROR",
                        "found_text": target,
                        "message": f"Target file '{rel_file_path}' does not exist on disk.",
                        "suggested_replacement": ""
                    })
                elif target_anchor:
                    # Check anchor inside the target file
                    target_headings = self.get_headings_for_file(target_file)
                    if target_anchor not in target_headings:
                        violations.append({
                            "file_path": str(file_path),
                            "line_number": idx,
                            "rule_id": "LINK-BROKEN-ANCHOR",
                            "severity": "WARNING",
                            "found_text": target,
                            "message": f"Target anchor '#{target_anchor}' not found in '{rel_file_path}'.",
                            "suggested_replacement": ""
                        })

        return violations

    def check_directory(self, dir_path: Path) -> List[Dict[str, Any]]:
        """Checks all Markdown files in a directory for broken links."""
        all_violations: List[Dict[str, Any]] = []
        for md_file in dir_path.rglob("*.md"):
            violations = self.check_file(md_file)
            all_violations.extend(violations)
        return all_violations
