"""Resolving a written book name to a USX code, in three languages.

Normalization lowercases and trims. It does nothing else, and in particular it
does not fold accents. That absence is the feature: `Jo` is John and `Jó` is
Job, and a port reaching for Unicode normalization to be helpful would make Job
unreachable while sending the reader to the wrong gospel with no error anywhere.

Precedence is Portuguese, then Douay English, then modern English, then Latin.
A name already claimed by an earlier source is not reclaimed, so a collision
resolves in one direction and `conflicts()` reports it rather than hiding it.
Two exist, `1 Kings` and `2 Kings`, and both go to Douay.
"""

from __future__ import annotations

import json
from enum import StrEnum

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.authored_names import (
    ENGLISH_MODERN,
    LATIN_ALIASES,
    LATIN_NAMES,
)
from catholic_bible.canon.books import CANON

ROMAN = ("I", "II", "III", "IV")


class Language(StrEnum):
    PT = "pt"
    EN = "en"
    LA = "la"


class Aliases:
    def __init__(self) -> None:
        self._by_language: dict[Language, dict[str, str]] = {
            language: {} for language in Language
        }
        self._conflicts: dict[str, list[str]] = {}
        self._resolved: dict[str, str] = {}

        for book in CANON:
            self._claim(Language.PT, book.name, book.code)
            self._claim(Language.PT, book.abbreviation, book.code)
            for alias in book.aliases:
                self._claim(Language.PT, alias, book.code)

        for name, code in _douay_names().items():
            self._claim(Language.EN, name, code)
        for code, name in ENGLISH_MODERN.items():
            self._claim(Language.EN, name, code)

        for code, name in LATIN_NAMES.items():
            self._claim(Language.LA, name, code)
        for code, names in LATIN_ALIASES.items():
            for name in names:
                self._claim(Language.LA, name, code)
        self._claim_apparatus()

    def resolve(self, written: str) -> str | None:
        """A USX code in its exact uppercase form, otherwise a written name.

        Case carries meaning at the code boundary and nowhere else. `JUD` is
        Jude, the code, and `Jud` is how a Portuguese reader writes Judite.
        Normalizing the first into the second would make an API caller passing
        a canonical code land in the wrong book.
        """
        code = written.strip()
        if CANON.by_code(code) is not None:
            return code
        return self._resolved.get(normalize(written))

    def codes_in(self, language: Language) -> set[str]:
        return set(self._by_language[language].values())

    def size(self) -> dict[Language, int]:
        """How many written forms each language resolves."""
        return {language: len(keys) for language, keys in self._by_language.items()}

    def conflicts(self) -> dict[str, list[str]]:
        """Aliases claimed for two different books, winner first.

        A test pins this to the two known ones, so a new alias that collides
        with anything fails the build instead of quietly losing.
        """
        return dict(self._conflicts)

    def _claim(self, language: Language, written: str, code: str) -> None:
        key = normalize(written)
        if not key:
            return

        held = self._resolved.get(key)
        if held is None:
            self._resolved[key] = code
        elif held != code:
            self._conflicts.setdefault(key, [held]).append(code)
            return

        self._by_language[language].setdefault(key, code)

    def _claim_apparatus(self) -> None:
        """The Latin abbreviations the original Douay prints in its margins."""
        single, numbered, defaults = _latin_abbreviations()

        for abbreviation, code in single.items():
            self._claim(Language.LA, abbreviation, code)

        for abbreviation, codes in numbered.items():
            for index, code in enumerate(codes, start=1):
                self._claim(Language.LA, f"{index}{abbreviation}", code)
                self._claim(Language.LA, f"{index} {abbreviation}", code)
                self._claim(Language.LA, f"{ROMAN[index - 1]} {abbreviation}", code)
            if abbreviation in defaults:
                self._claim(Language.LA, abbreviation, codes[0])


def normalize(written: str) -> str:
    """Lowercase and trim. Never fold accents."""
    return written.strip().lower()


def _douay_names() -> dict[str, str]:
    raw: dict[str, str] = json.loads(
        (DATA_DIR / "douay-names.json").read_text(encoding="utf-8")
    )
    return raw


def _latin_abbreviations() -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    raw = json.loads(
        (DATA_DIR / "latin-abbreviations.json").read_text(encoding="utf-8")
    )
    return raw["single"], raw["numbered"], raw["bare_defaults_to_first"]


ALIASES = Aliases()
