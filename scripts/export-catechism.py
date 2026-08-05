#!/usr/bin/env python3
"""Exports the Catechism citation index out of the private source repository.

Paragraph numbers, verse addresses and the citation as the Catechism wrote it.
No Catechism text, permanently, and there is nothing here that could carry any.

The source fixture runs from paragraph to verse. Both directions are published,
because the original is what somebody rendering a paragraph needs and it is
already in hand before the inversion runs.

Citations arrive in modern numbering rather than the spine's, so they map through
`org`. Reading them against the spine directly loses twenty Psalms silently.

Usage:
    scripts/export-catechism.py --source ~/path/to/private/repo
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _source import git, refuse_a_dirty_tree  # noqa: E402

from catholic_bible.canon.mapping import (  # noqa: E402
    Mapped,
    Scheme,
    map_address,
)
from catholic_bible.canon.reference import Reference, parse_reference  # noqa: E402
from catholic_bible.canon.spine import SPINE  # noqa: E402

DEST = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "catholic_bible"
    / "data"
    / "catechism"
)

FIXTURE = "database/data/catechism-scripture-citations.json.gz"

UPSTREAM = {
    "name": "nossbigg/catechism-ccc-json",
    "release": "v0.0.2",
    "url": "https://github.com/nossbigg/catechism-ccc-json",
    "licence": "none declared",
    "note": (
        "A third-party transcription. The citation graph is a fact whoever "
        "transcribed it and what establishes it is the hand check, not this name."
    ),
}

# The citations count Psalms the modern way. The spine counts them the Vulgate
# way. Nothing else in the fixture needs a scheme and this one does.
SCHEME = Scheme.ORG


@dataclass(frozen=True, slots=True)
class Resolved:
    ids: list[str] = field(default_factory=list)
    reason: str | None = None


def resolve(label: str) -> Resolved:
    """A written citation, read onto the spine.

    Total. A label naming a book that does not exist, or a verse past the end of
    its chapter, comes back with a reason rather than raising, because the
    printed apparatus contains both and losing them silently is worse than
    publishing them as orphans.
    """
    reference = parse_reference(label)
    if not isinstance(reference, Reference):
        return Resolved(reason=str(reference.reason))

    ids: list[str] = []
    reason: str | None = None
    for (start_chapter, start_verse), (end_chapter, end_verse) in reference.spans():
        start = map_address(SCHEME, reference.book, start_chapter, start_verse)
        end = map_address(SCHEME, reference.book, end_chapter, end_verse)
        # A disjoint citation keeps the parts that landed. `Mt 5,3-12.99` is a
        # real verse span beside a bad one, and discarding both loses a citation
        # the Catechism actually made.
        if not isinstance(start, Mapped):
            reason = reason or str(start.reason)
            continue
        if not isinstance(end, Mapped):
            reason = reason or str(end.reason)
            continue

        first, last = SPINE.order_of(start.verse), SPINE.order_of(end.verse)
        if first is None or last is None:
            reason = reason or "no_counterpart"
            continue
        if last < first:
            first, last = last, first
        for order in range(first, last + 1):
            address = SPINE.at_order(order)
            if address is not None:
                ids.append(str(address))
    if not ids:
        # Never None. A reason of None buckets under the string "None" in the
        # orphan report and reads as a category rather than a hole.
        return Resolved(reason=reason or "no_counterpart")
    return Resolved(ids=ids, reason=reason)


def index(
    fixture: dict[str, list[str]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], list[Any]]:
    """The fixture, read into both directions and an orphan list.

    An orphan is counted against the paragraph that cited it and indexed
    nowhere, so a consumer never sees a citation pointing at an address that is
    not on the spine.
    """
    by_verse: dict[str, list[dict[str, Any]]] = {}
    by_paragraph: dict[str, list[dict[str, Any]]] = {}
    orphans: list[dict[str, Any]] = []

    for number, labels in sorted(fixture.items(), key=lambda pair: int(pair[0])):
        paragraph = int(number)
        for label in sorted(labels):
            resolved = resolve(label)
            if resolved.reason is not None:
                # A partial keeps its addresses and is still reported, because a
                # citation that half resolved is not a citation that resolved.
                orphans.append(
                    {
                        "paragraph": paragraph,
                        "cited": label,
                        "reason": resolved.reason,
                        "partial": bool(resolved.ids),
                    }
                )
            if not resolved.ids:
                continue
            by_paragraph.setdefault(number, []).append(
                {"cited": label, "ids": resolved.ids}
            )
            for address in resolved.ids:
                by_verse.setdefault(address, []).append(
                    {"paragraph": paragraph, "cited": label}
                )

    return by_verse, by_paragraph, orphans


def render(record: Any) -> str:
    return json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def write(path: Path, record: Any) -> str:
    payload = render(record).encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.environ.get("CATHOLIC_BIBLE_SOURCE"))
    parser.add_argument("--dest", default=None)
    args = parser.parse_args()

    if not args.source:
        parser.error(
            "pass --source or set CATHOLIC_BIBLE_SOURCE to the private repository"
        )

    source = Path(args.source).expanduser().resolve()
    fixture_path = source / FIXTURE
    if not fixture_path.is_file():
        parser.error(f"{fixture_path} is not there")

    dirty = refuse_a_dirty_tree(source)
    if dirty:
        parser.error(dirty)

    with gzip.open(fixture_path, "rb") as handle:
        fixture = json.loads(handle.read())
    by_verse, by_paragraph, orphans = index(fixture)

    dest = Path(args.dest).resolve() if args.dest else DEST
    dest.mkdir(parents=True, exist_ok=True)

    pairs = sum(len(entries) for entries in by_verse.values())
    citations = write(dest / "citations.json", by_verse)
    paragraphs = write(dest / "paragraphs.json", by_paragraph)
    by_reason: dict[str, int] = {}
    for orphan in orphans:
        reason = str(orphan["reason"])
        by_reason[reason] = by_reason.get(reason, 0) + 1
    orphan_report = write(
        dest / "orphans.json",
        {
            "total": len(orphans),
            "by_reason": dict(sorted(by_reason.items())),
            "entries": orphans,
        },
    )

    provenance = {
        "source": {
            "repository": "meu-feed-catolico-api",
            "commit": git(source, "rev-parse", "HEAD"),
            "commit_date": git(source, "log", "-1", "--format=%cI"),
            "private": True,
        },
        "upstream": UPSTREAM,
        "fixtures": {
            FIXTURE: hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        },
        "scheme": str(SCHEME),
        "files": {
            "citations.json": {
                "sha256": citations,
                "verses": len(by_verse),
                "pairs": pairs,
            },
            "paragraphs.json": {
                "sha256": paragraphs,
                "paragraphs": len(by_paragraph),
            },
            "orphans.json": {"sha256": orphan_report, "total": len(orphans)},
        },
        "carries_no_text": True,
    }
    (dest / "PROVENANCE.json").write_text(render(provenance), encoding="utf-8")

    print(f"{len(by_paragraph)} paragraphs cite {len(by_verse)} verses, {pairs} pairs")
    print(f"{len(orphans)} orphans: {dict(sorted(by_reason.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
