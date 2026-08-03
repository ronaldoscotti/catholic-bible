from typing import Literal

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from catholic_bible import __version__
from catholic_bible.api import errors, routes

app = FastAPI(
    title="Catholic Bible",
    version=__version__,
    description=(
        "A read-only API for the Catholic Bible. 73 books, Portuguese, English "
        "and Latin, public domain throughout."
    ),
)
app.add_exception_handler(errors.ApiError, errors.handle)
app.include_router(routes.router)


class Health(BaseModel):
    status: Literal["ok"]
    version: str


@app.get("/health", summary="Whether the service is up")
def health() -> Health:
    return Health(status="ok", version=__version__)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)
