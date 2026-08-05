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
    "english-scheme.json": "database/data/english-versification.json",
}
CANON_PHP = "database/data/catholic-canon.php"
DOUAY_PHP = "app/Services/Bible/DouayCanonMap.php"

CANON_KEYS = {"code", "testament", "canon_group", "deutero", "name", "abbr", "aliases"}
CANON_SIZE = 73

# One book per line, opening on the 'code' key. An upstream reformat matches
# nothing and fails the size check below rather than exporting a short canon.
BOOK_LINE = re.compile(r"^\s*\[(?P<fields>'code'.*)\],?\s*$")

DOUAY_PAIR = re.compile(r"'(?P<name>[A-Z0-9 ]+)'\s*=>\s*'(?P<code>[A-Z0-9]{3})'")

APPARATUS_PHP = "app/Services/Bible/DouayReferenceParser.php"
SINGLE_PAIR = re.compile(r"'(?P<abbr>[a-z]{2,})'\s*=>\s*'(?P<code>[A-Z0-9]{3})'")
NUMBERED_PAIR = re.compile(r"'(?P<abbr>[a-z]{2,})'\s*=>\s*\[(?P<codes>[^\]]+)\]")

SOURCE_OF = {
    **VERBATIM,
    "canon.json": CANON_PHP,
    "douay-names.json": DOUAY_PHP,
    "latin-abbreviations.json": APPARATUS_PHP,
}


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


def php_douay_names_to_json(php: str, codes: set[str]) -> dict[str, str]:
    """Reads the Douay book names out of the map's PHP const.

    Names are the ones the Douay-Rheims and Haydock print, so `1 KINGS` is
    Samuel here and `3 KINGS` is Kings. That is correct Douay usage and it
    collides with modern English, which the alias layer resolves in favour of
    Douay because this dataset is anchored on that apparatus.
    """
    names = {m.group("name"): m.group("code") for m in DOUAY_PAIR.finditer(php)}
    if len(names) != CANON_SIZE:
        raise ValueError(f"expected {CANON_SIZE} Douay names, parsed {len(names)}")
    unknown = sorted(set(names.values()) - codes)
    if unknown:
        raise ValueError(f"Douay names point at codes outside the canon: {unknown}")
    return names


def php_latin_abbreviations_to_json(php: str, codes: set[str]) -> dict[str, object]:
    """Reads the Latin abbreviations out of the Douay apparatus parser.

    The original Douay prints its cross-references in Latin, so the parser that
    reads that apparatus already carries the abbreviations: `ios`, `iudic`,
    `sap`, `eccli`, `apoc`.

    The two tables stay apart. Some abbreviations are in both, and merging them
    loses the distinction that resolves them: bare `io` is John while `1 io` is
    the first epistle. Flattened into one list the number would index the wrong
    book.
    """
    body = php[php.index("const SINGLE") :]
    numbered_at = body.index("const NUMBERED")
    defaults_at = body.index("BARE_DEFAULTS_TO_FIRST")

    single = {m["abbr"]: m["code"] for m in SINGLE_PAIR.finditer(body[:numbered_at])}
    numbered = {
        m["abbr"]: re.findall(r"'([A-Z0-9]{3})'", m["codes"])
        for m in NUMBERED_PAIR.finditer(body[numbered_at:defaults_at])
    }
    defaults_end = body.index("];", defaults_at)
    defaults = re.findall(r"'([a-z]{2,})'", body[defaults_at:defaults_end])

    seen = set(single.values()) | {c for targets in numbered.values() for c in targets}
    unknown = sorted(seen - codes)
    if unknown:
        raise ValueError(f"Latin abbreviations point outside the canon: {unknown}")
    if len(single) < 100 or not numbered or not defaults:
        raise ValueError(f"expected the full apparatus, parsed {len(single)} single")
    stray = sorted(set(defaults) - set(numbered))
    if stray:
        raise ValueError(f"bare defaults that name no numbered book: {stray}")
    # The alias layer spells these numbers in Roman up to IV, which the four
    # books of Kings already use to the last slot. A fifth would break at import.
    longest = max(len(targets) for targets in numbered.values())
    if longest > 4:
        raise ValueError(
            f"a numbered abbreviation carries {longest} books, Roman stops at IV"
        )

    return {
        "single": dict(sorted(single.items())),
        "numbered": dict(sorted(numbered.items())),
        "bare_defaults_to_first": sorted(set(defaults)),
    }


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
    parser.add_argument("--dest", default=None)
    args = parser.parse_args()

    if not args.source:
        parser.error(
            "pass --source or set CATHOLIC_BIBLE_SOURCE to the private repository"
        )

    source = Path(args.source).expanduser().resolve()
    if not (source / CANON_PHP).is_file():
        parser.error(f"{source} does not look like the source repository")

    # Provenance names a commit. If a file being read has uncommitted edits, the
    # bytes shipped are not the bytes that commit holds and the record lies,
    # while the checksums still match because they come from those same bytes.
    # Only the files actually read are checked, so unrelated dirt does not block.
    dirty = git(source, "status", "--porcelain", "--", *SOURCE_OF.values())
    if dirty:
        parser.error(f"the source files have uncommitted changes:\n{dirty}")

    dest = Path(args.dest).resolve() if args.dest else DEST
    dest.mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}
    for name, relative in VERBATIM.items():
        payload = (source / relative).read_bytes()
        (dest / name).write_bytes(payload)
        written[name] = hashlib.sha256(payload).hexdigest()

    books = php_canon_to_json((source / CANON_PHP).read_text(encoding="utf-8"))
    canon = (json.dumps(books, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (dest / "canon.json").write_bytes(canon)
    written["canon.json"] = hashlib.sha256(canon).hexdigest()

    names = php_douay_names_to_json(
        (source / DOUAY_PHP).read_text(encoding="utf-8"),
        {str(book["code"]) for book in books},
    )
    douay = (json.dumps(names, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (dest / "douay-names.json").write_bytes(douay)
    written["douay-names.json"] = hashlib.sha256(douay).hexdigest()

    latin = php_latin_abbreviations_to_json(
        (source / APPARATUS_PHP).read_text(encoding="utf-8"),
        {str(book["code"]) for book in books},
    )
    payload = (json.dumps(latin, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (dest / "latin-abbreviations.json").write_bytes(payload)
    written["latin-abbreviations.json"] = hashlib.sha256(payload).hexdigest()

    # The commit date rather than the run date, so re-exporting at the same
    # source commit is byte for byte identical.
    commit = git(source, "rev-parse", "HEAD")
    provenance = {
        "source": {
            "repository": "meu-feed-catolico-api",
            "commit": commit,
            "commit_date": git(source, "log", "-1", "--format=%cI"),
            "private": True,
        },
        "files": {
            name: {"sha256": digest, "from": SOURCE_OF[name]}
            for name, digest in sorted(written.items())
        },
    }
    (dest / "PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for name in sorted(written):
        print(f"  {name}  {written[name][:12]}")
    print(f"exported from {commit[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
