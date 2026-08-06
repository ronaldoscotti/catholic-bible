#!/usr/bin/env python3
"""Exports the Catechism citation index out of the private source repository.

Paragraph numbers, verse addresses and the citation as the Catechism wrote it.
No Catechism text, permanently, and there is nothing here that could carry any.

The source fixture runs from paragraph to verse. Both directions are published,
because the original is what somebody rendering a paragraph needs and it is
already in hand before the inversion runs.

Citations arrive in english numbering rather than the spine's, so they map
through `Scheme.ENGLISH`. Reading them against the spine directly loses twenty
Psalms, and reading them as `org` puts them on the wrong verse without saying so.

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
from catholic_bible.canon.schemes import ENGLISH  # noqa: E402

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

# The Catechism cites in english numbering. Not `org`, which is anchored on the
# Masoretic text and numbers a psalm superscription as verses. Reading one as the
# other resolves cleanly and lands one or two verses early, which is issue #36.
SCHEME = Scheme.ENGLISH


# A citation nobody wrote. Past this the range is a defect rather than a long
# reading, and walking it would cost more than reporting it.
LONGEST = 400


def walk(
    book: str, span: tuple[tuple[int, int], tuple[int, int]]
) -> tuple[list[tuple[int, int]], str | None]:
    """Every address a written span names, in the numbering it was written in.

    Walking the source rather than the spine. Mapping the two endpoints and
    filling the gap on spine order reads whatever sits between two landings as
    part of the citation, so `Dn 3,1-30` came back as 97 addresses because the
    spine carries the Song of the Three inside that chapter and english does
    not. It also hid an inverted result behind a swap, turning a 67 verse
    citation into two addresses.

    Returns what it walked and a reason when the span is not what was written.
    A range whose last verse english does not have still yields the verses it
    does have, and says so, because `2Cor 9,5-18` against a chapter of fifteen
    is a real citation with a bad end rather than nothing at all.
    """
    (first_chapter, first_verse), (last_chapter, last_verse) = span
    if (last_chapter, last_verse) < (first_chapter, first_verse):
        return [], "inverted_range"

    ceiling = ENGLISH.verse_count(book, last_chapter)
    overshoots = ceiling is not None and last_verse > ceiling

    written: list[tuple[int, int]] = []
    chapter, verse = first_chapter, first_verse
    while (chapter, verse) <= (last_chapter, last_verse):
        written.append((chapter, verse))
        if len(written) > LONGEST:
            return written, "range_too_long"
        count = ENGLISH.verse_count(book, chapter)
        if count is None:
            # Unknown chapter. The single address still resolves or orphans on
            # its own, and guessing a length here would invent addresses.
            return written, None if chapter == last_chapter else "unknown_chapter"
        if verse >= count:
            chapter, verse = chapter + 1, 1
        else:
            verse += 1
    return written, "verse_out_of_range" if overshoots else None


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
    for span in reference.spans():
        written, complaint = walk(reference.book, span)
        reason = reason or complaint
        # A disjoint citation keeps the parts that landed. `Mt 5,3-12.99` is a
        # real verse span beside a bad one, and discarding both loses a citation
        # the Catechism actually made.
        for chapter, verse in written:
            landed = map_address(SCHEME, reference.book, chapter, verse)
            if not isinstance(landed, Mapped):
                reason = reason or str(landed.reason)
                continue
            address = str(landed.verse)
            # A citation may name the same verse twice, `Mt 5,3-5.4`. Publishing
            # it twice inflates the pair count and says nothing extra.
            if address not in ids:
                ids.append(address)
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
    # Merged, not written. `build-catechism-pages.py` records the page map in
    # this same file and runs at a different time, so whichever goes second must
    # not erase the other. Clobbering here took the map's only checksum with it
    # and broke the test that checks it.
    record = dest / "PROVENANCE.json"
    held: dict[str, Any] = {}
    if record.is_file():
        held = json.loads(record.read_text(encoding="utf-8"))
    files = held.setdefault("files", {})
    assert isinstance(files, dict)
    written = provenance.pop("files")
    assert isinstance(written, dict)
    files.update(written)
    held.update(provenance)
    record.write_text(render(held), encoding="utf-8")

    print(f"{len(by_paragraph)} paragraphs cite {len(by_verse)} verses, {pairs} pairs")
    print(f"{len(orphans)} orphans: {dict(sorted(by_reason.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
