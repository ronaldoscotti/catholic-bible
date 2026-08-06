"""Reading the published citation index, and building a link out of it.

The dataset answers in both directions and holds no Catechism text. The link is
a page plus a paragraph number, because `vatican.va` publishes no per-paragraph
address in either edition.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from catholic_bible import catechism
from catholic_bible.canon.verse import VerseId

DATA = Path(catechism.__file__).resolve().parent / "data" / "catechism"


def test_a_verse_answers_with_the_paragraphs_that_cite_it() -> None:
    citing = catechism.citing(VerseId("MAT", 28, 19))

    assert citing, "Matthew 28,19 is the most cited verse in the Catechism"
    assert all(1 <= entry.paragraph <= 2865 for entry in citing)
    assert any(entry.cited.startswith("Mt 28") for entry in citing)


def test_a_verse_nobody_cites_answers_with_nothing_rather_than_raising() -> None:
    assert catechism.citing(VerseId("NUM", 7, 66)) == ()


def test_a_paragraph_answers_with_the_verses_it_cites() -> None:
    cites = catechism.cited_by(1223)

    assert cites
    for entry in cites:
        assert entry.ids
        assert all(isinstance(address, VerseId) for address in entry.ids)


def test_a_paragraph_that_cites_nothing_answers_with_nothing() -> None:
    assert catechism.cited_by(1) == ()


def test_the_two_directions_agree() -> None:
    """Every pair in one index is a pair in the other, or one of them is lying."""
    forward = {
        (str(address), entry.cited)
        for paragraph in catechism.paragraphs()
        for entry in catechism.cited_by(paragraph)
        for address in entry.ids
    }
    backward = {
        (verse, entry.cited)
        for verse in catechism.verses()
        for entry in catechism.citing(VerseId.parse(verse))  # type: ignore[arg-type]
    }
    assert forward == backward


@pytest.mark.parametrize("language", ["en", "pt"])
def test_a_link_names_a_page_and_the_paragraph_it_wants(language: str) -> None:
    link = catechism.link(199, language)

    assert link.url.startswith("https://www.vatican.va/archive/")
    assert " " not in link.url, "a space in a URL is not a URL"
    assert link.paragraph == 199
    assert link.language == language


def test_the_english_link_lands_closer_than_the_portuguese_one() -> None:
    """The reason the English edition is the one the examples use."""
    pages = json.loads((DATA / "pages.json").read_text(encoding="utf-8"))
    per_page = {
        edition: pages["paragraphs"] / len(pages["editions"][edition]["pages"])
        for edition in ("en", "pt")
    }
    assert per_page["en"] < per_page["pt"] / 5


def test_a_link_carries_a_text_fragment_as_well_as_the_page() -> None:
    """Best effort. It is a browser feature and no server promises it."""
    link = catechism.link(1223, "en")

    assert link.fragment.endswith("#:~:text=1223")
    assert link.fragment.startswith(link.url)


def test_the_prologue_is_reachable_in_portuguese() -> None:
    """Its page is the one whose name carries a space, so it is the one that breaks."""
    link = catechism.link(3, "pt")

    assert "prologo" in link.url.lower()
    assert "%20" in link.url


def test_every_paragraph_in_the_index_can_be_linked() -> None:
    for paragraph in catechism.paragraphs():
        for language in ("en", "pt"):
            assert catechism.link(paragraph, language).url


def test_a_language_nobody_published_is_refused() -> None:
    with pytest.raises(KeyError):
        catechism.link(199, "la")


def test_not_one_field_could_hold_catechism_text() -> None:
    """The whole epic in one assertion.

    Every published value is a paragraph number, a spine address or the citation
    as the Catechism wrote it. A field holding text would have to be a string
    that is none of those, so the shape is the guard rather than a list of
    banned names written beside it.
    """
    published = json.loads((DATA / "citations.json").read_text(encoding="utf-8"))
    for entries in published.values():
        for entry in entries:
            assert set(entry) == {"paragraph", "cited"}
            assert isinstance(entry["paragraph"], int)
            assert len(entry["cited"]) < 32, entry["cited"]

    other = json.loads((DATA / "paragraphs.json").read_text(encoding="utf-8"))
    for entries in other.values():
        for entry in entries:
            assert set(entry) == {"cited", "ids"}
            assert all(VerseId.parse(address) is not None for address in entry["ids"])


def test_the_orphan_report_says_what_did_not_resolve_and_why() -> None:
    report = json.loads((DATA / "orphans.json").read_text(encoding="utf-8"))

    assert report["total"] == len(report["entries"])
    assert set(report["by_reason"])
    for entry in report["entries"]:
        assert set(entry) == {"paragraph", "cited", "reason", "partial"}
        assert entry["reason"]
