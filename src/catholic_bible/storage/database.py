"""Opening the read database, and deciding where it is.

One read only connection per request. `sqlite3` connections are not thread safe
and uvicorn runs sync handlers in a threadpool, so a module level one passes
every serial test and fails under load. A pool is not earned yet.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

from catholic_bible import __version__
from catholic_bible.canon import DATA_DIR

OVERRIDE = "CATHOLIC_BIBLE_DB"

# Where a checkout and the Docker image put it, both of which build it ahead of
# time. Derived, so it is gitignored, so it is not in the wheel.
DB_PATH = DATA_DIR / "derived" / "bible.db"


def cache_root() -> Path:
    """The platform's cache directory, without a dependency to find it."""
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches"
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")


def resolve() -> Path:
    """Where the database is, or where an installed copy should build it.

    The version is in the cache path on purpose. Nothing readable from inside a
    a database says when it was filled, so a path reused across upgrades hands
    a stale one to every reader who runs `pip install -U` and says nothing.
    """
    override = os.environ.get(OVERRIDE)
    if override:
        return Path(override)
    if DB_PATH.is_file():
        return DB_PATH
    return cache_root() / "the-catholic-bible" / __version__ / "bible.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    """A read only connection, with rows addressable by column name."""
    target = resolve() if path is None else path
    if not target.is_file():
        raise FileNotFoundError(
            f"no database at {target}. run `catholic-bible-build-db` to build it"
        )

    connection = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection
