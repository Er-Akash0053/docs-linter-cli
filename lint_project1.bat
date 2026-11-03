@echo off
title Lint Project 1 Docs & Run SQL Report
echo ========================================================
echo Auditing Project 1 Documentation with Docstool (Python + SQL)
echo Target: D:\technical-writing-portfolio\project-1-docs-site\docs
echo ========================================================

cd /d "%~dp0"

echo.
echo [Step 1] Running Linter, Link Checker, and Metadata Validator...
python -m docstool.cli lint D:\technical-writing-portfolio\project-1-docs-site\docs

echo.
echo [Step 2] Executing SQL Analytical Queries on docs_audit.db...
python -m docstool.cli sql-report

echo.
pause
