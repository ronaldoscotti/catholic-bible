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

from catholic_bible.search import TOKEN_CAP, compile_query


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


ALPHABET = "abcçé 12\"*()-:.,;!?'“”…/\\[]{}^~&|+=<>#@%$_AND ORNEAR"


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


def test_a_term_repeated_is_searched_once() -> None:
    """A repeated term is free to write and expensive to run.

    FTS5 intersects the doclist once per term, and an identical broad term
    never shrinks the set it is intersecting with. 300 copies of `a*` in an 899
    character query cost 8.5 seconds of CPU on the built corpus, on one
    unauthenticated GET that the rate limiter counts as one request.
    """
    assert compile_query("Deus Deus Deus") == '"Deus"'
    assert compile_query("a* " * 300) == '"a"*'


def test_the_number_of_words_is_capped() -> None:
    """Deduplication answers the cheap attack and a cap answers the other one.

    600 distinct short prefixes are fast, because the set collapses after the
    first intersection. The cap is the floor under what dedupe cannot bound.
    """
    typed = " ".join(f"w{index}" for index in range(200))
    built = compile_query(typed)

    assert built is not None
    assert built.count(" AND ") + 1 == TOKEN_CAP


def test_a_long_phrase_is_bounded_the_same_way_a_long_query_is() -> None:
    """The cap counts words, because counting terms let a phrase walk past it.

    A quoted run is one term however many words it holds, so a 497 character
    phrase compiled to a single term and met neither the dedupe nor the cap.
    It cost 269 ms against 49 ms for an ordinary query, inside the 500
    character ceiling and inside the published rate limit.
    """
    built = compile_query('"' + " ".join(["a"] * 248) + '"')

    assert built is not None
    assert len(built.strip('"').split()) == TOKEN_CAP


def test_a_phrase_and_bare_words_share_one_budget() -> None:
    """Otherwise the phrase is a way of buying more words than the cap allows."""
    built = compile_query('"um dois tres" ' + " ".join(f"w{n}" for n in range(60)))

    assert built is not None
    assert (
        sum(len(term.strip('"*').split()) for term in built.split(" AND ")) == TOKEN_CAP
    )


@pytest.mark.parametrize(
    ("typed", "expected"),
    [("___", None), ("Deus ___", '"Deus"'), ("a_b", '"a b"')],
)
def test_an_underscore_is_not_a_word_to_the_tokenizer(
    typed: str, expected: str | None
) -> None:
    """`\\w` keeps the underscore and `unicode61` does not, and the gap ate queries.

    `___` survived as the phrase `"___"`, which tokenizes to nothing and
    matches nothing, so it answered 200 with an empty result. That is the claim
    about the corpus this module refuses to make for `!!!`. Worse in company:
    `Deus ___` returned zero and hid the 6463 verses `Deus` reaches, with no
    error and no hint.
    """
    assert compile_query(typed) == expected


def test_the_cap_keeps_the_terms_the_reader_wrote_first() -> None:
    typed = " ".join(f"w{index}" for index in range(200))
    built = compile_query(typed)

    assert built is not None
    assert built.startswith('"w0" AND "w1" AND')
