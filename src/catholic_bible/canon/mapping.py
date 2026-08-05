"""The total mapping function.

It always returns. An address with no target on the spine comes back as an
orphan carrying a distinguishable reason, never as an exception and never as
the nearest plausible verse.

This is the layer that decides what an orphan is. The scheme maps below it stay
pure and answer only where an address lands. See DECISIONS.md for why that
responsibility sits here rather than in an importer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from catholic_bible.canon.books import CANON
from catholic_bible.canon.schemes import DOUAY, ENGLISH, ORG, VULGATE
from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import VerseId

Address = tuple[str, int, int]


class Scheme(StrEnum):
    VULGATE = "vulgate"
    ORG = "org"
    DOUAY = "douay"
    ENGLISH = "english"


class OrphanReason(StrEnum):
    """Why an address has no home on the spine. A closed set."""

    UNKNOWN_BOOK = "unknown_book"
    NO_COUNTERPART = "no_counterpart"
    CHAPTER_OUT_OF_RANGE = "chapter_out_of_range"
    VERSE_OUT_OF_RANGE = "verse_out_of_range"
    PSALM_TITLE = "psalm_title"


@dataclass(frozen=True, slots=True)
class Mapped:
    verse: VerseId


@dataclass(frozen=True, slots=True)
class Orphan:
    scheme: Scheme
    source: Address
    reason: OrphanReason


Result = Mapped | Orphan


def map_address(scheme: Scheme, book: str, chapter: int, verse: int) -> Result:
    """Translates one address from `scheme` onto the spine."""
    match scheme:
        case Scheme.VULGATE:
            target = VULGATE.to_spine(book, chapter, verse)
        case Scheme.ORG:
            target = ORG.to_spine(book, chapter, verse)
        case Scheme.DOUAY:
            target = DOUAY.to_spine(book, chapter, verse)
        case Scheme.ENGLISH:
            target = ENGLISH.to_spine(book, chapter, verse)

    if SPINE.contains(*target):
        return Mapped(VerseId(*target))
    return Orphan(scheme, (book, chapter, verse), _why(scheme, book, target))


def to_scheme(scheme: Scheme, verse: VerseId) -> Result:
    """The other direction, a spine address read in `scheme`.

    Also total. The remap table is not a bijection, so the candidate is mapped
    forward again and only survives if it lands where it started. See
    DECISIONS.md.
    """
    source = (verse.book, verse.chapter, verse.verse)
    if not SPINE.contains(*source):
        return Orphan(scheme, source, _why(scheme, verse.book, source))

    match scheme:
        case Scheme.VULGATE:
            target = VULGATE.from_spine(*source)
        case Scheme.ORG:
            target = ORG.from_spine(*source)
        case Scheme.DOUAY:
            target = DOUAY.from_spine(*source)
        case Scheme.ENGLISH:
            target = ENGLISH.from_spine(*source)

    back = map_address(scheme, *target)
    if isinstance(back, Mapped) and back.verse == verse:
        return Mapped(VerseId(*target))
    return Orphan(scheme, source, OrphanReason.NO_COUNTERPART)


def _why(scheme: Scheme, source_book: str, target: Address) -> OrphanReason:
    target_book, chapter, verse = target

    if CANON.by_code(target_book) is None:
        known = scheme is not Scheme.DOUAY and VULGATE.declares(source_book)
        return OrphanReason.NO_COUNTERPART if known else OrphanReason.UNKNOWN_BOOK

    if SPINE.verse_count(target_book, chapter) is None:
        return OrphanReason.CHAPTER_OUT_OF_RANGE
    # Verse 0 is the title in the Vulgate psalter and nothing anywhere else.
    if verse == 0 and target_book == "PSA":
        return OrphanReason.PSALM_TITLE
    return OrphanReason.VERSE_OUT_OF_RANGE
