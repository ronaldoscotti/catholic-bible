"""Making the read database exist, wherever it is supposed to be.

Inside a checkout and inside the Docker image the build step puts it beside the
code, so `ensure` finds it and does nothing. Installed from a registry it cannot
be there, because it is derived and carries no checksum, and every published
file here carries one.

Ten seconds cold on the machine this was written on, from bytes the reader
already downloaded when they installed the package. A warm rebuild inside a
checkout is half that, which is why the message below promises no number.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path

from catholic_bible.storage.build import build
from catholic_bible.storage.database import resolve


def scratch_for(dest: Path) -> Path:
    """The half written file, named per process so two cannot collide."""
    return dest.with_suffix(f".{os.getpid()}.building")


def materialise(dest: Path) -> None:
    """Build into `dest`, atomically.

    Written beside the target and moved into place. A crash partway through
    otherwise leaves a file that reads as a database, which the next boot finds
    and trusts, and a corpus with holes in it beats no corpus only in the sense
    that it starts.

    The scratch name carries the process id. Two processes bootstrapping the
    same target, which is what `--workers` does, would otherwise delete each
    other's half written file and both move the result into place.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    scratch = scratch_for(dest)
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

    # Flushed, or block buffering holds it until after the build it announces.
    # On a terminal stdout is line buffered and this is invisible. Redirected
    # into a log, which is where a service actually runs, the line arrived
    # after uvicorn had already reported itself up.
    print(
        f"building the read database at {target}, once, this takes a moment",
        flush=True,
    )
    materialise(target)
    return target


def main() -> int:
    """`catholic-bible-build-db`, for an image that wants it in a layer.

    Set `CATHOLIC_BIBLE_DB` to the path the image will read from. Without it
    this writes where an installed copy would look, which is a per-user cache
    and belongs to whoever ran the command.
    """
    target = resolve()
    materialise(target)
    with closing(sqlite3.connect(f"file:{target}?mode=ro", uri=True)) as check:
        verses = check.execute("SELECT COUNT(*) FROM texts").fetchone()[0]
        addresses = check.execute("SELECT COUNT(*) FROM spine").fetchone()[0]
    print(f"built {target} with {verses} verses over {addresses} spine addresses")
    return 0
