"""
Format Converter Module.
Converts Markdown documents into HTML, structured JSON AST, or plain search text.
"""

import re
import json
from pathlib import Path
from typing import Dict, Any


class FormatConverter:
    """Handles multi-format conversion of Markdown documentation."""

    @staticmethod
    def strip_frontmatter(content: str) -> str:
        """Removes YAML frontmatter from document content."""
        return re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)

    @staticmethod
    def to_plain_text(content: str) -> str:
        """Strips Markdown syntax, returning clean readable plain text."""
        text = FormatConverter.strip_frontmatter(content)
        # Remove code blocks
        text = re.sub(r"```[^\n]*\n(.*?)```", r"\1", text, flags=re.DOTALL)
        # Remove inline code ticks
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove images ![alt](url)
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
        # Convert links [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Remove headings markers (#, ##, etc.)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Remove bold and italic markers
        text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
        # Remove blockquotes
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Collapse multiple empty lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def to_json_ast(file_path: Path, content: str) -> Dict[str, Any]:
        """Converts Markdown content into a structured JSON representation."""
        from .metadata_checker import MetadataChecker
        checker = MetadataChecker()
        meta, body, _ = checker.parse_file(file_path)

        sections = []
        current_section = {"heading": "Introduction", "level": 1, "paragraphs": [], "code_blocks": []}

        lines = body.splitlines()
        in_code = False
        code_lang = ""
        current_code = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code:
                    current_section["code_blocks"].append({
                        "language": code_lang,
                        "code": "\n".join(current_code)
                    })
                    in_code = False
                    code_lang = ""
                    current_code = []
                else:
                    in_code = True
                    code_lang = stripped.lstrip("`").strip()
                continue

            if in_code:
                current_code.append(line)
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if heading_match:
                if current_section["paragraphs"] or current_section["code_blocks"]:
                    sections.append(current_section)
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                current_section = {"heading": title, "level": level, "paragraphs": [], "code_blocks": []}
            elif stripped:
                current_section["paragraphs"].append(stripped)

        if current_section["paragraphs"] or current_section["code_blocks"]:
            sections.append(current_section)

        return {
            "source_file": str(file_path),
            "metadata": meta or {},
            "sections": sections
        }

    @staticmethod
    def to_html(content: str, title: str = "Documentation") -> str:
        """Converts Markdown to semantic HTML page with clean styling."""
        body = FormatConverter.strip_frontmatter(content)

        # Convert headers
        body = re.sub(r"^### (.*)$", r"<h3>\1</h3>", body, flags=re.M)
        body = re.sub(r"^## (.*)$", r"<h2>\1</h2>", body, flags=re.M)
        body = re.sub(r"^# (.*)$", r"<h1>\1</h1>", body, flags=re.M)

        # Convert bold & italic
        body = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", body)
        body = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", body)

        # Convert inline code
        body = re.sub(r"`([^`]+)`", r"<code>\1</code>", body)

        # Convert links
        body = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', body)

        # Convert code blocks
        body = re.sub(r"```[^\n]*\n(.*?)```", r"<pre><code>\1</code></pre>", body, flags=re.DOTALL)

        # Convert paragraphs (lines separated by blank lines)
        paragraphs = body.split("\n\n")
        html_paragraphs = []
        for p in paragraphs:
            p_strip = p.strip()
            if p_strip.startswith("<h") or p_strip.startswith("<pre"):
                html_paragraphs.append(p_strip)
            elif p_strip:
                html_paragraphs.append(f"<p>{p_strip}</p>")

        html_body = "\n".join(html_paragraphs)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #24292e; max-width: 860px; margin: 40px auto; padding: 0 20px; }}
        h1, h2, h3 {{ color: #1b1f23; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }}
        code {{ background: #f6f8fa; padding: .2em .4em; border-radius: 3px; font-family: monospace; font-size: 85%; }}
        pre {{ background: #f6f8fa; padding: 16px; border-radius: 6px; overflow: auto; }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
