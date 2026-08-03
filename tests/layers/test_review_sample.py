"""The sample a person has to read, and the one property it needs.

A sample that moves between runs is not a sample. Redrawing after seeing the
first result is how an error rate stops meaning anything, so the draw is pinned
to a seed and this is what pins the seed.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parent.parent.parent
SAMPLE = REPO / "docs" / "qa" / "haydock-translation-sample.csv"
VERDICTS = REPO / "docs" / "qa" / "haydock-translation-verdicts.csv"


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "draw_review_sample", REPO / "scripts" / "draw-review-sample.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _audit() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "audit_translation", REPO / "scripts" / "audit-translation.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_the_same_seed_draws_the_same_rows() -> None:
    script = _script()
    first = script.draw(20, script.SEED)
    second = script.draw(20, script.SEED)

    assert first == second
    assert script.draw(20, script.SEED + 1) != first


def test_the_committed_sample_is_what_the_seed_draws() -> None:
    """Not a file someone edited. Redrawing has to reproduce it byte for byte."""
    script = _script()
    drawn = script.draw(script.SIZE, script.SEED)

    with SAMPLE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["address", "label", "english", "portuguese", "verdict", "note"]
    assert [tuple(row) for row in rows[1:]] == drawn


def test_the_drawn_sample_still_carries_no_verdicts() -> None:
    """The verdicts live beside it rather than in it.

    `draw-review-sample.py` rewrites this file whole, so a verdict typed into the
    sample is a verdict the next draw destroys.
    """
    with SAMPLE.open(encoding="utf-8", newline="") as handle:
        verdicts = [row["verdict"] for row in csv.DictReader(handle)]

    assert len(verdicts) == 200
    assert not any(verdicts), "verdicts belong in haydock-translation-verdicts.csv"


def test_every_sampled_entry_has_a_verdict() -> None:
    with SAMPLE.open(encoding="utf-8", newline="") as handle:
        sampled = [row["address"] for row in csv.DictReader(handle)]
    with VERDICTS.open(encoding="utf-8", newline="") as handle:
        judged = {row["address"]: row["verdict"] for row in csv.DictReader(handle)}

    assert list(judged) == sampled
    assert set(judged.values()) <= {"faithful", "drifted", "wrong", "untranslated"}


def test_the_error_rate_the_prose_publishes_is_the_one_recorded() -> None:
    """README.md and LIMITS.md both carry 2.5% and five entries.

    A rate in the prose that nothing recomputes is a rate nobody can check, which
    is the same rule the structural audit numbers are held to.
    """
    with VERDICTS.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    flagged = [row for row in rows if row["verdict"] != "faithful"]
    inverted = [row for row in flagged if row["verdict"] == "wrong"]

    assert len(rows) == 200
    assert len(flagged) == 5
    assert len(inverted) == 2
    assert round(100 * len(flagged) / len(rows), 1) == 2.5
    assert all(row["note"] for row in flagged), "a flagged entry says why"


def test_no_flagged_entry_would_have_been_caught_by_the_audit() -> None:
    """The claim `LIMITS.md` makes about the boundary between the two checks.

    An inversion has the same length, markup and digits as a faithful rendering,
    so the mechanical audit passes all five. If that ever stops being true the
    prose saying so has to change.
    """
    audit = _audit()
    with VERDICTS.open(encoding="utf-8", newline="") as handle:
        flagged = {
            row["address"] for row in csv.DictReader(handle)
            if row["verdict"] != "faithful"
        }
    with SAMPLE.open(encoding="utf-8", newline="") as handle:
        pairs = [
            (row["address"], row["english"], row["portuguese"])
            for row in csv.DictReader(handle)
            if row["address"] in flagged
        ]

    found = audit.compare(pairs)
    assert all(not hits for hits in found.values()), found
