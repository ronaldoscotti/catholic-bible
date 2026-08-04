"""The two search routes, over HTTP, against the real corpus.

The first block is not the happy path. Every input in it is a 500 when handed to
FTS5 unchanged, and one of them is how half the world writes a reference.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

SEARCH = "/v1/search"
NOTES = "/v1/search/commentary"


@pytest.mark.parametrize(
    "typed",
    ["Deus (pai)", "Jo 3:16", "o Senhor's", "fé -", "a OR", "AND", "NEAR", "coração*"],
)
def test_nothing_a_reader_types_reaches_the_engine_as_an_error(
    client: TestClient, typed: str
) -> None:
    answer = client.get(SEARCH, params={"q": typed})

    assert answer.status_code == 200, answer.text


@pytest.mark.parametrize("typed", ["", "   ", '""', "!!!", "…"])
def test_a_query_with_no_words_is_refused_rather_than_answered_empty(
    client: TestClient, typed: str
) -> None:
    """An empty result would say the corpus lacks the word. It does not."""
    answer = client.get(SEARCH, params={"q": typed})

    assert answer.status_code == 422
    assert answer.json()["detail"]["reason"] == "malformed"


def test_a_search_answers_with_addresses_a_reader_can_open(
    client: TestClient,
) -> None:
    body = client.get(SEARCH, params={"q": "cordeiro de Deus"}).json()

    assert body["total"] > 0
    assert body["version"] == "matos-soares"
    first = body["hits"][0]
    assert first["id"].count(".") == 2
    assert first["reference"]
    assert first["version"] == "matos-soares"


def test_the_default_version_is_the_one_the_rest_of_the_api_uses(
    client: TestClient,
) -> None:
    asked = client.get(SEARCH, params={"q": "Deus"}).json()

    assert {hit["version"] for hit in asked["hits"]} == {"matos-soares"}


def test_accents_do_not_have_to_be_typed_and_the_answer_shows_them(
    client: TestClient,
) -> None:
    """Criterion 2 and criterion 3 in one request.

    The ported implementation highlights by replacing the literal the reader
    typed, so this exact query finds the verse and marks nothing. Here the index
    marks the token it matched.
    """
    body = client.get(SEARCH, params={"q": "coracao"}).json()

    assert body["total"] == 914
    marked = body["hits"][0]["snippet"]
    assert "<em>coraç" in marked.lower()


def test_latin_is_searchable_without_a_tokenizer_of_its_own(
    client: TestClient,
) -> None:
    body = client.get(
        SEARCH, params={"q": "Dominus", "version": "vulgata-clementina"}
    ).json()

    assert body["total"] > 0
    assert {hit["version"] for hit in body["hits"]} == {"vulgata-clementina"}


def test_a_book_is_named_the_way_every_other_route_names_one(
    client: TestClient,
) -> None:
    """`Sl`, `PSA` and `Salmos` are the same book to the alias table."""
    for written in ("PSA", "Sl", "Salmos"):
        body = client.get(SEARCH, params={"q": "coracao", "book": written}).json()

        assert body["total"] > 0, written
        assert {hit["book"] for hit in body["hits"]} == {"PSA"}, written


def test_a_book_nobody_has_says_so(client: TestClient) -> None:
    answer = client.get(SEARCH, params={"q": "Deus", "book": "Hogwarts"})

    assert answer.status_code == 404
    assert answer.json()["detail"]["reason"] == "unknown_book"


def test_a_version_nobody_publishes_says_so(client: TestClient) -> None:
    answer = client.get(SEARCH, params={"q": "Deus", "version": "king-james"})

    assert answer.status_code == 404
    assert answer.json()["detail"]["reason"] == "unknown_version"


def test_a_testament_bounds_the_answer(client: TestClient) -> None:
    body = client.get(SEARCH, params={"q": "Deus", "testament": "NEW"}).json()
    whole = client.get(SEARCH, params={"q": "Deus"}).json()

    assert 0 < body["total"] < whole["total"]


def test_all_reads_every_translation_and_every_hit_names_its_own(
    client: TestClient,
) -> None:
    """The repetition is the documented cost, so the response has to make it visible."""
    body = client.get(SEARCH, params={"q": "Deus", "version": "all"}).json()

    assert body["version"] == "all"
    assert len({hit["version"] for hit in body["hits"]}) > 1


def test_the_page_is_twenty_and_it_moves(client: TestClient) -> None:
    first = client.get(SEARCH, params={"q": "Deus"}).json()
    second = client.get(SEARCH, params={"q": "Deus", "offset": 20}).json()

    assert first["limit"] == 20 and first["offset"] == 0
    assert len(first["hits"]) == 20
    assert second["offset"] == 20
    assert [hit["id"] for hit in first["hits"]] != [hit["id"] for hit in second["hits"]]


def test_paging_past_the_cap_is_refused_rather_than_served_slowly(
    client: TestClient,
) -> None:
    """1000 is a decision with a measurement behind it, and `LIMITS.md` carries both."""
    assert client.get(SEARCH, params={"q": "Deus", "offset": 1000}).status_code == 200
    assert client.get(SEARCH, params={"q": "Deus", "offset": 1001}).status_code == 422


def test_a_page_larger_than_the_ceiling_is_refused(client: TestClient) -> None:
    assert client.get(SEARCH, params={"q": "Deus", "limit": 100}).status_code == 200
    assert client.get(SEARCH, params={"q": "Deus", "limit": 101}).status_code == 422
    assert client.get(SEARCH, params={"q": "Deus", "limit": 0}).status_code == 422


def test_a_word_the_corpus_does_not_hold_is_an_empty_answer_not_an_error(
    client: TestClient,
) -> None:
    body = client.get(SEARCH, params={"q": "bicicleta"}).json()

    assert body["total"] == 0
    assert body["hits"] == []


def test_the_commentary_route_answers_with_the_anchor_and_the_language(
    client: TestClient,
) -> None:
    body = client.get(NOTES, params={"q": "coracao"}).json()

    assert body["total"] > 0
    first = body["hits"][0]
    assert first["source"] == "haydock"
    assert first["language"] in {"pt-BR", "en-US"}
    assert first["start"].count(".") == 2
    assert first["reference"]
    assert "<em>" in first["snippet"]


def test_the_commentary_route_filters_by_language(client: TestClient) -> None:
    """The machine translation is searched like any other text and says which it is."""
    body = client.get(NOTES, params={"q": "coracao", "language": "pt-BR"}).json()

    assert body["total"] > 0
    assert {hit["language"] for hit in body["hits"]} == {"pt-BR"}


def test_the_commentary_route_filters_by_book(client: TestClient) -> None:
    body = client.get(NOTES, params={"q": "coracao", "book": "Sl"}).json()

    assert body["total"] > 0
    assert {hit["book"] for hit in body["hits"]} == {"PSA"}


def test_the_commentary_route_refuses_an_empty_query_the_same_way(
    client: TestClient,
) -> None:
    answer = client.get(NOTES, params={"q": "!!!"})

    assert answer.status_code == 422
    assert answer.json()["detail"]["reason"] == "malformed"


def test_a_search_is_not_cached_forever_the_way_a_verse_is(
    client: TestClient,
) -> None:
    """A verse is immutable. A result list depends on what is published."""
    headers = client.get(SEARCH, params={"q": "Deus"}).headers

    assert "immutable" not in headers.get("cache-control", "")


@pytest.mark.parametrize("value", ["haydok", "catena", ""])
def test_a_commentary_source_nobody_has_says_so(client: TestClient, value: str) -> None:
    """An empty result here would be a false statement about the corpus.

    This route already refuses an unknown book and an unknown version, and its
    own document declares a 404. Answering `source=haydok` with `total: 0` says
    Haydock has nothing on the query, which is not what happened.

    The empty string is in the list because an SPA rendering `&source=${sel}`
    with `sel` unset used to silently drop the filter and return everything
    while the interface claimed one source.
    """
    answer = client.get(NOTES, params={"q": "Deus", "source": value})

    assert answer.status_code == 404
    assert answer.json()["detail"]["reason"] == "unknown_source"


@pytest.mark.parametrize("value", ["fr-FR", "pt", ""])
def test_a_commentary_language_nobody_publishes_says_so(
    client: TestClient, value: str
) -> None:
    answer = client.get(NOTES, params={"q": "Deus", "language": value})

    assert answer.status_code == 404
    assert answer.json()["detail"]["reason"] == "unknown_language"


def test_a_repeated_term_costs_what_one_term_costs(client: TestClient) -> None:
    """The query that turned one GET into eight seconds of CPU.

    FTS5 intersects a doclist per term and an identical broad term never
    shrinks the set. 300 copies of `a*` fit in an 899 character URL, cost 8.46
    seconds against the built corpus, and the rate limiter counts them as one
    request. Sixty a minute is inside the published limit and pins the pool.

    166 copies here rather than 300, because the length ceiling now refuses
    900 characters outright. Both defences are real and this one is the floor
    under the other.
    """
    answer = client.get(SEARCH, params={"q": "a* " * 166})

    assert answer.status_code == 200
    assert (
        answer.json()["total"] == client.get(SEARCH, params={"q": "a*"}).json()["total"]
    )


def test_a_query_longer_than_a_search_box_is_refused(client: TestClient) -> None:
    """A ceiling under the compiler rather than only inside it."""
    answer = client.get(SEARCH, params={"q": "palavra " * 300})

    assert answer.status_code == 422
