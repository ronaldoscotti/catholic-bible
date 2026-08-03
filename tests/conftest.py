"""The database the suite reads.

Built once per machine into the path the application uses, and reused while it
is newer than everything it was built from. Building the full corpus on every
red green cycle costs seconds that nobody would pay twice.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from catholic_bible import storage
from catholic_bible.canon import DATA_DIR
from catholic_bible.storage.build import build
from catholic_bible.storage.database import DB_PATH, connect

INPUTS = (
    DATA_DIR / "canon.json",
    DATA_DIR / "versification.json",
    DATA_DIR / "corpus",
    Path(storage.__file__).parent / "build.py",
)


def _is_stale(target: Path) -> bool:
    if not target.is_file():
        return True

    built = target.stat().st_mtime
    for source in INPUTS:
        newest = max(
            (path.stat().st_mtime for path in source.rglob("*") if path.is_file()),
            default=source.stat().st_mtime,
        )
        if newest > built:
            return True
    return False


@pytest.fixture(scope="session")
def database_path() -> Path:
    if _is_stale(DB_PATH):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        scratch = DB_PATH.with_suffix(".building")
        scratch.unlink(missing_ok=True)
        connection = sqlite3.connect(scratch)
        try:
            build(connection)
        finally:
            connection.close()
        scratch.replace(DB_PATH)
    return DB_PATH


@pytest.fixture(scope="session")
def database(database_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)
    yield connection
    connection.close()
