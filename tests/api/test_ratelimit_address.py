"""Who the limiter thinks you are, and the configuration that decides it.

The first test is the spoofing case rather than the happy path. A limiter that
believes `X-Forwarded-For` from anyone is worse than no limiter, because the
caller sending a fresh value per request walks through while the honest one
stays counted.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from catholic_bible.api.ratelimit import Settings, resolve, trusted_set

NOBODY = trusted_set("")
CADDY = trusted_set("10.0.0.5")


def test_a_forwarded_header_from_an_untrusted_peer_is_ignored() -> None:
    """The attack. Anyone can send this header and nobody may be believed."""
    assert resolve("203.0.113.9", "1.1.1.1", NOBODY) == "203.0.113.9"
    assert resolve("203.0.113.9", "1.1.1.1, 2.2.2.2", CADDY) == "203.0.113.9"


def test_a_forwarded_header_from_a_trusted_peer_is_read() -> None:
    assert resolve("10.0.0.5", "203.0.113.9", CADDY) == "203.0.113.9"


def test_the_rightmost_untrusted_entry_wins_not_the_leftmost() -> None:
    """The left end is whatever the client sent and the right end is the truth.

    Each proxy appends, so reading left to right is reading the client's own
    claim first. `9.9.9.9` here is a value the caller made up.
    """
    assert resolve("10.0.0.5", "9.9.9.9, 203.0.113.9", CADDY) == "203.0.113.9"


def test_trusted_hops_are_skipped_from_the_right() -> None:
    chain = "203.0.113.9, 10.0.0.5"
    assert resolve("10.0.0.5", chain, CADDY) == "203.0.113.9"


def test_a_header_of_only_trusted_proxies_falls_back_to_the_peer() -> None:
    assert resolve("10.0.0.5", "10.0.0.5, 10.0.0.5", CADDY) == "10.0.0.5"


def test_a_malformed_header_falls_back_rather_than_raising() -> None:
    for header in ("", "   ", "not-an-address", "1.1.1.1, garbage", ",,,"):
        assert resolve("10.0.0.5", header, CADDY) == "10.0.0.5", header


def test_a_request_with_no_peer_is_limited_rather_than_exempt() -> None:
    """An unattributable request must not be a free one."""
    assert resolve(None, None, NOBODY) == "unknown"
    assert resolve(None, "1.1.1.1", CADDY) == "unknown"


def test_a_trusted_range_covers_the_addresses_docker_hands_out() -> None:
    """A compose network renumbers, so a bare address would need editing."""
    network = trusted_set("172.16.0.0/12")
    assert resolve("172.18.0.3", "203.0.113.9", network) == "203.0.113.9"
    assert resolve("192.168.1.1", "203.0.113.9", network) == "192.168.1.1"


def test_several_trusted_entries_are_all_honoured() -> None:
    both = trusted_set("10.0.0.5, 172.16.0.0/12")
    assert resolve("10.0.0.5", "203.0.113.9", both) == "203.0.113.9"
    assert resolve("172.18.0.3", "203.0.113.9", both) == "203.0.113.9"


def test_a_malformed_trusted_entry_fails_at_startup() -> None:
    """A typo here silently disables the header, which is the quiet failure."""
    with pytest.raises(ValueError, match="banana"):
        trusted_set("10.0.0.5, banana")


def test_the_defaults_are_the_ported_numbers(tmp_path: Path) -> None:
    settings = Settings.from_env({})

    assert settings.per_minute == 60
    assert settings.per_hour == 1000
    assert settings.enabled is True
    assert settings.trusted == frozenset()


def test_every_setting_is_overridable(tmp_path: Path) -> None:
    settings = Settings.from_env(
        {
            "RATE_LIMIT_PER_MINUTE": "10",
            "RATE_LIMIT_PER_HOUR": "20",
            "RATE_LIMIT_ENABLED": "false",
            "RATE_LIMIT_DB": str(tmp_path / "rl.db"),
            "RATE_LIMIT_TRUSTED_PROXIES": "10.0.0.5",
        }
    )

    assert settings.per_minute == 10
    assert settings.per_hour == 20
    assert settings.enabled is False
    assert settings.db_path == tmp_path / "rl.db"
    assert resolve("10.0.0.5", "203.0.113.9", settings.trusted) == "203.0.113.9"


def test_zero_disables_one_window_and_leaves_the_other() -> None:
    settings = Settings.from_env({"RATE_LIMIT_PER_MINUTE": "0"})

    assert settings.windows() == ((3600, 1000),)


def test_both_windows_are_enforced_by_default() -> None:
    assert Settings.from_env({}).windows() == ((60, 60), (3600, 1000))


def test_an_unparseable_limit_fails_at_startup_rather_than_defaulting() -> None:
    """A typo in a limit is not noticed until the bill arrives."""
    with pytest.raises(ValueError):
        Settings.from_env({"RATE_LIMIT_PER_MINUTE": "sixty"})


def test_a_negative_limit_is_refused() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"RATE_LIMIT_PER_HOUR": "-1"})


@pytest.mark.parametrize("value", ["false", "False", "0", "no", "off"])
def test_the_off_switch_accepts_what_a_person_would_write(value: str) -> None:
    assert Settings.from_env({"RATE_LIMIT_ENABLED": value}).enabled is False


@pytest.mark.parametrize("value", ["true", "True", "1", "yes", "on"])
def test_the_on_switch_accepts_what_a_person_would_write(value: str) -> None:
    assert Settings.from_env({"RATE_LIMIT_ENABLED": value}).enabled is True
