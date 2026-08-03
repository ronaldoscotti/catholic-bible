"""The commentary routes, over HTTP.

Two shapes, one by address and one by written reference, and neither takes a
version. A note on John 3:16 is the same note under any translation, so a
version segment would be a claim about what the answer depends on.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

ADDRESS = "/v1/books/JHN/chapters/3/verses/16/commentary"


def test_a_verse_answers_with_its_note_in_both_languages(client: TestClient) -> None:
    found = client.get(ADDRESS)

    assert found.status_code == 200
    body = found.json()
    assert body["ids"] == ["JHN.3.16"]
    assert body["reference"] == "Jo 3,16"

    source = body["sources"][0]
    assert source["code"] == "haydock"
    assert {entry["language"] for entry in source["entries"][0]["bodies"]} == {
        "en-US",
        "pt-BR",
    }


def test_the_note_says_it_was_machine_translated(client: TestClient) -> None:
    """The provenance travels with the data rather than only in the README.

    A consumer reading the API and never opening the repository still has to be
    able to tell that the Portuguese was produced by a model.
    """
    rights = client.get(ADDRESS).json()["sources"][0]["rights"]

    assert rights["text"] == "public-domain"
    assert rights["translation"] == "machine"
    assert "language model" in rights["translation_basis"]


def test_a_spanning_note_carries_the_span_it_covers(client: TestClient) -> None:
    """The note on John 3:16 runs to 17 and says so, rather than claiming one."""
    entry = client.get(ADDRESS).json()["sources"][0]["entries"][0]

    assert entry["start"] == "JHN.3.16"
    assert entry["end"] == "JHN.3.17"
    assert entry["reference"] == "Jo 3,16-17"
    assert entry["label"]


def test_the_body_carries_markup_and_the_same_body_without_it(
    client: TestClient,
) -> None:
    body = client.get(ADDRESS).json()["sources"][0]["entries"][0]["bodies"][0]

    assert "<em>" in body["html"]
    assert "<" not in body["text"]


def test_an_address_with_no_note_is_200_and_empty(client: TestClient) -> None:
    """Absence of commentary is an answer. 14803 addresses have none."""
    found = client.get("/v1/books/GEN/chapters/1/verses/5/commentary")

    assert found.status_code == 200
    assert found.json()["sources"] == []


def test_a_reference_reads_a_range(client: TestClient) -> None:
    found = client.get("/v1/commentary", params={"ref": "Mc 5,22-24"})

    assert found.status_code == 200
    body = found.json()
    assert body["ids"] == ["MRK.5.22", "MRK.5.23", "MRK.5.24"]


def test_a_note_covering_a_range_comes_back_once(client: TestClient) -> None:
    """Once per note, not once per address the note covers."""
    body = client.get("/v1/commentary", params={"ref": "Jo 3,16-17"}).json()
    starts = [entry["start"] for entry in body["sources"][0]["entries"]]

    assert len(starts) == len(set(starts))


def test_the_scheme_parameter_reaches_this_route_too(client: TestClient) -> None:
    """`Sl 51,1` under `org` is the Miserere, which is 50 on this spine."""
    found = client.get("/v1/commentary", params={"ref": "Sl 51,1", "scheme": "org"})

    assert found.status_code == 200
    assert found.json()["ids"] == ["PSA.50.1"]


def test_the_accented_book_still_lands_in_the_right_one(client: TestClient) -> None:
    john = client.get("/v1/commentary", params={"ref": "Jo 3,16"})
    job = client.get("/v1/commentary", params={"ref": "Jó 3,16"})

    assert john.json()["ids"] == ["JHN.3.16"]
    assert job.json()["ids"] == ["JOB.3.16"]


def test_a_verse_the_spine_does_not_have_is_404(client: TestClient) -> None:
    found = client.get("/v1/books/JHN/chapters/3/verses/999/commentary")

    assert found.status_code == 404
    assert found.json()["detail"]["reason"] == "not_on_spine"


def test_an_unknown_book_is_404(client: TestClient) -> None:
    found = client.get("/v1/books/Habakuk/chapters/3/verses/2/commentary")

    assert found.status_code == 404
    assert found.json()["detail"]["reason"] == "unknown_book"


def test_the_case_of_the_code_still_carries_meaning(client: TestClient) -> None:
    """`JUD` is Jude and `Jud` is Judith, on this route as on the reading ones."""
    jude = client.get("/v1/books/JUD/chapters/1/verses/1/commentary")
    judith = client.get("/v1/books/Jud/chapters/1/verses/1/commentary")

    assert jude.json()["ids"] == ["JUD.1.1"]
    assert judith.json()["ids"] == ["JDT.1.1"]


def test_an_unresolvable_reference_is_422(client: TestClient) -> None:
    found = client.get("/v1/commentary", params={"ref": "Habakuk 3,2"})

    assert found.status_code == 422
    assert found.json()["detail"]["reason"] == "unknown_book"


def test_the_answer_is_not_cached_as_immutable(client: TestClient) -> None:
    """Every reference in it is written in the default version's notation.

    Which version is the default is not in the URL, so a year of immutable is a
    year nothing can invalidate. Same reason `/v1/resolve` is not immutable.
    """
    assert client.get(ADDRESS).headers["cache-control"] == "public, max-age=3600"
