#!/usr/bin/env python3
"""
DEPRECATED — replaced by scripts/acquire_proton.py + scripts/acquire.sh.

The previous contents (an incomplete, hand-rolled SRP-6a client that
hard-coded share tokens and lacked OpenPGP block decryption) have been
removed because they were both insecure and non-functional.

Use the new fully-automated pipeline instead:

    make acquire                 # downloads everything from config/acquire.json
    ACQUIRE_OFFLINE=1 make acquire  # verify cached files only

See docs/acquisition.md for the full protocol overview and config
schema.
"""
from __future__ import annotations
import sys

_REPLACEMENT = (
    "scripts/acquire_proton_direct.py is deprecated.\n"
    "Use `make acquire` (which runs scripts/acquire.sh → scripts/acquire_proton.py) instead.\n"
    "See docs/acquisition.md for setup details."
)

if __name__ == "__main__":
    sys.stderr.write(_REPLACEMENT + "\n")
    sys.exit(2)
