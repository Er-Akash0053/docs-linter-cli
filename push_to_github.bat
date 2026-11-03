@echo off
title Push Docstool to GitHub
echo ========================================================
echo Pushing Docstool (Python + SQL) to GitHub
echo Repository: https://github.com/Er-Akash0053/docs-linter-cli
echo ========================================================

cd /d "%~dp0"

echo.
echo [1/3] Adding files to git staging...
git add .

echo.
echo [2/3] Committing changes...
git commit -m "feat: complete Python & SQL docs linter, automation CLI, and test suite" 2>nul
if %ERRORLEVEL% equ 0 (
    echo Changes committed successfully.
) else (
    echo Working tree is already up to date.
)

echo.
echo [3/3] Pushing to GitHub (main branch)...
git branch -M main

:: Check if origin exists, if not add it
git remote get-url origin >nul 2>&1
if %ERRORLEVEL% neq 0 (
    git remote add origin https://github.com/Er-Akash0053/docs-linter-cli.git
)

git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo [SUCCESS] Project 2 pushed successfully to GitHub!
    echo Visit: https://github.com/Er-Akash0053/docs-linter-cli
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo [NOTICE] Push encountered an issue.
    echo If you haven't created the repository on GitHub yet:
    echo 1. Go to https://github.com/new
    echo 2. Repository name: docs-linter-cli
    echo 3. Keep it Public (leave "Add README" UNCHECKED)
    echo 4. Click "Create repository"
    echo 5. Re-run this push_to_github.bat script!
    echo ========================================================
)

pause
