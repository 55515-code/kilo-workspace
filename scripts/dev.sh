#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting development environment..."

# Use docker compose if available, otherwise run locally
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
  echo "  → Using Docker Compose"
  docker compose up -d app
  echo "  → Dev container running. Attach with: docker compose exec app bash"
else
  echo "  → Running setup locally"
  bash scripts/setup.sh
  echo "  → Ready for local development"
fi
