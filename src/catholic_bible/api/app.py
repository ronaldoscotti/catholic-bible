from typing import Literal

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from catholic_bible import __version__
from catholic_bible.api import errors, routes
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


class Health(BaseModel):
    status: Literal["ok"]
    version: str


@app.get(
    "/health",
    summary="Whether the service can answer",
    response_model=Health,
    responses={
        503: {"model": errors.ErrorResponse, "description": "The store is unreadable"}
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
    return Health(status="ok", version=__version__)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)
