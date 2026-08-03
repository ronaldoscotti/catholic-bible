"""The cross-reference query and the address lookup beside it."""

from __future__ import annotations

import sqlite3

from catholic_bible.storage import reader


def order_of(connection: sqlite3.Connection, address: str) -> int:
    found = reader.address(connection, address)
    assert found is not None, address
    return int(found["canonical_order"])


def test_scattered_addresses_are_fetched_one_by_one(
    database: sqlite3.Connection,
) -> None:
    """Genesis 1:1 points at Acts and Revelation, so the range covering its
    targets is the whole spine. Reading it as a range cost 35845 rows to answer
    30 and took 35 ms over HTTP."""
    wanted = [1, 20000, 35845]
    found = reader.addresses_at(database, wanted)

    assert sorted(found) == wanted
    assert str(found[1]["id"]) == "GEN.1.1"


def test_an_empty_set_asks_nothing(database: sqlite3.Connection) -> None:
    assert reader.addresses_at(database, []) == {}


def test_the_cap_is_per_anchor_and_not_per_query(
    database: sqlite3.Connection,
) -> None:
    """A passage of many verses gets the cap on each of them, not shared."""
    first = order_of(database, "GEN.1.1")
    last = order_of(database, "GEN.1.31")

    rows = reader.cross_references_from(database, first, last, 30)
    per_anchor: dict[int, int] = {}
    for row in rows:
        per_anchor[int(row["from_order"])] = (
            per_anchor.get(int(row["from_order"]), 0) + 1
        )

    assert per_anchor[first] == 30
    assert max(per_anchor.values()) == 30
    assert len(rows) > 30


def test_the_best_reference_comes_first(database: sqlite3.Connection) -> None:
    """Curated Catholic sources at 100, OpenBible capped at 99 below them."""
    order = order_of(database, "GEN.1.1")
    rows = reader.cross_references_from(database, order, order, 30)

    weights = [int(row["weight"]) for row in rows]
    assert weights == sorted(weights, reverse=True)
    assert str(rows[0]["source"]) == "douay"
