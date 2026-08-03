"""The reading routes, through HTTP."""

from __future__ import annotations

from fastapi.testclient import TestClient

from catholic_bible.api.routes import CATALOGUE, IMMUTABLE


def test_the_versions_are_listed_with_the_default_first(client: TestClient) -> None:
    found = client.get("/v1/versions").json()
    assert [row["code"] for row in found] == [
        "matos-soares",
        "douay-rheims",
        "vulgata-clementina",
    ]
    assert found[0]["default"] is True
    assert sum(row["default"] for row in found) == 1
    assert found[0]["rights"]["text"] == "public-domain"


def test_the_version_list_is_not_cached_forever(client: TestClient) -> None:
    """It grows with every translation. A year of immutable hides the fourth."""
    assert client.get("/v1/versions").headers["cache-control"] == CATALOGUE
    assert (
        client.get("/v1/versions/matos-soares/books").headers["cache-control"]
        == CATALOGUE
    )


def test_verse_text_is_cached_forever(client: TestClient) -> None:
    response = client.get("/v1/versions/matos-soares/books/JHN/chapters/3")
    assert response.headers["cache-control"] == IMMUTABLE


def test_books_come_back_in_the_language_of_the_version(client: TestClient) -> None:
    def name_of(version: str, code: str) -> tuple[str, str]:
        books = client.get(f"/v1/versions/{version}/books").json()
        found = next(row for row in books if row["code"] == code)
        return found["name"], found["abbreviation"]

    assert name_of("matos-soares", "SIR") == ("Eclesiástico", "Eclo")
    assert name_of("douay-rheims", "SIR") == ("Ecclesiasticus", "Ecclus.")
    assert name_of("vulgata-clementina", "SIR") == ("Ecclesiasticus", "Eccli.")


def test_the_douay_reckoning_of_kings_reaches_the_wire(client: TestClient) -> None:
    books = client.get("/v1/versions/douay-rheims/books").json()
    named = {row["code"]: row["name"] for row in books}
    assert named["1SA"] == "1 Kings"
    assert named["1KI"] == "3 Kings"


def test_the_listing_is_what_the_version_reaches_and_not_the_raw_canon(
    client: TestClient,
) -> None:
    """All three reach all 73 today, so this pins that rather than the filter.

    A version arriving without the deuterocanonicals is what the filter is for,
    and none exists yet. Saying so beats a test that reads as if one did.
    """
    for version in ("matos-soares", "douay-rheims", "vulgata-clementina"):
        books = client.get(f"/v1/versions/{version}/books").json()
        assert len(books) == 73, version


def test_a_chapter_carries_its_neighbours(client: TestClient) -> None:
    found = client.get("/v1/versions/matos-soares/books/JHN/chapters/3").json()
    assert found["previous"] == {"book": "JHN", "chapter": 2}
    assert found["next"] == {"book": "JHN", "chapter": 4}
    assert len(found["verses"]) == 36


def test_the_first_chapter_of_the_canon_has_no_previous(client: TestClient) -> None:
    found = client.get("/v1/versions/matos-soares/books/GEN/chapters/1").json()
    assert found["previous"] is None


def test_the_last_chapter_of_the_canon_has_no_next(client: TestClient) -> None:
    found = client.get("/v1/versions/matos-soares/books/REV/chapters/22").json()
    assert found["next"] is None


def test_a_neighbour_crosses_a_book_boundary(client: TestClient) -> None:
    """Malachi ends the Old Testament at chapter 3 on this spine."""
    found = client.get("/v1/versions/matos-soares/books/MAT/chapters/1").json()
    assert found["previous"] == {"book": "MAL", "chapter": 3}

    back = client.get("/v1/versions/matos-soares/books/MAL/chapters/3").json()
    assert back["next"] == {"book": "MAT", "chapter": 1}


def test_the_psalter_carries_both_numbers(client: TestClient) -> None:
    def numbering(psalm: int) -> object:
        found = client.get(
            f"/v1/versions/matos-soares/books/PSA/chapters/{psalm}"
        ).json()
        return found["numbering"]

    assert numbering(50) == {"scheme": "org", "counterpart": "51"}
    assert numbering(9) == {"scheme": "org", "counterpart": "9-10"}
    assert numbering(113) == {"scheme": "org", "counterpart": "114-115"}
    assert numbering(114) == {"scheme": "org", "counterpart": "116"}
    assert numbering(115) == {"scheme": "org", "counterpart": "116"}
    assert numbering(3) is None, "psalms 1 to 8 agree, so there is nothing to say"


