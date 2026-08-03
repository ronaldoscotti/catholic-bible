import pytest

from catholic_bible.canon.aliases import ALIASES, Language, normalize
from catholic_bible.canon.books import CANON


def test_normalization_lowercases_and_trims() -> None:
    assert normalize("  Gênesis  ") == "gênesis"


def test_normalization_does_not_strip_accents() -> None:
    """The load-bearing absence.

    Folding accents would collapse Jó into jo and make Job unreachable, and the
    reader would land in John's gospel with nothing reporting an error.
    """
    assert normalize("Jó") != normalize("Jo")


def test_john_and_job_are_different_books_in_portuguese() -> None:
    assert ALIASES.resolve("Jo") == "JHN"
    assert ALIASES.resolve("Jó") == "JOB"
    assert ALIASES.resolve("jó") == "JOB"


def test_the_only_alias_collisions_are_the_documented_ones() -> None:
    """Two, both in English, both resolved in favour of Douay.

    Reporting them as zero would be the registry lying about a real ambiguity.
    A new alias that collides with anything else fails here.
    """
    assert ALIASES.conflicts() == {
        "1 kings": ["1SA", "1KI"],
        "2 kings": ["2SA", "2KI"],
    }


@pytest.mark.parametrize("language", list(Language))
def test_every_book_is_reachable_in_every_language(language: Language) -> None:
    reachable = set(ALIASES.codes_in(language))
    assert reachable == {book.code for book in CANON}


def test_the_douay_name_wins_the_kings_collision() -> None:
    """Douay prints Samuel as 1 and 2 Kings. Modern English does not.

    Both spellings are correct English, so one of them has to lose. This is a
    Catholic dataset anchored on the Douay and Haydock apparatus, so Douay wins
    and B3 documents it on the endpoint.
    """
    assert ALIASES.resolve("1 Kings") == "1SA"
    assert ALIASES.resolve("2 Kings") == "2SA"


def test_the_books_modern_english_calls_kings_stay_reachable() -> None:
    assert ALIASES.resolve("3 Kings") == "1KI"
    assert ALIASES.resolve("4 Kings") == "2KI"


def test_modern_english_resolves_where_it_does_not_collide() -> None:
    assert ALIASES.resolve("Joshua") == "JOS"
    assert ALIASES.resolve("Sirach") == "SIR"
    assert ALIASES.resolve("Revelation") == "REV"
    assert ALIASES.resolve("Song of Songs") == "SNG"


def test_the_douay_spellings_resolve_too() -> None:
    assert ALIASES.resolve("Josue") == "JOS"
    assert ALIASES.resolve("Ecclesiasticus") == "SIR"
    assert ALIASES.resolve("Apocalypse") == "REV"


def test_latin_liturgical_names_resolve() -> None:
    assert ALIASES.resolve("Apocalypsis") == "REV"
    assert ALIASES.resolve("Canticum Canticorum") == "SNG"
    assert ALIASES.resolve("Psalmi") == "PSA"


def test_the_latin_kings_follow_the_vulgate_reckoning() -> None:
    assert ALIASES.resolve("I Regum") == "1SA"
    assert ALIASES.resolve("III Regum") == "1KI"


def test_latin_abbreviations_from_the_apparatus_resolve() -> None:
    assert ALIASES.resolve("Ios") == "JOS"
    assert ALIASES.resolve("Sap") == "WIS"
    assert ALIASES.resolve("Apoc") == "REV"


def test_a_bare_numbered_latin_abbreviation_takes_the_first_book() -> None:
    assert ALIASES.resolve("Cor") == "1CO"
    assert ALIASES.resolve("1 Cor") == "1CO"
    assert ALIASES.resolve("2 Cor") == "2CO"


def test_the_alias_count_is_pinned_so_a_new_one_cannot_arrive_quietly() -> None:
    """The epic says nothing enters this repo without a case in the corpus,
    including a new alias. That was discipline until this test existed.

    Adding, removing or renaming any written form moves a number here, which
    forces whoever did it to look at the conformance corpus in the same change.
    """
    assert ALIASES.size() == {Language.PT: 219, Language.EN: 160, Language.LA: 476}


def test_an_unknown_name_resolves_to_nothing_rather_than_raising() -> None:
    assert ALIASES.resolve("Book of Mormon") is None
    assert ALIASES.resolve("") is None


def test_a_usx_code_resolves_to_itself() -> None:
    assert ALIASES.resolve("GEN") == "GEN"
    assert ALIASES.resolve("1CO") == "1CO"


def test_case_separates_the_code_jude_from_the_portuguese_for_judith() -> None:
    """JUD is Jude. Jud is how a Portuguese reader writes Judite."""
    assert ALIASES.resolve("JUD") == "JUD"
    assert ALIASES.resolve("Jud") == "JDT"
    assert ALIASES.resolve("jud") == "JDT"
