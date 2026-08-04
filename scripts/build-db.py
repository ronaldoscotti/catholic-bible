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

from catholic_bible.storage.bootstrap import main as build_where_it_belongs
from catholic_bible.storage.bootstrap import materialise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=None)
    args = parser.parse_args()

    if args.dest is None:
        return build_where_it_belongs()

    dest = Path(args.dest).resolve()
    materialise(dest)
    with closing(sqlite3.connect(f"file:{dest}?mode=ro", uri=True)) as check:
        verses = check.execute("SELECT COUNT(*) FROM texts").fetchone()[0]
        addresses = check.execute("SELECT COUNT(*) FROM spine").fetchone()[0]
    print(f"built {dest} with {verses} verses over {addresses} spine addresses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
