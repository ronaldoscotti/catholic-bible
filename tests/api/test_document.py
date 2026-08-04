"""The published document, and the two gates that keep it honest.

The committed copy matching the routes is one direction and CI runs it. The
other direction is a route that shipped with nothing said about it, which
FastAPI publishes without complaining, so nothing else notices.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from catholic_bible.api.app import app
from catholic_bible.api.document import rendered
from catholic_bible.api.errors import Reason
from catholic_bible.canon.mapping import OrphanReason
from catholic_bible.canon.reference import UnparsedReason

DOCUMENT = Path(__file__).resolve().parent.parent.parent / "openapi.json"


def _walk(routes: object) -> list[APIRoute]:
    """Included routers are not flattened into `app.routes`, so recurse.

    Reading only the top level finds `/health` and none of the seven that
    matter, and a walk over what it finds passes while proving nothing. That is
    what `test_there_are_routes_to_check` is for.
    """
    found: list[APIRoute] = []
    for route in routes:  # type: ignore[attr-defined]
        if isinstance(route, APIRoute):
            found.append(route)
        elif hasattr(route, "original_router"):
            found.extend(_walk(route.original_router.routes))
        elif hasattr(route, "routes"):
            found.extend(_walk(route.routes))
    return found


ROUTES = _walk(app.routes)
PUBLIC = [route for route in ROUTES if route.path.startswith("/v1")]


def identify(route: APIRoute) -> str:
    return route.path


def test_there_are_routes_to_check() -> None:
    """A walk over an empty list passes and proves nothing."""
    assert len(PUBLIC) == 13


@pytest.mark.parametrize("route", ROUTES, ids=identify)
def test_no_route_reaches_the_document_naked(route: APIRoute) -> None:
    assert route.summary, f"{route.path} carries no summary"
    assert route.response_model is not None, f"{route.path} declares no response model"


TAKES_INPUT = [
    route for route in PUBLIC if "{" in route.path or route.dependant.query_params
]


@pytest.mark.parametrize("route", TAKES_INPUT, ids=identify)
def test_every_route_taking_input_documents_how_it_refuses_it(
    route: APIRoute,
) -> None:
    """A route that can only succeed on paper is a route nobody handled.

    Only the ones taking input. `/v1/versions` reads no parameter and cannot
    fail, and documenting a 404 it never returns would be a lie that passes a
    checklist.
    """
    declared = {int(status) for status in route.responses}
    assert declared & {404, 422}, f"{route.path} documents no failure"


def test_the_only_route_exempt_from_that_is_the_one_taking_no_input() -> None:
    assert {route.path for route in PUBLIC} - {route.path for route in TAKES_INPUT} == {
        "/v1/versions"
    }


@pytest.mark.parametrize("route", ROUTES, ids=identify)
def test_the_api_is_read_only(route: APIRoute) -> None:
    """Criterion 8. Writing is refused rather than deferred.

    The connection is opened read only as well, so this holding is a
    convention and the driver refusing is the mechanism.
    """
    assert route.methods == {"GET"}, f"{route.path} answers {route.methods}"


def test_the_committed_document_matches_the_routes() -> None:
    """The same check CI runs, so a laptop notices before a push does."""
    assert DOCUMENT.read_text(encoding="utf-8") == rendered()


def test_every_reason_the_document_publishes_is_one_a_route_can_return() -> None:
    published = json.loads(DOCUMENT.read_text(encoding="utf-8"))
    enum = published["components"]["schemas"]["Reason"]["enum"]
    assert set(enum) == {str(reason) for reason in Reason}


def test_the_orphan_reasons_are_carried_through_rather_than_translated() -> None:
    """B1 owns them. A new one there has to surface here rather than vanish."""
    assert {str(reason) for reason in OrphanReason} <= {
        str(reason) for reason in Reason
    }
    assert {str(reason) for reason in UnparsedReason} <= {
        str(reason) for reason in Reason
    }


def test_the_health_route_stays_outside_the_versioned_surface(
    client: TestClient,
) -> None:
    """It is operational and it is not part of the contract a consumer pins."""
    assert client.get("/health").status_code == 200
    assert client.get("/v1/health").status_code == 404


def test_the_document_publishes_one_error_shape_and_only_one() -> None:
    """FastAPI's own validation error is a list under the same key.

    Declaring `responses={422: ErrorResponse}` replaces the entry in the
    document and not the behaviour, so the document promised an object while
    the runtime answered a list. A generated client breaks on the first
    malformed request and neither gate can see it, because both compare the
    document to the decorators.
    """
    published = DOCUMENT.read_text(encoding="utf-8")
    assert "HTTPValidationError" not in published

    schemas = json.loads(published)["components"]["schemas"]
    assert not [name for name in schemas if "Validation" in name]


@pytest.mark.parametrize(
    ("url", "why"),
    [
        ("/v1/resolve", "a required query parameter is missing"),
        ("/v1/resolve?ref=Jo 3,16&scheme=bogus", "an enum value is not one of them"),
        ("/v1/versions/matos-soares/books/JHN/chapters/x", "a path integer is not one"),
        (
            "/v1/versions/matos-soares/books/JHN/chapters/99999999999999999999",
            "a path integer is wider than the store can bind",
        ),
        (
            "/v1/books/JHN/chapters/99999999999999999999/verses/1/commentary",
            "the same number on the commentary route",
        ),
        (
            "/v1/books/JHN/chapters/3/verses/99999999999999999999/commentary",
            "and in the verse position",
        ),
    ],
)
def test_a_validation_failure_answers_in_the_published_shape(
    url: str, why: str, client: TestClient
) -> None:
    found = client.get(url)
    assert found.status_code == 422, why
    detail = found.json()["detail"]
    assert isinstance(detail, dict), why
    assert detail["reason"] == "malformed", why
    assert detail["message"], why


def test_health_fails_when_the_store_is_unreadable(tmp_path: Path) -> None:
    """Answering on the process alone reports healthy while every route 500s.

    `docker compose up --wait` then succeeds on a service that cannot serve a
    verse, which is the one thing the quickstart claims.
    """
    from catholic_bible.storage import database  # noqa: PLC0415

    # The override rather than the packaged path. Emptying that one only moves
    # resolution down to the per-user cache, so on a machine that has ever run
    # an installed copy this passed for the wrong reason.
    original = os.environ.get(database.OVERRIDE)
    os.environ[database.OVERRIDE] = str(tmp_path / "absent.db")
    try:
        found = TestClient(app, raise_server_exceptions=False).get("/health")
    finally:
        if original is None:
            del os.environ[database.OVERRIDE]
        else:
            os.environ[database.OVERRIDE] = original

    assert found.status_code == 503
    assert found.json()["detail"]["reason"] == "store_unavailable"
