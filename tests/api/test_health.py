from importlib.metadata import version

from fastapi.testclient import TestClient

from catholic_bible.api.app import app

client = TestClient(app)


def test_health_reports_ok_and_the_installed_version() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": version("catholic-bible")}
