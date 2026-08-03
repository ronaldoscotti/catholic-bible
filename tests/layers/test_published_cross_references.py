"""What the published apparatus has to be, checked against the file.

The export needs the private database and cannot run here. What CI can check is
that the artifact is internally consistent, that both ends of every reference
are on the spine, and that the excluded source stayed excluded.
"""

from __future__ import annotations

import hashlib
import json

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.spine import SPINE
from catholic_bible.cross_references import load

PROVENANCE = json.loads(
    (DATA_DIR / "cross-references" / "PROVENANCE.json").read_text(encoding="utf-8")
)

ORPHANS = json.loads(
    (DATA_DIR / "derived" / "cross-reference-orphans.json").read_text(encoding="utf-8")
)


def test_the_file_matches_its_recorded_checksum() -> None:
    for name, record in PROVENANCE["files"].items():
        payload = (DATA_DIR / "cross-references" / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == record["sha256"], name


def test_the_ave_maria_apparatus_is_absent_and_the_exclusion_is_recorded() -> None:
    """It is not a flag on the export. A flag can be passed by accident."""
    apparatus = load()

    assert set(apparatus.sources) == {"douay", "na27", "openbible"}
    assert not [row for row in apparatus.references if row.source == "ave-maria"]
    assert "ave-maria" in PROVENANCE["files"]["references.json"]["excluded"]


def test_both_ends_of_every_reference_are_on_the_spine() -> None:
    """A reference that drifted by one reads as a curated connection and is not."""
    for row in load().references:
        assert SPINE.order_of(row.anchor) is not None, row.anchor
        assert SPINE.order_of(row.target) is not None, row.target


def test_the_counts_agree_with_the_provenance() -> None:
    apparatus = load()
    record = PROVENANCE["files"]["references.json"]

    assert len(apparatus.references) == record["references"] == 207636
    assert len({row.anchor for row in apparatus.references}) == record["anchors"]

    by_source: dict[str, int] = {}
    for row in apparatus.references:
        by_source[row.source] = by_source.get(row.source, 0) + 1
    assert by_source == record["by_source"]


def test_openbible_reaches_no_deuterocanonical_book() -> None:
    """The epic's problem statement, asserted rather than described.

    204601 references and not one of them touches Tobit, Judith, Wisdom,
    Sirach, Baruch or the Maccabees, in either direction. If that ever stops
    being true this test is the thing that says so.
    """
    from catholic_bible.canon.books import CANON  # noqa: PLC0415

    deutero = {book.code for book in CANON if book.deuterocanonical}
    touching = [
        row
        for row in load().references
        if row.source == "openbible"
        and (row.anchor.book in deutero or row.target.book in deutero)
    ]

    assert touching == []


def test_the_deuterocanonical_links_come_from_the_two_curated_sources() -> None:
    from catholic_bible.canon.books import CANON  # noqa: PLC0415

    deutero = {book.code for book in CANON if book.deuterocanonical}
    sources = {
        row.source
        for row in load().references
        if row.anchor.book in deutero or row.target.book in deutero
    }

    assert sources == {"douay", "na27"}


def test_the_orphan_report_says_what_it_can_and_cannot_answer() -> None:
    """An upper bound reported as an upper bound.

    The gap holds entries the import could not resolve and entries another
    source had already written. Both are absences and only one is an orphan.
    """
    assert set(ORPHANS) == {"douay", "na27", "openbible"}
    assert ORPHANS["openbible"]["fixture_pairs"] == 211804
    assert ORPHANS["openbible"]["exported"] == 204601
    assert ORPHANS["douay"]["fixture_pairs"] is None
    assert ORPHANS["douay"]["why"]


def test_the_worst_openbible_losses_are_in_daniel() -> None:
    """Not noise. The `org` scheme carries Susanna and Bel as their own books
    and this spine folds them into Daniel 13 and 14, so the remap is where the
    references go missing."""
    worst = ORPHANS["openbible"]["worst"]

    assert next(iter(worst)) == "DAN -> DAN"
