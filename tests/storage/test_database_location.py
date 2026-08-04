"""Where the read database is, which is three answers rather than one.

Inside a checkout and inside the Docker image the file is beside the code and
nothing changes. Installed from a registry it cannot be, because it is derived,
so it is not in the wheel and `site-packages` is not reliably writable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from catholic_bible import __version__
from catholic_bible.storage import database


def test_the_override_wins_over_everything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The operator's answer, and the one the tests use."""
    wanted = tmp_path / "elsewhere.db"
    monkeypatch.setenv("CATHOLIC_BIBLE_DB", str(wanted))

    assert database.resolve() == wanted


def test_the_packaged_file_wins_when_it_is_already_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A checkout and the image both build it ahead of time.

    Neither changes behaviour, which is the point of putting this branch above
    the cache rather than below it.
    """
    monkeypatch.delenv("CATHOLIC_BIBLE_DB", raising=False)
    packaged = tmp_path / "bible.db"
    packaged.write_bytes(b"")
    monkeypatch.setattr(database, "DB_PATH", packaged)

    assert database.resolve() == packaged


def test_an_installed_copy_falls_through_to_a_writable_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`site-packages` is not reliably writable and this is the installed case.

    A system install, a read-only container filesystem and a wheel installed as
    root then run unprivileged all fail to write beside the code, and a first
    boot that dies on permissions is worse than the 503 it replaces.
    """
    monkeypatch.delenv("CATHOLIC_BIBLE_DB", raising=False)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "absent.db")

    found = database.resolve()

    assert found != tmp_path / "absent.db"
    assert found.name == "bible.db"
    assert found.is_relative_to(database.cache_root())


def test_the_cache_path_carries_the_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`LIMITS.md` already has a heading for the failure this prevents.

    Nothing readable from inside a database says when it was filled, so a
    cache keyed on nothing would hand a stale one to everybody who ever runs
    `pip install -U` and say nothing about it.
    """
    monkeypatch.delenv("CATHOLIC_BIBLE_DB", raising=False)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "absent.db")

    assert __version__ in database.resolve().parts


def test_the_cache_root_follows_the_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """`XDG_CACHE_HOME` is the one a container or a CI runner actually sets."""
    monkeypatch.setattr(database.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CACHE_HOME", "/somewhere/cache")

    assert database.cache_root() == Path("/somewhere/cache")
