"""The coverage query, against the built database.

A note covers a range of addresses and most notes cover one. The two failures
that matter are a spanning note that cannot be found from its far end, and a
range query that returns the same note once per address it covers.
"""

from __future__ import annotations

import sqlite3

import pytest

from catholic_bible.storage import reader


def order_of(connection: sqlite3.Connection, address: str) -> int:
    found = reader.address(connection, address)
    assert found is not None, address
    return int(found["canonical_order"])


def test_a_verse_returns_the_note_that_names_it(database: sqlite3.Connection) -> None:
    order = order_of(database, "JHN.3.16")
    rows = reader.commentary_covering(database, order, order)

    assert rows, "John 3:16 has a Haydock note"
    assert {str(row["language"]) for row in rows} == {"en-US", "pt-BR"}


def test_a_verse_inside_a_spanning_note_finds_it(database: sqlite3.Connection) -> None:
    """The note has to be reachable from its last address, not only its first."""
    widest = database.execute(
        "SELECT first_order, last_order FROM commentary"
        " ORDER BY last_order - first_order DESC LIMIT 1"
    ).fetchone()
    first, last = int(widest["first_order"]), int(widest["last_order"])
    assert last - first == 15, "the widest published note spans 15 addresses"

    found = reader.commentary_covering(database, last, last)
    assert first in {int(row["first_order"]) for row in found}


def test_a_range_returns_a_spanning_note_once(database: sqlite3.Connection) -> None:
    """The bug the private reader deduplicates for, pinned here instead."""
    widest = database.execute(
        "SELECT id, first_order, last_order FROM commentary"
        " ORDER BY last_order - first_order DESC LIMIT 1"
    ).fetchone()
    first, last = int(widest["first_order"]), int(widest["last_order"])

    rows = reader.commentary_covering(database, first, last)
    ids = [int(row["id"]) for row in rows if int(row["id"]) == int(widest["id"])]

    assert len(ids) == 2, "once per language, not once per address covered"


def test_an_address_with_no_note_returns_nothing(database: sqlite3.Connection) -> None:
    """Absence is an answer. 14803 of 35845 addresses have no note."""
    empty = database.execute(
        """
        SELECT canonical_order FROM spine WHERE NOT EXISTS (
            SELECT 1 FROM commentary
            WHERE spine.canonical_order BETWEEN first_order AND last_order
        ) LIMIT 1
        """
    ).fetchone()
    order = int(empty["canonical_order"])

    assert reader.commentary_covering(database, order, order) == []


@pytest.mark.parametrize("address", ["MAT.15.26", "LUK.1.73"])
def test_a_clamped_note_is_readable(database: sqlite3.Connection, address: str) -> None:
    """Both are invisible upstream, where the range runs backwards."""
    order = order_of(database, address)
    assert reader.commentary_covering(database, order, order)


def test_the_floor_does_not_change_the_answer(database: sqlite3.Connection) -> None:
    """The floor is performance. A floor that dropped a note would be a bug.

    Compared against the unbounded form over a thousand addresses rather than
    argued from the widest span, because the argument is what could be wrong.
    """
    for order in range(1, 35845, 37):
        floored = {
            (int(row["id"]), str(row["language"]))
            for row in reader.commentary_covering(database, order, order)
        }
        unbounded = {
            (int(row["id"]), str(row["language"]))
            for row in database.execute(
                "SELECT commentary.id, commentary_body.language FROM commentary"
                " JOIN commentary_body ON commentary_body.commentary = commentary.id"
                " WHERE first_order <= ? AND last_order >= ?",
                (order, order),
            )
        }
        assert floored == unbounded, order


def test_the_widest_span_is_read_off_the_build(database: sqlite3.Connection) -> None:
    measured = database.execute(
        "SELECT MAX(last_order - first_order) AS widest FROM commentary"
    ).fetchone()
    assert reader.widest_commentary_span(database) == int(measured["widest"])
