"""That the limiter is on where it matters.

`tests/conftest.py` turns it off, because 596 tests arrive from one address and
would spend the real budget partway through. Turning something off for the tests
is how it ends up off everywhere, so this is the file that stops that.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from catholic_bible.api.ratelimit import Settings

REPO = Path(__file__).resolve().parent.parent
COMPOSE = (REPO / "compose.yaml").read_text(encoding="utf-8")
DOCKERFILE = (REPO / "Dockerfile").read_text(encoding="utf-8")
CONFTEST = (REPO / "tests" / "conftest.py").read_text(encoding="utf-8")

# Covers the three ways this could be written off: compose `KEY: value`, a
# Dockerfile `ENV KEY=value`, and the `setdefault(KEY, value)` in conftest.
OFF = re.compile(
    r"RATE_LIMIT_ENABLED[\"']?\s*[:=,]\s*[\"']?(0|false|no|off)\b", re.IGNORECASE
)


def test_the_shipped_default_is_on() -> None:
    """With nothing configured at all, the limiter limits."""
    assert Settings.from_env({}).enabled is True


def test_the_application_the_service_starts_actually_refuses(tmp_path: Path) -> None:
    """That `app` installs the limiter, not just that a limiter works.

    Every other test in this epic wraps `RateLimiter` around the app by hand,
    and `conftest.py` disables the one the app installs. Deleting
    `add_middleware` from `app.py` left the whole suite green, which means
    criterion 1 was verified against a limiter the service does not run.

    A subprocess rather than a reload, because the settings are read once at
    import and this has to be the real import. The path is one that does not
    exist, so the limiter is proved to run in front of routing and no corpus
    database has to be built for it.
    """
    script = textwrap.dedent(
        """
        from fastapi.testclient import TestClient
        from catholic_bible.api.app import app

        client = TestClient(app, client=("203.0.113.9", 1))
        print([client.get("/nothing-here").status_code for _ in range(4)])
        """
    )
    finished = subprocess.run(
        [sys.executable, "-c", script],
        env={
            **os.environ,
            "RATE_LIMIT_ENABLED": "true",
            "RATE_LIMIT_PER_MINUTE": "2",
            "RATE_LIMIT_PER_HOUR": "0",
            "RATE_LIMIT_DB": str(tmp_path / "rl.db"),
        },
        capture_output=True,
        text=True,
        check=True,
    )

    assert finished.stdout.strip() == "[404, 404, 429, 429]", finished.stderr


def test_nothing_that_ships_turns_the_limiter_off() -> None:
    for name, text in (("compose.yaml", COMPOSE), ("Dockerfile", DOCKERFILE)):
        assert not OFF.search(text), f"{name} disables rate limiting"


def test_the_suite_is_the_only_place_that_turns_it_off() -> None:
    """Named here so the exemption is one grep away rather than a surprise."""
    assert OFF.search(CONFTEST), "conftest no longer disables it, so this file lies"


def test_the_ported_limits_are_what_ships() -> None:
    """60 a minute and 1000 an hour, both from the private source in production.

    A default nobody chose is a default nobody can defend. These two ran on a
    live service before they were copied here.
    """
    settings = Settings.from_env({})

    assert settings.windows() == ((60, 60), (3600, 1000))


def test_no_proxy_is_trusted_until_something_configures_one() -> None:
    """B6 owns this value. Empty is the only safe guess.

    Trusting a forwarded header by default would let anyone hand themselves a
    fresh bucket per request, which limits the honest caller and nobody else.
    """
    assert Settings.from_env({}).trusted == frozenset()
    assert 'RATE_LIMIT_TRUSTED_PROXIES: "${RATE_LIMIT_TRUSTED_PROXIES:-}"' in COMPOSE


def test_the_limits_can_be_changed_without_editing_a_file() -> None:
    """Criterion 3. The compose file passes the shell through with defaults."""
    for name, default in (
        ("RATE_LIMIT_PER_MINUTE", 60),
        ("RATE_LIMIT_PER_HOUR", 1000),
    ):
        assert f'{name}: "${{{name}:-{default}}}"' in COMPOSE


def test_the_readme_publishes_the_limits_it_enforces() -> None:
    """A limit a caller cannot read about is a limit they discover by being cut off."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    settings = Settings.from_env({})

    assert f"{settings.per_minute} requests a minute" in readme
    assert f"{settings.per_hour} an hour" in readme
    assert "RateLimit-Remaining" in readme
