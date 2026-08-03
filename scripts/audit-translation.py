#!/usr/bin/env python3
"""Structural comparison of the Portuguese commentary against its English source.

Five mechanical checks. None of them reads for meaning, so none of them replaces
the human sample `draw-review-sample.py` writes. What they catch is a body that
was never translated, one that was truncated, markup that moved and a citation
number that did not survive.

The numbers this prints are the ones quoted in `README.md` and `LIMITS.md`. It is
committed so a reader can re-derive them rather than take them on trust, which
was a review finding against the first version of those tables.

Usage:
    scripts/audit-translation.py            the whole corpus and the sample
    scripts/audit-translation.py --show 6   plus six of each difference
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from catholic_bible.commentary import load  # noqa: E402
from catholic_bible.storage.build import plain  # noqa: E402

SAMPLE = Path(__file__).resolve().parent.parent / "docs" / "qa"

SOURCE, TARGET = "en-US", "pt-BR"

_EMPHASIS = re.compile(r"<(/?)(em|strong)\b")
_NUMBER = re.compile(r"\d+")

# English writes 400,000 and Portuguese writes 400.000. Without joining the
# groups first the comparison reports 112 differences where 28 are punctuation.
_THOUSANDS = re.compile(r"(?<=\d)[,.   ](?=\d{3}(?!\d))")

# Outside this band a body is either truncated or padded. The 244 bodies the
# export cuts at a leaked marker land between 0.85 and 1.32 once cut.
FLOOR, CEILING = 0.6, 1.8


def digits(text: str) -> collections.Counter[str]:
    joined = text
    for _ in range(3):
        joined = _THOUSANDS.sub("", joined)
    return collections.Counter(_NUMBER.findall(joined))


def compare(pairs: list[tuple[str, str, str]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {
        "empty": [],
        "identical to the source": [],
        "length outside the band": [],
        "emphasis markup differs": [],
        "a digit does not survive": [],
    }
    for key, source, target in pairs:
        clean_source, clean_target = plain(source), plain(target)
        if not clean_target.strip():
            found["empty"].append(key)
            continue
        if clean_target.strip() == clean_source.strip():
            found["identical to the source"].append(key)
        ratio = len(clean_target) / max(len(clean_source), 1)
        if ratio < FLOOR or ratio > CEILING:
            found["length outside the band"].append(key)
        if sorted(_EMPHASIS.findall(source)) != sorted(_EMPHASIS.findall(target)):
            found["emphasis markup differs"].append(key)
        if digits(clean_source) != digits(clean_target):
            found["a digit does not survive"].append(key)
    return found


def report(label: str, pairs: list[tuple[str, str, str]], show: int) -> None:
    found = compare(pairs)
    total = len(pairs)
    print(f"--- {label}: {total} entries ---")
    for name, hits in found.items():
        share = 100 * len(hits) / total if total else 0
        print(f"  {name:28} {len(hits):5}  {share:6.2f}%")
        for key in hits[:show]:
            print(f"      {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", type=int, default=0)
    args = parser.parse_args()

    entries = load("haydock").entries
    report(
        "the whole corpus",
        [(str(e.start), e.body[SOURCE], e.body[TARGET]) for e in entries],
        args.show,
    )

    print()
    with (SAMPLE / "haydock-translation-sample.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    report(
        "the committed sample",
        [(row["address"], row["english"], row["portuguese"]) for row in rows],
        args.show,
    )

    print()
    print(
        "None of these reads for meaning. A fluent paragraph saying the opposite"
        " of the original passes every one of them."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
