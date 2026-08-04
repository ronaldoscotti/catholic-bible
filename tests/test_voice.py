"""The voice lint, and the documents it has to keep clean.

The last test is the one the epic asks for. The ones above it exist because a
lint that passes on everything, including prose that breaks the rule, is worse
than no lint, and only a case that fails proves it is looking.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parent.parent


def _lint() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "lint_voice", REPO / "scripts" / "lint-voice.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _reasons(text: str) -> list[str]:
    return [reason for _, _, reason in _lint().check("sample.md", text)]


def test_an_em_dash_is_caught() -> None:
    assert _reasons("The spine is mixed — and that is the rule.") == ["em-dash"]


def test_a_banned_word_is_caught_whatever_its_case() -> None:
    assert _reasons("A Meticulous audit.") == ["banned word 'meticulous'"]


def test_a_banned_word_in_portuguese_is_caught() -> None:
    assert _reasons("Um relatório abrangente.") == ["banned word 'abrangente'"]


def test_a_signposting_opener_is_caught_and_only_as_an_opener() -> None:
    assert _reasons("Moreover, the table is inverted.") == [
        "signposting opener 'Moreover'"
    ]
    assert _reasons("The table is moreover inverted.") == []


def test_a_word_that_merely_contains_a_banned_one_is_left_alone() -> None:
    """`realm` inside `overwhelmed` is not a finding."""
    assert _reasons("The importer was overwhelmed.") == []


def test_code_is_not_prose() -> None:
    """A banned word inside a fence or backticks is a filename, not a voice."""
    fenced = "Text.\n\n```\nmeticulous --realm\n```\n\nMore text.\n"
    assert _reasons(fenced) == []
    assert _reasons("The `--meticulous` flag.") == []


def test_the_line_number_points_at_the_finding() -> None:
    findings = _lint().check("sample.md", "one\ntwo\nthree — four\n")
    assert findings == [("sample.md", 3, "em-dash")]


def test_testament_is_allowed_because_this_repo_is_about_the_canon() -> None:
    assert _reasons("Applied to the Old Testament only.") == []


def test_every_published_document_passes() -> None:
    """Criterion 7 of the epic, as an assertion rather than as a claim."""
    lint = _lint()
    paths = lint.targets()
    findings = [
        finding
        for path in paths
        for finding in lint.check(
            path.relative_to(REPO).as_posix(), path.read_text(encoding="utf-8")
        )
    ]

    assert findings == []
    assert len(paths) >= 6, [p.name for p in paths]


def test_the_two_readmes_publish_the_same_fetch_line() -> None:
    """The one-liner is duplicated, so drift between them has to be loud.

    `cdn.yml` reads the tag out of `README.md` and verifies it against the live
    CDN. Nothing verifies the Portuguese copy, so a release that bumps one and
    forgets the other would leave a documented 404 that no job runs.
    """
    english = (REPO / "README.md").read_text(encoding="utf-8")
    portuguese = (REPO / "README.pt-BR.md").read_text(encoding="utf-8")

    def fetch_line(text: str) -> str:
        lines = [line for line in text.splitlines() if line.startswith("const book")]
        assert len(lines) == 1, lines
        return lines[0]

    assert fetch_line(english) == fetch_line(portuguese)


def test_the_documents_the_epic_names_are_all_linted() -> None:
    """A clean run over a list missing a file is a clean run that proves nothing."""
    linted = {path.name for path in _lint().targets()}

    assert {
        "README.md",
        "README.pt-BR.md",
        "DECISIONS.md",
        "LIMITS.md",
        "CONTRIBUTING.md",
        "ROADMAP.md",
    } <= linted
    assert "B7-decisions-and-limits.md" in linted
