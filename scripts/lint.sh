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

# Standalone Python syntax check (no venv required).
if command -v python3 &>/dev/null; then
  echo "  → Python syntax check (scripts/, tests/)"
  for f in scripts/*.py tests/smoke/test_acquire_proton.py; do
    [ -f "$f" ] || continue
    python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])" "$f" \
      || { echo "  ❌ Syntax error in $f"; ERRORS=$((ERRORS + 1)); }
  done
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
