#!/usr/bin/env python3
"""
DEPRECATED — replaced by scripts/acquire_proton.py + scripts/acquire.sh.

The previous contents (a Playwright-based downloader that depended on
Proton's web client working in a headless browser) have been removed.
Proton's web client uses WebCrypto inside a Service Worker context that
is unreliable when automated; the new direct-API client is more robust.

Use the new fully-automated pipeline instead:

    make acquire                 # downloads everything from config/acquire.json
    ACQUIRE_OFFLINE=1 make acquire  # verify cached files only

See docs/acquisition.md for the full protocol overview and config
schema.
"""
from __future__ import annotations
import sys

_REPLACEMENT = (
    "scripts/acquire_proton_playwright.py is deprecated.\n"
    "Use `make acquire` (which runs scripts/acquire.sh → scripts/acquire_proton.py) instead.\n"
    "See docs/acquisition.md for setup details."
)

if __name__ == "__main__":
    sys.stderr.write(_REPLACEMENT + "\n")
    sys.exit(2)
