"""
Docstool Command Line Interface (CLI).
Engineered in Python and SQL to lint, validate, convert, and generate technical documentation.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .db import AuditDatabase
from .rules import DEFAULT_STYLE_RULES
from .linter import StyleLinter
from .link_checker import LinkChecker
from .metadata_checker import MetadataChecker
from .converter import FormatConverter
from .release_notes import ReleaseNotesAssembler

# Try to use rich for colored tables, fall back gracefully if not available
try:
    from rich.console import Console
    from rich.table import Table
    console = Console(highlight=False)
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def print_banner():
    if HAS_RICH:
        console.print("[bold blue]Docstool[/bold blue] - Technical Docs Linter & SQL Audit Engine", style="bold")
    else:
        print("Docstool - Technical Docs Linter & SQL Audit Engine")


def print_violations_table(violations: List[Dict[str, Any]]):
    if not violations:
        if HAS_RICH:
            console.print("[bold green][OK] Zero issues detected! Documentation is in perfect shape.[/bold green]")
        else:
            print("[OK] Zero issues detected! Documentation is in perfect shape.")
        return

    if HAS_RICH:
        table = Table(title="Documentation Audit Violations")
        table.add_column("Severity", style="bold")
        table.add_column("File", style="cyan")
        table.add_column("Line", justify="right")
        table.add_column("Rule ID", style="magenta")
        table.add_column("Message")
        table.add_column("Suggestion", style="green")

        for v in violations:
            sev = v["severity"]
            sev_color = "red" if sev == "ERROR" else "yellow" if sev == "WARNING" else "blue"
            table.add_row(
                f"[{sev_color}]{sev}[/{sev_color}]",
                str(Path(v["file_path"]).name),
                str(v["line_number"]),
                v["rule_id"],
                v["message"],
                v.get("suggested_replacement", "")
            )
        console.print(table)
    else:
        print(f"\nFound {len(violations)} issue(s):")
        for v in violations:
            print(f"[{v['severity']}] {v['file_path']}:{v['line_number']} | {v['rule_id']} | {v['message']}")


def handle_lint(args) -> int:
    target_dir = Path(args.path)
    if not target_dir.exists():
        print(f"Error: Path '{target_dir}' does not exist.", file=sys.stderr)
        return 1

    db = AuditDatabase(args.db)
    db.populate_default_rules(DEFAULT_STYLE_RULES)

    print(f"Scanning Markdown files in: {target_dir.resolve()} ...")
    md_files = list(target_dir.rglob("*.md"))
    print(f"Found {len(md_files)} Markdown document(s).")

    all_violations: List[Dict[str, Any]] = []

    # 1. Metadata Check
    meta_checker = MetadataChecker()
    metadata_list, meta_violations = meta_checker.check_directory(target_dir)
    all_violations.extend(meta_violations)

    for meta in metadata_list:
        db.upsert_document_metadata(meta)

    # 2. Style & Terminology Check
    style_linter = StyleLinter(DEFAULT_STYLE_RULES)
    style_violations = style_linter.lint_directory(target_dir)
    all_violations.extend(style_violations)

    # 3. Link & Anchor Check
    link_checker = LinkChecker(target_dir)
    link_violations = link_checker.check_directory(target_dir)
    all_violations.extend(link_violations)

    # Record into SQL Database
    run_id = db.record_audit_run(str(target_dir), len(md_files), all_violations)

    print_violations_table(all_violations)

    error_count = sum(1 for v in all_violations if v["severity"] == "ERROR")
    warning_count = sum(1 for v in all_violations if v["severity"] == "WARNING")

    print(f"\nAudit Run #{run_id} complete. Saved to SQLite database '{args.db}'.")
    print(f"Summary: {error_count} Error(s), {warning_count} Warning(s) across {len(md_files)} file(s).")

    db.close()
    return 1 if (error_count > 0 and args.strict) else 0


def handle_sql_report(args) -> int:
    """Executes SQL analytical queries against docs_audit.db and displays reports."""
    db = AuditDatabase(args.db)

    print(f"\n=======================================================")
    print(f" SQL ANALYTICAL AUDIT REPORT (from {args.db})")
    print(f"=======================================================\n")

    # 1. Top Violating Files Query
    top_violators = db.query_top_violating_files(limit=5)
    if HAS_RICH:
        t1 = Table(title="Top 5 Files with Linting Issues (SQL Aggregation)")
        t1.add_column("File Path", style="cyan")
        t1.add_column("Total Issues", justify="right")
        t1.add_column("Errors", justify="right", style="red")
        t1.add_column("Warnings", justify="right", style="yellow")
        for row in top_violators:
            t1.add_row(Path(row["file_path"]).name, str(row["issue_count"]), str(row["error_count"]), str(row["warning_count"]))
        console.print(t1)
    else:
        print("--- Top 5 Files with Issues ---")
        for row in top_violators:
            print(f"{row['file_path']}: {row['issue_count']} issues ({row['error_count']} errors, {row['warning_count']} warnings)")

    # 2. Issues by Category Query
    categories = db.query_violations_by_category()
    print()
    if HAS_RICH:
        t2 = Table(title="Violations Grouped by Category (SQL JOIN & GROUP BY)")
        t2.add_column("Category", style="magenta")
        t2.add_column("Total Count", justify="right")
        t2.add_column("Errors", justify="right", style="red")
        for row in categories:
            t2.add_row(row["category"], str(row["total_count"]), str(row["errors"]))
        console.print(t2)
    else:
        print("--- Violations by Category ---")
        for row in categories:
            print(f"Category: {row['category']} - Count: {row['total_count']}")

    # 3. Content Inventory Query
    inventory = db.query_content_inventory()
    print()
    if HAS_RICH:
        t3 = Table(title="Document Content Inventory (SQL Query)")
        t3.add_column("Document Title", style="bold")
        t3.add_column("Word Count", justify="right")
        t3.add_column("Est. Read Time", justify="right")
        t3.add_column("Valid Frontmatter", justify="center")
        for row in inventory:
            t3.add_row(
                row["title"] or Path(row["file_path"]).name,
                f"{row['word_count']:,} words",
                f"{row['reading_time_min']} min",
                "[green]YES[/green]" if row["has_valid_frontmatter"] else "[red]NO[/red]"
            )
        console.print(t3)
    else:
        print("--- Content Inventory ---")
        for row in inventory:
            print(f"{row['title']}: {row['word_count']} words (~{row['reading_time_min']} min)")

    db.close()
    return 0


def handle_convert(args) -> int:
    src_file = Path(args.file)
    if not src_file.exists():
        print(f"Error: File '{src_file}' not found.", file=sys.stderr)
        return 1

    with open(src_file, "r", encoding="utf-8") as f:
        content = f.read()

    fmt = args.to.lower()
    if fmt == "html":
        output = FormatConverter.to_html(content, title=src_file.stem)
    elif fmt == "json":
        ast = FormatConverter.to_json_ast(src_file, content)
        import json
        output = json.dumps(ast, indent=2)
    elif fmt == "text":
        output = FormatConverter.to_plain_text(content)
    else:
        print(f"Error: Unknown format '{fmt}'. Choose from html, json, text.", file=sys.stderr)
        return 1

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Converted '{src_file}' -> '{out_path}' ({fmt.upper()}).")
    else:
        print(output)

    return 0


def handle_release_notes(args) -> int:
    assembler = ReleaseNotesAssembler(args.repo)
    db = AuditDatabase(args.db)

    print(f"Extracting Git commits from: {Path(args.repo).resolve()} ...")
    raw_commits = assembler.get_git_commits(args.commit_range)

    if not raw_commits:
        print("No Git commits found in specified range.", file=sys.stderr)
        return 1

    parsed_commits = []
    for c in raw_commits:
        parsed = assembler.parse_commit(c)
        parsed_commits.append(parsed)
        db.record_commit(parsed)

    md = assembler.generate_markdown(args.version, parsed_commits, args.title)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Generated release notes saved to: '{out_path}'.")
    else:
        print(md)

    db.close()
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="docstool",
        description="Technical Documentation Linter, Automation CLI & SQL Audit Engine."
    )
    parser.add_argument("--db", default="docs_audit.db", help="Path to SQLite audit database (default: docs_audit.db)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. lint
    p_lint = subparsers.add_parser("lint", help="Run full audit (style, broken links, metadata)")
    p_lint.add_argument("path", default=".", nargs="?", help="Directory or file to lint")
    p_lint.add_argument("--strict", action="store_true", help="Exit with code 1 if any ERROR is found")

    # 2. sql-report
    p_report = subparsers.add_parser("sql-report", help="Run SQL analytics and display documentation audit report")

    # 3. convert
    p_convert = subparsers.add_parser("convert", help="Convert Markdown file to HTML, JSON AST, or plain text")
    p_convert.add_argument("file", help="Path to source Markdown file")
    p_convert.add_argument("--to", choices=["html", "json", "text"], required=True, help="Target format")
    p_convert.add_argument("-o", "--output", help="Output file path (prints to stdout if omitted)")

    # 4. release-notes
    p_rel = subparsers.add_parser("release-notes", help="Assemble release notes from Git commits")
    p_rel.add_argument("--repo", default=".", help="Path to git repository")
    p_rel.add_argument("--range", dest="commit_range", help="Git commit range (e.g. HEAD~5..HEAD or v1.0..v2.0)")
    p_rel.add_argument("--version", default="v1.0.0", help="Release version tag")
    p_rel.add_argument("--title", help="Custom release notes title")
    p_rel.add_argument("-o", "--output", help="Output Markdown file path")

    args = parser.parse_args()

    if args.command == "lint":
        sys.exit(handle_lint(args))
    elif args.command == "sql-report":
        sys.exit(handle_sql_report(args))
    elif args.command == "convert":
        sys.exit(handle_convert(args))
    elif args.command == "release-notes":
        sys.exit(handle_release_notes(args))


if __name__ == "__main__":
    main()
