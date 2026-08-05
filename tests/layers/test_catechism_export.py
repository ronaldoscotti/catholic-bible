"""Reading a Catechism citation onto the spine.

The export runs against a fixture in a repository this one does not have, so
what is testable here is the resolution, which is the part with the decisions in
it. The scheme is `org` rather than the spine's own, ranges expand, and anything
that reaches nothing comes back as an orphan with a reason instead of vanishing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parent.parent.parent


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_catechism", REPO / "scripts" / "export-catechism.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EXPORT = _script()


def test_one_verse_resolves_to_one_address() -> None:
    resolved = EXPORT.resolve("Jo 3,16")
    assert resolved.ids == ["JHN.3.16"]
    assert resolved.reason is None


def test_a_range_expands_onto_every_verse_it_covers() -> None:
    resolved = EXPORT.resolve("Mt 28,19-20")
    assert resolved.ids == ["MAT.28.19", "MAT.28.20"]


def test_a_range_across_chapters_expands_across_them() -> None:
    resolved = EXPORT.resolve("Ex 13,21-14,2")
    assert resolved.ids[0] == "EXO.13.21"
    assert resolved.ids[-1] == "EXO.14.2"
    assert len(resolved.ids) > 2


def test_a_disjoint_citation_expands_both_parts_and_nothing_between() -> None:
    resolved = EXPORT.resolve("Nm 12,3.7-8")
    assert resolved.ids == ["NUM.12.3", "NUM.12.7", "NUM.12.8"]


@pytest.mark.parametrize(
    ("label", "spine"),
    [
        # The source numbers Psalms the modern way and the spine numbers them the
        # Vulgate way. Reading these against the spine directly loses all 20.
        # Neither of these psalms numbers a superscription, so the scheme alone
        # is enough for them.
        ("Sl 119,105", "PSA.118.105"),
        ("Sl 23,1", "PSA.22.1"),
    ],
)
def test_psalms_arrive_through_the_org_scheme(label: str, spine: str) -> None:
    assert EXPORT.resolve(label).ids == [spine]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "issue #36. The Catechism cites in english numbering and `org` is hebrew "
        "numbering, which counts the two superscription lines of psalm 51. The "
        "address resolves cleanly and lands two verses early, so nothing here "
        "can catch it and only the text can. B4's apparatus has the same defect."
    ),
)
def test_a_psalm_with_a_numbered_superscription_lands_two_verses_early() -> None:
    # PSA.50.19 is "cor contritum et humiliatum", which is english Ps 51,17.
    # PSA.50.17 is "Domine, labia mea aperies", which is english Ps 51,15.
    assert EXPORT.resolve("Sl 51,17").ids == ["PSA.50.19"]


def test_a_verse_past_the_end_of_its_chapter_is_an_orphan_with_a_reason() -> None:
    # The one label in the real fixture that reaches nothing. 2 Corinthians 9
    # has fifteen verses and the printed apparatus says 5-18.
    resolved = EXPORT.resolve("2Cor 9,5-18")
    assert resolved.ids == []
    assert resolved.reason == "verse_out_of_range"


def test_an_unknown_book_is_an_orphan_rather_than_a_crash() -> None:
    resolved = EXPORT.resolve("Zzz 9,9")
    assert resolved.ids == []
    assert resolved.reason == "unknown_book"


def test_a_malformed_label_is_an_orphan_rather_than_a_crash() -> None:
    resolved = EXPORT.resolve("this is not a reference")
    assert resolved.ids == []
    assert resolved.reason is not None


def test_the_index_runs_both_ways_over_the_same_pairs() -> None:
    by_verse, by_paragraph, orphans = EXPORT.index({"1223": ["Mt 28,19-20"]})

    assert by_verse == {
        "MAT.28.19": [{"paragraph": 1223, "cited": "Mt 28,19-20"}],
        "MAT.28.20": [{"paragraph": 1223, "cited": "Mt 28,19-20"}],
    }
    assert by_paragraph == {
        "1223": [{"cited": "Mt 28,19-20", "ids": ["MAT.28.19", "MAT.28.20"]}]
    }
    assert orphans == []


def test_an_orphan_is_recorded_against_its_paragraph_and_indexed_nowhere() -> None:
    by_verse, by_paragraph, orphans = EXPORT.index({"2122": ["2Cor 9,5-18"]})

    assert by_verse == {}
    assert by_paragraph == {}
    assert orphans == [
        {"paragraph": 2122, "cited": "2Cor 9,5-18", "reason": "verse_out_of_range"}
    ]


def test_no_exported_record_carries_anything_but_numbers_and_addresses() -> None:
    """The whole epic in one assertion.

    A field holding text would arrive here as a string that is neither a verse
    id nor a citation label, so the shape of the record is the guard rather than
    a list of banned field names written beside it.
    """
    _, by_paragraph, _ = EXPORT.index({"1223": ["Mt 28,19-20"], "206": ["Jz 13,18"]})

    for entries in by_paragraph.values():
        for entry in entries:
            assert set(entry) == {"cited", "ids"}
