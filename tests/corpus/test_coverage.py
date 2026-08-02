import json

import pytest

from catholic_bible.coverage import REPORT_PATH, build_report, render

COMMITTED = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

# Measured. The epic predicted the Vulgate would demonstrate the spine perfectly.
UNFILLED = {"matos-soares": 282, "douay-rheims": 81, "vulgata-clementina": 69}


def test_the_committed_report_is_what_the_code_produces() -> None:
    assert render(build_report()) == REPORT_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize(("code", "count"), sorted(UNFILLED.items()))
def test_the_unfilled_count_is_pinned(code: str, count: int) -> None:
    assert COMMITTED["versions"][code]["unfilled"] == count


@pytest.mark.parametrize("code", sorted(UNFILLED))
def test_published_and_unfilled_account_for_the_whole_spine(code: str) -> None:
    section = COMMITTED["versions"][code]
    assert section["published"] + section["unfilled"] == COMMITTED["spine_addresses"]


def test_the_report_refuses_to_state_an_orphan_rate_it_cannot_measure() -> None:
    """The epic asks for one. Nothing in this repo remembers the dropped verses.

    Publishing a zero would read as clean when it means unmeasured, which is the
    exact failure the honesty rules name.
    """
    assert COMMITTED["orphans"]["measurable_here"] is False
    assert len(COMMITTED["orphans"]["why"]) > 60


def test_the_vulgate_does_not_demonstrate_the_spine_perfectly() -> None:
    """The epic said zero. It is 69, and the epic is corrected rather than the
    number rounded."""
    assert COMMITTED["versions"]["vulgata-clementina"]["unfilled"] == 69
