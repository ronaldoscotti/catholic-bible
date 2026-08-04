"""The two indexes, the table change one of them needed, and the queries over them.

Counts are asserted against the tables the indexes are built from rather than
against a constant typed here, so a half built index fails rather than agreeing
with a number somebody wrote down. Where a count is pinned to a literal it is
because the literal is the point, and the docstring says which.
"""

from __future__ import annotations

import sqlite3

from catholic_bible.search import compile_query
from catholic_bible.storage import reader


def expression(typed: str) -> str:
    built = compile_query(typed)
    assert built is not None, typed
    return built


def test_commentary_body_can_be_addressed_by_rowid(
    database: sqlite3.Connection,
) -> None:
    """An FTS5 external content index reaches its content table by rowid.

    This table was `WITHOUT ROWID`, which put it out of reach. Nothing else in
    the suite would notice that coming back, because every reader above it
    addresses the row by `(commentary, language)` and still can.
    """
    rows = database.execute(
        "SELECT rowid AS addressed, id FROM commentary_body ORDER BY id LIMIT 3"
    ).fetchall()

    assert [row["addressed"] for row in rows] == [row["id"] for row in rows]
    assert rows[0]["id"] == 1


def test_the_address_the_readers_use_is_still_unique(
    database: sqlite3.Connection,
) -> None:
    """The key that stopped being primary is still the key that has to hold."""
    duplicated = database.execute(
        "SELECT COUNT(*) AS n FROM ("
        " SELECT commentary, language FROM commentary_body"
        " GROUP BY commentary, language HAVING COUNT(*) > 1)"
    ).fetchone()["n"]

    assert duplicated == 0


def counted(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])


def test_every_verse_reached_the_index(database: sqlite3.Connection) -> None:
    assert counted(database, "verse_search") == counted(database, "texts")


def test_every_note_reached_the_index(database: sqlite3.Connection) -> None:
    assert counted(database, "note_search") == counted(database, "commentary_body")


def test_the_tokenizer_is_the_one_that_folds_accents(
    database: sqlite3.Connection,
) -> None:
    """Criterion 2 is this argument and nothing else.

    Every accent test below would still pass on a query that happens to be
    spelled correctly, so the argument itself is asserted. Losing it silently
    would leave the suite green and the feature gone.
    """
    for table in ("verse_search", "note_search"):
        sql = database.execute(
            "SELECT sql FROM sqlite_master WHERE name = ?", (table,)
        ).fetchone()["sql"]

        assert 'tokenize="unicode61 remove_diacritics 2"' in sql, table


def matched(connection: sqlite3.Connection, table: str, expression: str) -> int:
    return int(
        connection.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE {table} MATCH ?", (expression,)
        ).fetchone()["n"]
    )


def test_a_portuguese_word_is_found_without_its_accents(
    database: sqlite3.Connection,
) -> None:
    """The question the epic asks in its second criterion."""
    accented = matched(database, "verse_search", '"coração"')

    assert accented > 0
    assert matched(database, "verse_search", '"coracao"') == accented


def test_latin_needs_no_handling_of_its_own(database: sqlite3.Connection) -> None:
    assert matched(database, "verse_search", '"Dominus"') > 0


def test_the_snippet_marks_the_word_the_text_actually_carries(
    database: sqlite3.Connection,
) -> None:
    """The divergence from the ported implementation, pinned.

    There the highlight is a literal replace after the match, so searching
    `coracao` finds the verse and marks nothing. Here the index marks the token
    it matched, accents and all.
    """
    snippet = database.execute(
        "SELECT snippet(verse_search, 0, '<em>', '</em>', '…', 64) AS s"
        " FROM verse_search WHERE verse_search MATCH ? LIMIT 1",
        ('"coracao"',),
    ).fetchone()["s"]

    assert "<em>" in snippet
    assert "coraç" in snippet.lower()


def test_a_verse_search_carries_what_a_result_list_renders(
    database: sqlite3.Connection,
) -> None:
    hits = reader.search_verses(database, expression("coracao"), version="matos-soares")

    first = hits[0]
    assert set(first.keys()) >= {
        "id",
        "book",
        "chapter",
        "verse",
        "version",
        "snippet",
    }
    assert first["version"] == "matos-soares"
    assert "<em>" in first["snippet"]


def test_the_phrase_and_the_conjunction_are_pinned_apart(
    database: sqlite3.Connection,
) -> None:
    """The bug a first draft of the compiler shipped, held at this level too.

    Quoting each word separately reads to FTS5 as an implicit conjunction. Both
    expressions are valid, both return hits, and only the counts tell them
    apart, which is why the string assertion in `tests/test_query_compiler.py` is not
    enough on its own.
    """
    phrase = reader.count_verses(database, expression('"cordeiro de Deus"'))
    conjunction = reader.count_verses(database, expression("cordeiro de Deus"))

    assert phrase == 2
    assert conjunction == 10


