"""The reading routes.

Nested nouns under `/v1`, so a version can never be mistaken for a literal
prefix by the router. The private repo serves a flat shape and orders its
literals first, which works and needs the care. This does not need it.
"""

from __future__ import annotations

import bisect
import sqlite3
from collections.abc import Iterator
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Response

from catholic_bible import cross_references
from catholic_bible.api import errors, models, resolving
from catholic_bible.canon import psalms
from catholic_bible.canon.aliases import (
    ALIASES,
    Language,
    abbreviation_of,
    name_of,
)
from catholic_bible.canon.formatter import format_reference
from catholic_bible.canon.mapping import Scheme
from catholic_bible.canon.reference import Reference
from catholic_bible.search import compile_query
from catholic_bible.storage import reader
from catholic_bible.storage.database import connect

# The text of a published version never changes. Corrections ship as a new
# version, which is the release policy, so a reader may cache it forever.
IMMUTABLE = "public, max-age=31536000, immutable"

# Not the version list, and not an answer that depends on which version is the
# default. Both move without the URL moving, and a year of immutable is a year
# nothing can invalidate.
CATALOGUE = "public, max-age=3600"

router = APIRouter(prefix="/v1", responses=errors.TOO_MANY)

# A path number outside 64 bits reaches `sqlite3` as a bind parameter and raises
# OverflowError, which is a 500 with a traceback. Both ends, because the driver
# refuses both and the first version of this guard only bounded the top. The
# bound is the driver's rather than the canon's, so a chapter of 0 or -1 still
# answers 404 the way it always has.
InPath = Annotated[int, Path(ge=-(2**63), le=2**63 - 1)]

# Cross-references per address at read time. Genesis 1:1 carries more than
# sixty strong ones and a client rendering all of them renders noise. Ported
# rather than derived, and DECISIONS.md says so.
PER_ADDRESS = 30


def database() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()


Database = Annotated[sqlite3.Connection, Depends(database)]


