import pytest

from catholic_bible.canon.books import CANON
from catholic_bible.canon.spine import SPINE

# Measured from the frozen data. Asserted rather than computed so a change in
# the export moves a number here instead of passing quietly.
TOTAL_ADDRESSES = 35845


def test_the_spine_covers_every_book_of_the_canon() -> None:
    assert {book.code for book in CANON} == set(SPINE.books())


def test_the_psalter_follows_the_vulgate() -> None:
    """150 psalms, and the Miserere numbered 50 with 21 verses."""
    assert SPINE.chapter_count("PSA") == 150
    assert SPINE.verse_count("PSA", 50) == 21


def test_daniel_has_susanna_and_bel() -> None:
    assert SPINE.chapter_count("DAN") == 14


def test_esther_carries_the_greek_additions_as_chapters() -> None:
    assert SPINE.chapter_count("EST") == 16


def test_the_first_chronicles_genealogy_is_the_vulgate_length() -> None:
    assert SPINE.verse_count("1CH", 6) == 81


@pytest.mark.parametrize(("code", "chapters"), [("JOL", 4), ("MAL", 3)])
def test_the_spine_is_mixed_and_these_two_books_follow_org(
    code: str, chapters: int
) -> None:
    """The Vulgate divides Joel in 3 and Malachi in 4. The spine does not."""
    assert SPINE.chapter_count(code) == chapters


def test_contains_rejects_a_verse_past_the_end_of_a_chapter() -> None:
    assert SPINE.contains("PSA", 50, 21) is True
    assert SPINE.contains("PSA", 50, 22) is False


def test_contains_rejects_verse_zero() -> None:
    """The Vulgate psalm titles sit at verse 0 and the spine has no slot."""
    assert SPINE.contains("PSA", 50, 0) is False


def test_contains_rejects_an_unknown_book_and_an_absent_chapter() -> None:
    assert SPINE.contains("XYZ", 1, 1) is False
    assert SPINE.contains("GEN", 51, 1) is False
    assert SPINE.contains("GEN", 0, 1) is False


def test_the_enumeration_walks_every_address_in_canonical_order() -> None:
    addresses = list(SPINE.addresses())
    assert len(addresses) == TOTAL_ADDRESSES
    assert addresses[0] == ("GEN", 1, 1)
    assert addresses[-1][0] == "REV"


def test_the_enumeration_follows_canonical_order_and_not_file_order() -> None:
    seen = [
        code
        for code, chapter, verse in SPINE.addresses()
        if chapter == 1 and verse == 1
    ]
    assert seen == [book.code for book in CANON]


def test_verse_count_of_an_unknown_address_is_nothing_rather_than_an_error() -> None:
    assert SPINE.verse_count("XYZ", 1) is None
    assert SPINE.chapter_count("XYZ") is None
