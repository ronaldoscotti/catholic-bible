"""Writing a reference back out, in three languages."""

from __future__ import annotations

import pytest

from catholic_bible.canon.aliases import Language
from catholic_bible.canon.formatter import (
    abbreviation_for,
    format_chapter,
    format_reference,
)
from catholic_bible.canon.reference import Reference, parse_reference


def written(text: str, language: Language = Language.PT) -> str:
    parsed = parse_reference(text)
    assert isinstance(parsed, Reference), text
    return format_reference(parsed, language)


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        (Language.PT, "Jo 3,16"),
        (Language.EN, "John 3:16"),
        (Language.LA, "Ioan. 3,16"),
    ],
)
def test_one_verse_in_each_language(language: Language, expected: str) -> None:
    assert written("Jo 3,16", language) == expected


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        (Language.PT, "Eclo 24,1"),
        (Language.EN, "Ecclus. 24:1"),
        (Language.LA, "Eccli. 24,1"),
    ],
)
def test_the_book_the_roadmap_promises(language: Language, expected: str) -> None:
    """Sirach 24:1 is the verse the v1 gate names, so it is written out here."""
    assert written("Eclo 24,1", language) == expected


def test_a_range_inside_one_chapter() -> None:
    assert written("1Cor 13,4-7") == "1Cor 13,4-7"
    assert written("1Cor 13,4-7", Language.EN) == "1 Cor. 13:4-7"
    assert written("1Cor 13,4-7", Language.LA) == "I Cor. 13,4-7"


def test_a_range_crossing_a_chapter_reprints_the_chapter() -> None:
    assert written("Ex 13,1-14,5") == "Ex 13,1-14,5"
    assert written("Ex 13,1-14,5", Language.EN) == "Ex. 13:1-14:5"


def test_disjoint_parts_reprint_the_chapter_only_when_it_changes() -> None:
    assert written("Mc 5,22-24.35-43") == "Mc 5,22-24.35-43"
    assert written("Mc 5,22-24.35-43", Language.EN) == "Mark 5:22-24.35-43"


def test_a_whole_chapter_carries_no_verse() -> None:
    assert written("Sl 23") == "Sl 23"
    assert written("Sl 23", Language.EN) == "Ps. 23"
    assert format_chapter("PSA", 50, Language.LA) == "Ps. 50"


def test_a_reference_survives_a_round_trip() -> None:
    """Formatting has to produce something the parser reads back to the same thing.

    A string that renders nicely and does not parse is a deep link that breaks
    when a reader copies it out of one response and into another request.
    """
    for text in ("Jo 3,16", "1Cor 13,4-7", "Ex 13,1-14,5", "Mc 5,22-24.35-43", "Sl 23"):
        first = parse_reference(text)
        assert isinstance(first, Reference)
        again = parse_reference(format_reference(first, Language.PT))
        assert again == first, text


def test_the_english_round_trip_survives_the_colon() -> None:
    """The parser accepts both separators, which is what makes English work."""
    for text in ("John 3:16", "1 Cor. 13:4-7", "Ex. 13:1-14:5"):
        parsed = parse_reference(text)
        assert isinstance(parsed, Reference), text
        assert format_reference(parsed, Language.EN) == text


def test_an_unknown_book_falls_back_to_its_code() -> None:
    """Degrade rather than raise. Every book has all three today.

    It is the fallback the original has, and the code is a worse label than a
    name and a better one than a crash.
    """
    assert abbreviation_for("XYZ", Language.EN) == "XYZ"
    assert abbreviation_for("XYZ", Language.PT) == "XYZ"


def test_no_em_dash_reaches_a_formatted_reference() -> None:
    """The original prints an em dash across a chapter boundary and this does not.

    The comma in the second half already says a chapter follows, so the longer
    dash carries nothing, and the plain hyphen is what the parser reads back.
    """
    written_out = written("Ex 13,1-14,5")
    assert "—" not in written_out
    assert "–" not in written_out
