@echo off
title Run Docstool Unit Tests
echo ========================================================
echo Running Docstool Unit Test Suite (pytest)
echo ========================================================

cd /d "%~dp0"

python -m pytest tests -v

echo.
pause
