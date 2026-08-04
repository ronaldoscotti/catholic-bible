from typing import Literal

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from catholic_bible import __version__
from catholic_bible.api import errors, routes
from catholic_bible.api.ratelimit import RateLimiter, State
from catholic_bible.storage import bootstrap
from catholic_bible.storage.database import connect

app = FastAPI(
    title="Catholic Bible",
    version=__version__,
    description=(
        "A read-only API for the Catholic Bible. 73 books, Portuguese, English "
        "and Latin, public domain throughout."
    ),
)
app.add_exception_handler(errors.ApiError, errors.handle)
app.add_exception_handler(RequestValidationError, errors.handle_validation)
app.include_router(routes.router)

# Shared with the middleware so `/health` can say the limiter stopped working.
# A limiter that silently stopped limiting is the hole this is here to avoid.
LIMITER = State()
app.add_middleware(RateLimiter, state=LIMITER)


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    limiter: str | None = None


@app.get(
    "/health",
    summary="Whether the service can answer",
    response_model=Health,
    response_model_exclude_none=True,
    responses={
        429: {"model": errors.ErrorResponse, "description": "Rate limited"},
        503: {"model": errors.ErrorResponse, "description": "The store is unreadable"},
    },
)
def health() -> Health:
    """Reads the store rather than only proving the process is alive.

    Answering on the process alone reports healthy while every `/v1` route
    fails, which is what a missing database does, and `docker compose up
    --wait` then succeeds on a service that cannot serve a verse.
    """
    try:
        connection = connect()
    except FileNotFoundError as absent:
        raise errors.ApiError(
            503, errors.Reason.STORE_UNAVAILABLE, str(absent)
        ) from absent

    try:
        connection.execute("SELECT 1 FROM versions LIMIT 1").fetchone()
    finally:
        connection.close()

    if LIMITER.degraded is not None:
        return Health(status="degraded", version=__version__, limiter=LIMITER.degraded)
    return Health(status="ok", version=__version__)


def main() -> None:
    """Serve, building the store first if an installed copy has none yet.

    Before uvicorn rather than on the first request, so a boot that cannot
    build fails where somebody is watching instead of inside a 500.
    """
    bootstrap.ensure()
    uvicorn.run(app, host="0.0.0.0", port=8000)
