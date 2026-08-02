import pytest

from catholic_bible.canon.spine import SPINE
from catholic_bible.canon.verse import MalformedVerseId, VerseId

TOTAL_ADDRESSES = 35845


def test_the_published_form_is_book_chapter_verse() -> None:
    assert str(VerseId("PSA", 50, 3)) == "PSA.50.3"


def test_the_published_form_round_trips() -> None:
    parsed = VerseId.parse("PSA.50.3")
    assert parsed == VerseId("PSA", 50, 3)


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("PSA.50", "shape"),
        ("PSA.50.3.1", "shape"),
        ("", "shape"),
        ("PSA.fifty.3", "not_a_number"),
        ("PSA.0.3", "not_positive"),
        ("PSA.50.0", "not_positive"),
        ("PSA.-1.3", "not_positive"),
    ],
)
def test_a_malformed_id_comes_back_as_a_value_carrying_what_was_wrong(
    text: str, reason: str
) -> None:
    parsed = VerseId.parse(text)
    assert isinstance(parsed, MalformedVerseId)
    assert parsed.reason == reason
    assert parsed.text == text


@pytest.mark.parametrize("text", ["GEN.--5.1", "GEN.².3", "GEN.1.٥", "GEN.+1.1"])
def test_a_digit_that_is_not_an_integer_is_still_a_value(text: str) -> None:
    """The guard used to be lstrip and isdigit, and both lie.

    lstrip removes every leading dash, so `--5` passed and int() then raised.
    str.isdigit is true for superscripts and for other scripts, so `²` raised
    and Arabic-Indic `٥` parsed silently as five. Both would reach B3 as a 500
    where the contract says a structured error.
    """
    assert isinstance(VerseId.parse(text), MalformedVerseId)


def test_parsing_does_not_check_the_spine() -> None:
    """Shape and existence are different questions and different layers."""
    assert VerseId.parse("XYZ.1.1") == VerseId("XYZ", 1, 1)


def test_the_first_address_of_the_canon_has_order_one() -> None:
    assert SPINE.order_of(VerseId("GEN", 1, 1)) == 1


def test_order_is_dense_and_strictly_increasing_across_the_whole_spine() -> None:
    orders = [SPINE.order_of(VerseId(*address)) for address in SPINE.addresses()]
    assert orders == list(range(1, TOTAL_ADDRESSES + 1))


def test_the_last_address_carries_the_total_count() -> None:
    last = list(SPINE.addresses())[-1]
    assert SPINE.order_of(VerseId(*last)) == TOTAL_ADDRESSES


def test_order_round_trips_back_to_the_address() -> None:
    assert SPINE.at_order(1) == VerseId("GEN", 1, 1)
    assert SPINE.at_order(TOTAL_ADDRESSES) is not None
    assert SPINE.at_order(TOTAL_ADDRESSES + 1) is None
    assert SPINE.at_order(0) is None


def test_an_address_the_spine_does_not_hold_has_no_order() -> None:
    assert SPINE.order_of(VerseId("PSA", 50, 22)) is None
    assert SPINE.order_of(VerseId("XYZ", 1, 1)) is None


def test_the_miserere_keeps_its_published_form() -> None:
    """The wire identity is a string so no database seed order leaks into it."""
    assert str(SPINE.at_order(SPINE.order_of(VerseId("PSA", 50, 3)) or 0)) == "PSA.50.3"
