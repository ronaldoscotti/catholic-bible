"""The two verse identities.

Published is the string, `PSA.50.3`. Internal is a dense integer, and the spine
owns it because it is derived by walking the spine. The split is deliberate: an
integer is an artifact of the order a seed ran in, and a public contract that
freezes one cannot be undone later.

Parsing answers shape and says nothing about whether the address exists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ASCII digits, minus allowed so a negative reports as not positive rather than
# as not a number. No plus, because a published id has one spelling. str.isdigit
# accepts superscripts and other scripts that int() then refuses, which turned a
# value into an exception.
_NUMBER = re.compile(r"^-?[0-9]+$")


@dataclass(frozen=True, slots=True)
class MalformedVerseId:
    """A published id that is not shaped like one, with the reason."""

    text: str
    reason: str


@dataclass(frozen=True, slots=True)
class VerseId:
    book: str
    chapter: int
    verse: int

    def __str__(self) -> str:
        return f"{self.book}.{self.chapter}.{self.verse}"

    @staticmethod
    def parse(text: str) -> VerseId | MalformedVerseId:
        parts = text.split(".")
        if len(parts) != 3:
            return MalformedVerseId(text, "shape")

        book, raw_chapter, raw_verse = parts
        if not book:
            return MalformedVerseId(text, "shape")
        if not _NUMBER.match(raw_chapter) or not _NUMBER.match(raw_verse):
            return MalformedVerseId(text, "not_a_number")

        chapter, verse = int(raw_chapter), int(raw_verse)
        if chapter < 1 or verse < 1:
            return MalformedVerseId(text, "not_positive")
        return VerseId(book, chapter, verse)
