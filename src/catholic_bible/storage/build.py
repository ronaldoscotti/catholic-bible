"""Building the read database out of the published files.

The write side. It reads the canon, the spine and the published corpus and
writes a file. It imports no HTTP and the reader beside it imports none of this,
so the dependency direction runs one way.

The database is derived and never authored. It is not committed, it is rebuilt
from committed inputs whose checksums CI already verifies, and a checksum of its
own would prove nothing those do not.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
from collections.abc import Mapping

from catholic_bible import commentary, cross_references
from catholic_bible.canon.books import CANON
from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import VerseId
from catholic_bible.corpus import VERSIONS, Verse, load

DEFAULT_VERSION = "matos-soares"

# The published bodies carry `<em>` and `<strong>` and nothing else, counted over
# all 41410 of them. A parser would be the right tool against unknown HTML and
# this is not unknown HTML.
_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")

# The translation harness leaked its own control markers into 244 bodies once.
# The export cuts them and this refuses to build if any survive, so the same
# contamination cannot reach a reader twice.
_LEAKED = re.compile(r"\[\[\[")

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
    chapters INTEGER NOT NULL,
    first_order INTEGER NOT NULL,
    last_order INTEGER NOT NULL
) WITHOUT ROWID;

-- The spine is dense and canonical order runs contiguously inside a chapter, so
-- a chapter is a range rather than a set. Reading one is an indexed BETWEEN and
-- the neighbouring chapter is the next row, which is what makes previous and
-- next cost nothing.
CREATE TABLE chapters (
    book TEXT NOT NULL REFERENCES books(code),
    chapter INTEGER NOT NULL,
    verses INTEGER NOT NULL,
    first_order INTEGER NOT NULL,
    last_order INTEGER NOT NULL,
    PRIMARY KEY (book, chapter)
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

CREATE TABLE commentary_sources (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    author TEXT,
    description TEXT,
    language TEXT NOT NULL,
    rights TEXT NOT NULL,
    widest INTEGER NOT NULL,
    position INTEGER NOT NULL
) WITHOUT ROWID;

-- Keeps its rowid. `commentary_body` addresses it by that rowid, and B9 may want
-- an FTS5 index over the notes for the same reason `texts` keeps its own.
CREATE TABLE commentary (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL REFERENCES commentary_sources(code),
    first_order INTEGER NOT NULL,
    last_order INTEGER NOT NULL,
    label TEXT,
    position INTEGER NOT NULL
);

CREATE INDEX commentary_coverage ON commentary(source, first_order, last_order);

-- A row per language rather than a `pt` column. Two languages are in the data
-- today and a column named after one of them is a schema that has to change the
-- day a third arrives.
CREATE TABLE commentary_body (
    commentary INTEGER NOT NULL REFERENCES commentary(id),
    language TEXT NOT NULL,
    html TEXT NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (commentary, language)
) WITHOUT ROWID;

CREATE TABLE cross_reference_sources (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rights TEXT NOT NULL,
    rights_basis TEXT NOT NULL,
    attribution TEXT,
    url TEXT
) WITHOUT ROWID;

-- The second layer on the same anchor, and the reason B4 exists. Reading the
-- references on a passage is a range scan on the primary key, which is why the
-- anchor leads it.
CREATE TABLE cross_references (
    from_order INTEGER NOT NULL REFERENCES spine(canonical_order),
    to_order INTEGER NOT NULL REFERENCES spine(canonical_order),
    to_end INTEGER,
    whole_chapter INTEGER NOT NULL,
    weight INTEGER NOT NULL,
    source TEXT NOT NULL REFERENCES cross_reference_sources(code),
    PRIMARY KEY (from_order, to_order)
) WITHOUT ROWID;
"""


def build(connection: sqlite3.Connection) -> None:
    """The whole database, from the published files, in one transaction."""
    connection.executescript(SCHEMA)
    build_spine(connection)
    build_canon(connection)
    for code in VERSIONS:
        published = load(code)
        build_version(connection, code, published.metadata)
        build_texts(connection, code, published.verses)
    for position, code in enumerate(commentary.SOURCES):
        build_commentary(connection, commentary.load(code), position)
    build_cross_references(connection, cross_references.load())

    # Without statistics the planner guesses, and it guessed that scanning all
    # 41410 commentary bodies was cheaper than driving the join off the coverage
    # index. That is 9.5 ms a request against 0.027 ms. The corpus is static, so
    # the statistics are computed once here and never go stale.
    connection.execute("ANALYZE")
    connection.commit()


