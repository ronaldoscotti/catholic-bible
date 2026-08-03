"""The one error shape the whole document uses.

FastAPI emits `{"detail": …}` for its own validation failures and there is no way
to suppress that without fighting the framework, so errors go under that key with
a typed body inside rather than a sentence.

RFC 9457 problem details lost. It is the broader standard and adopting it would
mean either overriding FastAPI's built in validation shape or publishing two
error shapes in one document.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import Request
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
    NOT_ON_SPINE = "not_on_spine"
    UNPUBLISHED_IN_VERSION = "unpublished_in_version"
    MALFORMED = "malformed"
    WHOLE_CHAPTER = "whole_chapter"
    RANGE_TOO_LARGE = "range_too_large"

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


Responses = dict[int | str, dict[str, Any]]

NOT_FOUND: Responses = {
    404: {"model": ErrorResponse, "description": "No such resource"}
}
UNPROCESSABLE: Responses = {
    422: {"model": ErrorResponse, "description": "The reference cannot be resolved"}
}
