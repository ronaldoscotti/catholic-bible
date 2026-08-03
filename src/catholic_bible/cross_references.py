"""Reading the published cross-reference apparatus off disk.

Thin, like `corpus.py` and `commentary.py` beside it. It hands back what the
file holds and answers no question about it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.verse import VerseId

CROSS_REFERENCE_DIR = DATA_DIR / "cross-references"

# Below this a reference is the weak tail of OpenBible's vote count. At or above
# it is a curated Catholic apparatus or a strong consensus. DECISIONS.md carries
# the number and why it is the private repo's rather than one derived here.
PRIMARY = 20


@dataclass(frozen=True, slots=True)
class Reference:
    anchor: VerseId
    target: VerseId
    end: int | None
    """The last verse of a target range, where the target is one. None otherwise."""
    whole_chapter: bool
    weight: int
    source: str

    @property
    def primary(self) -> bool:
        return self.weight >= PRIMARY


@dataclass(frozen=True, slots=True)
class Apparatus:
    sources: dict[str, dict[str, object]]
    references: tuple[Reference, ...]


def _address(text: str) -> VerseId:
    parsed = VerseId.parse(text)
    if not isinstance(parsed, VerseId):
        raise ValueError(f"the published apparatus carries {text!r} as an address")
    return parsed


@cache
def load() -> Apparatus:
    raw = json.loads(
        (CROSS_REFERENCE_DIR / "references.json").read_text(encoding="utf-8")
    )
    return Apparatus(
        sources=raw["sources"],
        references=tuple(
            Reference(
                anchor=_address(anchor),
                target=_address(record["to"]),
                end=record.get("end"),
                whole_chapter=record.get("chapter", False),
                weight=record["weight"],
                source=record["source"],
            )
            for anchor, records in raw["references"].items()
            for record in records
        ),
    )
