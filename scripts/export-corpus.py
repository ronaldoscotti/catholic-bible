#!/usr/bin/env python3
"""Exports the three published translations out of the private source database.

The finished corpus lives in MySQL rather than in a file, because normalization
and the 1956 orthography allow-list run at import time. So this reaches into the
private repository's container, which keeps credentials and ports out of this
repo, and writes what comes back.

Usage:
    scripts/export-corpus.py --source ~/path/to/private/repo
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

DEST = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "catholic_bible"
    / "data"
    / "corpus"
)

CONTAINER = "meu-feed-catolico-api-mysql-1"

# The Ave Maria is in the same database and is under copyright. It is not here,
# and neither is the heading column, which carries 2305 of its pericope headings
# grafted onto Matos Soares at import time.
VERSIONS = ("matos-soares", "douay-rheims", "vulgata-clementina")

FIXTURES = {
    "matos-soares": "database/data/matos-soares.json.gz",
    "douay-rheims": "database/data/vulgata-source.json.gz",
    "vulgata-clementina": "database/data/vulgata-source.json.gz",
}

# Authored here. The source database holds NULL in its licence column for every
# version, so this cannot be exported. The text and the file it arrived in are
# separate questions and get separate answers.
RIGHTS = {
    "matos-soares": {
        "text": "public-domain",
        "text_basis": (
            "Brazilian copyright law, article 45. Matos Soares died in 1957 "
            "leaving no successors, so the translation is in the public domain."
        ),
        "fixture": "unstated",
        "fixture_basis": (
            "The upstream dump states no licence. The text is public domain regardless."
        ),
    },
    "douay-rheims": {
        "text": "public-domain",
        "text_basis": (
            "First published 1582 and 1610. Long out of copyright everywhere."
        ),
        "fixture": "MIT",
        "fixture_basis": "github.com/mborders/vulgata ships under MIT.",
    },
    "vulgata-clementina": {
        "text": "public-domain",
        "text_basis": (
            "Promulgated by Clement VIII in 1592. Long out of copyright everywhere."
        ),
        "fixture": "MIT",
        "fixture_basis": "github.com/mborders/vulgata ships under MIT.",
    },
}


def git(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(source), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def query(container: str, credentials: dict[str, str], sql: str) -> str:
    """Runs SQL in the source container and returns the single value it selects.

    utf8mb4 is not optional. The client defaults to latin1 here, which brings
    every accented character back as a raw byte and would corrupt the entire
    Portuguese and Latin corpus silently.
    """
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            container,
            "mysql",
            "--default-character-set=utf8mb4",
            f"-u{credentials['user']}",
            f"-p{credentials['password']}",
            credentials["database"],
            "-N",
            "-B",
            "--raw",
            "-e",
            sql,
        ],
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8").strip()


def read_credentials(source: Path) -> dict[str, str]:
    env = {}
    for line in (source / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(("DB_USERNAME=", "DB_PASSWORD=", "DB_DATABASE=")):
            key, _, value = line.partition("=")
            env[key] = value
    return {
        "user": env["DB_USERNAME"],
        "password": env["DB_PASSWORD"],
        "database": env["DB_DATABASE"],
    }


def fetch(
    container: str, credentials: dict[str, str], code: str
) -> list[dict[str, object]]:
    """Every verse of one version, ordered by the spine's canonical order.

    Columns are named. A SELECT * here would pick up the heading column and ship
    copyrighted material next to public domain text.
    """
    sql = f"""
        SET SESSION group_concat_max_len = 1000000000;
        SELECT JSON_ARRAYAGG(JSON_OBJECT(
            'book', b.code, 'chapter', v.chapter, 'verse', v.verse,
            'order', v.canonical_order, 'text', t.text))
        FROM bible_verse_texts t
        JOIN bible_verses v ON v.id = t.verse_id
        JOIN bible_books b ON b.id = v.book_id
        JOIN bible_versions ver ON ver.id = t.version_id
        WHERE ver.code = '{code}'
    """
    rows: list[dict[str, object]] = json.loads(query(container, credentials, sql))
    rows.sort(key=lambda row: int(str(row["order"])))
    return rows


def metadata(
    container: str, credentials: dict[str, str], code: str
) -> dict[str, object]:
    sql = f"""
        SELECT JSON_OBJECT('name', name, 'abbreviation', abbreviation,
                           'language', language, 'year', year, 'source_url', source_url)
        FROM bible_versions WHERE code = '{code}'
    """
    found: dict[str, object] = json.loads(query(container, credentials, sql))
    return found


def build(
    code: str, rows: list[dict[str, object]], info: dict[str, object]
) -> tuple[bytes, list[str]]:
    """The published document, and the addresses left out of it.

    An address whose text is blank upstream is omitted rather than published as
    an empty string. Twelve of them exist, all in Douay-Rheims, where the MIT
    fixture carries the Latin and leaves the English field empty. An empty
    string is a lie shaped like data: a consumer cannot tell it from a verse
    that genuinely says nothing, while a missing key is unmistakable.
    """
    verses: dict[str, dict[str, object]] = {}
    blank: list[str] = []
    for row in rows:
        key = f"{row['book']}.{row['chapter']}.{row['verse']}"
        if not str(row["text"]).strip():
            blank.append(key)
            continue
        verses[key] = {"order": row["order"], "text": row["text"]}

    document = {
        "version": {"code": code, **info, "rights": RIGHTS[code]},
        "verses": verses,
    }
    payload = (json.dumps(document, ensure_ascii=False, indent=1) + "\n").encode(
        "utf-8"
    )
    return payload, blank


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

    dirty = git(source, "status", "--porcelain", "--", *set(FIXTURES.values()))
    if dirty:
        parser.error(f"the input fixtures have uncommitted changes:\n{dirty}")

    credentials = read_credentials(source)
    dest = Path(args.dest).resolve() if args.dest else DEST
    dest.mkdir(parents=True, exist_ok=True)

    files: dict[str, dict[str, object]] = {}
    for code in VERSIONS:
        rows = fetch(args.container, credentials, code)
        payload, blank = build(code, rows, metadata(args.container, credentials, code))
        (dest / f"{code}.json").write_bytes(payload)
        files[f"{code}.json"] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "verses": len(rows) - len(blank),
            "blank_upstream": blank,
            "from": FIXTURES[code],
        }
        print(
            f"  {code}  {len(rows) - len(blank)} verses  {len(payload) // 1024} KiB"
            + (f"  ({len(blank)} blank upstream, omitted)" if blank else "")
        )

    # A table has no git hash. What the tables are a function of is the import
    # code at this commit plus these fixtures, so both are recorded. What that
    # cannot see is a database built at an older commit, which only the
    # re-import job catches. LIMITS.md says so.
    provenance = {
        "source": {
            "repository": "meu-feed-catolico-api",
            "commit": git(source, "rev-parse", "HEAD"),
            "commit_date": git(source, "log", "-1", "--format=%cI"),
            "private": True,
        },
        "fixtures": {
            relative: hashlib.sha256((source / relative).read_bytes()).hexdigest()
            for relative in sorted(set(FIXTURES.values()))
        },
        "files": dict(sorted(files.items())),
    }
    (dest / "PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"exported from {provenance['source']['commit'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
