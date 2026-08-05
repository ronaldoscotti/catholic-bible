"""The committed page map, checked without touching the network.

The map is built by a walk over somebody else's site and CI cannot repeat that,
so what CI can hold is that the committed file is internally sound and matches
the checksum recorded beside it. Whether it matches the site is `--verify`, and
that runs on demand.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
CATECHISM = REPO / "src" / "catholic_bible" / "data" / "catechism"
PAGES = CATECHISM / "pages.json"
PROVENANCE = CATECHISM / "PROVENANCE.json"

MAP = json.loads(PAGES.read_text(encoding="utf-8"))
EDITIONS = sorted(MAP["editions"])


def test_the_map_matches_the_checksum_recorded_beside_it() -> None:
    """Without this a hand edited map is undetectable, which no other data here is."""
    recorded = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    assert (
        recorded["files"]["pages.json"]["sha256"]
        == hashlib.sha256(PAGES.read_bytes()).hexdigest()
    )


def test_both_editions_are_published() -> None:
    assert EDITIONS == ["en", "pt"]


@pytest.mark.parametrize("edition", ["en", "pt"])
def test_a_map_opens_at_paragraph_one(edition: str) -> None:
    """Anything else leaves the opening paragraphs with no link at all."""
    assert MAP["editions"][edition]["pages"][0]["first"] == 1


@pytest.mark.parametrize("edition", ["en", "pt"])
def test_pages_ascend_and_no_two_start_at_the_same_paragraph(edition: str) -> None:
    firsts = [page["first"] for page in MAP["editions"][edition]["pages"]]
    assert firsts == sorted(firsts)
    assert len(set(firsts)) == len(firsts)


@pytest.mark.parametrize("edition", ["en", "pt"])
def test_no_page_starts_past_the_end_of_the_catechism(edition: str) -> None:
    firsts = [page["first"] for page in MAP["editions"][edition]["pages"]]
    assert max(firsts) <= MAP["paragraphs"]


def test_the_english_map_is_the_finer_one() -> None:
    """The reason english is the edition the links use, held as a number.

    Portuguese pages hold about a hundred paragraphs each. If that ever stopped
    being true the recommendation would need revisiting, and this is what would
    say so.
    """
    per_page = {
        edition: MAP["paragraphs"] / len(MAP["editions"][edition]["pages"])
        for edition in EDITIONS
    }
    assert per_page["en"] < 10
    assert per_page["pt"] > 50


def test_the_prologue_page_survived_the_range_pattern() -> None:
    """`prologo%201-25_po.html` reads as `201-25` to an unanchored pattern.

    That invented a page starting at 201, which passes every structural guard
    because an invented page holds nothing, and sent paragraphs 201 to 421 to the
    prologue.
    """
    portuguese = MAP["editions"]["pt"]["pages"]
    assert "prologo" in portuguese[0]["file"].lower()
    assert [page["first"] for page in portuguese if page["first"] == 201] == []
