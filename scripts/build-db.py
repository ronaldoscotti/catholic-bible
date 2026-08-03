#!/usr/bin/env python3
"""Builds the read database from the published files.

Derived and never authored. The inputs are committed and CI verifies their
checksums, so this file carries no checksum of its own and is not committed.

Usage:
    scripts/build-db.py [--dest path/to/bible.db]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from catholic_bible.storage.build import build
from catholic_bible.storage.database import DB_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=None)
    args = parser.parse_args()

    dest = Path(args.dest).resolve() if args.dest else DB_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Built beside the target and moved into place, so an interrupted run leaves
    # the previous database readable rather than a half written one.
    scratch = dest.with_suffix(".building")
    scratch.unlink(missing_ok=True)

    connection = sqlite3.connect(scratch)
    try:
        build(connection)
    finally:
        connection.close()
    scratch.replace(dest)

    with sqlite3.connect(f"file:{dest}?mode=ro", uri=True) as check:
        verses = check.execute("SELECT COUNT(*) FROM texts").fetchone()[0]
        addresses = check.execute("SELECT COUNT(*) FROM spine").fetchone()[0]
    print(f"built {dest} with {verses} verses over {addresses} spine addresses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
