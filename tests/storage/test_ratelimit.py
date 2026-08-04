"""The counter, with no HTTP anywhere near it.

Windows are arithmetic on an integer and a bucket is a string, so all of this is
testable without a request. The one property that needs a real file is the last
test, which is the whole reason this is not a dictionary.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from catholic_bible.storage.ratelimit import Counter


@pytest.fixture
def counter(tmp_path: Path) -> Iterator[Counter]:
    made = Counter(tmp_path / "ratelimit.db")
    yield made
    made.close()


def test_the_first_hit_is_one_and_the_next_is_two(counter: Counter) -> None:
    assert counter.hit("1.2.3.4", window=60, now=0) == 1
    assert counter.hit("1.2.3.4", window=60, now=0) == 2
    assert counter.hit("1.2.3.4", window=60, now=59) == 3


def test_two_buckets_do_not_see_each_other(counter: Counter) -> None:
    assert counter.hit("1.2.3.4", window=60, now=0) == 1
    assert counter.hit("5.6.7.8", window=60, now=0) == 1


def test_the_same_address_in_two_windows_is_two_buckets(counter: Counter) -> None:
    """A minute limit and an hour limit count the same request separately."""
    assert counter.hit("1.2.3.4", window=60, now=0) == 1
    assert counter.hit("1.2.3.4", window=3600, now=0) == 1


def test_the_next_window_starts_again_at_one(counter: Counter) -> None:
    assert counter.hit("1.2.3.4", window=60, now=59) == 1
    assert counter.hit("1.2.3.4", window=60, now=60) == 1
    assert counter.hit("1.2.3.4", window=60, now=61) == 2


def test_a_second_connection_sees_the_first_ones_count(tmp_path: Path) -> None:
    """The reason this is a file rather than a dictionary.

    Two uvicorn workers are two processes. In memory counters would give each
    one its own budget and enforce four times the configured limit on four
    workers, which is a limit nobody can reason about.
    """
    path = tmp_path / "ratelimit.db"
    first, second = Counter(path), Counter(path)
    try:
        assert first.hit("1.2.3.4", window=60, now=0) == 1
        assert second.hit("1.2.3.4", window=60, now=0) == 2
        assert first.hit("1.2.3.4", window=60, now=0) == 3
    finally:
        first.close()
        second.close()


def test_reset_reports_when_the_window_ends(counter: Counter) -> None:
    assert counter.reset_in(window=60, now=0) == 60
    assert counter.reset_in(window=60, now=59) == 1
    assert counter.reset_in(window=60, now=60) == 60
    assert counter.reset_in(window=3600, now=61) == 3539


def test_pruning_drops_dead_windows_and_keeps_the_live_one(counter: Counter) -> None:
    counter.hit("1.2.3.4", window=60, now=0)
    counter.hit("1.2.3.4", window=60, now=600)
    assert counter.rows() == 2

    counter.prune(window=60, now=600)

    assert counter.rows() == 1
    assert counter.hit("1.2.3.4", window=60, now=600) == 2


def test_pruning_keeps_the_window_immediately_before_this_one(
    counter: Counter,
) -> None:
    """Deleting it would forgive a caller who is one second into a new window.

    The previous window is still the one a `Retry-After` handed out a moment ago
    refers to, so it stays until it is two windows old.
    """
    counter.hit("1.2.3.4", window=60, now=0)
    counter.prune(window=60, now=60)

    assert counter.rows() == 1


def test_an_unwritable_store_raises_rather_than_counting_nothing(
    tmp_path: Path,
) -> None:
    """Silently counting nothing is the failure the middleware has to see.

    It decides to fail open. It can only do that if this layer is loud.
    """
    with pytest.raises(sqlite3.Error):
        Counter(tmp_path / "no-such-directory" / "ratelimit.db")
