"""The cross-reference routes, over HTTP.

The second layer on the same anchor, which is what makes B1's claim about the
verse id something other than an assertion.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

ADDRESS = "/v1/books/GEN/chapters/1/verses/1/cross-references"


def test_a_verse_answers_with_the_passages_it_points_at(client: TestClient) -> None:
    found = client.get(ADDRESS)

    assert found.status_code == 200
    body = found.json()
    assert body["ids"] == ["GEN.1.1"]
    assert body["reference"] == "Gn 1,1"
    assert body["references"]
    assert all(row["id"] == "GEN.1.1" for row in body["references"])


def test_the_openbible_attribution_travels_with_the_answer(
    client: TestClient,
) -> None:
    """CC BY requires it, and a notice only in the README is not with the data.

    A refactor can drop a field without anything failing, and a dropped
    attribution is a licence violation rather than a cosmetic loss.
    """
    sources = {
        source["code"]: source for source in client.get(ADDRESS).json()["sources"]
    }

    assert "openbible" in sources
    assert sources["openbible"]["rights"] == "CC BY 4.0"
    assert "OpenBible.info" in sources["openbible"]["attribution"]
    assert sources["openbible"]["url"]


def test_only_the_sources_this_answer_drew_on_come_back(client: TestClient) -> None:
    body = client.get(ADDRESS).json()
    drawn = {row["source"] for row in body["references"]}

    assert {source["code"] for source in body["sources"]} == drawn


def test_the_ave_maria_apparatus_is_not_served(client: TestClient) -> None:
    """Excluded at the export, so it cannot reach a response by any route."""
    body = client.get(ADDRESS).json()

    assert "ave-maria" not in {source["code"] for source in body["sources"]}


def test_a_curated_reference_outranks_the_open_tail(client: TestClient) -> None:
    """Weight orders the answer and never reaches the wire."""
    references = client.get(ADDRESS).json()["references"]

    assert references[0]["source"] == "douay"
    assert "weight" not in references[0]
    assert references[0]["primary"] is True


def test_at_most_thirty_references_per_address(client: TestClient) -> None:
    """Genesis 1:1 carries more than sixty strong ones."""
    assert len(client.get(ADDRESS).json()["references"]) == 30


def test_the_deuterocanonical_link_exists_in_both_directions(
    client: TestClient,
) -> None:
    """The whole reason `na27` ships.

    OpenBible carries 204601 references and not one of them reaches a
    deuterocanonical book. Matthew quoting Wisdom is a connection a Catholic
    reader needs and the largest available set does not have.
    """
    forward = client.get("/v1/cross-references", params={"ref": "Mt 4,4"}).json()
    backward = client.get("/v1/books/WIS/chapters/16/verses/26/cross-references").json()

    assert "WIS.16.26" in {row["to"] for row in forward["references"]}
    assert "MAT.4.4" in {row["to"] for row in backward["references"]}


def test_a_whole_chapter_reference_says_so(client: TestClient) -> None:
    """1062 of them. It anchors on verse 1 and the flag is what says which."""
    body = client.get("/v1/books/GEN/chapters/1/verses/6/cross-references").json()
    chapters = [row for row in body["references"] if row["whole_chapter"]]

    assert chapters
    assert chapters[0]["to"].endswith(".1")


def test_a_lectionary_reference_answers_only_for_the_verses_it_asked_for(
    client: TestClient,
) -> None:
    body = client.get("/v1/cross-references", params={"ref": "Mc 5,22-24.35-43"}).json()

    assert not {row["id"] for row in body["references"]} - set(body["ids"])


def test_an_address_with_no_reference_is_200_and_empty(client: TestClient) -> None:
    """9119 of 35845 addresses have none. Absence is an answer."""
    body = client.get("/v1/books/GEN/chapters/1/verses/8/cross-references").json()

    assert body["references"] == []
    assert body["sources"] == []


def test_a_verse_the_spine_does_not_have_is_404(client: TestClient) -> None:
    found = client.get("/v1/books/GEN/chapters/1/verses/999/cross-references")

    assert found.status_code == 404
    assert found.json()["detail"]["reason"] == "not_on_spine"


def test_an_unresolvable_reference_is_422(client: TestClient) -> None:
    found = client.get("/v1/cross-references", params={"ref": "Habakuk 3,2"})

    assert found.status_code == 422
    assert found.json()["detail"]["reason"] == "unknown_book"


def test_the_scheme_parameter_reaches_this_route_too(client: TestClient) -> None:
    found = client.get(
        "/v1/cross-references", params={"ref": "Sl 51,1", "scheme": "org"}
    )

    assert found.status_code == 200
    assert found.json()["ids"] == ["PSA.50.1"]


def test_the_answer_is_not_cached_as_immutable(client: TestClient) -> None:
    """Every reference in it is written in the default version's notation."""
    assert client.get(ADDRESS).headers["cache-control"] == "public, max-age=3600"