def test_accents_do_not_have_to_be_typed(database: sqlite3.Connection) -> None:
    """Criterion 2, asked the way a reader would ask it."""
    accented = reader.count_verses(
        database, expression("coração"), version="matos-soares"
    )

    assert accented == 914
    assert (
        reader.count_verses(database, expression("coracao"), version="matos-soares")
        == accented
    )


def test_latin_answers_from_the_same_index(database: sqlite3.Connection) -> None:
    hits = reader.search_verses(
        database, expression("Dominus"), version="vulgata-clementina"
    )

    assert hits
    assert all(hit["version"] == "vulgata-clementina" for hit in hits)


def test_a_book_filter_bounds_the_answer(database: sqlite3.Connection) -> None:
    hits = reader.search_verses(
        database, expression("coracao"), version="matos-soares", book="PSA"
    )

    assert hits
    assert {hit["book"] for hit in hits} == {"PSA"}


def test_a_testament_filter_bounds_the_answer(database: sqlite3.Connection) -> None:
    old = reader.count_verses(
        database, expression("Deus"), version="matos-soares", testament="OLD"
    )
    new = reader.count_verses(
        database, expression("Deus"), version="matos-soares", testament="NEW"
    )
    both = reader.count_verses(database, expression("Deus"), version="matos-soares")

    assert old and new
    assert old + new == both


def test_no_version_means_every_translation(database: sqlite3.Connection) -> None:
    """What `version=all` rests on. The repetition is real and it is the cost."""
    hits = reader.search_verses(database, expression("Deus"), limit=100)

    assert len({hit["version"] for hit in hits}) > 1


def test_a_word_the_corpus_does_not_hold_answers_nothing(
    database: sqlite3.Connection,
) -> None:
    assert reader.count_verses(database, expression("bicicleta")) == 0
    assert reader.search_verses(database, expression("bicicleta")) == []


def test_paging_neither_repeats_nor_skips(database: sqlite3.Connection) -> None:
    """bm25 ties are ordinary and a tie has no order of its own.

    Without a deterministic tie break, two pages of the same query can hand back
    the same verse twice and never show another. Nothing else in the suite would
    catch that, because each page on its own looks right.
    """

    def key(hit: sqlite3.Row) -> tuple[str, str]:
        return str(hit["id"]), str(hit["version"])

    found = expression("Deus")
    whole = [key(hit) for hit in reader.search_verses(database, found, limit=60)]
    paged = [
        key(hit)
        for start in range(0, 60, 20)
        for hit in reader.search_verses(database, found, limit=20, offset=start)
    ]

    assert whole == paged
    assert len(set(paged)) == len(paged)


def test_an_address_repeats_across_translations_and_that_is_the_cost(
    database: sqlite3.Connection,
) -> None:
    """What `version=all` buys and what it charges, held rather than argued.

    The same verse comes back once per translation that carries the word. It is
    the reason `version` defaults to one, and the reason every hit names its own.
    """
    hits = reader.search_verses(database, expression("Deus"), limit=60)
    ids = [hit["id"] for hit in hits]

    assert len(set(ids)) < len(ids)
    assert len({(hit["id"], hit["version"]) for hit in hits}) == len(hits)


def test_a_commentary_search_points_back_at_an_address(
    database: sqlite3.Connection,
) -> None:
    hits = reader.search_commentary(database, expression("coracao"))

    first = hits[0]
    assert set(first.keys()) >= {
        "source",
        "language",
        "start",
        "end",
        "book",
        "snippet",
    }
    assert "<em>" in first["snippet"]


def test_the_machine_translation_is_searched_like_any_other_text(
    database: sqlite3.Connection,
) -> None:
    """No demotion and no opt in. The `language` on the hit is what tells a reader."""
    portuguese = reader.count_commentary(
        database, expression("coracao"), language="pt-BR"
    )
    english = reader.count_commentary(database, expression("heart"), language="en-US")

    assert portuguese > 0
    assert english > 0
    assert reader.count_commentary(database, expression("coracao")) >= portuguese


def test_a_commentary_source_filter_bounds_the_answer(
    database: sqlite3.Connection,
) -> None:
    hits = reader.search_commentary(database, expression("coracao"), source="haydock")

    assert hits
    assert {hit["source"] for hit in hits} == {"haydock"}


def test_a_commentary_book_filter_bounds_the_answer(
    database: sqlite3.Connection,
) -> None:
    hits = reader.search_commentary(database, expression("coracao"), book="PSA")

    assert hits
    assert {hit["book"] for hit in hits} == {"PSA"}
