# [B3] Read API

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/api` |
| Depends on | B1, B2 |
| Blocks | B6, and C1 in `concordantia` |

**As** a developer building a Catholic app
**I need** an HTTP API that returns Scripture by reference, chapter and range
**So that** I can ship something on a weekend without cloning a repo, running a generator, or learning how the dataset is laid out

**As** the author of `concordantia`
**I need** that same API to be the only way I reach this data
**So that** the contract gets exercised by a real consumer from the first week instead of after it is too late to change

## Context

Static JSON on a CDN already covers a developer who wants to read a chapter, and B5 ships exactly that. The API earns its place on two other things. It answers by reference rather than by file path, which is what an application actually holds, and it is the seam the sibling repo consumes.

The second point is the one that matters more than it looks. If `concordantia` reaches into this repo's database, the two are one system wearing two names and the contract is never tested. If it consumes the published API and the published artifact the way a stranger would, a wrong contract shows up in the first hour.

## Source

The endpoints exist and are documented in a private repo, with the passage reader, the controller and the response shapes already tested. `CONTEXT.local.md` lists the exact routes that port and the three that do not, along with the API documents that serve as the contract. Match the existing response shape unless there is a reason to break it, and record the reason when there is.

## Problem

Reading a specific verse today means picking a data dump, learning its layout, writing a parser for its book names, and handling its numbering scheme. Every consumer redoes that work, and the versions they arrive at disagree with each other.

## Acceptance criteria

- [ ] Endpoints cover the canon listing, a book, a chapter, a single verse, and a verse range
- [ ] A free-form reference in Portuguese or English resolves to a canonical address, and `Jo 3,16` and `Jó 3,16` land in different books
- [ ] A range that crosses a chapter boundary resolves correctly
- [ ] Every response carries the structured verse id, so a caller can anchor other data on it
- [ ] Request and response schemas are typed and the OpenAPI document is published
- [ ] `openapi.json` is committed, and a CI job regenerates it from the code and fails when the committed copy differs
- [ ] No route reaches the document naked. A route with no summary, no response model or no documented error responses fails the build
- [ ] The API is read-only. No endpoint writes
- [ ] An unresolvable reference returns a structured error explaining why, never a stack trace and never a guess
- [ ] The whole service runs from `docker compose up` on a clean checkout with no external database

## Constraints

Read-only. Writing is not deferred, it is refused.

No external database. The corpus is a static file and it belongs on local disk, which is what makes running this cost nothing and answer in under a millisecond.

`concordantia` consumes this API and the B5 artifact. It never touches the datastore directly, and a contract test in the sibling repo fails loudly when the schema drifts.

## Out of scope

No full-text search. Lexical search is B9 and semantic search belongs to `concordantia`. No rate limiting, that is B8. No authentication.

## Verification

Test-driven on the handlers and the reference resolver. Contract tests run against the published OpenAPI schema. The conformance corpus from B1 is exercised through the HTTP layer as well, because a parser that is right in a unit test and wrong behind a URL encoder is still wrong.

The documented surface gets its own gate, in two directions. The committed `openapi.json` has to match what the code generates, which catches a route that changed without the document following. And every route has to carry a summary, a response model and its error responses, which catches a route that shipped with nothing said about it. FastAPI publishes an undocumented route without complaining, so the second direction is the one that rots quietly.

The idea is borrowed from the private repo, where a coverage test compares the API client collection against the real routes in both directions and blocks the push when either side is missing. That mechanism is why the collection there is still accurate. What changes here is that the document is generated rather than written, so the missing half is not a missing file. It is a route nobody described.
