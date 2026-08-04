"""Turning what a person typed into something FTS5 will run.

The first test is not the happy path. `MATCH` takes an expression language, and
six of ten realistic inputs are a syntax error when handed to it raw, including
a parenthesis, an apostrophe and a chapter and verse written with a colon. This
module exists so none of those reaches SQLite.
"""

from __future__ import annotations

import random
import sqlite3
from collections.abc import Iterator

import pytest

from catholic_bible.search import compile_query


@pytest.fixture(scope="module")
def fts() -> Iterator[sqlite3.Connection]:
    """A tiny index, only to prove an expression parses and runs."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE VIRTUAL TABLE t USING fts5(text,"
        ' tokenize="unicode61 remove_diacritics 2")'
    )
    connection.execute("INSERT INTO t VALUES ('o Cordeiro de Deus e o coração')")
    yield connection
    connection.close()


def runs(connection: sqlite3.Connection, expression: str) -> int:
    return int(
        connection.execute(
            "SELECT count(*) FROM t WHERE t MATCH ?", (expression,)
        ).fetchone()[0]
    )


def test_bare_words_are_all_required() -> None:
    """What a search box means by a space."""
    assert compile_query("cordeiro de Deus") == '"cordeiro" AND "de" AND "Deus"'


def test_a_quoted_phrase_stays_one_phrase() -> None:
    """The case a first draft of this function got wrong.

    Emitting three quoted words side by side reads to FTS5 as an implicit AND,
    which answered 10 verses where the phrase answers 2. The string looked
    right, so `tests/storage/test_search_index.py` pins the counts as well.
    """
    assert compile_query('"cordeiro de Deus"') == '"cordeiro de Deus"'


def test_a_trailing_star_survives_as_a_prefix() -> None:
    """The only tool a reader has for an inflection, since there is no stemmer."""
    assert compile_query("amar*") == '"amar"*'


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("Deus (pai)", '"Deus" AND "pai"'),
        ("Jo 3:16", '"Jo" AND "3 16"'),
        ("o Senhor's", '"o" AND "Senhor s"'),
        ("fé -", '"fé"'),
        ("a OR", '"a" AND "OR"'),
        ("AND", '"AND"'),
        ("NEAR", '"NEAR"'),
    ],
)
def test_what_used_to_be_a_server_error(typed: str, expected: str) -> None:
    """Every one of these is a 500 today when handed to `MATCH` unchanged.

    `AND`, `OR` and `NEAR` are words in this corpus rather than operators. The
    bare `NEAR` alone reaches 217 verses.
    """
    assert compile_query(typed) == expected


@pytest.mark.parametrize("typed", ["", "   ", '""', "!!!", "-", "(())", "…"])
def test_a_query_with_no_words_left_is_refused_rather_than_run(typed: str) -> None:
    """`None` is the 422. An empty result would claim the corpus lacks the word."""
    assert compile_query(typed) is None


def test_accents_are_left_alone_here(fts: sqlite3.Connection) -> None:
    """Folding belongs to the tokenizer and is not repeated on the way in.

    Stripping accents here as well would work and would put the same rule in two
    places, which is how the two stop agreeing.
    """
    assert compile_query("coração") == '"coração"'
    assert runs(fts, '"coracao"') == 1


def test_the_phrase_and_the_conjunction_are_different_questions(
    fts: sqlite3.Connection,
) -> None:
    row = "o Cordeiro de Deus e o coração"

    assert runs(fts, compile_query('"cordeiro de Deus"') or "") == 1
    assert runs(fts, compile_query('"Deus cordeiro"') or "") == 0, row


ALPHABET = "abcçé 12\"*()-:.,;!?'“”…/\\[]{}^~&|+=<>#@%$AND ORNEAR"


def test_nothing_a_person_can_type_reaches_sqlite_as_a_syntax_error(
    fts: sqlite3.Connection,
) -> None:
    """The whole reason this function exists, over 2000 seeded inputs.

    Each one either compiles to an expression FTS5 executes or compiles to
    `None`. Never a raised exception and never a failing `MATCH`.
    """
    dice = random.Random(0)
    for _ in range(2000):
        typed = "".join(dice.choice(ALPHABET) for _ in range(dice.randint(0, 24)))
        expression = compile_query(typed)
        if expression is None:
            continue
        try:
            runs(fts, expression)
        except sqlite3.OperationalError as broken:  # pragma: no cover
            pytest.fail(f"{typed!r} compiled to {expression!r} and {broken}")
