#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Kilo Workspace — setup"

# Python venv
if [ ! -d ".venv" ]; then
  echo "  → Creating Python virtual environment"
  python3 -m venv .venv
fi

# Install Python dev deps if requirements exist
if [ -f "requirements-dev.txt" ]; then
  echo "  → Installing Python dev dependencies"
  .venv/bin/pip install -r requirements-dev.txt -q
fi

# Node deps if package.json exists
if [ -f "package.json" ]; then
  echo "  → Installing Node dependencies"
  npm install --no-audit --no-fund -s 2>/dev/null || true
fi

# Make all scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

echo "✅ Setup complete"
