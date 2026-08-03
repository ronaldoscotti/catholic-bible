"""Resolving a written reference, and reading a passage across versions."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_a_single_verse_resolves(client: TestClient) -> None:
    found = client.get("/v1/resolve", params={"ref": "Jo 3,16"}).json()
    assert found == {
        "reference": "Jo 3,16",
        "book": "JHN",
        "ids": ["JHN.3.16"],
        "preview": found["preview"],
    }
    assert found["preview"].startswith("Porque Deus amou de tal modo")


def test_a_range_resolves_to_every_address_in_it(client: TestClient) -> None:
    found = client.get("/v1/resolve", params={"ref": "1Cor 13,4-7"}).json()
    assert found["ids"] == ["1CO.13.4", "1CO.13.5", "1CO.13.6", "1CO.13.7"]
    assert found["reference"] == "1Cor 13,4-7"


def test_a_range_crossing_a_chapter_resolves(client: TestClient) -> None:
    """Criterion 3. The last verse of one chapter and the first of the next."""
    found = client.get("/v1/resolve", params={"ref": "Ex 13,21-14,2"}).json()
    assert found["ids"][:2] == ["EXO.13.21", "EXO.13.22"]
    assert found["ids"][2:] == ["EXO.14.1", "EXO.14.2"]


def test_a_disjoint_reference_unions_its_parts(client: TestClient) -> None:
    found = client.get("/v1/resolve", params={"ref": "Mc 5,22-24.35-37"}).json()
    assert found["ids"] == [
        "MRK.5.22",
        "MRK.5.23",
        "MRK.5.24",
        "MRK.5.35",
        "MRK.5.36",
        "MRK.5.37",
    ]


def test_the_scheme_decides_which_psalm_the_reader_meant(client: TestClient) -> None:
    """`Sl 51,1` is two different verses and both answers are correct.

    Without the parameter it resolves onto the spine and the reader who wanted
    the Miserere gets the next psalm, with a 200 and nothing said. This is the
    failure the roadmap opens by naming.
    """
    spine = client.get("/v1/resolve", params={"ref": "Sl 51,1"}).json()
    assert spine["ids"] == ["PSA.51.1"]

    org = client.get("/v1/resolve", params={"ref": "Sl 51,1", "scheme": "org"}).json()
    assert org["ids"] == ["PSA.50.1"]

    vulgate = client.get(
        "/v1/resolve", params={"ref": "Sl 50,1", "scheme": "vulgate"}
    ).json()
    assert vulgate["ids"] == ["PSA.50.1"]


def test_an_address_that_orphans_under_a_scheme_says_which_reason(
    client: TestClient,
) -> None:
    found = client.get("/v1/resolve", params={"ref": "Sl 151,1", "scheme": "org"})
    assert found.status_code == 422
    assert found.json()["detail"]["reason"] == "chapter_out_of_range"

    # And the psalm that does have a counterpart is not refused with it.
    fine = client.get("/v1/resolve", params={"ref": "Sl 147,1", "scheme": "org"})
    assert fine.status_code == 200
    assert fine.json()["ids"] == ["PSA.146.1"]


def test_a_malformed_reference_is_refused_with_a_reason(client: TestClient) -> None:
    found = client.get("/v1/resolve", params={"ref": "!!!"})
    assert found.status_code == 422
    assert found.json()["detail"]["reason"] == "malformed"


def test_an_unknown_book_in_a_query_is_unprocessable_rather_than_missing(
    client: TestClient,
) -> None:
    """A path names a resource and a query carries what somebody typed."""
    found = client.get("/v1/resolve", params={"ref": "Habakuk 3,2"})
    assert found.status_code == 422
    assert found.json()["detail"] == {
        "reason": "unknown_book",
        "message": "no book named 'Habakuk'",
        "input": "Habakuk 3,2",
    }


def test_a_whole_chapter_is_refused_and_points_at_the_chapter_route(
    client: TestClient,
) -> None:
    """`Ex 13-14` parses as chapter 13 with chapter 14 dropped.

    Answering it would be a 200 returning less than was asked for, which is
    worse than an absent answer because nothing tells the caller.
    """
    for ref in ("Sl 23", "Ex 13-14"):
        found = client.get("/v1/resolve", params={"ref": ref})
        assert found.status_code == 422, ref
        assert found.json()["detail"]["reason"] == "whole_chapter"


def test_a_span_wider_than_the_cap_is_refused(client: TestClient) -> None:
    found = client.get("/v1/resolve", params={"ref": "Sl 1,1-40,1"})
    assert found.status_code == 422
    assert found.json()["detail"]["reason"] == "range_too_large"


def test_the_cap_is_a_span_and_not_a_count(client: TestClient) -> None:
    """Ported as it stands. A disjoint pair far apart is refused on two verses.

    Two verses is not a large response. The rule measures the distance between
    the ends, which is the behaviour being ported, so it is pinned rather than
    quietly improved.
    """
    found = client.get("/v1/resolve", params={"ref": "Sl 1,1.60,1"})
    assert found.status_code == 422
    assert found.json()["detail"]["reason"] == "range_too_large"


def test_a_passage_defaults_to_the_default_version(client: TestClient) -> None:
    found = client.get("/v1/passage", params={"ref": "Jo 3,16"}).json()
    assert found["versions"] == ["matos-soares"]
    assert found["verses"][0]["texts"][0]["version"] == "matos-soares"


def test_a_passage_aligns_every_requested_version(client: TestClient) -> None:
    found = client.get(
        "/v1/passage",
        params={"ref": "Jo 3,16-17", "versions": "matos-soares,douay-rheims"},
    ).json()

    assert found["reference"] == "Jo 3,16-17"
    assert [verse["id"] for verse in found["verses"]] == ["JHN.3.16", "JHN.3.17"]
    for verse in found["verses"]:
        assert [text["version"] for text in verse["texts"]] == [
            "matos-soares",
            "douay-rheims",
        ]


def test_a_version_without_the_verse_is_a_null_and_never_a_short_column(
    client: TestClient,
) -> None:
    """`PSA.150.6` is blank upstream in Douay and B2 omitted it.

    The column has to stay in place. A shorter one slides two rendered
    translations against each other and nothing anywhere says so.
    """
    found = client.get(
        "/v1/passage",
        params={
            "ref": "Sl 150,5-6",
            "versions": "matos-soares,douay-rheims,vulgata-clementina",
        },
    ).json()

    last = found["verses"][-1]
    assert last["id"] == "PSA.150.6"
    assert [text["version"] for text in last["texts"]] == [
        "matos-soares",
        "douay-rheims",
        "vulgata-clementina",
    ]
    assert last["texts"][1]["text"] is None
    assert last["texts"][0]["text"] is not None
    assert last["texts"][2]["text"] is not None


def test_the_reference_follows_the_first_requested_version(
    client: TestClient,
) -> None:
    found = client.get(
        "/v1/passage", params={"ref": "Eclo 24,1", "versions": "douay-rheims"}
    ).json()
    assert found["reference"] == "Ecclus. 24:1"
    assert found["verses"][0]["reference"] == "Ecclus. 24:1"


def test_an_unknown_version_in_a_passage_is_a_404(client: TestClient) -> None:
    found = client.get(
        "/v1/passage", params={"ref": "Jo 3,16", "versions": "king-james"}
    )
    assert found.status_code == 404
    assert found.json()["detail"]["reason"] == "unknown_version"


def test_a_passage_crosses_a_book_boundary(client: TestClient) -> None:
    found = client.get("/v1/passage", params={"ref": "Ml 3,23-24"}).json()
    assert [verse["id"] for verse in found["verses"]] == ["MAL.3.23", "MAL.3.24"]
