"""
Release Notes Assembler Module.
Extracts Git commits, parses Conventional Commits, stores them in SQLite, and generates formatted release notes.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ReleaseNotesAssembler:
    """Compiles release notes from Git commit logs."""

    # Regex matches: type(optional_scope)!: description
    CONVENTIONAL_COMMIT_REGEX = re.compile(
        r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
    )

    SECTION_MAP = {
        "feat": ("🚀 Features", 1),
        "fix": ("🐛 Bug Fixes", 2),
        "perf": ("⚡ Performance Improvements", 3),
        "docs": ("📝 Documentation", 4),
        "refactor": ("♻️ Refactoring", 5),
        "chore": ("🔧 Maintenance & Tooling", 6),
    }

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def get_git_commits(self, commit_range: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extracts commit logs from Git via git command line."""
        cmd = ["git", "log", "--pretty=format:%H%x1f%s%x1f%an%x1f%ad", "--date=short"]
        if commit_range:
            cmd.append(commit_range)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.SubprocessError as e:
            # Fallback for repositories without git history or brand-new repos
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\x1f")
            if len(parts) >= 4:
                commits.append({
                    "commit_hash": parts[0][:8],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3]
                })

        return commits

    def parse_commit(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        """Parses a commit message according to Conventional Commits specification."""
        subject = commit["subject"].strip()
        match = self.CONVENTIONAL_COMMIT_REGEX.match(subject)

        if match:
            c_type = match.group("type").lower()
            scope = match.group("scope")
            breaking = bool(match.group("breaking")) or "BREAKING CHANGE" in subject
            description = match.group("desc").strip()
        else:
            c_type = "chore"
            scope = None
            breaking = False
            description = subject

        return {
            "commit_hash": commit["commit_hash"],
            "commit_type": c_type,
            "scope": scope,
            "description": description,
            "author": commit["author"],
            "date": commit["date"],
            "is_breaking": breaking
        }

    def generate_markdown(
        self,
        version: str,
        parsed_commits: List[Dict[str, Any]],
        title: Optional[str] = None
    ) -> str:
        """Assembles parsed commits into a structured Markdown release document."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        heading = title or f"Release Notes - {version} ({date_str})"

        breaking_list = [c for c in parsed_commits if c.get("is_breaking")]

        # Group commits by category
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for c in parsed_commits:
            t = c["commit_type"]
            grouped.setdefault(t, []).append(c)

        md = [f"# {heading}\n"]

        # 1. Breaking Changes Section
        if breaking_list:
            md.append("## ⚠️ BREAKING CHANGES\n")
            for c in breaking_list:
                scope_str = f"**{c['scope']}**: " if c.get("scope") else ""
                md.append(f"- {scope_str}{c['description']} (`{c['commit_hash']}`)")
            md.append("")

        # 2. Standard Categorized Sections
        sorted_sections = sorted(
            self.SECTION_MAP.items(),
            key=lambda item: item[1][1]
        )

        for type_key, (section_title, _) in sorted_sections:
            if type_key in grouped:
                md.append(f"## {section_title}\n")
                for c in grouped[type_key]:
                    scope_str = f"**{c['scope']}**: " if c.get("scope") else ""
                    md.append(f"- {scope_str}{c['description']} (`{c['commit_hash']}`) - by @{c['author']}")
                md.append("")

        # 3. Other commits
        other_keys = set(grouped.keys()) - set(self.SECTION_MAP.keys())
        if other_keys:
            md.append("## 📦 Other Changes\n")
            for k in sorted(other_keys):
                for c in grouped[k]:
                    md.append(f"- {c['description']} (`{c['commit_hash']}`)")
            md.append("")

        return "\n".join(md)