def _book_out(row: reader.Row, language: Language) -> models.BookOut:
    code = str(row["code"])
    return models.BookOut(
        code=code,
        name=name_of(code, language),
        abbreviation=abbreviation_of(code, language),
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
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
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
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
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
    if not verses:
        raise errors.not_found(
            errors.Reason.UNPUBLISHED_IN_VERSION,
            f"{version} does not publish {code}",
            code,
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
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
)
def read_chapter(
    version: str,
    book: str,
    chapter: InPath,
    connection: Database,
    response: Response,
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
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
)
def read_verse(
    version: str,
    book: str,
    chapter: InPath,
    verse: InPath,
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


def _commentary_out(
    connection: sqlite3.Connection,
    reference: Reference,
    orders: list[int],
    language: Language,
) -> models.CommentaryOut:
    """The notes covering a span, grouped by source and then by note.

    The reader returns one row per note and language, in the order the response
    wants them, so grouping is a walk rather than a sort.

    The query reads the envelope and the answer is filtered back to the
    addresses that were asked for. A lectionary reference like `Mc 5,22-24.35-43`
    leaves a hole, and returning the notes on verses 25 to 34 would contradict
    the `ids` beside them in the same response.
    """

    def asked_for(first: int, last: int) -> bool:
        """Whether any requested address falls inside a note's span.

        `orders` is sorted, so the first candidate at or after the note's start
        is the only one worth testing.
        """
        index = bisect.bisect_left(orders, first)
        return index < len(orders) and orders[index] <= last

    rows = [
        row
        for row in reader.commentary_covering(connection, orders[0], orders[-1])
        if asked_for(int(row["first_order"]), int(row["last_order"]))
    ]

    # One range query for every address either the span or a note reaches. A
    # note can start before the span and end after it, so the window is widened
    # rather than assumed, and asking per note would be a round trip per note.
    reached = [
        order for row in rows for order in (row["first_order"], row["last_order"])
    ]
    addresses = reader.addresses_between(
        connection,
        min([orders[0], *reached]),
        max([orders[-1], *reached]),
    )

    entries: dict[str, list[models.CommentaryEntry]] = {}
    seen: dict[int, models.CommentaryEntry] = {}
    for row in rows:
        entry = seen.get(int(row["id"]))
        if entry is None:
            start = addresses[int(row["first_order"])]
            end = addresses[int(row["last_order"])]
            span = (
                (int(start["chapter"]), int(start["verse"])),
                (int(end["chapter"]), int(end["verse"])),
            )
            entry = models.CommentaryEntry(
                start=str(start["id"]),
                end=str(end["id"]),
                reference=format_reference(
                    Reference(str(start["book"]), span), language
                ),
                label=row["label"],
                bodies=[],
            )
            seen[int(row["id"])] = entry
            entries.setdefault(str(row["source"]), []).append(entry)
        entry.bodies.append(
            models.Body(
                language=str(row["language"]),
                html=str(row["html"]),
                text=str(row["text"]),
            )
        )

    return models.CommentaryOut(
        reference=format_reference(reference, language),
        ids=[str(addresses[order]["id"]) for order in orders if order in addresses],
        sources=[
            models.CommentarySource(
                code=str(source["code"]),
                name=str(source["name"]),
                author=source["author"],
                description=source["description"],
                language=str(source["language"]),
                rights=models.CommentaryRights.model_validate_json(
                    str(source["rights"])
                ),
                entries=entries[str(source["code"])],
            )
            for source in reader.commentary_sources(connection)
            if str(source["code"]) in entries
        ],
    )


@router.get(
    "/books/{book}/chapters/{chapter}/verses/{verse}/commentary",
    summary="Commentary on one verse",
    response_model=models.CommentaryOut,
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
)
def read_commentary(
    book: str,
    chapter: InPath,
    verse: InPath,
    connection: Database,
    response: Response,
) -> models.CommentaryOut:
    """Version agnostic, so no version segment.

    A note on John 3:16 is the same note whichever translation is on screen, and
    a version in the path would be a claim about what the answer depends on.
    """
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
    point = (chapter, verse)
    language = reader.language_of(str(reader.default_version(connection)["language"]))

    # Not immutable, for the same reason `/v1/resolve` is not. Every reference
    # in the answer is written in the default version's notation, and which
    # version is the default is not in the URL.
    response.headers["Cache-Control"] = CATALOGUE
    return _commentary_out(
        connection, Reference(code, (point, point)), [order], language
    )


@router.get(
    "/commentary",
    summary="Commentary on a written reference",
    response_model=models.CommentaryOut,
    responses=errors.UNPROCESSABLE,
)
def commentary_for(
    connection: Database,
    response: Response,
    ref: str,
    scheme: resolving.InputScheme = resolving.InputScheme.SPINE,
) -> models.CommentaryOut:
    reference, orders = resolving.read(ref, scheme)
    language = reader.language_of(str(reader.default_version(connection)["language"]))

    # Not immutable, for the same reason `/v1/resolve` is not. Every reference
    # in the answer is written in the default version's notation, and which
    # version is the default is not in the URL.
    response.headers["Cache-Control"] = CATALOGUE
    return _commentary_out(connection, reference, orders, language)


def _cross_references_out(
    connection: sqlite3.Connection,
    reference: Reference,
    orders: list[int],
    language: Language,
) -> models.CrossReferencesOut:
    rows = [
        row
        for row in reader.cross_references_from(
            connection, orders[0], orders[-1], PER_ADDRESS
        )
        if int(row["from_order"]) in set(orders)
    ]

    # Addressed one by one rather than as a range. Targets run from Genesis to
    # Revelation, so the range covering them is the whole spine.
    addresses = reader.addresses_at(
        connection,
        [
            *orders,
            *(int(row["from_order"]) for row in rows),
            *(int(row["to_order"]) for row in rows),
        ],
    )

    found = []
    for row in rows:
        anchor = addresses[int(row["from_order"])]
        target = addresses[int(row["to_order"])]
        book = str(target["book"])
        chapter, verse = int(target["chapter"]), int(target["verse"])
        end = row["to_end"]
        span = ((chapter, verse), (chapter, int(end) if end is not None else verse))
        found.append(
            models.CrossReference(
                id=str(anchor["id"]),
                to=str(target["id"]),
                end=None if end is None else int(end),
                reference=format_reference(Reference(book, span), language),
                whole_chapter=bool(row["whole_chapter"]),
                primary=int(row["weight"]) >= cross_references.PRIMARY,
                source=str(row["source"]),
            )
        )

    drawn = {row.source for row in found}
    return models.CrossReferencesOut(
        reference=format_reference(reference, language),
        ids=[str(addresses[order]["id"]) for order in orders if order in addresses],
        sources=[
            models.CrossReferenceSource(
                code=str(source["code"]),
                name=str(source["name"]),
                rights=str(source["rights"]),
                rights_basis=str(source["rights_basis"]),
                attribution=source["attribution"],
                url=source["url"],
            )
            for source in reader.cross_reference_sources(connection)
            if str(source["code"]) in drawn
        ],
        references=found,
    )


@router.get(
    "/books/{book}/chapters/{chapter}/verses/{verse}/cross-references",
    summary="The passages one verse points at",
    response_model=models.CrossReferencesOut,
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
)
def read_cross_references(
    book: str,
    chapter: InPath,
    verse: InPath,
    connection: Database,
    response: Response,
) -> models.CrossReferencesOut:
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
    point = (chapter, verse)
    language = reader.language_of(str(reader.default_version(connection)["language"]))

    response.headers["Cache-Control"] = CATALOGUE
    return _cross_references_out(
        connection, Reference(code, (point, point)), [order], language
    )


@router.get(
    "/cross-references",
    summary="The passages a written reference points at",
    response_model=models.CrossReferencesOut,
    responses=errors.UNPROCESSABLE,
)
def cross_references_for(
    connection: Database,
    response: Response,
    ref: str,
    scheme: resolving.InputScheme = resolving.InputScheme.SPINE,
) -> models.CrossReferencesOut:
    reference, orders = resolving.read(ref, scheme)
    language = reader.language_of(str(reader.default_version(connection)["language"]))

    response.headers["Cache-Control"] = CATALOGUE
    return _cross_references_out(connection, reference, orders, language)


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

    addresses = reader.addresses_between(connection, orders[0], orders[-1])

    # Not immutable. The preview and the notation both come from whichever
    # version is the default, and that is not in the URL.
    response.headers["Cache-Control"] = CATALOGUE
    return models.ResolvedOut(
        reference=format_reference(reference, language),
        book=reference.book,
        ids=[str(addresses[order]["id"]) for order in orders if order in addresses],
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
    addresses = reader.addresses_between(connection, orders[0], orders[-1])

    verses = []
    for order in orders:
        address = addresses.get(order)
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

    # Immutable only when the caller named the versions. Left to the default,
    # the answer moves when the default does and the URL says nothing.
    response.headers["Cache-Control"] = IMMUTABLE if versions else CATALOGUE
    return models.PassageOut(
        reference=format_reference(reference, language),
        book=reference.book,
        versions=codes,
        verses=verses,
    )


# A result list depends on what is published, so it cannot carry the immutable
# year a verse carries. Short enough that a reader paging through a query pays
# for the scan once.
SEARCHED = "public, max-age=300"

# Ranking sorts every match before it can page, so the cost grows with the
# offset rather than with the page. The three ceilings here bound the offset,
# the page and the query, and the term cap in `search.py` bounds the work one
# query can ask for. LIMITS.md carries the measurements.
DEEPEST = 1000
WIDEST = 100

# A search box, not a document. The compiler already deduplicates and caps the
# terms it builds, and this is the ceiling under it so the parse itself is
# bounded too.
LONGEST = 500

Query_ = Annotated[
    str,
    Query(max_length=LONGEST, description="Words, or a phrase in double quotes"),
]
Offset = Annotated[int, Query(ge=0, le=DEEPEST)]
Limit = Annotated[int, Query(ge=1, le=WIDEST)]
Testament = Annotated[Literal["OLD", "NEW"] | None, Query()]

# Every translation rather than one. A word, because a reader types it, and it
# cannot collide with a version code while every code carries a hyphen.
EVERY = "all"


def _expression_or_422(q: str) -> str:
    """What a person typed, compiled into something FTS5 will run.

    A refusal rather than an empty result. An empty result set is an answer
    about the corpus, and `!!!` is not a question about the corpus.
    """
    built = compile_query(q)
    if built is None:
        raise errors.unprocessable(
            errors.Reason.MALFORMED, "the query carries no searchable word", q
        )
    return built


def _searched_version(connection: sqlite3.Connection, asked: str | None) -> str:
    if asked is None:
        return str(reader.default_version(connection)["code"])
    if asked == EVERY:
        return EVERY
    _version_or_404(connection, asked)
    return asked


def _searched_book(connection: sqlite3.Connection, asked: str | None) -> str | None:
    return None if asked is None else str(_book_or_404(connection, asked)["code"])


def _commentary_languages(connection: sqlite3.Connection) -> set[str]:
    """Read off the bodies rather than off the sources.

    A source declares the language it was written in. A body exists per
    translation, and the Portuguese Haydock is a body without being a source.

    Called only when a language was asked for. As an argument it ran on every
    request, scanning all 41410 bodies to validate a filter nobody sent, which
    was a third of an ordinary commentary search.
    """
    return {
        str(row["language"])
        for row in connection.execute(
            "SELECT DISTINCT language FROM commentary_body"
        ).fetchall()
    }


def _one_of_or_404(
    asked: str | None, published: set[str], reason: errors.Reason, what: str
) -> str | None:
    """A filter nobody publishes is a 404, the way an unknown book already is.

    Passing it through answers `total: 0`, which reads as the corpus having
    nothing to say. `source=haydok` is a typo and not a question about the
    corpus. The empty string is refused for the same reason rather than
    treated as no filter, because a client rendering an unset value would get
    everything back while its interface claimed one.
    """
    if asked is None:
        return None
    if asked not in published:
        raise errors.not_found(reason, f"no {what} named {asked!r}", asked)
    return asked


@router.get(
    "/search",
    summary="Verses carrying a word or a phrase",
    response_model=models.SearchOut,
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
)
def search(
    connection: Database,
    response: Response,
    q: Query_,
    version: Annotated[str | None, Query(description="A code, or all")] = None,
    book: Annotated[
        str | None, Query(description="A code or any name that resolves")
    ] = None,
    testament: Testament = None,
    offset: Offset = 0,
    limit: Limit = 20,
) -> models.SearchOut:
    expression = _expression_or_422(q)
    asked = _searched_version(connection, version)
    code = _searched_book(connection, book)
    scoped = None if asked == EVERY else asked

    languages = {
        str(row["code"]): reader.language_of(str(row["language"]))
        for row in reader.versions(connection)
    }
    rows = reader.search_verses(
        connection, expression, scoped, code, testament, limit, offset
    )

    response.headers["Cache-Control"] = SEARCHED
    return models.SearchOut(
        query=q,
        version=asked,
        total=reader.count_verses(connection, expression, scoped, code, testament),
        offset=offset,
        limit=limit,
        hits=[_verse_hit(row, languages) for row in rows],
    )


def _verse_hit(row: reader.Row, languages: dict[str, Language]) -> models.VerseHit:
    book, chapter, verse = str(row["book"]), int(row["chapter"]), int(row["verse"])
    point = (chapter, verse)
    version = str(row["version"])
    return models.VerseHit(
        id=str(row["id"]),
        book=book,
        chapter=chapter,
        verse=verse,
        reference=format_reference(Reference(book, (point, point)), languages[version]),
        version=version,
        snippet=str(row["snippet"]),
    )


@router.get(
    "/search/commentary",
    summary="Commentary carrying a word or a phrase",
    response_model=models.CommentarySearchOut,
    responses={**errors.NOT_FOUND, **errors.UNPROCESSABLE},
)
def search_commentary(
    connection: Database,
    response: Response,
    q: Query_,
    source: Annotated[str | None, Query(examples=["haydock"])] = None,
    language: Annotated[str | None, Query(examples=["pt-BR"])] = None,
    book: Annotated[
        str | None, Query(description="A code or any name that resolves")
    ] = None,
    offset: Offset = 0,
    limit: Limit = 20,
) -> models.CommentarySearchOut:
    expression = _expression_or_422(q)
    code = _searched_book(connection, book)
    named = _one_of_or_404(
        source,
        {str(row["code"]) for row in reader.commentary_sources(connection)},
        errors.Reason.UNKNOWN_SOURCE,
        "commentary source",
    )
    written = (
        None
        if language is None
        else _one_of_or_404(
            language,
            _commentary_languages(connection),
            errors.Reason.UNKNOWN_LANGUAGE,
            "commentary language",
        )
    )
    rows = reader.search_commentary(
        connection, expression, named, written, code, limit, offset
    )

    response.headers["Cache-Control"] = SEARCHED
    return models.CommentarySearchOut(
        query=q,
        total=reader.count_commentary(connection, expression, named, written, code),
        offset=offset,
        limit=limit,
        hits=[_commentary_hit(row) for row in rows],
    )


def _commentary_hit(row: reader.Row) -> models.CommentaryHit:
    """The anchor, formatted in the language the note is written in.

    A note has one span and two languages, so the reference is written the way
    the body a reader is looking at would write it.
    """
    book = str(row["book"])
    span = (
        (int(row["start_chapter"]), int(row["start_verse"])),
        (int(row["end_chapter"]), int(row["end_verse"])),
    )
    language = reader.language_of(str(row["language"]))
    return models.CommentaryHit(
        source=str(row["source"]),
        language=str(row["language"]),
        start=str(row["start"]),
        end=str(row["end"]),
        book=book,
        reference=format_reference(Reference(book, span), language),
        label=row["label"],
        snippet=str(row["snippet"]),
    )
