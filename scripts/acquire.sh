#!/usr/bin/env bash
# Acquire source assets from Proton Drive — fully automated.
#
# This wrapper:
#   1. Ensures a Python venv with the acquire-time dependencies exists.
#   2. Validates that an acquire.json config is present.
#   3. Invokes scripts/acquire_proton.py for every share in the config.
#   4. Returns a non-zero exit code if any share failed.
#
# The wrapper is idempotent. Once assets have been successfully fetched
# and their SHA-256 matches the manifest, subsequent runs are no-ops
# (the Python script detects this and short-circuits per-file).
#
# Environment variables
# ---------------------
#   ACQUIRE_CONFIG      Override the path to the acquire.json file.
#   ACQUIRE_OFFLINE=1   Skip all network I/O; only verify cached files.
#   ACQUIRE_VERBOSE=1   Pass -v to the Python script (repeat for -vv).
#   ACQUIRE_RETRIES=N   Override the per-request retry count (default 5).
#
# Exit codes
# ----------
#   0   all shares acquired (or already cached and verified)
#   1   one or more shares failed
#   2   configuration error (missing config, missing dependencies, etc.)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV_DIR="${ACQUIRE_VENV:-$ROOT/.venv}"
PY_REQ="$ROOT/requirements-acquire.txt"
PY_SCRIPT="$ROOT/scripts/acquire_proton.py"

log()  { printf '%b\n' "$*" >&2; }
fail() { log "❌ $*"; exit "${2:-1}"; }

# ---------------------------------------------------------------------------
# 1. Locate Python and venv
# ---------------------------------------------------------------------------

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 is required but not found in PATH"
fi

# Bootstrap a venv if either it doesn't exist or any acquire-time dep is
# missing. We use a lightweight import check rather than re-pip-installing
# every time.
needs_install=0
if [ ! -x "$VENV_DIR/bin/python" ]; then
  needs_install=1
  log "→ Creating Python venv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# If requirements-acquire.txt is newer than a stamp file, reinstall.
STAMP="$VENV_DIR/.acquire-deps.stamp"
if [ ! -f "$STAMP" ] || [ "$PY_REQ" -nt "$STAMP" ]; then
  needs_install=1
fi

if [ "$needs_install" -eq 1 ]; then
  log "→ Installing acquire-time dependencies (this is a one-time cost)"
  "$VENV_DIR/bin/pip" install --quiet --disable-pip-version-check -r "$PY_REQ"
  touch "$STAMP"
fi

PY="$VENV_DIR/bin/python"

# ---------------------------------------------------------------------------
# 2. Validate config presence
# ---------------------------------------------------------------------------

CONFIG_PATH="${ACQUIRE_CONFIG:-$ROOT/config/acquire.json}"
if [ ! -f "$CONFIG_PATH" ]; then
  if [ -f "$ROOT/config/acquire.example.json" ]; then
    log "❌ No acquire config found at $CONFIG_PATH"
    log "   Copy config/acquire.example.json to config/acquire.json and fill in the share tokens + secrets."
    log "   See docs/acquisition.md for details."
  else
    log "❌ No acquire config found at $CONFIG_PATH"
    log "   Set ACQUIRE_CONFIG or create config/acquire.json (see docs/acquisition.md)."
  fi
  exit 2
fi

# ---------------------------------------------------------------------------
# 3. Build CLI flags
# ---------------------------------------------------------------------------

FLAGS=(--config "$CONFIG_PATH")

if [ "${ACQUIRE_OFFLINE:-0}" = "1" ]; then
  FLAGS+=(--offline)
fi

if [ -n "${ACQUIRE_VERBOSE:-}" ]; then
  # shellcheck disable=SC2206
  VERB_LEVEL=$(( ACQUIRE_VERBOSE > 2 ? 2 : ACQUIRE_VERBOSE ))
  for _ in $(seq 1 "$VERB_LEVEL"); do
    FLAGS+=(-v)
  done
fi

if [ -n "${ACQUIRE_RETRIES:-}" ]; then
  FLAGS+=(--retries "$ACQUIRE_RETRIES")
fi

# ---------------------------------------------------------------------------
# 4. Run
# ---------------------------------------------------------------------------

log "📥 Acquiring source assets from Proton Drive"
log "   config: $CONFIG_PATH"

set +e
"$PY" "$PY_SCRIPT" "${FLAGS[@]}"
rc=$?
set -e

case "$rc" in
  0) log "✅ Acquire complete" ;;
  1) log "⚠️  Acquire finished with errors (see summary above)" ;;
  *) log "❌ Acquire failed (exit $rc)" ;;
esac

exit "$rc"
