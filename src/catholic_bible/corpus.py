"""Reading the published corpus off disk.

Deliberately thin. B2 publishes the files and proves they are what they claim to
be. Serving them by reference is B3, and a reader that grew query methods here
would be that epic arriving early.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache

from catholic_bible.canon import DATA_DIR

CORPUS_DIR = DATA_DIR / "corpus"

VERSIONS = ("matos-soares", "douay-rheims", "vulgata-clementina")


@dataclass(frozen=True, slots=True)
class Verse:
    text: str
    order: int


@dataclass(frozen=True, slots=True)
class Version:
    code: str
    metadata: dict[str, object]
    verses: dict[str, Verse]


@cache
def load(code: str) -> Version:
    """One published translation.

    The code is checked against the published set before it reaches a path. B3
    hands this a segment from an HTTP route, where an unchecked value reads
    outside the corpus directory and every distinct string a caller sends
    becomes a permanent cache entry.
    """
    if code not in VERSIONS:
        raise KeyError(f"no published version named {code!r}")
    raw = json.loads((CORPUS_DIR / f"{code}.json").read_text(encoding="utf-8"))
    return Version(
        code=code,
        metadata=raw["version"],
        verses={
            key: Verse(text=record["text"], order=record["order"])
            for key, record in raw["verses"].items()
        },
    )
