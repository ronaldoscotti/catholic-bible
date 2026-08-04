"""The middleware, against a real app, with the clock injected.

Waiting out a real window would put an hour in the suite, so time is a function
the limiter is handed. Everything else here is the running application.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from catholic_bible.api.ratelimit import RateLimiter, Settings, State

VERSE = "/v1/versions/vulgata-clementina/books/SIR/chapters/24/verses/1"


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


def stack(settings: Settings, clock: Clock, state: State | None = None) -> RateLimiter:
    """The real application with the limiter wrapped around it.

    Wrapping rather than `add_middleware`, because the app is a module level
    object and mutating it would leak the limiter into every other test.
    """
    from catholic_bible.api.app import app

    return RateLimiter(
        app,
        settings=settings,
        state=state if state is not None else State(),
        clock=clock,
    )


def build(
    settings: Settings, clock: Clock, state: State | None = None
) -> Iterator[TestClient]:
    with TestClient(
        stack(settings, clock, state), client=("203.0.113.9", 5000)
    ) as client:
        yield client


@pytest.fixture
def limited(tmp_path: Path, clock: Clock) -> Iterator[TestClient]:
    settings = Settings(
        per_minute=3, per_hour=5, db_path=tmp_path / "rl.db", enabled=True
    )
    yield from build(settings, clock)


def test_a_request_under_the_limit_reaches_the_route(limited: TestClient) -> None:
    answer = limited.get(VERSE)

    assert answer.status_code == 200
    assert answer.json()["id"] == "SIR.24.1"


def test_the_last_allowed_request_passes_and_the_next_is_refused(
    limited: TestClient,
) -> None:
    """The boundary the epic's verification names."""
    for _ in range(3):
        assert limited.get(VERSE).status_code == 200

    refused = limited.get(VERSE)

    assert refused.status_code == 429


def test_the_refusal_uses_the_one_error_shape_this_api_publishes(
    limited: TestClient,
) -> None:
    for _ in range(4):
        answer = limited.get(VERSE)

    assert answer.status_code == 429
    assert answer.json()["detail"]["reason"] == "rate_limited"
    assert answer.json()["detail"]["message"]


def test_retry_after_counts_to_the_end_of_the_window(
    limited: TestClient, clock: Clock
) -> None:
    clock.now = 10.0
    for _ in range(4):
        answer = limited.get(VERSE)

    assert answer.status_code == 429
    assert answer.headers["retry-after"] == "50"


def test_the_next_window_admits_the_caller_again(tmp_path: Path, clock: Clock) -> None:
    """The reset window the epic's verification names.

    The hour is switched off here on purpose. With both windows on, a caller
    who spends the minute limit repeatedly is eventually refused by the hour,
    and this test would then pass or fail on the wrong window.
    """
    settings = Settings(per_minute=3, per_hour=0, db_path=tmp_path / "rl.db")
    for client in build(settings, clock):
        for _ in range(3):
            assert client.get(VERSE).status_code == 200
        assert client.get(VERSE).status_code == 429

        clock.now = 60.0

        assert client.get(VERSE).status_code == 200


def test_the_hour_is_what_retry_after_reports_when_both_are_spent(
    limited: TestClient, clock: Clock
) -> None:
    """The hour is the one the caller actually has to wait out."""
    for minute in range(3):
        clock.now = float(minute * 60)
        for _ in range(2):
            limited.get(VERSE)

    assert limited.get(VERSE).status_code == 429
    assert int(limited.get(VERSE).headers["retry-after"]) == 3600 - 120


def test_two_addresses_do_not_share_a_budget(tmp_path: Path, clock: Clock) -> None:
    settings = Settings(per_minute=2, per_hour=0, db_path=tmp_path / "rl.db")
    limited = stack(settings, clock)

    with TestClient(limited, client=("203.0.113.9", 1)) as first:
        assert first.get(VERSE).status_code == 200
        assert first.get(VERSE).status_code == 200
        assert first.get(VERSE).status_code == 429

    with TestClient(limited, client=("198.51.100.4", 1)) as second:
        assert second.get(VERSE).status_code == 200


def test_loopback_is_never_counted(tmp_path: Path, clock: Clock) -> None:
    """The container health check is the service asking itself if it is alive.

    Twelve times a minute, forever, and it would spend a real budget.
    """
    settings = Settings(per_minute=2, per_hour=0, db_path=tmp_path / "rl.db")

    with TestClient(stack(settings, clock), client=("127.0.0.1", 1)) as inside:
        for _ in range(10):
            assert inside.get("/health").status_code == 200


