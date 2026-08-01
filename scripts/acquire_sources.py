#!/usr/bin/env python3
"""
DEPRECATED — replaced by scripts/acquire_proton.py + scripts/acquire.sh.

This file is kept only as a placeholder so that legacy `python3
scripts/acquire_sources.py` invocations fail loudly with a clear
message rather than running the old, broken, and insecure code that
used to live here (hard-coded tokens, an incorrect SRP-6a flow, and
no OpenPGP unwrapping).

Use the new fully-automated pipeline instead:

    make acquire                 # downloads everything from config/acquire.json
    ACQUIRE_OFFLINE=1 make acquire  # verify cached files only

See docs/acquisition.md for the full protocol overview and config
schema.
"""
from __future__ import annotations
import sys

_REPLACEMENT = (
    "scripts/acquire_sources.py is deprecated.\n"
    "Use `make acquire` (which runs scripts/acquire.sh → scripts/acquire_proton.py) instead.\n"
    "See docs/acquisition.md for setup details."
)

if __name__ == "__main__":
    sys.stderr.write(_REPLACEMENT + "\n")
    sys.exit(2)
