"""What the routes return.

No envelope, and the verse id on the wire is the published string. Both are in
DECISIONS.md with what lost.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from catholic_bible.canon.mapping import Scheme


class Rights(BaseModel):
    text: str
    text_basis: str
    fixture: str
    fixture_basis: str


class VersionOut(BaseModel):
    code: str = Field(examples=["matos-soares"])
    name: str
    abbreviation: str | None
    language: str = Field(examples=["pt-BR"])
    year: int | None
    source_url: str | None
    rights: Rights
    default: bool


class BookOut(BaseModel):
    code: str = Field(examples=["PSA"])
    name: str = Field(description="In the language of the version")
    abbreviation: str
    testament: str = Field(examples=["OLD"])
    group: str = Field(examples=["WISDOM"])
    deuterocanonical: bool
    chapters: int


class VerseOut(BaseModel):
    id: str = Field(examples=["PSA.50.3"], description="The published verse id")
    book: str
    chapter: int
    verse: int
    reference: str = Field(examples=["Sl 50,3"])
    text: str


class Numbering(BaseModel):
    """What another scheme calls this chapter.

    A string rather than a number, because the answer is sometimes a range. The
    Vulgate psalm 9 is 9 and 10 elsewhere, and 114 and 115 are both 116.
    """

    scheme: Scheme
    counterpart: str = Field(examples=["9-10"])


class Neighbour(BaseModel):
    book: str
    chapter: int


class ChapterOut(BaseModel):
    version: str
    book: BookOut
    chapter: int
    numbering: Numbering | None
    previous: Neighbour | None
    next: Neighbour | None
    verses: list[VerseOut]


class ChapterOfBook(BaseModel):
    chapter: int
    numbering: Numbering | None
    verses: list[VerseOut]


class BookWhole(BaseModel):
    version: str
    book: BookOut
    chapters: list[ChapterOfBook]


class Aligned(BaseModel):
    version: str
    text: str | None = Field(
        description="Null where this version does not carry the verse"
    )


class AlignedVerse(BaseModel):
    id: str
    book: str
    chapter: int
    verse: int
    reference: str
    texts: list[Aligned]


class PassageOut(BaseModel):
    reference: str = Field(examples=["Jo 3,16-17"])
    book: str
    versions: list[str]
    verses: list[AlignedVerse]


class ResolvedOut(BaseModel):
    reference: str = Field(examples=["1Cor 13,4-7"])
    book: str
    ids: list[str] = Field(examples=[["1CO.13.4", "1CO.13.5"]])
    preview: str | None = Field(
        description=(
            "The first verse of the span the default version publishes. Where "
            "that version has a gap it is a later verse, and the ids say which "
            "addresses the span covers."
        )
    )
