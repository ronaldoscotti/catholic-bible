"""The versification spine: how many verses each chapter has.

A Vulgate-cardinality superset over the `org` scheme, applied to the Old
Testament only. Per chapter the count is the larger of what `org` has and what
the Vulgate has, so the spine never reduces. That makes it mixed rather than
uniform. The Psalter ends up numbered in Vulgate and Joel and Malachi end up
numbered in `org`, which is a result of the rule rather than a rule of its own.

Append-only. A published address never changes meaning.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.books import CANON
from catholic_bible.canon.verse import VerseId

Address = tuple[str, int, int]


class Spine:
    def __init__(self, counts: dict[str, list[int]]) -> None:
        self._counts = counts
        self._order = [book.code for book in CANON if book.code in counts]
        self._dense: list[Address] = list(self.addresses())
        self._by_address = {
            address: n for n, address in enumerate(self._dense, start=1)
        }

    def books(self) -> tuple[str, ...]:
        """Book codes in canonical order."""
        return tuple(self._order)

    def chapter_count(self, book: str) -> int | None:
        chapters = self._counts.get(book)
        return None if chapters is None else len(chapters)

    def verse_count(self, book: str, chapter: int) -> int | None:
        chapters = self._counts.get(book)
        if chapters is None or chapter < 1 or chapter > len(chapters):
            return None
        return chapters[chapter - 1]

    def contains(self, book: str, chapter: int, verse: int) -> bool:
        count = self.verse_count(book, chapter)
        return count is not None and 1 <= verse <= count

    def addresses(self) -> Iterator[Address]:
        """Every valid address, in canonical order."""
        for code in self._order:
            for index, count in enumerate(self._counts[code], start=1):
                for verse in range(1, count + 1):
                    yield code, index, verse

    def order_of(self, verse: VerseId) -> int | None:
        """The dense internal integer, or nothing when the spine has no such address."""
        return self._by_address.get((verse.book, verse.chapter, verse.verse))

    def at_order(self, order: int) -> VerseId | None:
        if order < 1 or order > len(self._dense):
            return None
        return VerseId(*self._dense[order - 1])


def _load() -> Spine:
    raw: dict[str, list[int]] = json.loads(
        (DATA_DIR / "versification.json").read_text(encoding="utf-8")
    )
    return Spine(raw)


SPINE = _load()
