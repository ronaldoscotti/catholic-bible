"""The built database against the files it was built from.

Counts are asserted against the published documents rather than against a
constant typed here, so a truncated build fails instead of agreeing with a
number somebody updated by hand.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing

import pytest

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.books import CANON
from catholic_bible.canon.spine import SPINE
from catholic_bible.corpus import VERSIONS, Verse, load
from catholic_bible.storage.build import DEFAULT_VERSION, SCHEMA, build_texts


@pytest.fixture
def blank() -> Iterator[sqlite3.Connection]:
    """An empty database on the real schema, for what does not need the corpus."""
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.executescript(SCHEMA)
        yield connection


def test_the_canon_is_whole(database: sqlite3.Connection) -> None:
    assert database.execute("SELECT COUNT(*) AS n FROM books").fetchone()["n"] == 73
    assert len(CANON) == 73


def test_the_spine_is_whole(database: sqlite3.Connection) -> None:
    held = database.execute("SELECT COUNT(*) AS n FROM spine").fetchone()["n"]
    assert held == len(list(SPINE.addresses()))


def test_every_published_verse_crossed_over(database: sqlite3.Connection) -> None:
    for code in VERSIONS:
        held = database.execute(
            "SELECT COUNT(*) AS n FROM texts WHERE version = ?", (code,)
        ).fetchone()["n"]
        assert held == len(load(code).verses), code


def test_the_build_refuses_an_order_the_spine_disagrees_with(
    blank: sqlite3.Connection,
) -> None:
    """The file carries an order and this repo walks one. B2 proved they match.

    Nothing forces them to keep matching, and a silent disagreement would point
    a verse at its neighbour. So the build checks rather than the schema
    carrying the address twice to be compared later.
    """
    with pytest.raises(ValueError, match="GEN.1.1"):
        build_texts(
            blank, "matos-soares", {"GEN.1.1": Verse(text="No princípio…", order=2)}
        )


def test_a_range_crosses_a_chapter_boundary(database: sqlite3.Connection) -> None:
    """Genesis 1 ends at 31 and Genesis 2 starts at 1, contiguous in order."""
    ids = [
        row["id"]
        for row in database.execute(
            """
            SELECT id FROM spine WHERE canonical_order BETWEEN
                (SELECT canonical_order FROM spine WHERE id = 'GEN.1.30') AND
                (SELECT canonical_order FROM spine WHERE id = 'GEN.2.2')
            ORDER BY canonical_order
            """
        )
    ]
    assert ids == ["GEN.1.30", "GEN.1.31", "GEN.2.1", "GEN.2.2"]


def test_a_range_crosses_a_book_boundary(database: sqlite3.Connection) -> None:
    """Malachi ends the Old Testament at 3:24 on this spine, not at 4:6.

    Most English editions print four chapters. The spine numbers Malachi in
    `org`, which prints three, and that is a result of the superset rule rather
    than a choice about Malachi. Worth pinning here because a range crossing the
    testaments is where an assumed chapter count would go unnoticed.
    """
    ids = [
        row["id"]
        for row in database.execute(
            """
            SELECT id FROM spine WHERE canonical_order BETWEEN
                (SELECT canonical_order FROM spine WHERE id = 'MAL.3.24') AND
                (SELECT canonical_order FROM spine WHERE id = 'MAT.1.2')
            ORDER BY canonical_order
            """
        )
    ]
    assert ids == ["MAL.3.24", "MAT.1.1", "MAT.1.2"]


def test_the_default_version_is_named_once(database: sqlite3.Connection) -> None:
    named = [
        row["code"]
        for row in database.execute("SELECT code FROM versions WHERE is_default = 1")
    ]
    assert named == [DEFAULT_VERSION]


def test_version_metadata_survives(database: sqlite3.Connection) -> None:
    for code in VERSIONS:
        published = load(code).metadata
        row = database.execute(
            "SELECT * FROM versions WHERE code = ?", (code,)
        ).fetchone()
        assert row["name"] == published["name"]
        assert row["language"] == published["language"]
        assert json.loads(row["rights"]) == published["rights"]


def test_no_text_is_blank(database: sqlite3.Connection) -> None:
    """B2 omits a verse blank upstream rather than publishing an empty string."""
    empty = database.execute(
        "SELECT COUNT(*) AS n FROM texts WHERE TRIM(text) = ''"
    ).fetchone()["n"]
    assert empty == 0


def test_the_twelve_douay_gaps_are_gaps(database: sqlite3.Connection) -> None:
    """A gap is an address the spine holds and one version does not fill.

    It is the distinction the whole error taxonomy rests on, so it is asserted
    on the data before any route depends on it.
    """
    provenance = json.loads(
        (DATA_DIR / "corpus" / "PROVENANCE.json").read_text(encoding="utf-8")
    )
    missing = provenance["files"]["douay-rheims.json"]["blank_upstream"]
    assert len(missing) == 12

    for verse_id in missing:
        row = database.execute(
            """
            SELECT texts.rowid FROM spine
            LEFT JOIN texts ON texts.canonical_order = spine.canonical_order
                           AND texts.version = 'douay-rheims'
            WHERE spine.id = ?
            """,
            (verse_id,),
        ).fetchone()
        assert row is not None, f"{verse_id} is not on the spine"
        assert row["rowid"] is None, f"{verse_id} should be unfilled in Douay"


def test_the_schema_leaves_room_for_full_text_search(
    blank: sqlite3.Connection,
) -> None:
    """B9 adds FTS5 beside this without migrating anything.

    Proved by building the external content table B9 would build. An external
    content index needs a rowid on `texts`, which is why that one table is not
    WITHOUT ROWID while the others are.
    """
    blank.executescript(
        """
        INSERT INTO versions (code, name, language, rights)
             VALUES ('v', 'V', 'la', '{}');
        INSERT INTO books VALUES ('GEN', 1, 'OLD', 'PENTATEUCH', 0, 50);
        INSERT INTO spine VALUES (1, 'GEN.1.1', 'GEN', 1, 1);
        INSERT INTO texts (version, canonical_order, text)
             VALUES ('v', 1, 'in principio creavit Deus');

        CREATE VIRTUAL TABLE texts_fts USING fts5(
            text, content='texts', content_rowid='rowid'
        );
        INSERT INTO texts_fts(texts_fts) VALUES ('rebuild');
        """
    )

    found = blank.execute(
        """
        SELECT spine.id FROM texts_fts
        JOIN texts ON texts.rowid = texts_fts.rowid
        JOIN spine ON spine.canonical_order = texts.canonical_order
        WHERE texts_fts MATCH 'principio'
        """
    ).fetchall()
    assert [row[0] for row in found] == ["GEN.1.1"]