def test_health_counts_against_the_same_budget_as_scripture(
    limited: TestClient,
) -> None:
    """One budget per address, so flooding the cheap route buys nothing."""
    assert limited.get("/health").status_code == 200
    assert limited.get(VERSE).status_code == 200
    assert limited.get("/health").status_code == 200

    assert limited.get(VERSE).status_code == 429


def test_the_headers_let_a_caller_slow_down_before_being_refused(
    limited: TestClient,
) -> None:
    """A limit discoverable only by being refused guarantees one refusal."""
    answer = limited.get(VERSE)

    assert answer.status_code == 200
    assert answer.headers["ratelimit-limit"] == "3"
    assert answer.headers["ratelimit-remaining"] == "2"
    assert answer.headers["ratelimit-reset"] == "60"

    assert limited.get(VERSE).headers["ratelimit-remaining"] == "1"


def test_the_headers_report_the_window_closest_to_being_spent(
    limited: TestClient, clock: Clock
) -> None:
    """Two windows, and the useful one is whichever bites first."""
    for minute in range(2):
        clock.now = float(minute * 60)
        for _ in range(2):
            limited.get(VERSE)

    clock.now = 120.0
    answer = limited.get(VERSE)

    assert answer.headers["ratelimit-limit"] == "5"
    assert answer.headers["ratelimit-remaining"] == "0"


def test_a_disabled_limiter_never_refuses_and_writes_nothing(
    tmp_path: Path, clock: Clock
) -> None:
    store = tmp_path / "rl.db"
    settings = Settings(per_minute=1, per_hour=1, db_path=store, enabled=False)
    for client in build(settings, clock):
        for _ in range(5):
            assert client.get(VERSE).status_code == 200
        assert "ratelimit-limit" not in client.get(VERSE).headers

    assert not store.exists(), "a disabled limiter touches no disk"


def test_an_unusable_store_serves_the_request_and_says_so(
    tmp_path: Path, clock: Clock
) -> None:
    """Fail open and loud. The state before B8 was unlimited, so serving is a
    return to the previous posture rather than a new hole. Being quiet is the
    hole.
    """
    state = State()
    settings = Settings(
        per_minute=1, per_hour=0, db_path=tmp_path / "gone" / "rl.db", enabled=True
    )
    for client in build(settings, clock, state):
        for _ in range(3):
            assert client.get(VERSE).status_code == 200

    assert state.degraded is not None
    assert "rl.db" in state.degraded


def test_health_says_ok_in_exactly_the_bytes_the_readme_publishes() -> None:
    """`ci.yml` greps that line out of `README.md` and compares it literally.

    A new field serialised as null breaks the quickstart job, so the healthy
    body has to stay character for character what it was before B8.
    """
    from catholic_bible.api.app import app

    with TestClient(app) as client:
        answer = client.get("/health")

    published = [
        line
        for line in (Path("README.md").read_text(encoding="utf-8")).splitlines()
        if line.startswith('{"status"')
    ]

    assert answer.status_code == 200
    assert published == [answer.text]


def test_health_reports_degraded_while_the_limiter_is_unusable(
    tmp_path: Path, clock: Clock
) -> None:
    """Fail open and loud, and this is the loud half.

    A limiter that silently stopped limiting is the classic hole in security
    middleware. The failure shows up in the same place everything else about
    this service shows up.
    """
    from catholic_bible.api import app as module

    state = module.LIMITER
    settings = Settings(
        per_minute=1, per_hour=0, db_path=tmp_path / "gone" / "rl.db", enabled=True
    )
    try:
        for client in build(settings, clock, state):
            body = client.get("/health").json()

        assert body["status"] == "degraded"
        assert "rl.db" in body["limiter"]
    finally:
        state.degraded = None


def test_a_store_that_dies_after_opening_still_fails_open(
    tmp_path: Path, clock: Clock, monkeypatch: pytest.MonkeyPatch
) -> None:
    from catholic_bible.storage import ratelimit as store

    state = State()
    settings = Settings(per_minute=1, per_hour=0, db_path=tmp_path / "rl.db")

    def explode(*args: object, **kwargs: object) -> int:
        raise sqlite3.OperationalError("disk I/O error")

    for client in build(settings, clock, state):
        assert client.get(VERSE).status_code == 200
        monkeypatch.setattr(store.Counter, "hit", explode)
        assert client.get(VERSE).status_code == 200
        assert client.get(VERSE).status_code == 200

    assert state.degraded is not None
