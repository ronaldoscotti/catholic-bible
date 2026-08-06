"""English numbering onto the spine, which is issue #36.

`org` is anchored on the Masoretic text and numbers a psalm superscription as
verses. English translations leave it unnumbered. An english address is a
perfectly valid `org` address, so reading one as the other maps cleanly, raises
nothing, produces no orphan, and lands one or two verses early.

Every expected value below was read out of the published Douay text rather than
reasoned about, because reasoning is what got this wrong the first time.
"""

from __future__ import annotations

import pytest

from catholic_bible.canon.mapping import Mapped, Scheme, map_address


def spine(book: str, chapter: int, verse: int) -> str:
    result = map_address(Scheme.ENGLISH, book, chapter, verse)
    assert isinstance(result, Mapped), result
    return str(result.verse)


@pytest.mark.parametrize(
    ("english", "expected", "opening"),
    [
        # Psalm 51 numbers two superscription lines in the Vulgate and in `org`,
        # so english runs two behind all the way through.
        ((51, 1), "PSA.50.3", "Have mercy on me, O God"),
        ((51, 10), "PSA.50.12", "Create a clean heart in me"),
        ((51, 17), "PSA.50.19", "A sacrifice to God is an afflicted spirit"),
        # Psalm 3 numbers one.
        ((3, 1), "PSA.3.2", "Why, O Lord, are they multiplied"),
        # Psalm 23 folds its title into the first verse, so there is no offset
        # and only the psalm number moves.
        ((23, 1), "PSA.22.1", "The Lord ruleth me"),
    ],
)
def test_a_psalm_lands_on_the_verse_that_carries_its_words(
    english: tuple[int, int], expected: str, opening: str
) -> None:
    assert spine("PSA", *english) == expected


def test_outside_the_psalter_english_is_the_spine() -> None:
    assert spine("JHN", 3, 16) == "JHN.3.16"
    assert spine("MAT", 28, 19) == "MAT.28.19"
    assert spine("ROM", 8, 28) == "ROM.8.28"


def test_english_differs_from_org_exactly_where_the_defect_was() -> None:
    """The regression this scheme exists to prevent, stated as a difference.

    Reading these as `org` is what B4 shipped, and it is why `PSA.50.10` carries
    a cross reference that belongs on `PSA.50.12`.
    """
    as_org = map_address(Scheme.ORG, "PSA", 51, 10)
    as_english = map_address(Scheme.ENGLISH, "PSA", 51, 10)
    assert isinstance(as_org, Mapped) and isinstance(as_english, Mapped)
    assert str(as_org.verse) == "PSA.50.10"
    assert str(as_english.verse) == "PSA.50.12"


@pytest.mark.parametrize(
    ("address", "expected", "opening"),
    [
        # This is not a psalm correction. An earlier draft of issue #36 said
        # nothing outside the Psalter was affected, and five lucky samples
        # agreed with it. Measured against the real apparatus, 5605 of the
        # 15672 addresses that move are in other books.
        (("DAN", 4, 30), "DAN.4.27", "Is not this the great Babylon"),
        (("HOS", 2, 8), "HOS.2.10", "she did not know that I gave her corn"),
        (("GEN", 32, 30), "GEN.32.31", "Jacob called the name of the place"),
        (("DEU", 29, 19), "DEU.29.18", None),
        (("JER", 9, 23), "JER.9.22", None),
    ],
)
def test_other_books_move_too_and_the_text_says_where(
    address: tuple[str, int, int], expected: str, opening: str | None
) -> None:
    assert spine(*address) == expected


def test_a_chapter_split_english_alone_can_cross() -> None:
    """Joel 2,30 in english is Joel 3,3 here, and `org` reaches nothing at all.

    The fix recovers addresses as well as moving them. Read as `org` this is an
    orphan, so the apparatus lost the reference rather than misplacing it.
    """
    assert map_address(Scheme.ORG, "JOL", 2, 30) is not None
    assert not isinstance(map_address(Scheme.ORG, "JOL", 2, 30), Mapped)
    assert spine("JOL", 2, 30) == "JOL.3.3"


def test_an_address_english_does_not_have_is_still_total() -> None:
    """Psalm 51 has 19 verses in english. Asking for 21 must not raise."""
    assert map_address(Scheme.ENGLISH, "PSA", 51, 21) is not None
