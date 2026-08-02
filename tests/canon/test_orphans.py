import json

import pytest

from catholic_bible.canon.mapping import OrphanReason
from catholic_bible.canon.orphans import REPORT_PATH, build_report, render

COMMITTED = json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def test_the_committed_report_is_what_the_code_produces() -> None:
    """Regeneration diff. The report cannot drift from the map that made it."""
    assert render(build_report()) == REPORT_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize("scheme", ["vulgate", "org"])
def test_every_reason_in_the_report_is_one_of_the_closed_set(scheme: str) -> None:
    reasons = set(COMMITTED["schemes"][scheme]["by_reason"])
    assert reasons <= {reason.value for reason in OrphanReason}


@pytest.mark.parametrize("scheme", ["vulgate", "org"])
def test_the_vulgate_psalm_titles_are_the_named_class_they_are(scheme: str) -> None:
    assert COMMITTED["schemes"][scheme]["by_reason"]["psalm_title"] == 147
    assert COMMITTED["schemes"][scheme]["by_book"]["PSA"] == {"psalm_title": 147}


def test_daniel_does_not_orphan_under_org() -> None:
    """It did, 251 times, before the inverse stopped trading good addresses."""
    assert "DAN" not in COMMITTED["schemes"]["org"]["by_book"]


def test_the_prayer_of_solomon_orphans_as_a_chapter_the_spine_does_not_have() -> None:
    assert COMMITTED["schemes"]["vulgate"]["by_book"]["SIR"] == {
        "chapter_out_of_range": 13
    }


def test_douay_says_it_is_not_reportable_rather_than_showing_zero() -> None:
    douay = COMMITTED["schemes"]["douay"]
    assert douay["reportable"] is False
    assert douay["why"]


def test_the_report_names_the_data_it_describes() -> None:
    describes = COMMITTED["describes"]
    provenance = json.loads(
        (REPORT_PATH.parent.parent / "PROVENANCE.json").read_text(encoding="utf-8")
    )
    assert describes["source_commit"] == provenance["source"]["commit"]
    assert (
        describes["spine_sha256"] == provenance["files"]["versification.json"]["sha256"]
    )


@pytest.mark.parametrize("scheme", ["vulgate", "org"])
def test_the_counts_add_up(scheme: str) -> None:
    section = COMMITTED["schemes"][scheme]
    assert section["resolved"] + section["orphans"] == section["addresses_examined"]
    assert sum(section["by_reason"].values()) == section["orphans"]
    assert (
        sum(sum(r.values()) for r in section["by_book"].values()) == section["orphans"]
    )
