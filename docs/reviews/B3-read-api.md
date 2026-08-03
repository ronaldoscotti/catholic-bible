# Code review, B3 read API

*Stage 7. Written 2026-08-02, one author, plus the review tool run against the
epic.*

**A self review is not the gate.** One person, one repo. What is true is the
mechanism. Branch, pull request, never a push to `main`.

## What the diff is

A SQLite store built from the published corpus, 219 authored strings, a ported
reference formatter, seven routes, the published document and the two gates that
keep it honest. 449 tests.

## The thing worth most attention

**The scheme parameter is the whole epic in one field.** Without it `Sl 51,1`
resolves onto the spine, answers Psalm 51, and the reader who wanted the
Miserere gets the next psalm with a 200 and nothing said. The roadmap opens by
naming that failure as the reason this repo exists, and the first draft of the
spec had nothing on it.

It was found by a review of the spec, before any code. That is the gate working
rather than a story about the gate.

## The review tool ran, and the acceptance walk was wrong

Ten findings. Nine were real and one was a naming rather than a discovery. The
first one broke an acceptance criterion I had already marked met.

**A 500 with a traceback, on the criterion that forbids exactly that.**
`GET /v1/passage?ref=Jo 3,16&versions=,,` answered `500 Internal Server Error`.
The guard read the raw string, which is not empty for `,,` or for a single
space, and the comprehension below it then stripped every part away and returned
an empty list that the handler indexed.

```
$ curl -o /dev/null -w '%{http_code}' "…/v1/passage?ref=Jo%203,16&versions=,,"
500
```

Criterion 9 says an unresolvable reference returns a structured error, never a
stack trace. `docs/qa/B3-read-api.md` said met, and it was met for every input I
thought to try. The guard now reads the parsed list, five separator shapes are
pinned by a test, and the acceptance walk carries the correction rather than a
quiet edit.

**The published 422 was a lie on every route.** Declaring
`responses={422: ErrorResponse}` replaces the entry in the document and not the
behaviour. FastAPI's own validation failure answers with a list under `detail`
while the document promised an object with `reason` and `message`, so a
generated client breaks on the first malformed request.

Neither gate could see it, because both compare the document to the decorators
and neither sends a request. Fixed by reshaping validation failures into the
same body, so the document now has one error type and `HTTPValidationError`
appears nowhere in it. A test asserts that, and three parameterized cases send
real malformed requests and read the shape back.

**A whole book with no text answered 200 and an empty list**, where the chapter
and verse routes both answer 404 with `unpublished_in_version`. Not reachable
with three versions that all carry 73 books, and it is the silent empty response
that `versions_named` rejects in its own docstring one file over.

**Immutable caching on two answers the URL does not determine.** `resolve` and
`passage` without `versions` both take the preview, the text and the notation
from whichever version is the default, and that is not in the address. A year of
immutable is a year nothing can invalidate. Both now carry the same short header
the version list does, and `passage` keeps the immutable one when the caller
names the versions.

**One point query per address**, up to 501 round trips for a passage at the cap,
where the range is contiguous by construction. One `BETWEEN` replaces them. A
500 verse three version passage went from 21 ms to 5 ms, measured on a laptop.

**`preview` was documented as the first verse of the span** and is the first
verse the default version publishes. Matos Soares has 282 unfilled addresses, so
a span opening on one returns a later verse with nothing saying the first is
missing. The description now says which it is.

**`/health` could not fail the way the service fails.** It touched no storage,
so a missing database left every route failing while the container reported
healthy and `docker compose up --wait` succeeded. It reads the store now and
answers 503 with a named reason, and a test removes the file and checks.

**`LIMITS.md` contradicted itself inside one commit**, saying there was no API
four lines above a section about the API.

**Rationale was duplicated between docstrings and `DECISIONS.md`.** Three
modules restated an entry in full. Two copies of one argument drift and the
docstring is the copy nobody updates, so they point instead.

## The one finding that is a naming rather than a defect

**FTS5 work landed in an epic that says search is out of scope.** The schema
carries a decision made for B9 and a test builds an external content index to
prove the decision holds. It is argued in `DECISIONS.md` with what lost, and the
spec review already called it gold plating and was answered rather than
overruled quietly. It stays, and this paragraph is the record that the epic
boundary moved.

## What I checked because it would fail quietly

**Whether the three authored string invariants bite.** Mutated `Ecclus.` into
`Eccles.`, the abbreviation of the book beside it, and watched three tests fail.
An invariant nothing can fail is decoration.

**Whether the document gates bite, in both directions.** Edited one summary in
the committed document and `--check` exited 1. Deleted one summary from a route
and the walk failed that route by name.

**Whether the route walk walks anything.** The first version read `app.routes`,
which does not flatten an included router, so it inspected `/health` and passed
while the seven routes that matter went unexamined. A test asserting the count
is what caught it and it stays in the file.

**Whether the ported psalm table is right.** Compared against B1's `to_scheme`
verse by verse across all 150. They agree on 148 and disagree on 2, and that
disagreement is a B1 defect rather than a table error. Issue #22.

## What a second reviewer should look at first

The 219 authored strings, and specifically whether they are the forms a printed
Bible uses. Every check in this repo answers whether a string is consistent with
its book and none answers whether it is conventional. Nine carry conformance
cases and 210 do not.

Then the scheme parameter, which widened the public surface on day one and sends
three of its four values through B1 code carrying a known defect.
