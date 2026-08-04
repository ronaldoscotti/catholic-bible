"""Counting requests per bucket per window.

Knows nothing about HTTP. A bucket is whatever the caller says identifies a
client and a window is a number of seconds, so all the arithmetic here is
testable without a request.

This is a file rather than a dictionary because a dictionary is per process. Two
uvicorn workers with in memory counters enforce twice the configured limit, and
a limit that multiplies by the worker count is a limit nobody can reason about.

Separate from the corpus database on purpose. That one is opened read only and
nothing writes to it, which is a claim `CLAUDE.md` makes about this whole
repository and which stays literally true.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# The window is a column rather than part of the bucket string. It used to be
# glued into the key, which left housekeeping unable to tell a minute row from
# an hourly one, so pruning the minute deleted every hourly bucket on the box.
SCHEMA = """
CREATE TABLE IF NOT EXISTS hits (
  bucket       TEXT    NOT NULL,
  window       INTEGER NOT NULL,
  window_start INTEGER NOT NULL,
  count        INTEGER NOT NULL,
  PRIMARY KEY (bucket, window, window_start)
) WITHOUT ROWID
"""

COUNT = """
INSERT INTO hits (bucket, window, window_start, count) VALUES (?, ?, ?, 1)
ON CONFLICT (bucket, window, window_start) DO UPDATE SET count = count + 1
RETURNING count
"""

# Scoped to one window. One window of grace beyond that, because the window
# before this one is what a `Retry-After` handed out a moment ago still refers
# to, so it is dropped only once it is two old.
PRUNE = "DELETE FROM hits WHERE window = ? AND window_start < ?"


class Counter:
    """A shared tally of hits per bucket per window.

    Opening one is the point at which an unusable store fails. The middleware
    above decides whether that is fatal, and it can only decide if this is loud.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._connection = sqlite3.connect(path, isolation_level=None)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.execute("PRAGMA busy_timeout=2000")
        self._connection.execute(SCHEMA)

    @staticmethod
    def _start(window: int, now: int) -> int:
        return now - now % window

    def hit(self, bucket: str, window: int, now: int) -> int:
        """Record one request and return how many are in this window so far."""
        row = self._connection.execute(
            COUNT, (bucket, window, self._start(window, now))
        ).fetchone()
        return int(row[0])

    def reset_in(self, window: int, now: int) -> int:
        """Seconds until the current window ends."""
        return self._start(window, now) + window - now

    def prune(self, window: int, now: int) -> None:
        """Drop dead rows of this window only.

        Deleting across windows is what made the hourly limit unenforceable.
        """
        self._connection.execute(PRUNE, (window, self._start(window, now) - window))

    def rows(self) -> int:
        row = self._connection.execute("SELECT count(*) FROM hits").fetchone()
        return int(row[0])

    def close(self) -> None:
        self._connection.close()
