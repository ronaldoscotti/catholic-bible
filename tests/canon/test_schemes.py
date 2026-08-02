import pytest

from catholic_bible.canon.schemes import DOUAY, ORG, VULGATE, Mode
from catholic_bible.canon.spine import SPINE


@pytest.mark.parametrize(
    ("book", "chapter", "verse", "expected"),
    [
        ("GEN", 31, 55, ("GEN", 32, 1)),
        ("GEN", 32, 1, ("GEN", 32, 2)),
        ("GEN", 1, 1, ("GEN", 1, 1)),
    ],
)
def test_the_vulgate_boundary_shift_in_genesis(
    book: str, chapter: int, verse: int, expected: tuple[str, int, int]
) -> None:
    assert VULGATE.to_spine(book, chapter, verse) == expected


def test_the_psalter_is_read_as_vulgate_so_the_vulgate_passes_through() -> None:
    assert VULGATE.mode_for("PSA") is Mode.IDENTITY
    assert VULGATE.to_spine("PSA", 50, 3) == ("PSA", 50, 3)


@pytest.mark.parametrize("book", ["MAL", "JOL"])
def test_the_books_where_the_spine_numbers_in_org(book: str) -> None:
    assert VULGATE.mode_for(book) is Mode.ORG


def test_the_vulgate_four_chapter_malachi_folds_into_three() -> None:
    assert VULGATE.to_spine("MAL", 4, 1) == ("MAL", 3, 19)


def test_a_book_absent_from_the_scheme_table_defaults_to_identity() -> None:
    assert VULGATE.mode_for("EST") is Mode.IDENTITY
    assert VULGATE.to_spine("EST", 11, 1) == ("EST", 11, 1)


def test_the_miserere_arrives_from_org_at_psalm_fifty() -> None:
    """Psalm 51 nearly everywhere, Psalm 50 in the Vulgate and in the missal."""
    assert ORG.to_spine("PSA", 51, 1) == ("PSA", 50, 1)
    assert ORG.to_spine("PSA", 51, 3) == ("PSA", 50, 3)


def test_susanna_and_the_song_of_the_three_arrive_from_org_inside_daniel() -> None:
    """org keeps them as separate books. The spine has no such books."""
    assert ORG.to_spine("SUS", 1, 1) == ("DAN", 13, 1)
    assert ORG.to_spine("S3Y", 1, 1) == ("DAN", 3, 24)


def test_a_merged_verse_inverts_to_the_first_of_its_declared_origins() -> None:
    """The Vulgate splits org Psalm 2:12 in two, so inverting has two answers."""
    assert ORG.to_spine("PSA", 2, 12) == ("PSA", 2, 12)


def test_an_origin_with_no_slot_on_the_spine_loses_to_one_that_has_a_slot() -> None:
    """The table declares the Song of the Three from both DAN and DAG.

    Only DAN has a slot. Keeping whichever the file happened to list last would
    orphan 65 addresses that the table itself says are resolvable.
    """
    assert ORG.to_spine("S3Y", 1, 1) == ("DAN", 3, 24)
    assert ORG.to_spine("S3Y", 1, 67) == ("DAN", 3, 90)


def test_an_address_on_the_spine_is_not_traded_for_one_that_is_not() -> None:
    """The table carries source versifications beyond the Vulgate.

    Greek Daniel travels as DAG, so inverting hands org DAN 1:1 an origin of
    DAG 1:1, which the canon does not have. Applying it would orphan 251
    addresses of a book that maps perfectly well.
    """
    assert ORG.to_spine("DAN", 1, 1) == ("DAN", 1, 1)
    assert ORG.to_spine("DAN", 3, 24) == ("DAN", 3, 91)


def test_org_passes_through_where_the_spine_already_numbers_in_org() -> None:
    assert ORG.to_spine("MAL", 3, 19) == ("MAL", 3, 19)
    assert ORG.to_spine("GEN", 1, 1) == ("GEN", 1, 1)


def test_douay_names_are_douay_and_not_modern() -> None:
    assert DOUAY.to_usx("1 KINGS") == "1SA"
    assert DOUAY.to_usx("3 KINGS") == "1KI"
    assert DOUAY.to_usx("APOCALYPSE") == "REV"
    assert DOUAY.to_usx("ECCLESIASTICUS") == "SIR"


def test_an_unknown_douay_name_resolves_to_nothing() -> None:
    assert DOUAY.to_usx("BOOK OF MORMON") is None


@pytest.mark.parametrize(
    ("book", "chapter", "verse", "expected"),
    [
        ("JOL", 2, 28, ("JOL", 3, 1)),
        ("JOL", 2, 32, ("JOL", 3, 5)),
        ("JOL", 3, 1, ("JOL", 4, 1)),
        ("JOL", 2, 27, ("JOL", 2, 27)),
        ("MAL", 4, 1, ("MAL", 3, 19)),
        ("MAL", 4, 6, ("MAL", 3, 24)),
        ("MAL", 3, 1, ("MAL", 3, 1)),
        ("GEN", 1, 1, ("GEN", 1, 1)),
    ],
)
def test_douay_shifts_only_joel_and_malachi(
    book: str, chapter: int, verse: int, expected: tuple[str, int, int]
) -> None:
    assert DOUAY.to_spine(book, chapter, verse) == expected


def test_the_spine_was_not_inflated_by_a_boundary_difference() -> None:
    """The load-bearing subtlety, asserted through its consequence.

    The Vulgate gives Genesis 31 fifty five verses and the spine gives it fifty
    four, because the fifty fifth is Genesis 32:1 in org rather than an extra
    verse. Had the spine build taken the Vulgate maximum from raw coordinates
    it would have recorded fifty five, Genesis would have counted zero identity
    orphans, and the book would have flipped to identity. Every org address in
    Genesis would then have resolved one verse off.
    """
    assert SPINE.verse_count("GEN", 31) == 54
    assert VULGATE.mode_for("GEN") is Mode.ORG
