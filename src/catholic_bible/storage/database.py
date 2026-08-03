"""Opening the read database.

One read only connection per request. `sqlite3` connections are not thread safe
and uvicorn runs sync handlers in a threadpool, so a module level one passes
every serial test and fails under load. A pool is not earned yet.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from catholic_bible.canon import DATA_DIR

DB_PATH = DATA_DIR / "derived" / "bible.db"


def connect(path: Path | None = None) -> sqlite3.Connection:
    """A read only connection, with rows addressable by column name."""
    target = DB_PATH if path is None else path
    if not target.is_file():
        raise FileNotFoundError(f"no database at {target}. run `make db` to build it")

    connection = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection
