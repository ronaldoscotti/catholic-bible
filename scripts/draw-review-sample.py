#!/usr/bin/env python3
"""Draws the sample a human has to read to give the translation an error rate.

This does not review anything. It picks the rows, writes them where a person can
work through them, and prints the interval the sample size supports. The verdict
column comes back filled in or the criterion stays unchecked.

Usage:
    scripts/draw-review-sample.py           into docs/qa/haydock-translation-sample.csv
    scripts/draw-review-sample.py --size 50  a smaller draw, same seed, same order
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from catholic_bible.commentary import load  # noqa: E402

DEST = Path(__file__).resolve().parent.parent / "docs" / "qa"

# Fixed, so the draw is the same on any machine and in any year. Redrawing a
# different sample after seeing the first one is how a rate stops meaning
# anything.
SEED = 20705

SIZE = 200

VERDICTS = "faithful | drifted | wrong | untranslated"

COLUMNS = ["address", "label", "english", "portuguese", "verdict", "note"]


def draw(size: int, seed: int) -> list[tuple[str, ...]]:
    entries = load("haydock").entries
    chosen = random.Random(seed).sample(range(len(entries)), size)
    chosen.sort()
    return [
        (
            str(entries[index].start),
            entries[index].label or "",
            entries[index].body["en-US"],
            entries[index].body["pt-BR"],
            "",
            "",
        )
        for index in chosen
    ]


def interval(size: int, rate: float = 0.05) -> float:
    """The half width of a 95% interval on a proportion, at this sample size.

    Printed rather than promised, so the README can state a bound the sample
    actually supports instead of a number that sounds careful.
    """
    return 1.96 * math.sqrt(rate * (1 - rate) / size)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=SIZE)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--dest", default=None)
    args = parser.parse_args()

    rows = draw(args.size, args.seed)
    dest = Path(args.dest) if args.dest else DEST / "haydock-translation-sample.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)

    with dest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    half = interval(args.size)
    print(f"drew {len(rows)} of 20705 entries, seed {args.seed}, into {dest}")
    print(f"fill in `verdict` with one of: {VERDICTS}")
    print(
        f"at this size an observed rate near 5% carries a 95% interval of "
        f"plus or minus {half * 100:.1f} points"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
