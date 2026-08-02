#!/usr/bin/env python3
"""Exports the address data for B1 out of the private source repository.

Only finished data crosses over. Extraction, orthography normalization and the
spine build stay where they are already solved and already tested. See
DECISIONS.md for the choice and what it costs.

Usage:
    scripts/export-spine.py --source ~/path/to/private/repo
    CATHOLIC_BIBLE_SOURCE=~/path/to/private/repo scripts/export-spine.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "src" / "catholic_bible" / "data"

VERBATIM = {
    "versification.json": "database/data/catholic-versification.json",
    "vulgate-scheme.json": "database/data/vulgata-versification.json",
}
CANON_PHP = "database/data/catholic-canon.php"

CANON_KEYS = {"code", "testament", "canon_group", "deutero", "name", "abbr", "aliases"}
CANON_SIZE = 73

# One book per line, opening on the 'code' key. An upstream reformat matches
# nothing and fails the size check below rather than exporting a short canon.
BOOK_LINE = re.compile(r"^\s*\[(?P<fields>'code'.*)\],?\s*$")


def php_canon_to_json(php: str) -> list[dict[str, object]]:
    """Rewrites the canon's PHP array literal as JSON and parses it.

    Each entry is an associative array of single-quoted strings, booleans and
    one nested list, so it becomes a JSON object while the nested list stays a
    list. The file holds no double quote and no escaped apostrophe, which is
    what makes swapping the quote character safe, and both are checked rather
    than assumed because they are properties of one upstream file.
    """
    if '"' in php:
        raise ValueError("canon literal grew a double quote, the quote swap is unsafe")
    if "\\'" in php:
        raise ValueError(
            "canon literal grew an escaped apostrophe, the quote swap is unsafe"
        )

    books: list[dict[str, object]] = []
    for line in php.splitlines():
        match = BOOK_LINE.match(line)
        if match is None:
            continue
        fields = match.group("fields").replace("=>", ":").replace("'", '"')
        book = json.loads("{" + re.sub(r",(\s*\])", r"\1", fields) + "}")
        if set(book) != CANON_KEYS:
            raise ValueError(f"unexpected keys in canon entry: {sorted(book)}")
        book["order"] = len(books) + 1
        books.append(book)

    if len(books) != CANON_SIZE:
        raise ValueError(
            f"expected {CANON_SIZE} books in the canon, parsed {len(books)}"
        )
    return books


def git(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(source), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.environ.get("CATHOLIC_BIBLE_SOURCE"))
    args = parser.parse_args()

    if not args.source:
        parser.error(
            "pass --source or set CATHOLIC_BIBLE_SOURCE to the private repository"
        )

    source = Path(args.source).expanduser().resolve()
    if not (source / CANON_PHP).is_file():
        parser.error(f"{source} does not look like the source repository")

    DEST.mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}
    for name, relative in VERBATIM.items():
        payload = (source / relative).read_bytes()
        (DEST / name).write_bytes(payload)
        written[name] = hashlib.sha256(payload).hexdigest()

    books = php_canon_to_json((source / CANON_PHP).read_text(encoding="utf-8"))
    canon = (json.dumps(books, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (DEST / "canon.json").write_bytes(canon)
    written["canon.json"] = hashlib.sha256(canon).hexdigest()

    # The commit date rather than the run date, so re-exporting at the same
    # source commit is byte for byte identical.
    provenance = {
        "source": {
            "repository": "meu-feed-catolico-api",
            "commit": git(source, "rev-parse", "HEAD"),
            "commit_date": git(source, "log", "-1", "--format=%cI"),
            "private": True,
        },
        "files": {
            name: {"sha256": digest, "from": VERBATIM.get(name, CANON_PHP)}
            for name, digest in sorted(written.items())
        },
    }
    (DEST / "PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for name in sorted(written):
        print(f"  {name}  {written[name][:12]}")
    print(f"exported from {provenance['source']['commit'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
