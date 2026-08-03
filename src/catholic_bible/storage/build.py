"""Building the read database out of the published files.

The write side. It reads the canon, the spine and the published corpus and
writes a file. It imports no HTTP and the reader beside it imports none of this,
so the dependency direction runs one way.

The database is derived and never authored. It is not committed, it is rebuilt
from committed inputs whose checksums CI already verifies, and a checksum of its
own would prove nothing those do not.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping

from catholic_bible.canon.books import CANON
from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import VerseId
from catholic_bible.corpus import VERSIONS, Verse, load

DEFAULT_VERSION = "matos-soares"

# `texts` keeps its rowid while the other three drop theirs. An FTS5 external
# content index addresses its content table by rowid, so B9 cannot add search
# beside a WITHOUT ROWID table without rebuilding this one.
SCHEMA = """
CREATE TABLE books (
    code TEXT PRIMARY KEY,
    position INTEGER NOT NULL UNIQUE,
    testament TEXT NOT NULL,
    canon_group TEXT NOT NULL,
    deuterocanonical INTEGER NOT NULL,
    chapters INTEGER NOT NULL
) WITHOUT ROWID;

CREATE TABLE spine (
    canonical_order INTEGER PRIMARY KEY,
    id TEXT NOT NULL UNIQUE,
    book TEXT NOT NULL REFERENCES books(code),
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL
);

CREATE UNIQUE INDEX spine_address ON spine(book, chapter, verse);

CREATE TABLE versions (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT,
    language TEXT NOT NULL,
    year INTEGER,
    source_url TEXT,
    rights TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0
) WITHOUT ROWID;

CREATE TABLE texts (
    version TEXT NOT NULL REFERENCES versions(code),
    canonical_order INTEGER NOT NULL REFERENCES spine(canonical_order),
    text TEXT NOT NULL
);

CREATE UNIQUE INDEX texts_address ON texts(version, canonical_order);
"""


def build(connection: sqlite3.Connection) -> None:
    """The whole database, from the published files, in one transaction."""
    connection.executescript(SCHEMA)
    build_canon(connection)
    build_spine(connection)
    for code in VERSIONS:
        published = load(code)
        build_version(connection, code, published.metadata)
        build_texts(connection, code, published.verses)
    connection.commit()


def build_canon(connection: sqlite3.Connection) -> None:
    connection.executemany(
        "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                book.code,
                book.order,
                str(book.testament),
                str(book.group),
                int(book.deuterocanonical),
                SPINE.chapter_count(book.code) or 0,
            )
            for book in CANON
        ],
    )


def build_spine(connection: sqlite3.Connection) -> None:
    connection.executemany(
        "INSERT INTO spine VALUES (?, ?, ?, ?, ?)",
        [
            (order, f"{book}.{chapter}.{verse}", book, chapter, verse)
            for order, (book, chapter, verse) in enumerate(SPINE.addresses(), start=1)
        ],
    )


def build_version(
    connection: sqlite3.Connection, code: str, metadata: Mapping[str, object]
) -> None:
    connection.execute(
        "INSERT INTO versions (code, name, abbreviation, language, year, source_url,"
        " rights, is_default) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            code,
            metadata["name"],
            metadata.get("abbreviation"),
            metadata["language"],
            metadata.get("year"),
            metadata.get("source_url"),
            json.dumps(metadata.get("rights", {}), ensure_ascii=False, sort_keys=True),
            int(code == DEFAULT_VERSION),
        ),
    )


def build_texts(
    connection: sqlite3.Connection, code: str, verses: Mapping[str, Verse]
) -> None:
    """One version's text, addressed by the order this repo walks.

    The published file carries an order and the spine derives one. B2 proved
    they agree on all 107103 verses and nothing forces them to keep agreeing, so
    a disagreement stops the build rather than pointing a verse at its
    neighbour.
    """
    rows = []
    for key, verse in verses.items():
        parsed = VerseId.parse(key)
        if isinstance(parsed, VerseId):
            walked = SPINE.order_of(parsed)
        else:
            walked = None

        if walked != verse.order:
            raise ValueError(
                f"{key} carries order {verse.order} and the spine walks {walked}"
            )
        rows.append((code, verse.order, verse.text))

    rows.sort(key=lambda row: row[1])
    connection.executemany("INSERT INTO texts VALUES (?, ?, ?)", rows)
