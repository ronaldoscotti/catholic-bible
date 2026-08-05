#!/usr/bin/env python3
"""Builds the read database from the published files.

Derived and never authored. The inputs are committed and CI verifies their
checksums, so this file carries no checksum of its own and is not committed.

The work lives in `catholic_bible.storage.bootstrap`, which is also what the
installed `catholic-bible-build-db` runs and what the API calls on a first
boot. Three callers, one implementation.

Usage:
    scripts/build-db.py [--dest path/to/bible.db]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from catholic_bible.storage.bootstrap import materialise
from catholic_bible.storage.database import DB_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=None)
    args = parser.parse_args()

    # The packaged path, always, and never whatever `resolve()` would pick.
    # This script only exists inside a checkout, and `resolve()` answers where
    # to *read* from, which falls through to a per-user cache when the file is
    # not there yet. That is exactly the state a clean checkout and the Docker
    # builder are in, so routing this through it sent `make db` and the image
    # build into `~/.cache` and left the checkout with no database at all.
    dest = Path(args.dest).resolve() if args.dest else DB_PATH
    materialise(dest)
    with closing(sqlite3.connect(f"file:{dest}?mode=ro", uri=True)) as check:
        verses = check.execute("SELECT COUNT(*) FROM texts").fetchone()[0]
        addresses = check.execute("SELECT COUNT(*) FROM spine").fetchone()[0]
    print(f"built {dest} with {verses} verses over {addresses} spine addresses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