def build_canon(connection: sqlite3.Connection) -> None:
    """The books and their chapters, with the order range each one spans.

    Runs after the spine, because the ranges are read back off it rather than
    recomputed here. Two walks of the same numbers disagree eventually.
    """
    connection.execute(
        "INSERT INTO chapters "
        "SELECT book, chapter, COUNT(*), MIN(canonical_order), MAX(canonical_order) "
        "FROM spine GROUP BY book, chapter"
    )

    spans = {
        str(book): (int(first), int(last))
        for book, first, last in connection.execute(
            "SELECT book, MIN(first_order), MAX(last_order) FROM chapters GROUP BY book"
        )
    }
    connection.executemany(
        "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                book.code,
                book.order,
                str(book.testament),
                str(book.group),
                int(book.deuterocanonical),
                SPINE.chapter_count(book.code) or 0,
                *spans[book.code],
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


def plain(markup: str) -> str:
    """The body without its markup, for search and for a client that wants none."""
    return _SPACE.sub(" ", html.unescape(_TAG.sub("", markup))).strip()


def build_commentary(
    connection: sqlite3.Connection, source: commentary.Source, position: int
) -> None:
    """One commentary source, its entries and their bodies.

    Both ends of every anchor are checked against the spine rather than trusted,
    the way `build_texts` checks the corpus. A note whose anchor drifted by one
    reads as a note about the neighbouring verse and nothing downstream can tell.

    An entry running backwards stops the build. The export clamps the two that
    do, so reaching here means the export was bypassed or a new one appeared.
    """
    widest = 0
    entries: list[tuple[object, ...]] = []
    bodies: list[tuple[object, ...]] = []
    for index, entry in enumerate(source.entries, start=1):
        for address, order in (
            (entry.start, entry.first_order),
            (entry.end, entry.last_order),
        ):
            walked = SPINE.order_of(address)
            if walked != order:
                raise ValueError(
                    f"{address} carries order {order} and the spine walks {walked}"
                )
        if entry.last_order < entry.first_order:
            raise ValueError(f"{entry.start} ends at {entry.end}, before it starts")

        for language, markup in entry.body.items():
            if _LEAKED.search(markup):
                raise ValueError(
                    f"{entry.start} carries a leaked pipeline marker in {language}"
                )

        widest = max(widest, entry.last_order - entry.first_order)
        entries.append(
            (
                index,
                source.code,
                entry.first_order,
                entry.last_order,
                entry.label,
                entry.position,
            )
        )
        bodies.extend(
            (index, language, markup, plain(markup))
            for language, markup in sorted(entry.body.items())
        )

    metadata = source.metadata
    connection.execute(
        "INSERT INTO commentary_sources (code, name, author, description, language,"
        " rights, widest, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            source.code,
            metadata["name"],
            metadata.get("author"),
            metadata.get("description"),
            metadata["language"],
            json.dumps(metadata.get("rights", {}), ensure_ascii=False, sort_keys=True),
            widest,
            position,
        ),
    )
    connection.executemany("INSERT INTO commentary VALUES (?, ?, ?, ?, ?, ?)", entries)
    connection.executemany("INSERT INTO commentary_body VALUES (?, ?, ?, ?)", bodies)


def build_cross_references(
    connection: sqlite3.Connection, apparatus: cross_references.Apparatus
) -> None:
    """The apparatus, with both ends checked against the spine.

    Same rule as the corpus and the commentary. A reference whose anchor or
    target drifted by one points a reader at a neighbouring verse, which reads
    as a curated connection and is not one.
    """
    connection.executemany(
        "INSERT INTO cross_reference_sources (code, name, rights, rights_basis,"
        " attribution, url) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                code,
                info["name"],
                info["rights"],
                info["rights_basis"],
                info.get("attribution"),
                info.get("url"),
            )
            for code, info in sorted(apparatus.sources.items())
        ],
    )

    rows = []
    for reference in apparatus.references:
        anchor = SPINE.order_of(reference.anchor)
        target = SPINE.order_of(reference.target)
        if anchor is None or target is None:
            raise ValueError(
                f"{reference.anchor} to {reference.target} is not on the spine"
            )
        rows.append(
            (
                anchor,
                target,
                reference.end,
                int(reference.whole_chapter),
                reference.weight,
                reference.source,
            )
        )

    rows.sort(key=lambda row: (row[0], row[1]))
    connection.executemany(
        "INSERT INTO cross_references VALUES (?, ?, ?, ?, ?, ?)", rows
    )
