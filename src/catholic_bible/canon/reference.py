"""Reading a written reference into a book, a chapter and a verse span.

Ported from the working implementation, with one change. That one raises on a
book it cannot resolve and this one returns a value, because a reader typing a
name that does not exist is the most ordinary thing that happens to a reference
parser rather than a fault. The reasoning is in DECISIONS.md.

The grammar covers what a Portuguese missal and a lectionary actually print.
`Jo 3,16`, `Jo 3,16-18`, `Ex 13,1-14,5`, `Mc 5,22-24.35-43`, `Sl 23`, `Ex 13-14`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from catholic_bible.canon.aliases import ALIASES

Point = tuple[int, int]
Span = tuple[Point, Point]

DASH = r"[-—–]"

_SPAN = re.compile(
    rf"^\s*(.+?)\s+(\d+)[,:](\d+)(?:\s*{DASH}\s*(?:(\d+)[,:])?(\d+))?\s*$"
)
_PARTS = re.compile(r"^\s*(.+?)\s+(\d+)[,:](.+?)\s*$")
_PART_WITH_CHAPTER = re.compile(r"^(\d+)[,:](.+)$")
_PART_VERSES = re.compile(rf"^(\d+)(?:\s*{DASH}\s*(\d+))?$")
_CHAPTER = re.compile(rf"^\s*(.+?)\s+(\d+)(?:\s*{DASH}\s*\d+)?\s*$")


@dataclass(frozen=True, slots=True)
class UnparsedReference:
    text: str
    reason: str
    book: str | None = None


@dataclass(frozen=True, slots=True)
class Reference:
    book: str
    bounds: Span
    whole_chapter: bool = False
    parts: tuple[Span, ...] | None = None

    @property
    def is_range(self) -> bool:
        return self.bounds[0] != self.bounds[1]

    @property
    def is_disjoint(self) -> bool:
        return self.parts is not None and len(self.parts) > 1

    def spans(self) -> tuple[Span, ...]:
        return self.parts if self.parts is not None else (self.bounds,)


Parsed = Reference | UnparsedReference


def parse_reference(text: str) -> Parsed:
    if "." in text:
        return _parse_parts(text)

    match = _SPAN.match(text)
    if match is None:
        return _parse_whole_chapter(text)

    code = ALIASES.resolve(match[1])
    if code is None:
        return UnparsedReference(text, "unknown_book", match[1])

    chapter, verse = int(match[2]), int(match[3])
    start = (chapter, verse)
    if match[5] is None:
        return Reference(code, (start, start))

    end = (int(match[4]) if match[4] else chapter, int(match[5]))
    return Reference(code, (start, end))


def _parse_parts(text: str) -> Parsed:
    """The lectionary shape, `Mc 5,22-24.35-43`.

    A part with no chapter of its own inherits the one before it, which is how
    a lectionary prints a reading that skips verses inside a chapter.
    """
    match = _PARTS.match(text)
    if match is None:
        return UnparsedReference(text, "malformed")

    code = ALIASES.resolve(match[1])
    if code is None:
        return UnparsedReference(text, "unknown_book", match[1])

    chapter = int(match[2])
    parts: list[Span] = []
    for piece in match[3].split("."):
        piece = piece.strip()
        owned = _PART_WITH_CHAPTER.match(piece)
        if owned is not None:
            chapter, piece = int(owned[1]), owned[2]

        verses = _PART_VERSES.match(piece)
        if verses is None:
            return UnparsedReference(text, "malformed", match[1])

        first = int(verses[1])
        last = int(verses[2]) if verses[2] else first
        parts.append(((chapter, first), (chapter, last)))

    return Reference(code, (parts[0][0], parts[-1][1]), parts=tuple(parts))


def _parse_whole_chapter(text: str) -> Parsed:
    """`Sl 23`, and `Ex 13-14` anchored on the first chapter."""
    match = _CHAPTER.match(text)
    if match is None:
        return UnparsedReference(text, "malformed")

    code = ALIASES.resolve(match[1])
    if code is None:
        return UnparsedReference(text, "unknown_book", match[1])

    chapter = int(match[2])
    return Reference(code, ((chapter, 1), (chapter, 1)), whole_chapter=True)
