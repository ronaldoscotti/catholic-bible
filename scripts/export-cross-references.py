#!/usr/bin/env python3
"""Exports the cross-reference apparatus out of the private source database.

Three sources. The Ave Maria apparatus is not one of them and is not a flag
either, because a flag can be passed by accident and an absent source cannot.
Its 879 entries were scraped out of the same protected 1957 edition whose text
this repository already refuses, and they carry exactly one deuterocanonical
link, so nothing is lost by refusing them too.

Usage:
    scripts/export-cross-references.py --source ~/path/to/private/repo
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _source import (  # noqa: E402
    CONTAINER,
    git,
    query,
    read_credentials,
    refuse_a_dirty_tree,
)

DEST = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "catholic_bible"
    / "data"
    / "cross-references"
)

ORPHANS = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "catholic_bible"
    / "data"
    / "derived"
    / "cross-reference-orphans.json"
)

PAGE = 20000

# Authored here. The source database holds no licence column for these, and the
# three answers are different enough that one string could not carry them.
SOURCES: dict[str, dict[str, Any]] = {
    "douay": {
        "name": "The Douay-Rheims marginal apparatus",
        "fixture": "database/data/douay-cross-references.json.gz",
        "structured": False,
        "rights": "CC0",
        "rights_basis": (
            "The 1582 and 1610 margins. Out of copyright everywhere, and the "
            "transcription is dedicated to the public domain."
        ),
        "attribution": None,
        "url": None,
    },
    "na27": {
        "name": "New Testament allusions to the deuterocanonical books",
        "fixture": "database/data/na27-cross-references.json.gz",
        "structured": True,
        "rights": "uncopyrightable-facts",
        "rights_basis": (
            "292 pairs of addresses and no text of any kind. A bare pair of "
            "Scripture references is a fact about Scripture rather than an "
            "expression of anyone's editorial work. LIMITS.md carries the "
            "reasoning and the fact that it is a reading rather than a ruling."
        ),
        "attribution": None,
        "url": None,
    },
    "openbible": {
        "name": "OpenBible.info cross-references",
        "fixture": "database/data/openbible-cross-references.json.gz",
        "structured": True,
        "rights": "CC BY 4.0",
        "rights_basis": (
            "Published by OpenBible.info under Creative Commons Attribution. "
            "Attribution is a condition of the licence and travels with the data."
        ),
        "attribution": "Cross-references courtesy of OpenBible.info, CC BY 4.0.",
        "url": "https://www.openbible.info/labs/cross-references/",
    },
}


def fetch(container: str, credentials: dict[str, str], offset: int) -> list[Any]:
    """One page of resolved references, both ends already on the spine."""
    codes = ", ".join(f"'{code}'" for code in SOURCES)
    sql = f"""
        SET SESSION group_concat_max_len = 1000000000;
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'from_book', fb.code, 'from_chapter', fv.chapter, 'from_verse', fv.verse,
            'to_book', tb.code, 'to_chapter', tv.chapter, 'to_verse', tv.verse,
            'to_end', x.target_verse_end, 'whole_chapter', x.whole_chapter,
            'weight', x.weight, 'source', x.source))
        FROM (
            SELECT x.* FROM bible_cross_references x
            WHERE x.source IN ({codes}) AND x.target_verse_id IS NOT NULL
            ORDER BY x.verse_id, x.id
            LIMIT {PAGE} OFFSET {offset}
        ) x
        JOIN bible_verses fv ON fv.id = x.verse_id
        JOIN bible_books fb ON fb.id = fv.book_id
        JOIN bible_verses tv ON tv.id = x.target_verse_id
        JOIN bible_books tb ON tb.id = tv.book_id
    """
    raw = query(container, credentials, sql)
    if raw in ("", "NULL"):
        return []
    page: list[Any] = json.loads(raw)
    return page


def reference_of(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """One published reference, keyed by the address it hangs on.

    `end` and `chapter` are omitted at their default. 155901 of the references
    point at a single verse and all but 1062 point at a verse rather than a
    whole chapter, so writing both on every row would be four megabytes of the
    word null.
    """
    anchor = f"{row['from_book']}.{row['from_chapter']}.{row['from_verse']}"
    entry: dict[str, Any] = {
        "to": f"{row['to_book']}.{row['to_chapter']}.{row['to_verse']}",
        "weight": int(row["weight"]),
        "source": row["source"],
    }
    if row["to_end"] is not None and int(row["to_end"]) != int(row["to_verse"]):
        entry["end"] = int(row["to_end"])
    if row["whole_chapter"]:
        entry["chapter"] = True
    return anchor, entry


def orphan_report(
    source: Path, exported: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    """What the fixtures hold that the exported rows do not.

    The importer counts unresolved entries and throws them away, so the database
    cannot answer this. The fixtures are files, so a diff against them can.

    It is a diff and not a second resolver. The comparison is per pair of books,
    because the versification remap moves a chapter and a verse and never moves a
    book, so counting `GEN -> REV` on both sides needs none of the mapping code.

    The gap it reports is an upper bound rather than an orphan count. It holds
    entries the import could not resolve and entries another source had already
    written, which the unique constraint drops without asking. Both are
    absences and only the first is an orphan. `LIMITS.md` says so.

    The Douay fixture is prose. Its references are strings like
    `Act. 14, 15. 17, 24.` that only the parser can split, so it is reported at
    the anchor level and the per reference number is stated as unavailable
    rather than estimated.
    """
    shipped: dict[str, Counter[str]] = {}
    for anchor, entries in exported.items():
        anchor_book = anchor.split(".")[0]
        for entry in entries:
            target_book = str(entry["to"]).split(".")[0]
            shipped.setdefault(str(entry["source"]), Counter())[
                f"{anchor_book} -> {target_book}"
            ] += 1

    report: dict[str, Any] = {}
    for code, info in SOURCES.items():
        with gzip.open(source / str(info["fixture"])) as handle:
            raw = json.loads(handle.read())
        landed = shipped.get(code, Counter())

        if not info["structured"]:
            report[code] = {
                "fixture_anchors": len(raw),
                "fixture_pairs": None,
                "exported": sum(landed.values()),
                "unaccounted": None,
                "why": (
                    "The fixture holds reference strings rather than addresses. "
                    "Splitting them needs the parser, and a second parser here "
                    "would be a second set of bugs rather than a check."
                ),
            }
            continue

        wanted: Counter[str] = Counter()
        for entry in raw:
            for ref in entry["refs"]:
                wanted[f"{entry['book']} -> {ref['book']}"] += 1

        short = {
            pair: count - landed.get(pair, 0)
            for pair, count in wanted.items()
            if count > landed.get(pair, 0)
        }
        report[code] = {
            "fixture_anchors": len(raw),
            "fixture_pairs": sum(wanted.values()),
            "exported": sum(landed.values()),
            "unaccounted": sum(short.values()),
            "worst": dict(sorted(short.items(), key=lambda pair: -pair[1])[:20]),
        }
    return report


def write(path: Path, sources: dict[str, Any], anchors: dict[str, Any]) -> bytes:
    """The published document, one anchor per line.

    Grouped by anchor, so the address is written once instead of once per
    reference hanging off it. 26726 anchors carry 207636 references.
    """
    digest = hashlib.sha256()
    with path.open("wb") as handle:

        def emit(text: str) -> None:
            payload = text.encode("utf-8")
            digest.update(payload)
            handle.write(payload)

        emit('{\n "sources": ')
        emit(json.dumps(sources, ensure_ascii=False, indent=2, sort_keys=True))
        emit(',\n "references": {\n')
        for index, (anchor, entries) in enumerate(sorted(anchors.items())):
            separator = ",\n" if index else ""
            emit(f'{separator}  "{anchor}": ' + json.dumps(entries, ensure_ascii=False))
        emit("\n }\n}\n")
    return digest.digest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.environ.get("CATHOLIC_BIBLE_SOURCE"))
    parser.add_argument("--container", default=CONTAINER)
    parser.add_argument("--dest", default=None)
    parser.add_argument("--orphans", default=None)
    args = parser.parse_args()

    if not args.source:
        parser.error(
            "pass --source or set CATHOLIC_BIBLE_SOURCE to the private repository"
        )

    source = Path(args.source).expanduser().resolve()
    if not (source / ".env").is_file():
        parser.error(f"{source} does not look like the source repository")

    dirty = refuse_a_dirty_tree(source)
    if dirty:
        parser.error(dirty)

    credentials = read_credentials(source)
    dest = Path(args.dest).resolve() if args.dest else DEST
    dest.mkdir(parents=True, exist_ok=True)

    anchors: dict[str, list[dict[str, Any]]] = {}
    total, offset = 0, 0
    while page := fetch(args.container, credentials, offset):
        for row in page:
            anchor, entry = reference_of(row)
            anchors.setdefault(anchor, []).append(entry)
            total += 1
        offset += PAGE
        print(f"  {total} references")

    for entries in anchors.values():
        entries.sort(key=lambda entry: (-int(entry["weight"]), str(entry["to"])))

    internal = ("fixture", "structured")
    published = {
        code: {key: value for key, value in info.items() if key not in internal}
        for code, info in SOURCES.items()
    }
    digest = write(dest / "references.json", published, anchors)

    by_source: dict[str, int] = {}
    for entries in anchors.values():
        for entry in entries:
            by_source[entry["source"]] = by_source.get(entry["source"], 0) + 1

    provenance = {
        "source": {
            "repository": "meu-feed-catolico-api",
            "commit": git(source, "rev-parse", "HEAD"),
            "commit_date": git(source, "log", "-1", "--format=%cI"),
            "private": True,
        },
        "fixtures": {
            str(info["fixture"]): hashlib.sha256(
                (source / str(info["fixture"])).read_bytes()
            ).hexdigest()
            for info in SOURCES.values()
        },
        "files": {
            "references.json": {
                "sha256": digest.hex(),
                "anchors": len(anchors),
                "references": total,
                "by_source": dict(sorted(by_source.items())),
                "excluded": {
                    "ave-maria": (
                        "Scraped from the Ave Maria apparatus, the same protected "
                        "1957 edition whose text this repository refuses. 879 rows."
                    )
                },
                "from": "bible_cross_references",
            }
        },
    }
    (dest / "PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    orphans = Path(args.orphans) if args.orphans else ORPHANS
    orphans.parent.mkdir(parents=True, exist_ok=True)
    orphans.write_text(
        json.dumps(orphan_report(source, anchors), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"exported {total} references on {len(anchors)} anchors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
