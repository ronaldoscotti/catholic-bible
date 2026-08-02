import hashlib
import json

import pytest

from catholic_bible.canon.books import CANON
from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import VerseId
from catholic_bible.corpus import CORPUS_DIR, VERSIONS, load

PROVENANCE = json.loads((CORPUS_DIR / "PROVENANCE.json").read_text(encoding="utf-8"))

# Measured against the source database while writing the spec.
EXPECTED_VERSES = {
    "matos-soares": 35563,
    "douay-rheims": 35764,
    "vulgata-clementina": 35776,
}


@pytest.mark.parametrize("code", VERSIONS)
def test_no_published_record_carries_a_heading(code: str) -> None:
    """The one thing here that would ship by accident.

    2305 Ave Maria pericope headings sit in the heading column of the same rows
    as the Matos Soares text, and that text is under copyright. This asserts the
    output, and the export names its columns, so both have to fail together.
    """
    raw = json.loads((CORPUS_DIR / f"{code}.json").read_text(encoding="utf-8"))
    for key, record in raw["verses"].items():
        assert set(record) == {"order", "text"}, key


@pytest.mark.parametrize("code", VERSIONS)
def test_the_ave_maria_is_nowhere_in_the_published_bytes(code: str) -> None:
    payload = (CORPUS_DIR / f"{code}.json").read_bytes().lower()
    assert b"ave-maria" not in payload
    assert b"ave maria" not in payload


def test_only_the_three_translations_are_published() -> None:
    published = {path.stem for path in CORPUS_DIR.glob("*.json")} - {"PROVENANCE"}
    assert published == set(VERSIONS)


@pytest.mark.parametrize("code", VERSIONS)
def test_all_seventy_three_books_are_present(code: str) -> None:
    books = {key.split(".")[0] for key in load(code).verses}
    assert books == {book.code for book in CANON}


@pytest.mark.parametrize("code", VERSIONS)
def test_the_verse_count_is_what_the_source_holds(code: str) -> None:
    assert len(load(code).verses) == EXPECTED_VERSES[code]


@pytest.mark.parametrize("code", VERSIONS)
def test_every_published_address_exists_on_the_spine(code: str) -> None:
    """Criterion two. Nothing is published at an address B1 does not hold."""
    for key in load(code).verses:
        parsed = VerseId.parse(key)
        assert isinstance(parsed, VerseId), key
        assert SPINE.contains(parsed.book, parsed.chapter, parsed.verse), key


@pytest.mark.parametrize("code", VERSIONS)
def test_the_published_order_agrees_with_the_spine(code: str) -> None:
    """The two identities are computed by two codebases and must not disagree.

    The integer comes from the private repository's own column. The spine walks
    the versification independently. A mismatch would mean one of them is wrong
    about the shape of the canon.
    """
    for key, verse in load(code).verses.items():
        parsed = VerseId.parse(key)
        assert isinstance(parsed, VerseId)
        assert SPINE.order_of(parsed) == verse.order, key


@pytest.mark.parametrize("code", VERSIONS)
def test_no_verse_is_published_empty(code: str) -> None:
    """An empty string is a lie shaped like data. A missing key is not."""
    empty = [key for key, verse in load(code).verses.items() if not verse.text.strip()]
    assert empty == []


def test_the_twelve_english_gaps_are_recorded_rather_than_papered_over() -> None:
    """The MIT fixture carries the Latin and leaves the English field empty.

    Omitted from the published file and listed in provenance, so a consumer can
    tell a gap from a verse that says nothing.
    """
    blank = PROVENANCE["files"]["douay-rheims.json"]["blank_upstream"]
    assert len(blank) == 12
    assert "PSA.150.6" in blank
    assert load("douay-rheims").verses.get("PSA.150.6") is None
    assert load("vulgata-clementina").verses["PSA.150.6"].text.strip()


@pytest.mark.parametrize("code", VERSIONS)
def test_the_rights_are_machine_readable(code: str) -> None:
    """Criterion ten. Authored here, because the source holds NULL."""
    rights = load(code).metadata["rights"]
    assert isinstance(rights, dict)
    assert rights["text"] == "public-domain"
    assert len(str(rights["text_basis"])) > 40


@pytest.mark.parametrize("code", VERSIONS)
def test_every_file_matches_its_recorded_checksum(code: str) -> None:
    payload = (CORPUS_DIR / f"{code}.json").read_bytes()
    recorded = PROVENANCE["files"][f"{code}.json"]
    assert hashlib.sha256(payload).hexdigest() == recorded["sha256"]
    assert recorded["verses"] == EXPECTED_VERSES[code]


def test_provenance_names_the_source_and_its_inputs() -> None:
    """A table has no git hash, so the record names what the tables come from."""
    assert len(PROVENANCE["source"]["commit"]) == 40
    assert PROVENANCE["source"]["private"] is True
    assert set(PROVENANCE["fixtures"]) == {
        "database/data/matos-soares.json.gz",
        "database/data/vulgata-source.json.gz",
    }
    for digest in PROVENANCE["fixtures"].values():
        assert len(digest) == 64


def test_the_miserere_reads_correctly_in_three_languages() -> None:
    """Accents included, because the client defaults to latin1.

    The first export came back with every accented character as a raw byte. A
    corpus that is wrong in this way passes every structural check.
    """
    assert (
        load("matos-soares")
        .verses["PSA.50.3"]
        .text.startswith("Tem piedade de mim, ó Deus")
    )
    assert (
        load("vulgata-clementina")
        .verses["PSA.50.3"]
        .text.startswith("Miserere mei, Deus")
    )
    assert (
        load("douay-rheims")
        .verses["PSA.50.3"]
        .text.startswith("Have mercy on me, O God")
    )


def test_susanna_and_bel_carry_text() -> None:
    """Deuterocanonical chapters org has no slot for at all."""
    for code in VERSIONS:
        verses = load(code).verses
        assert verses["DAN.13.1"].text.strip()
        assert verses["DAN.14.1"].text.strip()


def test_only_a_published_code_reaches_the_filesystem() -> None:
    """B3 hands this a path segment from an HTTP route.

    Unchecked, it reads outside the corpus directory and every distinct string a
    caller sends becomes a permanent cache entry.
    """
    with pytest.raises(KeyError):
        load("../PROVENANCE")
    with pytest.raises(KeyError):
        load("ave-maria")


def test_the_recorded_count_is_the_count_in_the_document() -> None:
    """Taken from the rows it would overstate what the file holds, because two
    source rows at one address collapse into one published entry."""
    for code in VERSIONS:
        raw = json.loads((CORPUS_DIR / f"{code}.json").read_text(encoding="utf-8"))
        assert PROVENANCE["files"][f"{code}.json"]["verses"] == len(raw["verses"])
