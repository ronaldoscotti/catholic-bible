"""Turning a written reference into addresses, and addresses into text.

The one place that decides which numbering an incoming reference is written in.
Without it `Sl 51,1` resolves onto the spine, returns Psalm 51, and the reader
who asked for the Miserere gets the next psalm with a 200 and nothing said.
"""

from __future__ import annotations

import sqlite3
from enum import StrEnum

from catholic_bible.api import errors
from catholic_bible.canon.mapping import Mapped, Orphan, Scheme, map_address
from catholic_bible.canon.reference import (
    Reference,
    UnparsedReference,
    parse_reference,
)
from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import VerseId
from catholic_bible.storage import reader

# Ported as it stands, and it is a span on the dense order rather than a count.
# A contiguous 501 verse range passes and a two verse disjoint reference whose
# parts sit 600 orders apart does not.
MAX_SPAN = 500


class InputScheme(StrEnum):
    """Which numbering the caller wrote the reference in."""

    SPINE = "spine"
    VULGATE = "vulgate"
    ORG = "org"
    DOUAY = "douay"


def read(text: str, scheme: InputScheme) -> tuple[Reference, list[int]]:
    """A written reference, and the canonical orders it covers.

    Raises rather than returning a value, because every caller is an HTTP
    handler and the only thing any of them would do with the value is raise.
    """
    parsed = parse_reference(text)
    if isinstance(parsed, UnparsedReference):
        raise errors.unprocessable(
            errors.from_unparsed(parsed.reason),
            _explain(parsed),
            text,
        )

    if parsed.whole_chapter:
        raise errors.unprocessable(
            errors.Reason.WHOLE_CHAPTER,
            f"{text!r} names a chapter rather than a passage. "
            "read a whole chapter through its own route",
            text,
        )

    orders: list[int] = []
    for start, end in parsed.spans():
        first = _order_of(parsed.book, start, scheme, text)
        last = _order_of(parsed.book, end, scheme, text)
        orders.extend(range(min(first, last), max(first, last) + 1))

    unique = sorted(set(orders))
    if unique[-1] - unique[0] > MAX_SPAN:
        raise errors.unprocessable(
            errors.Reason.RANGE_TOO_LARGE,
            f"{text!r} spans {unique[-1] - unique[0]} verses and the limit "
            f"is {MAX_SPAN}",
            text,
        )
    return parsed, unique


def _explain(parsed: UnparsedReference) -> str:
    if parsed.book is not None:
        return f"no book named {parsed.book!r}"
    return f"{parsed.text!r} is not shaped like a reference"


def _order_of(
    book: str, point: tuple[int, int], scheme: InputScheme, given: str
) -> int:
    chapter, verse = point

    if scheme is not InputScheme.SPINE:
        result = map_address(Scheme(str(scheme)), book, chapter, verse)
        if isinstance(result, Orphan):
            raise errors.unprocessable(
                errors.from_orphan(result.reason),
                f"{book} {chapter}:{verse} in {scheme} reaches no address on the spine",
                given,
            )
        assert isinstance(result, Mapped)
        chapter, verse = result.verse.chapter, result.verse.verse
        book = result.verse.book

    order = SPINE.order_of(VerseId(book, chapter, verse))
    if order is None:
        raise errors.unprocessable(
            errors.Reason.NOT_ON_SPINE,
            f"the spine has no {book} {chapter}:{verse}",
            given,
        )
    return order


def versions_named(
    connection: sqlite3.Connection, written: str | None
) -> list[reader.Row]:
    """The versions a passage was asked for, or the default when it was not.

    The original defaults to an empty list and answers with empty columns, which
    is a silent empty response on a public contract.
    """
    if not written:
        return [reader.default_version(connection)]

    found = []
    for code in [part.strip() for part in written.split(",") if part.strip()]:
        row = reader.version(connection, code)
        if row is None:
            raise errors.not_found(
                errors.Reason.UNKNOWN_VERSION, f"no version named {code!r}", code
            )
        found.append(row)
    return found
