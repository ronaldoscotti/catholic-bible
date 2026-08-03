#!/usr/bin/env python3
"""Exports the Haydock commentary out of the private source database.

Both languages. The English is the 1859 transcription, public domain. The
Portuguese was produced by a language model and `README.md` says so on its first
screen.

The Catena Aurea lives in the same two tables and does not ship, so the source
code is checked rather than passed through, and every column is named. A
`SELECT *` here would carry material whose provenance is open.

Usage:
    scripts/export-commentary.py --source ~/path/to/private/repo
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
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
    / "commentary"
)

SOURCE_CODE = "haydock"

FIXTURE = "storage/app/haydock-translation/done.jsonl"

# Rows per round trip. The bodies average 800 bytes and the whole source is
# 16.3 MB, so one JSON_ARRAYAGG over all of it would hold the document twice on
# both sides of the pipe for no gain.
PAGE = 2000

LANGUAGES = {"body_html": "en-US", "body_html_translated": "pt-BR"}

# The translation harness wrote its own control markers into 244 Portuguese
# bodies, `[[[REVIEW:category|reason]]` followed by `[[[ID:n]]]` and then the
# whole translation of another entry. The English side is clean. Everything from
# the first marker onward is contamination, so the body is cut there.
_LEAKED = re.compile(r"\[\[\[")

# Authored here. The source database holds one licence string for the whole
# source and cannot say that the two languages have different answers.
RIGHTS = {
    "text": "public-domain",
    "text_basis": (
        "George Leo Haydock died in 1849 and the commentary was printed between "
        "1811 and 1814. Out of copyright everywhere."
    ),
    "translation": "machine",
    "translation_basis": (
        "The Portuguese was produced by a language model under a fixed prompt "
        "requiring faithful rendering, Catholic ecclesiastical terminology and "
        "untouched Scripture citations. Human review is pending and welcome. "
        "See LIMITS.md."
    ),
}


def fetch(container: str, credentials: dict[str, str], offset: int) -> list[Any]:
    """One page of entries, oldest anchor first.

    Ordered inside the subquery so the page boundary is stable between runs.
    JSON_ARRAYAGG makes no ordering promise of its own, and the caller sorts.
    """
    sql = f"""
        SET SESSION group_concat_max_len = 1000000000;
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'start_book', sb.code, 'start_chapter', sv.chapter, 'start_verse', sv.verse,
            'end_book', eb.code, 'end_chapter', ev.chapter, 'end_verse', ev.verse,
            'start_order', e.start_order, 'end_order', e.end_order,
            'label', e.ref_label, 'position', e.sort_order,
            'body_html', e.body_html, 'body_html_translated', e.body_html_translated))
        FROM (
            SELECT e.* FROM bible_commentary_entries e
            JOIN bible_commentaries c ON c.id = e.commentary_id
            WHERE c.code = '{SOURCE_CODE}'
            ORDER BY e.start_order, e.id
            LIMIT {PAGE} OFFSET {offset}
        ) e
        JOIN bible_verses sv ON sv.id = e.verse_start_id
        JOIN bible_books sb ON sb.id = sv.book_id
        JOIN bible_verses ev ON ev.id = e.verse_end_id
        JOIN bible_books eb ON eb.id = ev.book_id
    """
    raw = query(container, credentials, sql)
    if raw in ("", "NULL"):
        return []
    page: list[Any] = json.loads(raw)
    return page


def metadata(container: str, credentials: dict[str, str]) -> dict[str, Any]:
    sql = f"""
        SELECT JSON_OBJECT('name', name, 'author', author, 'description', description)
        FROM bible_commentaries WHERE code = '{SOURCE_CODE}'
    """
    found: dict[str, Any] = json.loads(query(container, credentials, sql))
    return found


def entry_of(row: dict[str, Any]) -> tuple[dict[str, Any], bool, bool]:
    """One published entry, whether its end was clamped and whether it was cut.

    Two notes are labelled `26-7` and `73-4`, meaning verses 26 to 27 and 73 to
    74. The upstream extraction read the elided second number literally, so the
    end lands before the start and the coverage test matches nothing, which
    makes both notes invisible rather than wrong.

    Clamping the end onto the start publishes the note on the first verse of the
    pair and drops it from the second. Reading `27` out of the label would be
    this script authoring a value the source does not hold, and a convincing
    invention is still an invention.
    """
    start_order, end_order = int(row["start_order"]), int(row["end_order"])
    start = f"{row['start_book']}.{row['start_chapter']}.{row['start_verse']}"
    end = f"{row['end_book']}.{row['end_chapter']}.{row['end_verse']}"

    clamped = end_order < start_order
    if clamped:
        end, end_order = start, start_order

    body, cut = {}, False
    for column, language in LANGUAGES.items():
        markup = row.get(column)
        if not markup:
            continue
        leak = _LEAKED.search(markup)
        if leak:
            markup, cut = markup[: leak.start()].rstrip(), True
        body[language] = markup

    return (
        {
            "start": start,
            "end": end,
            "start_order": start_order,
            "end_order": end_order,
            "label": row["label"],
            "position": int(row["position"]),
            "body": body,
        },
        clamped,
        cut,
    )


def write(path: Path, source: dict[str, Any], rows: list[dict[str, Any]]) -> bytes:
    """The published document, one entry per line.

    Streamed rather than serialised whole. The entries are 16.3 MB and a single
    `json.dumps` holds the rows, the document and the bytes at once. One line per
    entry also makes a diff between two exports readable, which a pretty printed
    20705 entry array is not.
    """
    digest = hashlib.sha256()
    with path.open("wb") as handle:

        def emit(text: str) -> None:
            payload = text.encode("utf-8")
            digest.update(payload)
            handle.write(payload)

        emit('{\n "source": ')
        emit(json.dumps(source, ensure_ascii=False, sort_keys=True))
        emit(',\n "entries": [\n')
        for index, entry in enumerate(rows):
            separator = ",\n" if index else ""
            emit(separator + "  " + json.dumps(entry, ensure_ascii=False))
        emit("\n ]\n}\n")
    return digest.digest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.environ.get("CATHOLIC_BIBLE_SOURCE"))
    parser.add_argument("--container", default=CONTAINER)
    parser.add_argument("--dest", default=None)
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

    rows: list[dict[str, Any]] = []
    clamped: list[str] = []
    cut: list[str] = []
    offset = 0
    while page := fetch(args.container, credentials, offset):
        for row in page:
            entry, was_clamped, was_cut = entry_of(row)
            # The source language, not merely some language. A translation
            # without the text it was made from is a note with no provenance.
            if "en-US" not in entry["body"]:
                raise RuntimeError(f"{entry['start']} carries no body in en-US")
            rows.append(entry)
            if was_clamped:
                clamped.append(entry["start"])
            if was_cut:
                cut.append(entry["start"])
        offset += PAGE
        print(f"  {len(rows)} entries")

    rows.sort(key=lambda entry: (entry["start_order"], entry["end_order"]))

    info = metadata(args.container, credentials)
    document = {
        "code": SOURCE_CODE,
        "language": "en-US",
        "translations": ["pt-BR"],
        "rights": RIGHTS,
        **info,
    }
    digest = write(dest / "haydock.json", document, rows)

    languages: dict[str, int] = {}
    for entry in rows:
        for language in entry["body"]:
            languages[language] = languages.get(language, 0) + 1

    provenance = {
        "source": {
            "repository": "meu-feed-catolico-api",
            "commit": git(source, "rev-parse", "HEAD"),
            "commit_date": git(source, "log", "-1", "--format=%cI"),
            "private": True,
        },
        "files": {
            "haydock.json": {
                "sha256": digest.hex(),
                "entries": len(rows),
                "bodies": dict(sorted(languages.items())),
                "clamped": sorted(clamped),
                "cut_at_a_leaked_marker": len(cut),
                "from": "bible_commentary_entries",
                "translation_from": FIXTURE,
            }
        },
    }
    (dest / "PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"exported {len(rows)} entries, {len(clamped)} clamped,"
        f" {len(cut)} cut at a leaked marker"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
