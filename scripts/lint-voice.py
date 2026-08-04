#!/usr/bin/env python3
"""Fails on prose this repo does not allow itself to publish.

Three rules, all from `CLAUDE.md` and the voice skill behind it: no em-dash
anywhere, no word off the banned list, no paragraph opening on a signposting
connector.

The lists are committed here rather than read from the author's private voice
skill, because a lint that needs a file outside the checkout cannot run for
anyone else. They are a subset. A machine can catch a banned word and it cannot
catch a sentence that merely sounds like nobody wrote it, which is why the
epic's verification is a human read and this is only the floor under it.

Code is not prose. Fenced blocks and inline spans are blanked before any check,
with the line count preserved so a finding points at the right line.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FILES = (
    "README.md",
    "README.pt-BR.md",
    "DECISIONS.md",
    "LIMITS.md",
    "CONTRIBUTING.md",
    "ROADMAP.md",
)
GLOBS = ("docs/epics/*.md",)

EM_DASH = "—"

# `testament` is on the voice skill's English list and is deliberately not here.
# A repository about the Catholic canon has to be able to write Old Testament.
BANNED_WORDS_EN = (
    "delve",
    "tapestry",
    "realm",
    "leverage",
    "utilize",
    "unveil",
    "embark",
    "foster",
    "underscore",
    "illuminate",
    "empower",
    "garner",
    "showcase",
    "streamline",
    "seamless",
    "multifaceted",
    "pivotal",
    "meticulous",
    "intricate",
    "vibrant",
    "transformative",
    "cutting-edge",
    "holistic",
    "paradigm",
    "cornerstone",
)

BANNED_WORDS_PT = (
    "primordial",
    "robusto",
    "multifacetado",
    "abrangente",
    "holístico",
    "intricado",
    "meticuloso",
    "transformador",
    "disruptivo",
    "tapeçaria",
    "alavancar",
    "potencializar",
    "fomentar",
    "viabilizar",
    "desbravar",
)

BANNED_PHRASES = (
    "in today's",
    "in the realm of",
    "at the forefront of",
    "navigate the complexities",
    "stands as a testament to",
    "the rich tapestry of",
    "let's dive in",
    "embark on a journey",
    "it's worth noting that",
    "it's important to note that",
    "é importante ressaltar",
    "vale ressaltar",
    "vale destacar",
    "no mundo de hoje",
    "no cenário atual",
    "na era digital",
)

BANNED_OPENERS = (
    "Furthermore",
    "Moreover",
    "Additionally",
    "In addition",
    "Consequently",
    "Notably",
    "Importantly",
    "Ultimately",
    "In conclusion",
    "In summary",
    "Além disso",
    "Ademais",
    "Outrossim",
    "Dessa forma",
    "Desse modo",
    "Nesse sentido",
    "Diante disso",
    "Em contrapartida",
    "Em suma",
    "Em resumo",
    "Em conclusão",
    "Em última análise",
)

Finding = tuple[str, int, str]


def prose_lines(text: str) -> list[str]:
    """The document with every code span blanked, line for line."""
    lines: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            lines.append("")
            continue
        lines.append("" if fenced else re.sub(r"`[^`]*`", "", line))
    return lines


def check(name: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = prose_lines(text)

    for number, line in enumerate(lines, start=1):
        if EM_DASH in line:
            findings.append((name, number, "em-dash"))

        lowered = line.lower()
        for word in BANNED_WORDS_EN + BANNED_WORDS_PT:
            if re.search(rf"\b{re.escape(word)}\b", lowered):
                findings.append((name, number, f"banned word {word!r}"))

        stripped = line.lstrip("*_> ")
        for opener in BANNED_OPENERS:
            if re.match(rf"{re.escape(opener)}\b,", stripped):
                findings.append((name, number, f"signposting opener {opener!r}"))

    # Phrases are checked against the whole paragraph rather than the line. The
    # prose here is hard wrapped at 80 columns, so a four word phrase is about
    # as likely to straddle a line break as to sit inside one, and a per line
    # search would miss exactly the half that got wrapped.
    for start, paragraph in paragraphs(lines):
        joined = re.sub(r"\s+", " ", paragraph.lower())
        for phrase in BANNED_PHRASES:
            if phrase in joined:
                findings.append((name, start, f"banned phrase {phrase!r}"))

    return sorted(findings, key=lambda finding: finding[1])


def paragraphs(lines: list[str]) -> list[tuple[int, str]]:
    """Runs of non-blank lines, each with the line number it starts on."""
    found: list[tuple[int, str]] = []
    start = 0
    buffer: list[str] = []
    for number, line in enumerate(lines, start=1):
        if line.strip():
            if not buffer:
                start = number
            buffer.append(line)
            continue
        if buffer:
            found.append((start, " ".join(buffer)))
            buffer = []
    if buffer:
        found.append((start, " ".join(buffer)))
    return found


def targets() -> list[Path]:
    found = [REPO / name for name in FILES]
    for pattern in GLOBS:
        found.extend(sorted(REPO.glob(pattern)))
    return [path for path in found if path.exists()]


def main() -> int:
    findings: list[Finding] = []
    paths = targets()
    for path in paths:
        findings.extend(
            check(
                path.relative_to(REPO).as_posix(),
                path.read_text(encoding="utf-8"),
            )
        )

    for name, number, reason in findings:
        print(f"{name}:{number}: {reason}")

    if findings:
        print(f"\n{len(findings)} findings across {len(paths)} documents")
        return 1

    print(f"{len(paths)} documents clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
