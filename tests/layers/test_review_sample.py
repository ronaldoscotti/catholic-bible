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


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "draw_review_sample", REPO / "scripts" / "draw-review-sample.py"
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


def test_the_sample_carries_no_verdicts_yet() -> None:
    """Unchecked because this column is empty, not because nobody bothered."""
    with SAMPLE.open(encoding="utf-8", newline="") as handle:
        verdicts = [row["verdict"] for row in csv.DictReader(handle)]

    assert len(verdicts) == 200
    assert not any(verdicts), "a filled sample means LIMITS.md has to be updated"
