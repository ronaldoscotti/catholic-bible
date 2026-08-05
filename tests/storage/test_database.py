"""Opening the database, and the ways it refuses to be written to."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

import pytest

from catholic_bible.storage.database import connect


def test_it_refuses_a_write(database_path: Path) -> None:
    """Read only is the driver's job and not a convention the routes keep.

    Criterion 8 says no endpoint writes. A route added in a hurry keeps a
    convention until it does not, so the connection itself refuses.
    """
    with closing(connect(database_path)) as connection:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("DELETE FROM texts")


def test_it_says_which_file_is_missing(tmp_path: Path) -> None:
    """And names something the reader can actually run.

    It used to say `make db`, which is a Makefile target inside a checkout. A
    reader who installed from a registry has no Makefile, so the one
    instruction the failure offered was unreachable from where they stood.
    """
    with pytest.raises(FileNotFoundError, match="catholic-bible-build-db"):
        connect(tmp_path / "absent.db")


def test_rows_are_addressable_by_column_name(database_path: Path) -> None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            "SELECT id, book FROM spine WHERE id = 'JHN.3.16'"
        ).fetchone()
    assert row["book"] == "JHN"


def test_it_survives_being_read_from_several_threads(database_path: Path) -> None:
    """One connection per request, and uvicorn runs sync handlers in a pool.

    A module level connection passes every serial test and fails here, which is
    the whole reason this test exists rather than a note in the plan.
    """

    def read(verse: str) -> str | None:
        # closing, not the connection's own context manager, which manages a
        # transaction and leaves the handle open.
        with closing(connect(database_path)) as connection:
            row = connection.execute(
                "SELECT text FROM texts JOIN spine USING (canonical_order) "
                "WHERE spine.id = ? AND texts.version = 'vulgata-clementina'",
                (verse,),
            ).fetchone()
            return None if row is None else str(row["text"])

    verses = ["JHN.3.16", "GEN.1.1", "PSA.50.3", "SIR.24.1"] * 8
    with ThreadPoolExecutor(max_workers=8) as pool:
        found = list(pool.map(read, verses))

    assert all(text for text in found)
    assert len(set(found)) == 4
