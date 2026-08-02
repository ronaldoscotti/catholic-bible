"""The 73 books, in canonical order.

Exported from the private source repository. See PROVENANCE.json for the commit
it came from and DECISIONS.md for why the generator stayed behind.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum

from catholic_bible.canon import DATA_DIR


class Testament(StrEnum):
    OLD = "OLD"
    NEW = "NEW"


class CanonGroup(StrEnum):
    PENTATEUCH = "PENTATEUCH"
    HISTORICAL = "HISTORICAL"
    WISDOM = "WISDOM"
    PROPHETIC = "PROPHETIC"
    GOSPELS = "GOSPELS"
    ACTS = "ACTS"
    EPISTLES = "EPISTLES"
    REVELATION = "REVELATION"


@dataclass(frozen=True, slots=True)
class Book:
    """One book of the canon, addressed by its USX code."""

    code: str
    order: int
    testament: Testament
    group: CanonGroup
    deuterocanonical: bool
    name: str
    abbreviation: str
    aliases: tuple[str, ...]


class Canon(Sequence[Book]):
    """The canon in canonical order, indexable by position and by USX code."""

    def __init__(self, books: Sequence[Book]) -> None:
        self._books = tuple(books)
        self._by_code = {book.code: book for book in self._books}

    def __len__(self) -> int:
        return len(self._books)

    def __getitem__(self, index: int) -> Book:  # type: ignore[override]
        return self._books[index]

    def __iter__(self) -> Iterator[Book]:
        return iter(self._books)

    def by_code(self, code: str) -> Book | None:
        return self._by_code.get(code)


def _load() -> Canon:
    raw = json.loads((DATA_DIR / "canon.json").read_text(encoding="utf-8"))
    return Canon(
        [
            Book(
                code=entry["code"],
                order=entry["order"],
                testament=Testament(entry["testament"]),
                group=CanonGroup(entry["canon_group"]),
                deuterocanonical=entry["deutero"],
                name=entry["name"],
                abbreviation=entry["abbr"],
                aliases=tuple(entry["aliases"]),
            )
            for entry in raw
        ]
    )


CANON = _load()
