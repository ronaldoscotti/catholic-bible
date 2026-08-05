from collections.abc import Iterator
from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient

from catholic_bible.api.app import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Enters the context manager so the app lifespan runs, which B1 will need."""
    with TestClient(app) as c:
        yield c


def test_health_reports_ok_and_the_installed_version(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": version("the-catholic-bible"),
    }
