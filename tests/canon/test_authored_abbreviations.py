"""The 219 strings authored here, checked three ways.

None of the three is a second copy of the table. A table transcribed twice by
the same hand on the same afternoon is the same mistake written down twice.

What none of them catches is stated in LIMITS.md. All three answer "is this
string consistent with this book" and none answers "is this the form the
tradition prints". That one is a human reading against a printed Bible.
"""

from __future__ import annotations

import pytest

from catholic_bible.canon.aliases import ALIASES, Language, normalize
from catholic_bible.canon.authored_names import (
    ENGLISH_ABBREVIATIONS,
    ENGLISH_DISPLAY,
    ENGLISH_MODERN,
    LATIN_ABBREVIATIONS,
    LATIN_NAMES,
)
from catholic_bible.canon.books import CANON

AUTHORED = (ENGLISH_ABBREVIATIONS, LATIN_ABBREVIATIONS, ENGLISH_DISPLAY)

NUMERALS = ("1", "2", "3", "4", "I", "II", "III", "IV")


def _bare(abbreviation: str) -> str:
    """The letters, without a leading numeral and without a trailing period."""
    text = abbreviation.strip().rstrip(".")
    # Only when a space follows. Without that, `Ioel` loses its `I` and the
    # check degenerates into asking whether `oel` is inside `Ioel`.
    for numeral in NUMERALS:
        if text.startswith(f"{numeral} "):
            return text[len(numeral) :].strip()
    return text


def _is_subsequence(needle: str, haystack: str) -> bool:
    remaining = iter(haystack.lower())
    return all(character in remaining for character in needle.lower())


def _names_for(code: str, language: Language) -> list[str]:
    """Every name this book is known by in that language."""
    if language is Language.EN:
        return [ENGLISH_DISPLAY[code], ENGLISH_MODERN[code]]
    return [LATIN_NAMES[code]]


@pytest.mark.parametrize("table", AUTHORED)
def test_every_book_is_covered(table: dict[str, str]) -> None:
    assert set(table) == {book.code for book in CANON}
    assert len(table) == 73


def test_the_authored_surface_is_the_size_the_plan_named() -> None:
    assert sum(len(table) for table in AUTHORED) == 219


@pytest.mark.parametrize(
    ("table", "language"),
    [
        (ENGLISH_ABBREVIATIONS, Language.EN),
        (LATIN_ABBREVIATIONS, Language.LA),
    ],
)
def test_an_abbreviation_resolves_back_to_its_own_book(
    table: dict[str, str], language: Language
) -> None:
    """The alias table is built from exported data, so it is not what is tested.

    This catches an abbreviation pasted against the wrong book, and a duplicate,
    because a duplicate resolves to whichever book claimed it first.
    """
    for code, abbreviation in table.items():
        assert ALIASES.resolve(abbreviation) == code, f"{abbreviation} for {code}"


@pytest.mark.parametrize(
    ("table", "language"),
    [
        (ENGLISH_ABBREVIATIONS, Language.EN),
        (LATIN_ABBREVIATIONS, Language.LA),
    ],
)
def test_an_abbreviation_is_a_subsequence_of_a_name_the_book_has(
    table: dict[str, str], language: Language
) -> None:
    """Every letter in order, against any of that book's names in that language.

    Against any and not only the canonical one. `Ecclus.` is a subsequence of
    `Ecclesiasticus` and `Sir.` is not, because `Ecclesiasticus` carries no `r`,
    and both are right for the same book.
    """
    for code, abbreviation in table.items():
        bare = _bare(abbreviation)
        names = _names_for(code, language)
        assert any(_is_subsequence(bare, name) for name in names), (
            f"{abbreviation} for {code}, against {names}"
        )


def test_the_check_rejects_the_pair_this_canon_confuses() -> None:
    """Sirach and Ecclesiastes are the two an English reader mixes up.

    A test of the check itself. An invariant nothing can fail is decoration.
    """
    assert _is_subsequence("Ecclus", "Ecclesiasticus")
    assert not _is_subsequence("Ecclus", "Ecclesiastes")
    assert not _is_subsequence("Sir", "Ecclesiasticus")
    assert _is_subsequence("Sir", "Sirach")


def test_the_numeral_is_stripped_before_the_letters_are_compared() -> None:
    assert _bare("1 Cor.") == "Cor"
    assert _bare("III Ioan.") == "Ioan"
    assert _bare("Ruth") == "Ruth"
    assert _bare("1 John") == "John"


@pytest.mark.parametrize("table", AUTHORED)
def test_no_two_books_share_a_string(table: dict[str, str]) -> None:
    normalized = [normalize(value) for value in table.values()]
    assert len(set(normalized)) == len(normalized)


def test_the_authored_strings_introduced_no_new_collision() -> None:
    """Two collisions were known before this epic and both go to Douay.

    A new one means an authored string was already claimed by another book, and
    it has to be resolved deliberately rather than losing quietly.
    """
    assert set(ALIASES.conflicts()) == {"1 kings", "2 kings"}


def test_a_display_name_is_not_the_uppercase_margin_form() -> None:
    """`douay-names.json` holds the apparatus forms, which are not for display.

    Title casing them is what this set exists to avoid, so the test asserts the
    two places a mechanical rule breaks.
    """
    assert ENGLISH_DISPLAY["SNG"] == "Canticle of Canticles"
    assert ENGLISH_DISPLAY["1SA"] == "1 Kings"
    assert all(name != name.upper() for name in ENGLISH_DISPLAY.values())


def test_the_douay_reckoning_of_kings_survives() -> None:
    """In this reckoning 1 Kings is Samuel and 3 Kings is what others call 1 Kings.

    It is the single most confusable thing in the English canon and the
    abbreviations have to carry it rather than quietly normalising to the
    modern names.
    """
    assert ENGLISH_DISPLAY["1SA"] == "1 Kings"
    assert ENGLISH_DISPLAY["1KI"] == "3 Kings"
    assert ENGLISH_ABBREVIATIONS["1SA"] != ENGLISH_ABBREVIATIONS["1KI"]
    assert LATIN_NAMES["1SA"] == "I Regum"
    assert LATIN_NAMES["1KI"] == "III Regum"
