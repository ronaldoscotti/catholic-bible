"""What an installed copy does when the database is not there yet.

Derived data is not in the wheel, so the first run of an installed package has
no store at all. Before this, every `/v1` route answered 500 and `/health`
answered 503 telling the reader to run `make db`, which is a Makefile target
inside a checkout they do not have.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
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


def test_the_notice_reaches_a_log_before_the_build_it_announces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Redirected stdout is block buffered, which is where a service runs.

    `capsys` cannot see this, because pytest replaces the stream. Run for real,
    into a pipe, and read the line while the build is still going.
    """
    wanted = tmp_path / "bible.db"
    script = "from catholic_bible.storage import bootstrap; bootstrap.ensure()"  # noqa: E501
    with subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.PIPE,
        text=True,
        env={**os.environ, database.OVERRIDE: str(wanted)},
    ) as running:
        assert running.stdout is not None
        said = running.stdout.readline()
        building = not wanted.is_file()
        running.wait(timeout=120)

    assert str(tmp_path) in said, said
    assert building, "the line only arrived after the build had finished"


def test_serving_the_app_directly_builds_it_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`uvicorn catholic_bible.api.app:app` is a real way to run this.

    The build used to live in `main()`, so the console script was covered and
    every other way of serving the same ASGI app booted into the 503 this epic
    exists to remove. It is a lifespan now, which every server runs.
    """
    from fastapi.testclient import TestClient  # noqa: PLC0415

    from catholic_bible.api.app import app  # noqa: PLC0415

    wanted = tmp_path / "bible.db"
    monkeypatch.setenv(database.OVERRIDE, str(wanted))

    with TestClient(app) as client:
        assert wanted.is_file()
        assert client.get("/health").status_code == 200


def test_the_scratch_file_is_not_shared_between_processes(tmp_path: Path) -> None:
    """`--workers 4` runs four of these at once against one target.

    A fixed scratch name means each deletes the others' half written file and
    all four move whatever is left into place, which is the corrupt database
    the atomic write exists to prevent.
    """
    seen = {
        bootstrap.scratch_for(tmp_path / "bible.db"),
        bootstrap.scratch_for(tmp_path / "bible.db"),
    }

    assert str(os.getpid()) in str(seen.pop())


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
