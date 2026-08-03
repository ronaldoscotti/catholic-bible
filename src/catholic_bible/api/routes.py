"""The reading routes.

Nested nouns under `/v1`, so a version can never be mistaken for a literal
prefix by the router. The private repo serves a flat shape and orders its
literals first, which works and needs the care. This does not need it.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from catholic_bible.api import errors, models, resolving
from catholic_bible.canon import psalms
from catholic_bible.canon.aliases import ALIASES, Language
from catholic_bible.canon.authored_names import (
    ENGLISH_ABBREVIATIONS,
    ENGLISH_DISPLAY,
    LATIN_ABBREVIATIONS,
    LATIN_NAMES,
)
from catholic_bible.canon.books import CANON
from catholic_bible.canon.formatter import format_reference
from catholic_bible.canon.mapping import Scheme
from catholic_bible.canon.reference import Reference
from catholic_bible.storage import reader
from catholic_bible.storage.database import connect

# The text of a published version never changes. Corrections ship as a new
# version, which is the release policy, so a reader may cache it forever.
IMMUTABLE = "public, max-age=31536000, immutable"

# Not the version list. It grows with every translation and every epic that adds
# one, and a client that cached it for a year never sees the fourth.
CATALOGUE = "public, max-age=3600"

router = APIRouter(prefix="/v1")


def database() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()


Database = Annotated[sqlite3.Connection, Depends(database)]


def _name_of(code: str, language: Language) -> str:
    if language is Language.EN:
        return ENGLISH_DISPLAY[code]
    if language is Language.LA:
        return LATIN_NAMES[code]
    found = CANON.by_code(code)
    return code if found is None else found.name


def _abbreviation_of(code: str, language: Language) -> str:
    if language is Language.EN:
        return ENGLISH_ABBREVIATIONS[code]
    if language is Language.LA:
        return LATIN_ABBREVIATIONS[code]
    found = CANON.by_code(code)
    return code if found is None else found.abbreviation


def _book_out(row: reader.Row, language: Language) -> models.BookOut:
    code = str(row["code"])
    return models.BookOut(
        code=code,
        name=_name_of(code, language),
        abbreviation=_abbreviation_of(code, language),
        testament=str(row["testament"]),
        group=str(row["canon_group"]),
        deuterocanonical=bool(row["deuterocanonical"]),
        chapters=int(row["chapters"]),
    )


def _verse_out(row: reader.Row, language: Language) -> models.VerseOut:
    book, chapter, verse = str(row["book"]), int(row["chapter"]), int(row["verse"])
    point = (chapter, verse)
    return models.VerseOut(
        id=str(row["id"]),
        book=book,
        chapter=chapter,
        verse=verse,
        reference=format_reference(Reference(book, (point, point)), language),
        text=str(row["text"]),
    )


def _numbering(book: str, chapter: int) -> models.Numbering | None:
    if book != "PSA" or not psalms.differs(chapter):
        return None
    return models.Numbering(scheme=Scheme.ORG, counterpart=psalms.counterpart(chapter))


def _version_or_404(connection: sqlite3.Connection, code: str) -> reader.Row:
    found = reader.version(connection, code)
    if found is None:
        raise errors.not_found(
            errors.Reason.UNKNOWN_VERSION, f"no version named {code!r}", code
        )
    return found


def _book_or_404(connection: sqlite3.Connection, written: str) -> reader.Row:
    """A path segment names a book by code or by any name that resolves.

    Case carries meaning at the code boundary. `JUD` is Jude and `Jud` is how a
    Portuguese reader writes Judite, and the alias table already knows.
    """
    code = ALIASES.resolve(written)
    found = None if code is None else reader.book(connection, code)
    if found is None:
        raise errors.not_found(
            errors.Reason.UNKNOWN_BOOK, f"no book named {written!r}", written
        )
    return found


def _chapter_or_404(
    connection: sqlite3.Connection, code: str, number: int
) -> reader.Row:
    found = reader.chapter(connection, code, number)
    if found is None:
        raise errors.not_found(
            errors.Reason.NOT_ON_SPINE,
            f"the spine has no chapter {number} in {code}",
            f"{code} {number}",
        )
    return found


@router.get(
    "/versions",
    summary="Every published translation",
    response_model=list[models.VersionOut],
)
def list_versions(connection: Database, response: Response) -> list[models.VersionOut]:
    response.headers["Cache-Control"] = CATALOGUE
    return [
        models.VersionOut(
            code=str(row["code"]),
            name=str(row["name"]),
            abbreviation=row["abbreviation"],
            language=str(row["language"]),
            year=row["year"],
            source_url=row["source_url"],
            rights=models.Rights.model_validate_json(str(row["rights"])),
            default=bool(row["is_default"]),
        )
        for row in reader.versions(connection)
    ]


@router.get(
    "/versions/{version}/books",
    summary="The books one translation reaches",
    response_model=list[models.BookOut],
    responses=errors.NOT_FOUND,
)
def list_books(
    version: str, connection: Database, response: Response
) -> list[models.BookOut]:
    found = _version_or_404(connection, version)
    language = reader.language_of(str(found["language"]))
    response.headers["Cache-Control"] = CATALOGUE
    return [_book_out(row, language) for row in reader.books_in(connection, version)]


@router.get(
    "/versions/{version}/books/{book}",
    summary="A whole book, grouped by chapter",
    response_model=models.BookWhole,
    responses=errors.NOT_FOUND,
)
def read_book(
    version: str, book: str, connection: Database, response: Response
) -> models.BookWhole:
    found = _version_or_404(connection, version)
    language = reader.language_of(str(found["language"]))
    row = _book_or_404(connection, book)
    code = str(row["code"])

    verses = reader.verses_between(
        connection, version, int(row["first_order"]), int(row["last_order"])
    )
    grouped: dict[int, list[models.VerseOut]] = {}
    for verse in verses:
        grouped.setdefault(int(verse["chapter"]), []).append(
            _verse_out(verse, language)
        )

    response.headers["Cache-Control"] = IMMUTABLE
    return models.BookWhole(
        version=version,
        book=_book_out(row, language),
        chapters=[
            models.ChapterOfBook(
                chapter=number, numbering=_numbering(code, number), verses=members
            )
            for number, members in sorted(grouped.items())
        ],
    )


@router.get(
    "/versions/{version}/books/{book}/chapters/{chapter}",
    summary="One chapter, with its neighbours",
    response_model=models.ChapterOut,
    responses=errors.NOT_FOUND,
)
def read_chapter(
    version: str, book: str, chapter: int, connection: Database, response: Response
) -> models.ChapterOut:
    found = _version_or_404(connection, version)
    language = reader.language_of(str(found["language"]))
    row = _book_or_404(connection, book)
    code = str(row["code"])
    span = _chapter_or_404(connection, code, chapter)

    first, last = int(span["first_order"]), int(span["last_order"])
    verses = reader.verses_between(connection, version, first, last)
    if not verses:
        raise errors.not_found(
            errors.Reason.UNPUBLISHED_IN_VERSION,
            f"{version} does not publish {code} {chapter}",
            f"{code} {chapter}",
        )

    previous = reader.neighbour(connection, version, first, -1)
    following = reader.neighbour(connection, version, first, 1)

    response.headers["Cache-Control"] = IMMUTABLE
    return models.ChapterOut(
        version=version,
        book=_book_out(row, language),
        chapter=chapter,
        numbering=_numbering(code, chapter),
        previous=_neighbour_out(previous),
        next=_neighbour_out(following),
        verses=[_verse_out(verse, language) for verse in verses],
    )


def _neighbour_out(row: reader.Row | None) -> models.Neighbour | None:
    if row is None:
        return None
    return models.Neighbour(book=str(row["book"]), chapter=int(row["chapter"]))


@router.get(
    "/versions/{version}/books/{book}/chapters/{chapter}/verses/{verse}",
    summary="One verse",
    response_model=models.VerseOut,
    responses=errors.NOT_FOUND,
)
def read_verse(
    version: str,
    book: str,
    chapter: int,
    verse: int,
    connection: Database,
    response: Response,
) -> models.VerseOut:
    found = _version_or_404(connection, version)
    language = reader.language_of(str(found["language"]))
    row = _book_or_404(connection, book)
    code = str(row["code"])
    _chapter_or_404(connection, code, chapter)

    address = reader.address(connection, f"{code}.{chapter}.{verse}")
    if address is None:
        raise errors.not_found(
            errors.Reason.NOT_ON_SPINE,
            f"the spine has no verse {verse} in {code} {chapter}",
            f"{code}.{chapter}.{verse}",
        )

    order = int(address["canonical_order"])
    members = reader.verses_between(connection, version, order, order)
    if not members:
        raise errors.not_found(
            errors.Reason.UNPUBLISHED_IN_VERSION,
            f"{version} does not publish {code}.{chapter}.{verse}",
            f"{code}.{chapter}.{verse}",
        )

    response.headers["Cache-Control"] = IMMUTABLE
    return _verse_out(members[0], language)


@router.get(
    "/resolve",
    summary="A written reference, resolved to addresses",
    response_model=models.ResolvedOut,
    responses=errors.UNPROCESSABLE,
)
def resolve(
    connection: Database,
    response: Response,
    ref: str,
    scheme: resolving.InputScheme = resolving.InputScheme.SPINE,
) -> models.ResolvedOut:
    reference, orders = resolving.read(ref, scheme)
    default = reader.default_version(connection)
    language = reader.language_of(str(default["language"]))

    members = reader.verses_between(
        connection, str(default["code"]), orders[0], orders[-1]
    )
    wanted = set(orders)
    covered = [row for row in members if int(row["canonical_order"]) in wanted]

    ids = []
    for order in orders:
        found = reader.at_order(connection, order)
        if found is not None:
            ids.append(str(found["id"]))

    response.headers["Cache-Control"] = IMMUTABLE
    return models.ResolvedOut(
        reference=format_reference(reference, language),
        book=reference.book,
        ids=ids,
        preview=str(covered[0]["text"]) if covered else None,
    )


@router.get(
    "/passage",
    summary="A written reference, read in one or more versions",
    response_model=models.PassageOut,
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
)
def passage(
    connection: Database,
    response: Response,
    ref: str,
    versions: str | None = None,
    scheme: resolving.InputScheme = resolving.InputScheme.SPINE,
) -> models.PassageOut:
    reference, orders = resolving.read(ref, scheme)
    wanted = resolving.versions_named(connection, versions)
    codes = [str(row["code"]) for row in wanted]
    language = reader.language_of(str(wanted[0]["language"]))

    held = reader.texts_at(connection, codes, orders)

    verses = []
    for order in orders:
        address = reader.at_order(connection, order)
        if address is None:
            continue
        book = str(address["book"])
        point = (int(address["chapter"]), int(address["verse"]))
        verses.append(
            models.AlignedVerse(
                id=str(address["id"]),
                book=book,
                chapter=point[0],
                verse=point[1],
                reference=format_reference(Reference(book, (point, point)), language),
                texts=[
                    # Every requested version gets a column, and a version
                    # without the verse gets a null one. A shorter column slides
                    # two rendered translations against each other with nothing
                    # to notice.
                    models.Aligned(version=code, text=held.get((code, order)))
                    for code in codes
                ],
            )
        )

    response.headers["Cache-Control"] = IMMUTABLE
    return models.PassageOut(
        reference=format_reference(reference, language),
        book=reference.book,
        versions=codes,
        verses=verses,
    )
