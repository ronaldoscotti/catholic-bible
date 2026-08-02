import pytest

from catholic_bible.canon.reference import Reference, UnparsedReference, parse_reference


def ref(text: str) -> Reference:
    parsed = parse_reference(text)
    assert isinstance(parsed, Reference), parsed
    return parsed


def failure(text: str) -> str:
    parsed = parse_reference(text)
    assert isinstance(parsed, UnparsedReference), parsed
    return parsed.reason


@pytest.mark.parametrize("text", ["Jo 3,16", "Jo 3:16", " Jo  3,16 "])
def test_a_single_verse(text: str) -> None:
    parsed = ref(text)
    assert parsed.book == "JHN"
    assert parsed.bounds == ((3, 16), (3, 16))
    assert parsed.is_range is False


def test_the_accent_decides_the_book() -> None:
    assert ref("Jo 3,16").book == "JHN"
    assert ref("Jó 3,16").book == "JOB"


def test_a_range_inside_a_chapter() -> None:
    parsed = ref("Jo 3,16-18")
    assert parsed.bounds == ((3, 16), (3, 18))
    assert parsed.is_range is True


def test_a_range_across_a_chapter_boundary() -> None:
    parsed = ref("Ex 13,1-14,5")
    assert parsed.book == "EXO"
    assert parsed.bounds == ((13, 1), (14, 5))


def test_disjoint_lectionary_parts_inherit_the_chapter() -> None:
    parsed = ref("Mc 5,22-24.35-43")
    assert parsed.book == "MRK"
    assert parsed.parts == (((5, 22), (5, 24)), ((5, 35), (5, 43)))
    assert parsed.bounds == ((5, 22), (5, 43))
    assert parsed.is_disjoint is True


def test_a_disjoint_part_can_carry_its_own_chapter() -> None:
    parsed = ref("Mc 5,22-24.6,1-2")
    assert parsed.parts == (((5, 22), (5, 24)), ((6, 1), (6, 2)))


def test_a_whole_chapter() -> None:
    parsed = ref("Sl 23")
    assert parsed.book == "PSA"
    assert parsed.whole_chapter is True
    assert parsed.bounds == ((23, 1), (23, 1))


def test_a_chapter_range_anchors_on_the_first_chapter() -> None:
    parsed = ref("Ex 13-14")
    assert parsed.whole_chapter is True
    assert parsed.bounds == ((13, 1), (13, 1))


@pytest.mark.parametrize("dash", ["-", "–", "—"])
def test_the_three_dashes_a_reader_actually_types(dash: str) -> None:
    assert ref(f"Jo 3,16{dash}18").bounds == ((3, 16), (3, 18))


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("Gênesis 1,1", "GEN"),
        ("Genesis 1,1", "GEN"),
        ("Josue 1,1", "JOS"),
        ("Joshua 1,1", "JOS"),
        ("Apocalypsis 1,1", "REV"),
        ("Apoc 1,1", "REV"),
        ("Eclo 1,1", "SIR"),
    ],
)
def test_all_three_languages_reach_the_same_addresses(text: str, code: str) -> None:
    assert ref(text).book == code


def test_an_unknown_book_is_a_value_and_not_an_exception() -> None:
    """CLAUDE.md rule. A reader typing a wrong name is not a fault."""
    assert failure("Nephi 3,16") == "unknown_book"


def test_the_failure_carries_what_could_not_be_read() -> None:
    parsed = parse_reference("Nephi 3,16")
    assert isinstance(parsed, UnparsedReference)
    assert parsed.text == "Nephi 3,16"
    assert parsed.book == "Nephi"


@pytest.mark.parametrize("text", ["", "   ", "3,16", "Jo", "Jo capitulo tres"])
def test_something_that_is_not_a_reference_at_all(text: str) -> None:
    assert failure(text) in {"malformed", "unknown_book"}


def test_a_dotted_abbreviation_is_a_known_limit() -> None:
    """The source treats any dot as a lectionary separator and so does this.

    `Mt. 5,3` is common in Portuguese and it does not parse. Recorded here so
    the limit is visible rather than discovered, and it stays a limit until the
    conformance corpus says otherwise.
    """
    assert failure("Mt. 5,3") == "unknown_book"