def test_only_the_psalter_carries_numbering(client: TestClient) -> None:
    found = client.get("/v1/versions/matos-soares/books/JHN/chapters/3").json()
    assert found["numbering"] is None


def test_a_verse_carries_its_reference_in_the_right_notation(
    client: TestClient,
) -> None:
    def read(version: str) -> dict[str, str]:
        found: dict[str, str] = client.get(
            f"/v1/versions/{version}/books/JHN/chapters/3/verses/16"
        ).json()
        return found

    assert read("matos-soares")["reference"] == "Jo 3,16"
    assert read("douay-rheims")["reference"] == "John 3:16"
    assert read("vulgata-clementina")["reference"] == "Ioan. 3,16"
    assert read("matos-soares")["id"] == "JHN.3.16"


def test_a_book_can_be_named_by_any_form_that_resolves(client: TestClient) -> None:
    for written in ("PSA", "Sl", "Salmos", "Psalms", "Ps."):
        found = client.get(
            f"/v1/versions/matos-soares/books/{written}/chapters/50/verses/3"
        )
        assert found.status_code == 200, written
        assert found.json()["id"] == "PSA.50.3"


def test_jo_and_job_are_different_books_behind_a_url(client: TestClient) -> None:
    """The accent has to survive the encoder. It is why this repo exists."""
    john = client.get("/v1/versions/matos-soares/books/Jo/chapters/3/verses/16")
    job = client.get("/v1/versions/matos-soares/books/Jó/chapters/3/verses/16")
    assert john.json()["book"] == "JHN"
    assert job.json()["book"] == "JOB"


def test_the_code_boundary_is_case_sensitive(client: TestClient) -> None:
    """`JUD` is Jude the code and `Jud` is how a Portuguese reader writes Judite."""
    jude = client.get("/v1/versions/matos-soares/books/JUD/chapters/1/verses/1")
    judith = client.get("/v1/versions/matos-soares/books/Jud/chapters/1/verses/1")
    assert jude.json()["book"] == "JUD"
    assert judith.json()["book"] == "JDT"


def test_a_whole_book_is_grouped_by_chapter(client: TestClient) -> None:
    found = client.get("/v1/versions/matos-soares/books/JON").json()
    assert [chapter["chapter"] for chapter in found["chapters"]] == [1, 2, 3, 4]
    assert found["book"]["code"] == "JON"
    assert found["chapters"][0]["verses"][0]["id"] == "JON.1.1"


def test_an_unknown_version_is_a_404_saying_so(client: TestClient) -> None:
    found = client.get("/v1/versions/king-james/books")
    assert found.status_code == 404
    assert found.json()["detail"]["reason"] == "unknown_version"


def test_an_unknown_book_is_a_404_saying_so(client: TestClient) -> None:
    found = client.get("/v1/versions/matos-soares/books/Habakuk/chapters/3")
    assert found.status_code == 404
    assert found.json()["detail"] == {
        "reason": "unknown_book",
        "message": "no book named 'Habakuk'",
        "input": "Habakuk",
    }


def test_a_chapter_off_the_spine_is_not_the_same_as_an_unpublished_one(
    client: TestClient,
) -> None:
    """The distinction the whole taxonomy exists for.

    Malachi 4 is printed in most English editions and is not on this spine, so
    it does not exist. `PSA.150.6` does exist and Douay does not carry it, and a
    caller has to be able to tell those apart.
    """
    absent = client.get("/v1/versions/douay-rheims/books/MAL/chapters/4")
    assert absent.status_code == 404
    assert absent.json()["detail"]["reason"] == "not_on_spine"

    unfilled = client.get("/v1/versions/douay-rheims/books/PSA/chapters/150/verses/6")
    assert unfilled.status_code == 404
    assert unfilled.json()["detail"]["reason"] == "unpublished_in_version"

    published = client.get("/v1/versions/matos-soares/books/PSA/chapters/150/verses/6")
    assert published.status_code == 200


def test_a_verse_past_the_end_of_a_chapter_is_not_on_the_spine(
    client: TestClient,
) -> None:
    found = client.get("/v1/versions/matos-soares/books/JHN/chapters/3/verses/99")
    assert found.status_code == 404
    assert found.json()["detail"]["reason"] == "not_on_spine"
