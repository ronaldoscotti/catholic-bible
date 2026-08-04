"""Making the read database exist, wherever it is supposed to be.

Inside a checkout and inside the Docker image it already does, so nothing here
runs. Installed from a registry the file cannot ship, because it is derived and
carries no checksum, and every published file here carries one.

Ten seconds cold on the machine this was written on, from bytes the reader
already downloaded when they installed the package. A warm rebuild inside a
checkout is half that, which is why the message below promises no number.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from catholic_bible.storage.build import build
from catholic_bible.storage.database import resolve


def materialise(dest: Path) -> None:
    """Build into `dest`, atomically.

    Written beside the target and moved into place. A crash partway through
    otherwise leaves a file that reads as a database, which the next boot finds
    and trusts, and a corpus with holes in it beats no corpus only in the sense
    that it starts.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    scratch = dest.with_suffix(".building")
    scratch.unlink(missing_ok=True)

    connection = sqlite3.connect(scratch)
    try:
        build(connection)
    except BaseException:
        connection.close()
        scratch.unlink(missing_ok=True)
        raise
    connection.close()
    scratch.replace(dest)


def ensure() -> Path:
    """The database, built first if it is not there. Silent when it is."""
    target = resolve()
    if target.is_file():
        return target

    print(f"building the read database at {target}, once, this takes a moment")
    materialise(target)
    return target


def main() -> int:
    """`catholic-bible-build-db`, for an image that wants it in a layer."""
    target = resolve()
    materialise(target)
    # `closing`, because sqlite3's own context manager commits and does not
    # close, so the plain `with` leaks the handle.
    with closing(sqlite3.connect(f"file:{target}?mode=ro", uri=True)) as check:
        verses = check.execute("SELECT COUNT(*) FROM texts").fetchone()[0]
        addresses = check.execute("SELECT COUNT(*) FROM spine").fetchone()[0]
    print(f"built {target} with {verses} verses over {addresses} spine addresses")
    return 0
