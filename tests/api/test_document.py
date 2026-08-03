"""The published document, and the two gates that keep it honest.

The committed copy matching the routes is one direction and CI runs it. The
other direction is a route that shipped with nothing said about it, which
FastAPI publishes without complaining, so nothing else notices.
"""

from __future__ import annotations

import json
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
    assert len(PUBLIC) == 7


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
