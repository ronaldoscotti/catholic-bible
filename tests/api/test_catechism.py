"""The three Catechism routes, over HTTP.

They answer by reference and never with text. The assertion that matters most is
the last one, and it is about what the response cannot contain.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from catholic_bible.api.app import app

CLIENT = TestClient(app)


def test_a_verse_answers_with_the_paragraphs_that_cite_it() -> None:
    answer = CLIENT.get("/v1/books/MAT/chapters/28/verses/19/catechism")

    assert answer.status_code == 200
    body = answer.json()
    assert body["ids"] == ["MAT.28.19"]
    assert body["paragraphs"], "Matthew 28,19 is the most cited verse there is"
    assert all(1 <= entry["paragraph"] <= 2865 for entry in body["paragraphs"])


def test_the_answer_says_why_it_may_be_published() -> None:
    body = CLIENT.get("/v1/books/MAT/chapters/28/verses/19/catechism").json()

    assert "No Catechism text" in body["rights"]
    assert "LIMITS.md" in body["rights"]


def test_a_verse_nobody_cites_answers_with_an_empty_list() -> None:
    """Not a 404. The verse is on the spine and the Catechism is silent on it."""
    answer = CLIENT.get("/v1/books/NUM/chapters/7/verses/66/catechism")

    assert answer.status_code == 200
    assert answer.json()["paragraphs"] == []


def test_a_verse_the_spine_does_not_have_is_a_404() -> None:
    answer = CLIENT.get("/v1/books/JHN/chapters/3/verses/999/catechism")

    assert answer.status_code == 404
    assert answer.json()["detail"]["reason"] == "not_on_spine"


def test_a_written_reference_answers_in_the_numbering_it_was_written_in() -> None:
    """`Sl 51,1` in english is the Miserere, which the spine numbers 50,3."""
    answer = CLIENT.get("/v1/catechism", params={"ref": "Sl 51,1", "scheme": "english"})

    assert answer.status_code == 200
    assert answer.json()["ids"] == ["PSA.50.3"]


def test_a_paragraph_answers_with_the_verses_it_cites() -> None:
    answer = CLIENT.get("/v1/catechism/paragraphs/1223")

    assert answer.status_code == 200
    body = answer.json()
    assert body["paragraph"] == 1223
    assert body["cites"]
    for entry in body["cites"]:
        assert entry["ids"]


def test_a_paragraph_citing_no_scripture_answers_with_nothing() -> None:
    """1672 of the 2865 cite none, and existing while citing nothing is not a 404."""
    answer = CLIENT.get("/v1/catechism/paragraphs/1")

    assert answer.status_code == 200
    assert answer.json()["cites"] == []


@pytest.mark.parametrize("number", [0, 2866, 99999])
def test_a_paragraph_the_catechism_does_not_have_is_refused(number: int) -> None:
    assert CLIENT.get(f"/v1/catechism/paragraphs/{number}").status_code == 422


def test_every_paragraph_carries_a_link_to_both_editions() -> None:
    body = CLIENT.get("/v1/books/MAT/chapters/28/verses/19/catechism").json()

    for entry in body["paragraphs"]:
        assert [link["language"] for link in entry["links"]] == ["en", "pt"]
        for link in entry["links"]:
            assert link["url"].startswith("https://www.vatican.va/archive/")
            assert link["text_fragment"].startswith(link["url"])


def test_a_paragraph_answers_once_for_a_span_it_cites_twice() -> None:
    """`Mt 28,19-20` covers both verses, and the paragraph is one paragraph."""
    body = CLIENT.get("/v1/catechism", params={"ref": "Mt 28,19-20"}).json()

    numbers = [entry["paragraph"] for entry in body["paragraphs"]]
    assert numbers == sorted(set(numbers))


def test_no_response_field_could_hold_catechism_text() -> None:
    """The line the epic drew, asserted on the shape rather than on a wordlist.

    Every string a response carries is a spine address, a citation label, a URL
    or the rights line. A paragraph's text, title, first line or breadcrumb
    would have to be a field that is none of those.
    """
    verse = CLIENT.get("/v1/books/MAT/chapters/28/verses/19/catechism").json()
    assert set(verse) == {"reference", "ids", "rights", "paragraphs"}
    for entry in verse["paragraphs"]:
        assert set(entry) == {"paragraph", "cited", "links"}
        assert len(entry["cited"]) < 32
        for link in entry["links"]:
            assert set(link) == {"language", "url", "text_fragment"}

    paragraph = CLIENT.get("/v1/catechism/paragraphs/1223").json()
    assert set(paragraph) == {"paragraph", "links", "rights", "cites"}
    for entry in paragraph["cites"]:
        assert set(entry) == {"cited", "ids"}
