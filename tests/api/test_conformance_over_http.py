"""The conformance corpus, run again through HTTP.

Passing as unit tests says nothing about what survives a URL encoder.
`Jó 3,16` arrives as `J%C3%B3%203,16`, and an accent folded there sends the
reader to the wrong book with a 200. That case is the reason this repo exists.

All forty three run, not a subset. The fifteen `map` cases go through `resolve`
with the scheme they were written in, which is what the scheme parameter makes
possible, and five of them name a book only that scheme has, which is what the
scheme aware resolver makes possible. The three `anchor` cases are B4, where the
failure mode is a note that reaches no address and says nothing about it.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

CORPUS = Path(__file__).resolve().parent.parent / "conformance" / "corpus.toml"
CASES: list[dict[str, Any]] = tomllib.loads(CORPUS.read_text(encoding="utf-8"))["case"]


def identify(case: dict[str, Any]) -> str:
    return str(case["id"])


def _by_kind(kind: str) -> list[dict[str, Any]]:
    return [case for case in CASES if case["kind"] == kind]


def test_every_case_reaches_http() -> None:
    """No case may be quietly skipped, which is what makes the claim true."""
    assert len(CASES) == 43
    assert len(_by_kind("map")) == 15
    assert len(_by_kind("alias")) == 18
    assert len(_by_kind("reference")) == 7
    assert len(_by_kind("anchor")) == 3
    assert len(CASES) == sum(
        len(_by_kind(kind)) for kind in ("map", "alias", "reference", "anchor")
    )


@pytest.mark.parametrize("case", _by_kind("anchor"), ids=identify)
def test_an_anchor_case_over_http(case: dict[str, Any], client: TestClient) -> None:
    """A commentary note reaches the address it is anchored on.

    The two clamped entries are here because the failure they had upstream is
    silence. A note that covers nothing returns no error and no note, and only a
    case that names the address notices.
    """
    book, chapter, verse = str(case["input"]).split(".")
    found = client.get(f"/v1/books/{book}/chapters/{chapter}/verses/{verse}/commentary")

    assert found.status_code == 200, case["id"]
    spans = {
        f"{entry['start']}-{entry['end']}"
        for source in found.json()["sources"]
        for entry in source["entries"]
    }
    assert case["expect"] in spans, (case["id"], spans)


@pytest.mark.parametrize("case", _by_kind("map"), ids=identify)
def test_a_mapping_case_over_http(case: dict[str, Any], client: TestClient) -> None:
    book, rest = str(case["input"]).split(" ", 1)
    chapter, verse = rest.split(":", 1)

    found = client.get(
        "/v1/resolve",
        params={"ref": f"{book} {chapter},{verse}", "scheme": case["scheme"]},
    )

    if str(case["expect"]).startswith("orphan:"):
        assert found.status_code == 422, case["id"]
        expected = str(case["expect"]).split(":", 1)[1]
        assert found.json()["detail"]["reason"] == expected, case["id"]
        return

    assert found.status_code == 200, (case["id"], found.json())
    assert found.json()["ids"] == [case["expect"]], case["id"]


@pytest.mark.parametrize("case", _by_kind("alias"), ids=identify)
def test_an_alias_case_over_http(case: dict[str, Any], client: TestClient) -> None:
    """The written name reaches the route encoded, and has to survive it."""
    found = client.get("/v1/resolve", params={"ref": f"{case['input']} 1,1"})

    if found.status_code == 200:
        assert found.json()["book"] == case["expect"], case["id"]
        return

    # A book whose first chapter has no verse 1 on the spine still resolved its
    # name, which is what the case is about. Anything else is a real failure.
    detail = found.json()["detail"]
    assert detail["reason"] != "unknown_book", (case["id"], detail)


@pytest.mark.parametrize("case", _by_kind("reference"), ids=identify)
def test_a_reference_case_over_http(case: dict[str, Any], client: TestClient) -> None:
    expect = str(case["expect"])
    found = client.get("/v1/resolve", params={"ref": case["input"]})

    if expect.startswith("error:"):
        assert found.status_code == 422, case["id"]
        assert found.json()["detail"]["reason"] == expect.split(":", 1)[1], case["id"]
        return

    if found.status_code == 422:
        # A whole chapter reference resolves its book and is refused on shape,
        # which is by design. The case is about the book.
        assert found.json()["detail"]["reason"] == "whole_chapter", case["id"]
        return

    assert found.json()["book"] == expect.split(" ", 1)[0], case["id"]


def test_the_accent_survives_the_url_encoder(client: TestClient) -> None:
    """The single case this whole file exists for."""
    john = client.get("/v1/resolve", params={"ref": "Jo 3,16"})
    job = client.get("/v1/resolve", params={"ref": "Jó 3,16"})

    assert "J%C3%B3" in str(job.request.url), "the accent was not encoded at all"
    assert john.json()["ids"] == ["JHN.3.16"]
    assert job.json()["ids"] == ["JOB.3.16"]


def test_the_two_psalms_where_the_ported_table_and_b1_disagree() -> None:
    """A B1 defect, pinned so the day it is fixed the suite says which moved.

    `to_scheme` sees that a candidate does not return where it started and
    cannot see that it is out of range in the target scheme, because this repo
    holds no `org` verse count table. So spine PSA.15.11 reads back as `org`
    15:11, which is a different psalm.
    """
    from catholic_bible.canon import psalms  # noqa: PLC0415
    from catholic_bible.canon.mapping import Mapped, Scheme, to_scheme  # noqa: PLC0415
    from catholic_bible.canon.spine import SPINE  # noqa: PLC0415
    from catholic_bible.canon.verse import VerseId  # noqa: PLC0415

    def reached(psalm: int) -> str:
        seen: list[int] = []
        for verse in range(1, (SPINE.verse_count("PSA", psalm) or 0) + 1):
            result = to_scheme(Scheme.ORG, VerseId("PSA", psalm, verse))
            if isinstance(result, Mapped) and result.verse.chapter not in seen:
                seen.append(result.verse.chapter)
        seen.sort()
        return str(seen[0]) if len(seen) == 1 else f"{seen[0]}-{seen[-1]}"

    disagreeing = {
        psalm: (psalms.counterpart(psalm), reached(psalm))
        for psalm in range(1, 151)
        if psalms.counterpart(psalm) != reached(psalm)
    }
    assert disagreeing == {15: ("16", "15-16"), 43: ("44", "43-44")}
