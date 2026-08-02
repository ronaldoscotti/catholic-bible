"""Translating other numbering schemes into the spine.

Three of them. The Vulgate, `org` (the Copenhagen scheme, anchored on the
Masoretic text) and Douay.

None of these validate against the spine. They answer where an address lands,
and whether that landing exists is the mapping layer's question.
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from functools import cached_property

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.spine import SPINE

Address = tuple[str, int, int]

_REF = re.compile(
    r"^(?P<book>\S+) (?P<chapter>\d+):(?P<verses>\d+)(?:-(?P<last>\d+))?$"
)


class Mode(StrEnum):
    """How the spine numbers one book."""

    IDENTITY = "identity"
    ORG = "org"


def expand(ref: str) -> list[str]:
    """`PSA 50:0-21` into the 22 single-verse keys it stands for."""
    match = _REF.match(ref)
    if match is None:
        return []
    book, chapter = match["book"], int(match["chapter"])
    first = int(match["verses"])
    last = int(match["last"]) if match["last"] else first
    return [f"{book} {chapter}:{verse}" for verse in range(first, last + 1)]


def _parse(ref: str) -> Address:
    book, rest = ref.split(" ", 1)
    chapter, verse = rest.split(":", 1)
    return book, int(chapter), int(verse)


class VulgateScheme:
    """Vulgate numbering into the spine.

    The Copenhagen table maps the Vulgate onto `org`. The spine is mixed, so
    applying that table wholesale would be wrong for the Psalter. Mode is
    therefore decided per book by counting: run every verse the Vulgate has
    through both readings, keep the one that lands fewer addresses outside the
    spine, and let a tie keep identity.
    """

    def __init__(self, table: dict[str, object]) -> None:
        raw_max = table.get("maxVerses", {})
        assert isinstance(raw_max, dict)
        # The counts arrive as strings upstream.
        self._max: dict[str, list[int]] = {
            book: [int(count) for count in counts] for book, counts in raw_max.items()
        }
        mapped = table.get("mappedVerses", {})
        assert isinstance(mapped, dict)
        self._per_verse = _pair_up(mapped)
        self._origins = tuple(mapped)
        self._mode: dict[str, Mode] = {}
        self._inverse_of: dict[str, str] = {}

    def declares(self, book: str) -> bool:
        """Whether the Copenhagen table knows this book at all."""
        return book in self._max

    def declared_books(self) -> dict[str, list[int]]:
        """Every book the table declares, with its Vulgate verse counts."""
        return dict(self._max)

    def declared_pairs(self) -> tuple[str, ...]:
        """The origin side of every remap the table declares, ranges unexpanded."""
        return self._origins

    def declared_targets(self) -> dict[str, str]:
        """Vulgate address to the `org` address the table names for it."""
        return dict(self._per_verse)

    def mode_for(self, book: str) -> Mode:
        cached = self._mode.get(book)
        if cached is None:
            cached = self._mode[book] = self._decide(book)
        return cached

    def to_spine(self, book: str, chapter: int, verse: int) -> Address:
        if self.mode_for(book) is Mode.ORG:
            return self._apply(book, chapter, verse)
        return book, chapter, verse

    def _decide(self, book: str) -> Mode:
        counts = self._max.get(book)
        if counts is None:
            return Mode.IDENTITY

        identity_misses = org_misses = 0
        for index, count in enumerate(counts, start=1):
            for verse in range(1, count + 1):
                if not SPINE.contains(book, index, verse):
                    identity_misses += 1
                if not SPINE.contains(*self._apply(book, index, verse)):
                    org_misses += 1
        return Mode.IDENTITY if identity_misses <= org_misses else Mode.ORG

    def from_spine(self, book: str, chapter: int, verse: int) -> Address:
        """The other direction, spine to Vulgate.

        Where the spine numbers a book in Vulgate there is nothing to do. Where
        it numbers in `org` the address has to come back through the table, so
        this asks the inverse index for it.
        """
        if self.mode_for(book) is Mode.IDENTITY:
            return book, chapter, verse
        origin = self._inverse_of.get(f"{book} {chapter}:{verse}")
        return _parse(origin) if origin else (book, chapter, verse)

    def bind_inverse(self, inverse: dict[str, str]) -> None:
        self._inverse_of = inverse

    def apply_table(self, book: str, chapter: int, verse: int) -> Address:
        """The table applied regardless of mode, Vulgate coordinates to `org`."""
        return self._apply(book, chapter, verse)

    def _apply(self, book: str, chapter: int, verse: int) -> Address:
        target = self._per_verse.get(f"{book} {chapter}:{verse}")
        return _parse(target) if target else (book, chapter, verse)


class OrgScheme:
    """`org` numbering into the spine, which is the inverse direction.

    The Copenhagen table runs Vulgate to `org`, so this inverts it and applies
    it only where the spine numbers a book in Vulgate. Where the spine already
    numbers in `org` an `org` address is already home.

    The index is sparse. Only addresses that actually diverge are rewritten, so
    applying it to a book with few pairs touches only those few.

    Inverting is not free. The table merges verses and it names the same target
    from more than one origin, so 135 `org` addresses arrive with two or more
    declared Vulgate origins. Taking whichever came last is arbitrary and it
    costs real resolutions: the Song of the Three is declared from both `DAN`
    and `DAG`, and only `DAN` has a slot on the spine.

    So the rule is first declared wins, unless the first has no slot on the
    spine and a later one does. That is a choice between origins the table
    already asserts rather than an invented address, and it recovers 103. Of the
    rest, 23 have no resolvable origin and 9 have several, and those 9 stay
    ambiguous on purpose. This diverges from the source implementation and the
    reasoning is in DECISIONS.md.

    The table also carries source versifications other than the Vulgate, `DAG`
    for Greek Daniel among them, so inverting can hand a perfectly good address
    a remap that lands nowhere. `DAN 1:1` is declared only from `DAG 1:1`, which
    the canon does not have. An address already on the spine is therefore never
    traded for one that is not.
    """

    def __init__(self, table: dict[str, object], vulgate: VulgateScheme) -> None:
        self._vulgate = vulgate
        mapped = table.get("mappedVerses", {})
        assert isinstance(mapped, dict)
        self._inverse: dict[str, str] = {}
        for origin, target in _pair_up(mapped).items():
            held = self._inverse.get(target)
            if held is None or (
                not SPINE.contains(*_parse(held)) and SPINE.contains(*_parse(origin))
            ):
                self._inverse[target] = origin

    def index(self) -> dict[str, str]:
        """The resolved inverse, `org` address to Vulgate origin."""
        return dict(self._inverse)

    def to_spine(self, book: str, chapter: int, verse: int) -> Address:
        if self._vulgate.mode_for(book) is not Mode.IDENTITY:
            return book, chapter, verse

        target = self._inverse.get(f"{book} {chapter}:{verse}")
        if target is None:
            return book, chapter, verse

        candidate = _parse(target)
        if not SPINE.contains(*candidate) and SPINE.contains(book, chapter, verse):
            return book, chapter, verse
        return candidate

    def from_spine(self, book: str, chapter: int, verse: int) -> Address:
        """The other direction, spine to `org`.

        Mirror image of `to_spine`. Where the spine numbers a book in Vulgate
        the table applies forward, and where it already numbers in `org` the
        address is already there.
        """
        if self._vulgate.mode_for(book) is not Mode.IDENTITY:
            return book, chapter, verse
        return self._vulgate.apply_table(book, chapter, verse)


class DouayScheme:
    """Douay-Rheims naming and numbering into the spine.

    Identity in 71 books. Joel and Malachi carry the Vulgate chapter division,
    which the spine does not, so they shift.
    """

    @cached_property
    def _names(self) -> dict[str, str]:
        raw: dict[str, str] = json.loads(
            (DATA_DIR / "douay-names.json").read_text(encoding="utf-8")
        )
        return raw

    def to_usx(self, douay_name: str) -> str | None:
        return self._names.get(douay_name)

    def to_spine(self, book: str, chapter: int, verse: int) -> Address:
        if book == "JOL":
            if chapter == 2 and verse >= 28:
                return book, 3, verse - 27
            if chapter == 3:
                return book, 4, verse
        elif book == "MAL" and chapter == 4:
            return book, 3, 18 + verse
        return book, chapter, verse

    def from_spine(self, book: str, chapter: int, verse: int) -> Address:
        if book == "JOL":
            if chapter == 3:
                return book, 2, verse + 27
            if chapter == 4:
                return book, 3, verse
        elif book == "MAL" and chapter == 3 and verse >= 19:
            return book, 4, verse - 18
        return book, chapter, verse


def _pair_up(mapped: dict[str, str]) -> dict[str, str]:
    """Expands the table's ranges into positional single-verse pairs.

    A pair whose two sides expand to different lengths is skipped rather than
    aligned by guesswork, which is what the source implementation does.
    """
    pairs: dict[str, str] = {}
    for origin, target in mapped.items():
        left, right = expand(origin), expand(target)
        if len(left) != len(right) or not left:
            continue
        pairs.update(zip(left, right, strict=True))
    return pairs


def _load() -> tuple[VulgateScheme, OrgScheme, DouayScheme]:
    table: dict[str, object] = json.loads(
        (DATA_DIR / "vulgate-scheme.json").read_text(encoding="utf-8")
    )
    vulgate = VulgateScheme(table)
    org = OrgScheme(table, vulgate)
    vulgate.bind_inverse(org.index())
    return vulgate, org, DouayScheme()


VULGATE, ORG, DOUAY = _load()
