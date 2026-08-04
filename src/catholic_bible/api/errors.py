"""The one error shape the whole document uses.

Errors go under FastAPI's own `detail` key with a typed body inside. Validation
failures are reshaped into the same body, so the document has one error type and
a generated client has one to handle. See DECISIONS.md for what lost.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from catholic_bible.canon.mapping import OrphanReason
from catholic_bible.canon.reference import UnparsedReason


class Reason(StrEnum):
    """Why a request could not be answered. A closed set, and the contract.

    A caller branches on this. The message beside it is a courtesy and it is
    free to change, which is why nothing should read it.

    The last five are B1's orphan reasons, carried through rather than
    translated, so an address that fails to map says the same thing here as it
    does in `orphans.json`. A test asserts the two sets stay in step.
    """

    UNKNOWN_VERSION = "unknown_version"
    UNKNOWN_BOOK = "unknown_book"
    UNKNOWN_SOURCE = "unknown_source"
    UNKNOWN_LANGUAGE = "unknown_language"
    NOT_ON_SPINE = "not_on_spine"
    UNPUBLISHED_IN_VERSION = "unpublished_in_version"
    MALFORMED = "malformed"
    WHOLE_CHAPTER = "whole_chapter"
    RANGE_TOO_LARGE = "range_too_large"
    STORE_UNAVAILABLE = "store_unavailable"
    RATE_LIMITED = "rate_limited"

    NO_COUNTERPART = "no_counterpart"
    CHAPTER_OUT_OF_RANGE = "chapter_out_of_range"
    VERSE_OUT_OF_RANGE = "verse_out_of_range"
    PSALM_TITLE = "psalm_title"


class Problem(BaseModel):
    reason: Reason
    message: str
    input: str | None = None


class ErrorResponse(BaseModel):
    detail: Problem


class ApiError(Exception):
    def __init__(
        self, status: int, reason: Reason, message: str, given: str | None = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.problem = Problem(reason=reason, message=message, input=given)


def not_found(reason: Reason, message: str, given: str | None = None) -> ApiError:
    return ApiError(404, reason, message, given)


def unprocessable(reason: Reason, message: str, given: str | None = None) -> ApiError:
    return ApiError(422, reason, message, given)


def from_orphan(reason: OrphanReason) -> Reason:
    return Reason(str(reason))


def from_unparsed(reason: UnparsedReason) -> Reason:
    return Reason(str(reason))


async def handle(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, ApiError)
    return JSONResponse(
        status_code=error.status,
        content={"detail": error.problem.model_dump()},
    )


async def handle_validation(request: Request, error: Exception) -> JSONResponse:
    """FastAPI's own 422, reshaped into the one error shape this API publishes.

    Left alone it answers with a list under `detail` while every route documents
    an object, so a generated client breaks on the first malformed request and
    the document gate cannot see it, because both directions only compare the
    document to the decorators.
    """
    assert isinstance(error, RequestValidationError)
    first = error.errors()[0]
    where = ".".join(str(part) for part in first["loc"][1:]) or "the request"
    problem = Problem(
        reason=Reason.MALFORMED,
        message=f"{where} is not acceptable. {first['msg']}",
        input=None if first.get("input") is None else str(first["input"]),
    )
    return JSONResponse(status_code=422, content={"detail": problem.model_dump()})


Responses = dict[int | str, dict[str, Any]]

NOT_FOUND: Responses = {
    404: {"model": ErrorResponse, "description": "No such resource"}
}
UNPROCESSABLE: Responses = {
    422: {"model": ErrorResponse, "description": "The reference cannot be resolved"}
}

# Declared on the router rather than on each route. Rate limiting happens in
# middleware, in front of everything, so it is not a property of any one route.
TOO_MANY: Responses = {
    429: {"model": ErrorResponse, "description": "Too many requests from this address"}
}
