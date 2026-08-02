import pytest

from catholic_bible.canon.mapping import (
    Mapped,
    Orphan,
    OrphanReason,
    Scheme,
    map_address,
    to_scheme,
)
from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import VerseId


def read_as(scheme: Scheme, published: str) -> str:
    parsed = VerseId.parse(published)
    assert isinstance(parsed, VerseId)
    result = to_scheme(scheme, parsed)
    assert isinstance(result, Mapped), result
    return str(result.verse)


def test_the_miserere_read_back_in_org() -> None:
    assert read_as(Scheme.ORG, "PSA.50.1") == "PSA.51.1"


def test_the_miserere_read_back_in_the_vulgate_is_itself() -> None:
    assert read_as(Scheme.VULGATE, "PSA.50.1") == "PSA.50.1"


def test_susanna_read_back_in_org_leaves_daniel() -> None:
    assert read_as(Scheme.ORG, "DAN.13.1") == "SUS.1.1"


def test_a_book_the_spine_numbers_in_org_reads_back_into_the_vulgate() -> None:
    assert read_as(Scheme.VULGATE, "MAL.3.19") == "MAL.4.1"
    assert read_as(Scheme.VULGATE, "GEN.32.1") == "GEN.31.55"


def test_douay_reads_back_its_two_shifted_books() -> None:
    assert read_as(Scheme.DOUAY, "JOL.3.1") == "JOL.2.28"
    assert read_as(Scheme.DOUAY, "JOL.4.1") == "JOL.3.1"
    assert read_as(Scheme.DOUAY, "MAL.3.19") == "MAL.4.1"


def test_an_address_the_spine_does_not_hold_is_an_orphan_going_out_too() -> None:
    result = to_scheme(Scheme.ORG, VerseId("PSA", 50, 22))
    assert isinstance(result, Orphan)
    assert result.reason is OrphanReason.VERSE_OUT_OF_RANGE


def test_the_reverse_direction_is_total_over_the_whole_spine() -> None:
    for scheme in Scheme:
        for address in SPINE.addresses():
            assert isinstance(to_scheme(scheme, VerseId(*address)), Mapped | Orphan)


@pytest.mark.parametrize("scheme", list(Scheme))
def test_every_address_it_returns_survives_the_round_trip(scheme: Scheme) -> None:
    """The whole spine, out to a scheme and back. No exceptions and no drift."""
    for address in SPINE.addresses():
        start = VerseId(*address)
        out = to_scheme(scheme, start)
        if isinstance(out, Orphan):
            continue
        back = map_address(scheme, out.verse.book, out.verse.chapter, out.verse.verse)
        assert isinstance(back, Mapped)
        assert back.verse == start


@pytest.mark.parametrize(
    ("scheme", "unreadable"),
    [(Scheme.VULGATE, 21), (Scheme.ORG, 41), (Scheme.DOUAY, 0)],
)
def test_the_addresses_no_scheme_can_name_are_counted(
    scheme: Scheme, unreadable: int
) -> None:
    """Where the schemes disagree about cardinality the way back closes on nothing.

    A scheme folds two spine verses into one, or splits one into two, and the
    reverse map has no address that means only this verse. Those come back as
    orphans rather than as the neighbouring verse, and the count is pinned so a
    change in the map moves a number here instead of passing quietly.
    """
    orphans = sum(
        isinstance(to_scheme(scheme, VerseId(*address)), Orphan)
        for address in SPINE.addresses()
    )
    assert orphans == unreadable
