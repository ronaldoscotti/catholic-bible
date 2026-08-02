"""The orphan report.

Every address a scheme declares, run through the mapping function, counted by
book and by reason. The number is whatever it is. Nothing here predicts it and
nothing rounds it.

Two schemes are reportable in B1. The Vulgate and `org` both have a declared
coordinate space, because the Copenhagen table names their books, their verse
counts and every address it remaps. Douay does not. Its coordinate space
arrives with the text in B2, so its section says so instead of showing a zero
that would read as clean.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.mapping import Orphan, Scheme, map_address
from catholic_bible.canon.schemes import VULGATE, expand

Address = tuple[str, int, int]

REPORT_PATH = DATA_DIR / "derived" / "orphans.json"

ENUMERABLE = (Scheme.VULGATE, Scheme.ORG)


def _key(address: Address) -> str:
    book, chapter, verse = address
    return f"{book} {chapter}:{verse}"


def _parse(key: str) -> Address:
    book, rest = key.split(" ", 1)
    chapter, verse = rest.split(":", 1)
    return book, int(chapter), int(verse)


def vulgate_addresses() -> list[Address]:
    """Every address the Copenhagen table names on its Vulgate side.

    The verse counts give the bulk of it. The remap origins are unioned in on
    top because they reach addresses the counts do not, and the Vulgate psalm
    titles at verse 0 are exactly that case.
    """
    seen: dict[Address, None] = {}
    for book, counts in VULGATE.declared_books().items():
        for chapter, count in enumerate(counts, start=1):
            for verse in range(1, count + 1):
                seen[(book, chapter, verse)] = None

    for ref in VULGATE.declared_pairs():
        for key in expand(ref):
            seen[_parse(key)] = None
    return list(seen)


def org_addresses() -> list[Address]:
    """The same space read in `org`, which is its image under the table.

    The table declares verse counts for the Vulgate and not for `org`, so
    sweeping the Vulgate counts would ask the `org` map about coordinates `org`
    never uses and manufacture orphans no source could emit.
    """
    pairs = VULGATE.declared_targets()
    seen: dict[Address, None] = {}
    for address in vulgate_addresses():
        seen[_parse(pairs.get(_key(address), _key(address)))] = None
    return list(seen)


def declared_addresses(scheme: Scheme) -> Iterator[Address]:
    yield from vulgate_addresses() if scheme is Scheme.VULGATE else org_addresses()


def build_report() -> dict[str, object]:
    provenance = json.loads((DATA_DIR / "PROVENANCE.json").read_text(encoding="utf-8"))

    schemes: dict[str, object] = {}
    for scheme in ENUMERABLE:
        addresses = list(declared_addresses(scheme))
        totals: dict[str, int] = {}
        books: dict[str, dict[str, int]] = {}
        resolved = 0
        for book, chapter, verse in addresses:
            result = map_address(scheme, book, chapter, verse)
            if not isinstance(result, Orphan):
                resolved += 1
                continue
            reason = result.reason.value
            totals[reason] = totals.get(reason, 0) + 1
            books.setdefault(book, {})
            books[book][reason] = books[book].get(reason, 0) + 1
        schemes[scheme.value] = {
            "addresses_examined": len(addresses),
            "resolved": resolved,
            "orphans": sum(totals.values()),
            "by_reason": dict(sorted(totals.items())),
            "by_book": {
                book: dict(sorted(r.items())) for book, r in sorted(books.items())
            },
        }

    schemes[Scheme.DOUAY.value] = {
        "reportable": False,
        "why": (
            "Douay has no declared coordinate space in this repo. "
            "It arrives with the text in B2."
        ),
    }

    return {
        "describes": {
            "source_commit": provenance["source"]["commit"],
            "spine_sha256": provenance["files"]["versification.json"]["sha256"],
        },
        "schemes": schemes,
    }


def render(report: dict[str, object]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
