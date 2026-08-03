"""Reading the published commentary off disk.

Thin on purpose, like `corpus.py` beside it. It hands back what the file holds.
Querying it by address is the storage layer's job and a coverage method here
would be that layer arriving in the wrong module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.verse import VerseId

COMMENTARY_DIR = DATA_DIR / "commentary"

SOURCES = ("haydock",)


@dataclass(frozen=True, slots=True)
class Entry:
    start: VerseId
    end: VerseId
    first_order: int
    last_order: int
    label: str | None
    position: int
    body: dict[str, str]
    """HTML, keyed by language tag. The source language is always present."""


@dataclass(frozen=True, slots=True)
class Source:
    code: str
    metadata: dict[str, object]
    entries: tuple[Entry, ...]


def _address(text: str) -> VerseId:
    parsed = VerseId.parse(text)
    if not isinstance(parsed, VerseId):
        raise ValueError(f"the published commentary carries {text!r} as an anchor")
    return parsed


@cache
def load(code: str) -> Source:
    """One published commentary source.

    The code is checked against the published set before it reaches a path, for
    the same two reasons `corpus.load` checks: a segment arriving from a route
    would otherwise read outside this directory, and every distinct string a
    caller sends would become a permanent cache entry.
    """
    if code not in SOURCES:
        raise KeyError(f"no published commentary named {code!r}")

    raw = json.loads((COMMENTARY_DIR / f"{code}.json").read_text(encoding="utf-8"))
    return Source(
        code=code,
        metadata=raw["source"],
        entries=tuple(
            Entry(
                start=_address(record["start"]),
                end=_address(record["end"]),
                first_order=record["start_order"],
                last_order=record["end_order"],
                label=record["label"],
                position=record["position"],
                body=record["body"],
            )
            for record in raw["entries"]
        ),
    )
