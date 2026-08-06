"""Reading the published Catechism citation index off disk.

Thin, like `cross_references.py` beside it. It hands back what the file holds
and answers no question about the Catechism.

**No Catechism text, permanently.** Not a paragraph, not a title, not a first
line, not a summary, not a breadcrumb. Paragraph numbers are facts and links are
links, and a reader who wants the words goes to `vatican.va`. `LIMITS.md` states
the basis and states that it is thinner than the basis for everything else here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.verse import VerseId

CATECHISM_DIR = DATA_DIR / "catechism"

LANGUAGES = ("en", "pt")
"""The editions `vatican.va` publishes that this links into."""


@dataclass(frozen=True, slots=True)
class Citation:
    """One paragraph citing the verse that was asked about."""

    paragraph: int
    cited: str
    """The citation as the Catechism wrote it, so an interface can say
    `CCC 1223 cites Mt 28,19-20` rather than that a verse is mentioned."""


@dataclass(frozen=True, slots=True)
class Cites:
    """One citation made by the paragraph that was asked about."""

    cited: str
    ids: tuple[VerseId, ...]


@dataclass(frozen=True, slots=True)
class Link:
    """Where to read a paragraph, which is a page rather than a paragraph.

    `vatican.va` publishes no per-paragraph address in either edition, so this
    is the containing page and the number to look for on it. English pages hold
    around eight paragraphs and Portuguese ones around a hundred, which is why
    English is the edition worth linking.
    """

    paragraph: int
    language: str
    url: str
    fragment: str
    """The same page with a text fragment appended. Browsers that support it
    scroll to the paragraph number. No server promises this, so it sits beside
    the plain URL rather than replacing it."""


@dataclass(frozen=True, slots=True)
class Index:
    by_verse: dict[str, tuple[Citation, ...]]
    by_paragraph: dict[int, tuple[Cites, ...]]
    editions: dict[str, tuple[str, list[int]]]
    """Language to its base URL and the first paragraph of each of its pages."""
    files: dict[str, list[str]]


def _address(text: str) -> VerseId:
    parsed = VerseId.parse(text)
    if not isinstance(parsed, VerseId):
        raise ValueError(f"the published index carries {text!r} as an address")
    return parsed


@cache
def load() -> Index:
    citations = json.loads(
        (CATECHISM_DIR / "citations.json").read_text(encoding="utf-8")
    )
    paragraphs = json.loads(
        (CATECHISM_DIR / "paragraphs.json").read_text(encoding="utf-8")
    )
    pages = json.loads((CATECHISM_DIR / "pages.json").read_text(encoding="utf-8"))

    editions = {}
    files = {}
    for language, edition in pages["editions"].items():
        editions[language] = (
            str(edition["base"]),
            [int(page["first"]) for page in edition["pages"]],
        )
        files[language] = [str(page["file"]) for page in edition["pages"]]

    return Index(
        by_verse={
            verse: tuple(
                Citation(paragraph=int(entry["paragraph"]), cited=str(entry["cited"]))
                for entry in entries
            )
            for verse, entries in citations.items()
        },
        by_paragraph={
            int(number): tuple(
                Cites(
                    cited=str(entry["cited"]),
                    ids=tuple(_address(one) for one in entry["ids"]),
                )
                for entry in entries
            )
            for number, entries in paragraphs.items()
        },
        editions=editions,
        files=files,
    )


def citing(verse: VerseId) -> tuple[Citation, ...]:
    """The paragraphs that cite one verse, in the order they appear in print."""
    return load().by_verse.get(str(verse), ())


def cited_by(paragraph: int) -> tuple[Cites, ...]:
    """The verses one paragraph cites."""
    return load().by_paragraph.get(paragraph, ())


def verses() -> tuple[str, ...]:
    return tuple(load().by_verse)


def paragraphs() -> tuple[int, ...]:
    return tuple(load().by_paragraph)


def link(paragraph: int, language: str) -> Link:
    """Where to read one paragraph, in one of the published editions.

    Raises on a language nothing was published for, rather than handing back a
    URL that does not exist, because a link is the one thing here a reader
    follows away from this dataset.
    """
    index = load()
    if language not in index.editions:
        raise KeyError(
            f"no edition published for {language!r}, only {sorted(index.editions)}"
        )

    base, firsts = index.editions[language]
    # The last page that opens at or before this paragraph. The map covers 1 to
    # 2865 with no gap, so a paragraph in range always has one.
    position = 0
    for index_of, first in enumerate(firsts):
        if first > paragraph:
            break
        position = index_of

    # The names come out of the published index as hrefs, so they are already
    # percent encoded. Encoding again turns the prologue's `%20` into `%25`
    # and the link 404s. Only a literal space needs handling.
    url = base + index.files[language][position].replace(" ", "%20")
    return Link(
        paragraph=paragraph,
        language=language,
        url=url,
        fragment=f"{url}#:~:text={paragraph}",
    )
