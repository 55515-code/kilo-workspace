#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Running tests..."

# Python tests
if [ -f ".venv/bin/pytest" ]; then
  echo "  → pytest"
  .venv/bin/pytest -v --tb=short
fi

# Node tests
if [ -f "package.json" ] && grep -q '"test"' package.json 2>/dev/null; then
  echo "  → npm test"
  npm test
fi

echo "✅ Tests complete"
