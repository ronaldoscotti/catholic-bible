"""What an installed copy does when the database is not there yet.

Derived data is not in the wheel, so the first run of an installed package has
no store at all. Before this, every `/v1` route answered 500 and `/health`
answered 503 telling the reader to run `make db`, which is a Makefile target
inside a checkout they do not have.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from catholic_bible.storage import bootstrap, database


def test_it_builds_when_nothing_is_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    wanted = tmp_path / "bible.db"
    monkeypatch.setenv(database.OVERRIDE, str(wanted))

    found = bootstrap.ensure()

    assert found == wanted
    assert wanted.is_file()
    with closing(sqlite3.connect(f"file:{wanted}?mode=ro", uri=True)) as check:
        assert check.execute("SELECT COUNT(*) FROM texts").fetchone()[0] > 0


def test_it_says_what_it_is_building_and_where(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Five seconds of silence on a first boot reads as a hang."""
    monkeypatch.setenv(database.OVERRIDE, str(tmp_path / "bible.db"))

    bootstrap.ensure()

    said = capsys.readouterr().out
    assert str(tmp_path) in said
    assert "once" in said


def test_it_does_not_rebuild_what_is_already_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Otherwise every restart pays for it, and a container restarts a lot."""
    wanted = tmp_path / "bible.db"
    monkeypatch.setenv(database.OVERRIDE, str(wanted))
    bootstrap.ensure()
    stamped = wanted.stat().st_mtime_ns
    capsys.readouterr()

    assert bootstrap.ensure() == wanted
    assert wanted.stat().st_mtime_ns == stamped
    assert capsys.readouterr().out == ""


def test_the_entry_point_builds_before_it_serves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before uvicorn, not on the first request.

    Nothing else asserts this. Deleting the call leaves the API booting into
    the 503 an installed copy was already giving, which reads as working
    because the process is up.
    """
    import uvicorn  # noqa: PLC0415

    from catholic_bible.api import app as application  # noqa: PLC0415

    wanted = tmp_path / "bible.db"
    monkeypatch.setenv(database.OVERRIDE, str(wanted))
    served: list[bool] = []
    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: served.append(wanted.is_file()))

    application.main()

    assert served == [True]


def test_an_interrupted_build_leaves_no_half_written_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A partial file at the target path reads as a database and is not one.

    The next boot would find a file, skip the build and serve a corpus with
    holes in it, which is worse than the crash that produced it.
    """
    wanted = tmp_path / "bible.db"
    monkeypatch.setenv(database.OVERRIDE, str(wanted))

    def explode(connection: sqlite3.Connection) -> None:
        raise RuntimeError("interrupted")

    monkeypatch.setattr(bootstrap, "build", explode)

    with pytest.raises(RuntimeError):
        bootstrap.ensure()

    assert not wanted.exists()
