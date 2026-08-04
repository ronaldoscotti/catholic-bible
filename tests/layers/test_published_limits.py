"""Every orphan number `LIMITS.md` prints, checked against the file it came from.

A failure rate published in prose and computed nowhere is a failure rate nobody
can check, and this document exists to be checked. The tables are read out of
the markdown and compared to `orphans.json` and `coverage.json`, so editing one
without the other turns the suite red.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
LIMITS = (REPO / "LIMITS.md").read_text(encoding="utf-8")
ORPHANS = json.loads((REPO / "data" / "orphans.json").read_text(encoding="utf-8"))
COVERAGE = json.loads((REPO / "data" / "coverage.json").read_text(encoding="utf-8"))

SCHEMES = ORPHANS["schemes"]

# Display name in the table to the USX code the report keys on.
BOOKS = {
    "2 Esdras": "2ES",
    "4 Maccabees": "4MA",
    "1 Esdras": "1ES",
    "Greek Esther": "ESG",
    "Greek Daniel": "DAG",
    "3 Maccabees": "3MA",
    "6 Ezra": "6EZ",
    "Letter of Jeremiah": "LJE",
    "Song of the Three": "S3Y",
    "Susanna": "SUS",
    "Bel and the Dragon": "BEL",
    "Laodiceans": "LAO",
    "Prayer of Manasseh": "MAN",
    "Psalm 151": "PS2",
}


def section(heading: str) -> str:
    """The text under one `###` heading, up to the next heading of any level."""
    found = re.search(rf"^### {re.escape(heading)}$(.*?)^#", LIMITS, re.M | re.S)
    assert found, f"LIMITS.md has no section {heading!r}"
    return found.group(1)


def row(heading: str, label: str) -> list[str]:
    """The cells of the one table row starting with this label, in one section."""
    body = section(heading)
    found = re.search(rf"^\| {re.escape(label)} \|(.*)\|$", body, re.M)
    assert found, f"{heading!r} has no row for {label!r}"
    return [cell.strip() for cell in found.group(1).split("|")]


def orphans_by_book(scheme: str) -> dict[str, int]:
    return {
        book: sum(reasons.values())
        for book, reasons in SCHEMES[scheme]["by_book"].items()
    }


SCHEME_TABLE = "Orphans per scheme"
BOOK_TABLE = "Where the concentration is, and why"
UNFILLED_TABLE = "Unfilled, which is the same question from the other side"


def test_the_per_scheme_totals_are_the_reported_ones() -> None:
    for label, scheme in (("Clementine Vulgate", "vulgate"), ("`org`", "org")):
        examined, resolved, orphans = row(SCHEME_TABLE, label)[:3]
        report = SCHEMES[scheme]
        assert int(examined) == report["addresses_examined"], label
        assert int(resolved) == report["resolved"], label
        assert int(orphans) == report["orphans"], label


def test_douay_is_published_as_not_reportable_rather_than_as_a_zero() -> None:
    assert SCHEMES["douay"]["reportable"] is False
    assert row(SCHEME_TABLE, "Douay")[0] == "not reportable"


def test_every_cause_row_is_the_count_the_report_carries() -> None:
    causes = {
        "The book has no counterpart on the spine": "no_counterpart",
        "A Vulgate psalm title, addressed at verse 0": "psalm_title",
        "The chapter is past the end of the book": "chapter_out_of_range",
        "The verse is past the end of the chapter": "verse_out_of_range",
    }
    for label, reason in causes.items():
        vulgate, org = row(SCHEME_TABLE, label)[:2]
        assert int(vulgate) == SCHEMES["vulgate"]["by_reason"][reason], label
        assert int(org) == SCHEMES["org"]["by_reason"][reason], label


def test_the_causes_account_for_every_orphan() -> None:
    """A breakdown that does not sum to the total is a breakdown with a hole."""
    for scheme in ("vulgate", "org"):
        assert sum(SCHEMES[scheme]["by_reason"].values()) == SCHEMES[scheme]["orphans"]


def test_every_book_row_is_the_count_the_report_carries() -> None:
    for label, code in BOOKS.items():
        vulgate, org = row(BOOK_TABLE, label)[:2]
        assert int(vulgate) == orphans_by_book("vulgate").get(code, 0), label
        assert int(org) == orphans_by_book("org").get(code, 0), label


def test_the_published_book_table_leaves_no_off_spine_book_out() -> None:
    """`LIMITS.md` claims these are all of them, so silence has to be checked.

    A book the table omits would be an orphan concentration the reader never
    sees, which is the one thing this document promises not to do.
    """
    from catholic_bible.canon.spine import SPINE  # noqa: PLC0415

    on_spine = set(SPINE.books())
    for scheme in ("vulgate", "org"):
        off = {
            book
            for book, count in orphans_by_book(scheme).items()
            if book not in on_spine and count
        }
        assert off <= set(BOOKS.values()), (scheme, off - set(BOOKS.values()))


def test_the_nine_named_addresses_are_the_ones_that_orphan() -> None:
    """The nine single verses `LIMITS.md` lists, and the eight it calls chosen.

    Named one by one in the prose, so the prose has to be the truth. If the
    spine ever grows one of those slots the sentence above them stops being
    true and this is what says so.
    """
    from catholic_bible.canon.mapping import (  # noqa: PLC0415
        Orphan,
        Scheme,
        map_address,
    )
    from catholic_bible.canon.orphans import declared_addresses  # noqa: PLC0415
    from catholic_bible.canon.spine import SPINE  # noqa: PLC0415

    on_spine = set(SPINE.books())
    found = {
        f"{book}.{chapter}.{verse}"
        for book, chapter, verse in declared_addresses(Scheme.VULGATE)
        if book in on_spine
        and isinstance(
            result := map_address(Scheme.VULGATE, book, chapter, verse), Orphan
        )
        and result.reason.value == "verse_out_of_range"
    }
    published = set(re.findall(r"`([A-Z0-9]{3}\.\d+\.\d+)`", section(BOOK_TABLE)))

    assert len(found) == 9
    assert found == published
    assert "JON.1.17" in found, "the one that is not New Testament"
    assert len(found - {"JON.1.17"}) == 8, "the eight the prose calls chosen"


def test_the_unfilled_table_is_what_coverage_measured() -> None:
    versions = {
        "Clementine Vulgate": "vulgata-clementina",
        "Douay-Rheims": "douay-rheims",
        "Matos Soares": "matos-soares",
    }
    for label, slug in versions.items():
        published, unfilled = row(UNFILLED_TABLE, label)[:2]
        record = COVERAGE["versions"][slug]
        assert int(published) == record["published"], label
        assert int(unfilled) == record["unfilled"], label


def test_the_spine_size_the_prose_states_is_the_spine() -> None:
    assert f"spine holds {COVERAGE['spine_addresses']} addresses" in LIMITS


def test_the_source_verse_orphan_rate_is_still_declared_unmeasurable() -> None:
    """`coverage.json` says it and `LIMITS.md` has to keep saying it too."""
    assert COVERAGE["orphans"]["measurable_here"] is False
    assert "not measurable from inside this repository" in LIMITS
