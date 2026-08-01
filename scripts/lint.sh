#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running linters..."

ERRORS=0

# Shellcheck
if command -v shellcheck &>/dev/null; then
  echo "  → ShellCheck"
  shellcheck scripts/*.sh || ERRORS=$((ERRORS + 1))
fi

# Python (if venv exists)
if [ -f ".venv/bin/ruff" ]; then
  echo "  → Ruff (Python)"
  .venv/bin/ruff check . || ERRORS=$((ERRORS + 1))
fi

# ESLint (if available)
if command -v npx &>/dev/null && [ -f "node_modules/.bin/eslint" ]; then
  echo "  → ESLint"
  npx eslint . --quiet || ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -gt 0 ]; then
  echo "❌ Linting found issues ($ERRORS tools reported errors)"
  exit 1
fi

echo "✅ All linters passed"
