import pytest

from catholic_bible.canon.mapping import (
    Mapped,
    Orphan,
    OrphanReason,
    Scheme,
    map_address,
)
from catholic_bible.canon.schemes import VULGATE
from catholic_bible.canon.verse import VerseId


def mapped(scheme: Scheme, book: str, chapter: int, verse: int) -> VerseId:
    result = map_address(scheme, book, chapter, verse)
    assert isinstance(result, Mapped), result
    return result.verse


def orphan(scheme: Scheme, book: str, chapter: int, verse: int) -> OrphanReason:
    result = map_address(scheme, book, chapter, verse)
    assert isinstance(result, Orphan), result
    return result.reason


def test_the_miserere_from_org_lands_on_psalm_fifty() -> None:
    assert str(mapped(Scheme.ORG, "PSA", 51, 1)) == "PSA.50.1"


def test_the_vulgate_resolves_against_a_spine_built_from_it() -> None:
    assert str(mapped(Scheme.VULGATE, "PSA", 50, 3)) == "PSA.50.3"
    assert str(mapped(Scheme.VULGATE, "GEN", 31, 55)) == "GEN.32.1"


def test_douay_joel_and_malachi_resolve() -> None:
    assert str(mapped(Scheme.DOUAY, "MAL", 4, 1)) == "MAL.3.19"
    assert str(mapped(Scheme.DOUAY, "JOL", 2, 28)) == "JOL.3.1"


def test_susanna_resolves_from_org_into_daniel() -> None:
    assert str(mapped(Scheme.ORG, "SUS", 1, 1)) == "DAN.13.1"
    assert str(mapped(Scheme.ORG, "BEL", 1, 2)) == "DAN.14.2"


def test_bel_opens_on_a_verse_the_table_declares_twice() -> None:
    """Two textual traditions, both asserted by the source and both on the spine.

    Daniel 13 ends at 64 in most editions and at 65 in the one that carries the
    transition into Bel. The table declares BEL 1:1 from that verse and from
    Daniel 14:1, so the first declared wins and the case is recorded rather than
    settled by a heuristic that would be picking a tradition.
    """
    assert str(mapped(Scheme.ORG, "BEL", 1, 1)) == "DAN.13.65"


def test_greek_esther_has_no_counterpart_coming_from_org() -> None:
    """The spine carries the additions inside Esther. org keeps them apart."""
    assert orphan(Scheme.ORG, "ESG", 1, 1) is OrphanReason.NO_COUNTERPART


def test_a_code_no_scheme_knows_is_an_unknown_book() -> None:
    assert orphan(Scheme.ORG, "XYZ", 1, 1) is OrphanReason.UNKNOWN_BOOK


def test_a_chapter_past_the_end_of_a_book() -> None:
    assert orphan(Scheme.VULGATE, "GEN", 99, 1) is OrphanReason.CHAPTER_OUT_OF_RANGE


def test_a_verse_past_the_end_of_a_chapter() -> None:
    assert orphan(Scheme.VULGATE, "GEN", 1, 99) is OrphanReason.VERSE_OUT_OF_RANGE


def test_a_vulgate_psalm_title_is_named_for_what_it_is() -> None:
    """147 of these. Calling them out of range would be the report lying."""
    assert orphan(Scheme.VULGATE, "PSA", 50, 0) is OrphanReason.PSALM_TITLE


@pytest.mark.parametrize(
    ("scheme", "book"), [(Scheme.ORG, "GEN"), (Scheme.DOUAY, "JHN")]
)
def test_verse_zero_outside_the_psalter_is_not_a_psalm_title(
    scheme: Scheme, book: str
) -> None:
    """The reason set is closed and its members name distinguishable causes.

    Verse 0 is a title in the Vulgate psalter and nowhere else. The report never
    saw this because it only sweeps declared addresses, where verse 0 occurs in
    PSA alone, so the mislabel was invisible until something asked directly.
    """
    assert orphan(scheme, book, 1, 0) is OrphanReason.VERSE_OUT_OF_RANGE


def test_an_orphan_carries_the_address_that_was_asked_for() -> None:
    result = map_address(Scheme.ORG, "ESG", 3, 7)
    assert isinstance(result, Orphan)
    assert result.source == ("ESG", 3, 7)
    assert result.scheme is Scheme.ORG


@pytest.mark.parametrize("scheme", list(Scheme))
def test_the_function_is_total_over_every_address_the_schemes_declare(
    scheme: Scheme,
) -> None:
    """Never raises, over every address the schemes declare plus the edges."""
    checked = 0
    for book, counts in VULGATE.declared_books().items():
        for chapter, count in enumerate(counts, start=1):
            for verse in range(0, count + 2):
                result = map_address(scheme, book, chapter, verse)
                assert isinstance(result, Mapped | Orphan)
                checked += 1
    assert checked > 35_000


def test_it_never_guesses_at_the_edge_of_a_chapter() -> None:
    """One past the end is an orphan and not the first verse of the next."""
    last = map_address(Scheme.VULGATE, "GEN", 1, 31)
    past = map_address(Scheme.VULGATE, "GEN", 1, 32)
    assert isinstance(last, Mapped)
    assert isinstance(past, Orphan)


def test_a_negative_or_zero_chapter_is_out_of_range_rather_than_an_error() -> None:
    assert orphan(Scheme.VULGATE, "GEN", 0, 1) is OrphanReason.CHAPTER_OUT_OF_RANGE
    assert orphan(Scheme.VULGATE, "GEN", -3, 1) is OrphanReason.CHAPTER_OUT_OF_RANGE
