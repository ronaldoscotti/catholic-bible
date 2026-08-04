"""The database the suite reads, and the client that reads it.

Built once per machine into the path the application uses, and reused while it
is newer than everything it was built from. Building the full corpus on every
red green cycle costs seconds that nobody would pay twice.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Before the application is imported, because the limiter reads its settings
# once at import. The whole suite arrives from one address and would spend the
# real budget partway through. The tests that care build their own limiter with
# their own numbers, and `tests/test_deployment.py` asserts that this default
# cannot reach a running container.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from catholic_bible import storage  # noqa: E402
from catholic_bible.api.app import app  # noqa: E402
from catholic_bible.api.routes import database as route_database  # noqa: E402
from catholic_bible.canon import DATA_DIR  # noqa: E402
from catholic_bible.storage.build import build  # noqa: E402
from catholic_bible.storage.database import DB_PATH, connect  # noqa: E402

INPUTS = (
    DATA_DIR / "canon.json",
    DATA_DIR / "versification.json",
    DATA_DIR / "corpus",
    DATA_DIR / "commentary",
    DATA_DIR / "cross-references",
    Path(storage.__file__).parent / "build.py",
)


def _is_stale(target: Path) -> bool:
    if not target.is_file():
        return True

    built = target.stat().st_mtime
    for source in INPUTS:
        newest = max(
            (path.stat().st_mtime for path in source.rglob("*") if path.is_file()),
            default=source.stat().st_mtime,
        )
        if newest > built:
            return True
    return False


@pytest.fixture(scope="session")
def database_path() -> Path:
    if _is_stale(DB_PATH):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        scratch = DB_PATH.with_suffix(".building")
        scratch.unlink(missing_ok=True)
        connection = sqlite3.connect(scratch)
        try:
            build(connection)
        finally:
            connection.close()
        scratch.replace(DB_PATH)
    return DB_PATH


@pytest.fixture(scope="session")
def database(database_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)
    yield connection
    connection.close()


@pytest.fixture
def client(database_path: Path) -> Iterator[TestClient]:
    """One client over the real database. Overridden so tests never build twice."""

    def read() -> Iterator[sqlite3.Connection]:
        connection = connect(database_path)
        try:
            yield connection
        finally:
            connection.close()

    app.dependency_overrides[route_database] = read
    yield TestClient(app)
    app.dependency_overrides.clear()
