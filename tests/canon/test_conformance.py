"""The conformance corpus runs here.

One test parameterized over the file. A new case is data and never a new test
function, which is what keeps the bar of entry at writing down why the case is
hard rather than at writing Python.
"""

import tomllib
from pathlib import Path
from typing import Any

import pytest

from catholic_bible.canon.aliases import ALIASES
from catholic_bible.canon.mapping import Mapped, Orphan, Scheme, map_address
from catholic_bible.canon.reference import Reference, UnparsedReference, parse_reference

CORPUS = Path(__file__).resolve().parent.parent / "conformance" / "corpus.toml"
CASES: list[dict[str, Any]] = tomllib.loads(CORPUS.read_text(encoding="utf-8"))["case"]

REQUIRED = {"id", "kind", "input", "expect", "provenance", "why_hard"}


def identify(case: dict[str, Any]) -> str:
    return str(case["id"])


@pytest.mark.parametrize("case", CASES, ids=identify)
def test_every_case_records_why_it_is_hard(case: dict[str, Any]) -> None:
    assert REQUIRED <= set(case), sorted(REQUIRED - set(case))
    assert len(case["why_hard"].strip()) > 40, "a note nobody can use is not a note"
    assert case["provenance"].strip()


def test_case_ids_are_unique() -> None:
    ids = [case["id"] for case in CASES]
    assert len(set(ids)) == len(ids)


def test_the_epic_minimum_is_covered() -> None:
    """The list the epic names, each tied to the case that answers it."""
    required = {
        "miserere-from-org",
        "susanna",
        "bel-second-verse-is-not",
        "greek-esther",
        "the-prayer-of-solomon",
        "joel-in-douay",
        "malachi-in-douay",
        "the-chronicles-genealogy",
        "john-three-sixteen",
        "job-three-sixteen",
    }
    assert required <= {case["id"] for case in CASES}


@pytest.mark.parametrize("case", [c for c in CASES if c["kind"] == "map"], ids=identify)
def test_a_mapping_case(case: dict[str, Any]) -> None:
    book, rest = case["input"].split(" ", 1)
    chapter, verse = (int(part) for part in rest.split(":", 1))
    result = map_address(Scheme(case["scheme"]), book, chapter, verse)

    expected = case["expect"]
    if expected.startswith("orphan:"):
        assert isinstance(result, Orphan), result
        assert result.reason.value == expected.removeprefix("orphan:")
    else:
        assert isinstance(result, Mapped), result
        assert str(result.verse) == expected


@pytest.mark.parametrize(
    "case", [c for c in CASES if c["kind"] == "reference"], ids=identify
)
def test_a_reference_case(case: dict[str, Any]) -> None:
    parsed = parse_reference(case["input"])
    expected = case["expect"]

    if expected.startswith("error:"):
        assert isinstance(parsed, UnparsedReference), parsed
        assert parsed.reason == expected.removeprefix("error:")
        return

    assert isinstance(parsed, Reference), parsed
    book, span = expected.split(" ", 1)
    assert parsed.book == book
    assert parsed.bounds == _span(span)

    if "parts" in case:
        assert parsed.spans() == tuple(_span(p) for p in case["parts"].split(","))


@pytest.mark.parametrize(
    "case", [c for c in CASES if c["kind"] == "alias"], ids=identify
)
def test_an_alias_case(case: dict[str, Any]) -> None:
    assert ALIASES.resolve(case["input"]) == case["expect"]


def _span(text: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start, end = text.split("-", 1)
    return _point(start), _point(end)


def _point(text: str) -> tuple[int, int]:
    chapter, verse = text.split(":", 1)
    return int(chapter), int(verse)
