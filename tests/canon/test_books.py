import pytest

from catholic_bible.canon.books import CANON, Testament

DEUTEROCANONICAL = {"TOB", "JDT", "WIS", "SIR", "BAR", "1MA", "2MA"}


def test_the_canon_holds_seventy_three_books() -> None:
    assert len(CANON) == 73


def test_canonical_order_is_contiguous_from_one() -> None:
    assert [book.order for book in CANON] == list(range(1, 74))


def test_codes_are_unique() -> None:
    codes = [book.code for book in CANON]
    assert len(set(codes)) == len(codes)


def test_the_testaments_split_forty_six_and_twenty_seven() -> None:
    old = [book for book in CANON if book.testament is Testament.OLD]
    new = [book for book in CANON if book.testament is Testament.NEW]
    assert (len(old), len(new)) == (46, 27)


def test_exactly_seven_books_are_deuterocanonical() -> None:
    assert {book.code for book in CANON if book.deuterocanonical} == DEUTEROCANONICAL


@pytest.mark.parametrize("code", ["DAN", "EST"])
def test_a_book_with_deuterocanonical_chapters_is_not_a_deuterocanonical_book(
    code: str,
) -> None:
    """Susanna, Bel and the Greek additions to Esther are chapters, not books."""
    assert CANON.by_code(code) is not None
    assert CANON.by_code(code).deuterocanonical is False  # type: ignore[union-attr]


def test_lookup_by_code() -> None:
    genesis = CANON.by_code("GEN")
    assert genesis is not None
    assert genesis.order == 1
    assert genesis.name == "Gênesis"


def test_an_unknown_code_resolves_to_nothing_rather_than_raising() -> None:
    assert CANON.by_code("XYZ") is None
