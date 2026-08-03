"""Writing a reference back out, in the language it will be read in.

Ported from the working implementation, which takes a language and has only ever
had Portuguese behind it. Here all three are filled, so the door it left open is
the one this module walks through.

Portuguese and Latin separate chapter from verse with a comma and English with a
colon. That is the notation each tradition prints, not a preference.
"""

from __future__ import annotations

from catholic_bible.canon.aliases import Language
from catholic_bible.canon.authored_names import (
    ENGLISH_ABBREVIATIONS,
    LATIN_ABBREVIATIONS,
)
from catholic_bible.canon.books import CANON
from catholic_bible.canon.reference import Reference

# A plain hyphen for a range that crosses a chapter, where the original prints an
# em dash. The comma in the second half already says a chapter follows, so the
# longer dash carries no information and the shorter one is what the parser
# reads back.
RANGE = "-"


def abbreviation_for(book: str, language: Language = Language.PT) -> str:
    """The short form printed in a reference, or the USX code if none is known."""
    if language is Language.EN:
        return ENGLISH_ABBREVIATIONS.get(book, book)
    if language is Language.LA:
        return LATIN_ABBREVIATIONS.get(book, book)

    found = CANON.by_code(book)
    return book if found is None else found.abbreviation


def _separator(language: Language) -> str:
    return ":" if language is Language.EN else ","


def format_chapter(book: str, chapter: int, language: Language = Language.PT) -> str:
    """A whole chapter, with no verse. `Lc 24`, `Luke 24`, `Luc. 24`."""
    return f"{abbreviation_for(book, language)} {chapter}"


def format_reference(reference: Reference, language: Language = Language.PT) -> str:
    if reference.whole_chapter:
        return format_chapter(reference.book, reference.bounds[0][0], language)

    if reference.is_disjoint:
        return _format_disjoint(reference, language)

    abbreviation = abbreviation_for(reference.book, language)
    separator = _separator(language)
    (start_chapter, start_verse), (end_chapter, end_verse) = reference.bounds

    if not reference.is_range:
        return f"{abbreviation} {start_chapter}{separator}{start_verse}"
    if start_chapter == end_chapter:
        return (
            f"{abbreviation} {start_chapter}{separator}{start_verse}{RANGE}{end_verse}"
        )
    return (
        f"{abbreviation} {start_chapter}{separator}{start_verse}"
        f"{RANGE}{end_chapter}{separator}{end_verse}"
    )


def _format_disjoint(reference: Reference, language: Language) -> str:
    """`Mc 5,22-24.35-43`. The chapter reappears only where it changes."""
    abbreviation = abbreviation_for(reference.book, language)
    separator = _separator(language)

    pieces: list[str] = []
    printed: int | None = None
    for (chapter, first), (_, last) in reference.spans():
        verses = f"{first}" if first == last else f"{first}{RANGE}{last}"
        pieces.append(verses if chapter == printed else f"{chapter}{separator}{verses}")
        printed = chapter

    return f"{abbreviation} " + ".".join(pieces)
