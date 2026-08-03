#!/usr/bin/env python3
"""Writes the published OpenAPI document.

Generated, never authored. CI regenerates it and fails when the committed copy
differs, which catches a route that changed without the document following.

Usage:
    scripts/build-openapi.py [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from catholic_bible.api.document import rendered

DEST = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    document = rendered()
    if not args.check:
        DEST.write_text(document, encoding="utf-8")
        print(f"wrote {DEST}")
        return 0

    if not DEST.is_file():
        print(f"{DEST} is missing. run `make openapi`")
        return 1
    if DEST.read_text(encoding="utf-8") != document:
        print(f"{DEST} does not match the routes. run `make openapi`")
        return 1
    print("the committed document matches the routes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
