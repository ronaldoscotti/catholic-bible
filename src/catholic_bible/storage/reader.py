"""Queries. Plain functions over a connection, returning rows.

Knows nothing about HTTP. Everything is addressed by the dense canonical order,
because a chapter is a contiguous range on the spine and a range is one indexed
BETWEEN rather than a scan.
"""

from __future__ import annotations

import sqlite3

from catholic_bible.canon.aliases import Language

Row = sqlite3.Row

LANGUAGES = {"pt-BR": Language.PT, "en-US": Language.EN, "la": Language.LA}


def language_of(code: str) -> Language:
    """The language a version is written in, for names and for notation.

    Falls back to Portuguese for a tag nothing here declares, which is the
    language of the default version rather than a guess about the text.
    """
    return LANGUAGES.get(code, Language.PT)


def _one(cursor: sqlite3.Cursor) -> Row | None:
    """`fetchone` is untyped in the stubs, so the cast lives in one place."""
    found: Row | None = cursor.fetchone()
    return found


def _all(cursor: sqlite3.Cursor) -> list[Row]:
    rows: list[Row] = cursor.fetchall()
    return rows


def versions(connection: sqlite3.Connection) -> list[Row]:
    return _all(
        connection.execute("SELECT * FROM versions ORDER BY is_default DESC, code")
    )


def version(connection: sqlite3.Connection, code: str) -> Row | None:
    return _one(connection.execute("SELECT * FROM versions WHERE code = ?", (code,)))


def default_version(connection: sqlite3.Connection) -> Row:
    found = _one(connection.execute("SELECT * FROM versions WHERE is_default = 1"))
    assert found is not None, "the build names exactly one default version"
    return found


def book(connection: sqlite3.Connection, code: str) -> Row | None:
    return _one(connection.execute("SELECT * FROM books WHERE code = ?", (code,)))


def books_in(connection: sqlite3.Connection, code: str) -> list[Row]:
    """The books this version reaches, in canonical order.

    Not the raw 73. A version carrying no deuterocanonicals would not list them,
    and the order range on each book is what makes the check one indexed probe.
    """
    return _all(
        connection.execute(
            """
        SELECT * FROM books WHERE EXISTS (
            SELECT 1 FROM texts
            WHERE texts.version = ?
              AND texts.canonical_order BETWEEN books.first_order AND books.last_order
        )
        ORDER BY position
        """,
            (code,),
        )
    )


def chapter(connection: sqlite3.Connection, code: str, number: int) -> Row | None:
    return _one(
        connection.execute(
            "SELECT * FROM chapters WHERE book = ? AND chapter = ?", (code, number)
        )
    )


def neighbour(
    connection: sqlite3.Connection, version_code: str, order: int, step: int
) -> Row | None:
    """The chapter before or after this one, in the version's own coverage.

    Crosses a book boundary, because canonical order does not stop at one, and
    skips a book the version does not carry rather than returning a chapter with
    no text in it.
    """
    comparison, direction = (">", "ASC") if step > 0 else ("<", "DESC")
    return _one(
        connection.execute(
            f"""
        SELECT chapters.* FROM chapters
        WHERE chapters.first_order {comparison} ?
          AND EXISTS (
              SELECT 1 FROM texts
              WHERE texts.version = ?
                AND texts.canonical_order
                    BETWEEN chapters.first_order AND chapters.last_order
          )
        ORDER BY chapters.first_order {direction}
        LIMIT 1
        """,
            (order, version_code),
        )
    )


def verses_between(
    connection: sqlite3.Connection, version_code: str, first: int, last: int
) -> list[Row]:
    return _all(
        connection.execute(
            """
        SELECT spine.id, spine.book, spine.chapter, spine.verse,
               spine.canonical_order, texts.text
        FROM spine
        JOIN texts ON texts.canonical_order = spine.canonical_order
        WHERE texts.version = ? AND spine.canonical_order BETWEEN ? AND ?
        ORDER BY spine.canonical_order
        """,
            (version_code, first, last),
        )
    )


def texts_at(
    connection: sqlite3.Connection, codes: list[str], orders: list[int]
) -> dict[tuple[str, int], str]:
    """Every version's text for a set of addresses, keyed for an outer join.

    The caller aligns. A version missing a verse has to show as a gap rather
    than as a shorter column, which is what keeps two rendered translations from
    silently sliding against each other.
    """
    if not codes or not orders:
        return {}

    version_marks = ",".join("?" * len(codes))
    wanted = set(orders)
    return {
        (str(row["version"]), int(row["canonical_order"])): str(row["text"])
        for row in connection.execute(
            f"SELECT version, canonical_order, text FROM texts "
            f"WHERE version IN ({version_marks}) "
            f"AND canonical_order BETWEEN ? AND ?",
            (*codes, min(orders), max(orders)),
        )
        if int(row["canonical_order"]) in wanted
    }


def widest_commentary_span(connection: sqlite3.Connection) -> int:
    """How far the widest note reaches, in canonical order.

    Computed at build time and read back rather than derived per request. It is
    the exact margin `commentary_covering` needs and nothing else.
    """
    found = _one(
        connection.execute("SELECT MAX(widest) AS widest FROM commentary_sources")
    )
    return 0 if found is None or found["widest"] is None else int(found["widest"])


def commentary_covering(
    connection: sqlite3.Connection, first: int, last: int
) -> list[Row]:
    """Every note covering any address in a range, with its bodies.

    Covering is `first_order <= last AND last_order >= first`. The extra floor
    changes no result, because no note is wider than the widest note, and it is
    what keeps the query bounded: without it the index is walked from the start
    of the source, which is 0.92 ms at the end of Revelation against 0.0065 ms
    with it.

    One row per note and language. A note is one to four entries for a verse, so
    the repeated columns are cheaper than a second round trip.
    """
    floor = first - widest_commentary_span(connection)
    return _all(
        connection.execute(
            """
        SELECT commentary.id, commentary.source, commentary.first_order,
               commentary.last_order, commentary.label, commentary.position,
               commentary_body.language, commentary_body.html, commentary_body.text
        FROM commentary
        JOIN commentary_sources ON commentary_sources.code = commentary.source
        JOIN commentary_body ON commentary_body.commentary = commentary.id
        WHERE commentary.first_order >= ?
          AND commentary.first_order <= ?
          AND commentary.last_order >= ?
        ORDER BY commentary_sources.position, commentary.first_order,
                 commentary.position, commentary.id, commentary_body.language
        """,
            (floor, last, first),
        )
    )


def commentary_sources(connection: sqlite3.Connection) -> list[Row]:
    return _all(
        connection.execute("SELECT * FROM commentary_sources ORDER BY position")
    )


def address(connection: sqlite3.Connection, verse_id: str) -> Row | None:
    return _one(connection.execute("SELECT * FROM spine WHERE id = ?", (verse_id,)))


def addresses_between(
    connection: sqlite3.Connection, first: int, last: int
) -> dict[int, Row]:
    """Every spine address in a range, keyed by order.

    One query. Asking per address is up to 501 round trips for a passage at the
    cap, and the range is contiguous by construction.
    """
    return {
        int(row["canonical_order"]): row
        for row in _all(
            connection.execute(
                "SELECT * FROM spine WHERE canonical_order BETWEEN ? AND ? "
                "ORDER BY canonical_order",
                (first, last),
            )
        )
    }
