"""What the published commentary file has to be, checked against the file.

The export needs the private database and cannot run here. What CI can check is
that the artifact it produced is internally consistent and matches the record
beside it, which is the same division B2 settled on for the corpus.
"""

from __future__ import annotations

import hashlib
import json

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import VerseId
from catholic_bible.commentary import SOURCES, load

PROVENANCE = json.loads(
    (DATA_DIR / "commentary" / "PROVENANCE.json").read_text(encoding="utf-8")
)


def test_the_file_matches_its_recorded_checksum() -> None:
    for name, record in PROVENANCE["files"].items():
        payload = (DATA_DIR / "commentary" / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == record["sha256"], name


def test_provenance_names_the_source_commit() -> None:
    source = PROVENANCE["source"]
    assert len(source["commit"]) == 40
    assert source["private"] is True


def test_the_haydock_reaches_every_book_in_both_languages() -> None:
    """Criterion 1 and criterion 2 of the epic, as one assertion.

    A commentary that covers 72 books is a commentary with a hole, and the hole
    is always a deuterocanonical book, because that is the one every Protestant
    source omits.
    """
    haydock = load("haydock")

    assert len(haydock.entries) == 20705
    assert {entry.start.book for entry in haydock.entries} == set(SPINE.books())
    assert all("en-US" in entry.body for entry in haydock.entries)
    assert all("pt-BR" in entry.body for entry in haydock.entries)


def test_every_anchor_is_on_the_spine_and_agrees_with_it() -> None:
    """The published order and the walked order, on both ends of every entry.

    B2 proved the corpus agrees and nothing forces it to stay that way. An
    anchor that drifts by one points a note at a neighbouring verse, which is
    the failure nobody notices.
    """
    for entry in load("haydock").entries:
        assert SPINE.order_of(entry.start) == entry.first_order, entry.start
        assert SPINE.order_of(entry.end) == entry.last_order, entry.end


def test_no_entry_runs_backwards() -> None:
    """The export clamps two of these and the count is in the provenance."""
    assert all(
        entry.first_order <= entry.last_order for entry in load("haydock").entries
    )
    assert PROVENANCE["files"]["haydock.json"]["clamped"] == ["LUK.1.73", "MAT.15.26"]


def test_the_clamped_entries_are_readable_at_their_first_verse() -> None:
    """What the clamp buys, stated as a test rather than as a comment.

    Both notes are invisible upstream, because a coverage test cannot match a
    range that runs backwards.
    """
    entries = load("haydock").entries
    for address in ("MAT.15.26", "LUK.1.73"):
        parsed = VerseId.parse(address)
        assert isinstance(parsed, VerseId)
        order = SPINE.order_of(parsed)
        assert order is not None
        covering = [
            entry for entry in entries if entry.first_order <= order <= entry.last_order
        ]
        assert covering, address


def test_the_only_published_source_is_the_haydock() -> None:
    """The Catena Aurea shares two tables with this and does not ship."""
    assert SOURCES == ("haydock",)
    assert not (DATA_DIR / "commentary" / "catena.json").exists()
