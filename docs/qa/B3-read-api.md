# QA, B3 read API

*Stage 6. Run 2026-08-02, on `feat/b3-read-api`.*

Reading the diff is not QA. This is what ran and what came back.

## The suite, the linter and the type checker

```
$ make lint
All checks passed!
88 files already formatted

$ make typecheck
Success: no issues found in 49 source files

$ make test
442 passed
```

## The acceptance criteria, walked one by one

**1. Endpoints cover the canon listing, a book, a chapter, a single verse and a
verse range.** Met. Seven routes, all in the published document.

```
$ uv run python -c "import json; print(*sorted(json.load(open('openapi.json'))['paths']), sep='\n')"
/health
/v1/passage
/v1/resolve
/v1/versions
/v1/versions/{version}/books
/v1/versions/{version}/books/{book}
/v1/versions/{version}/books/{book}/chapters/{chapter}
/v1/versions/{version}/books/{book}/chapters/{chapter}/verses/{verse}
```

**2. A free-form reference in Portuguese or English resolves, and `Jo 3,16` and
`Jó 3,16` land in different books.** Met, and verified through HTTP rather than
through a unit test, because the accent has to survive a URL encoder.

```
$ curl -sS "http://localhost:8000/v1/resolve?ref=Jo%203,16"
{"reference":"Jo 3,16","book":"JHN","ids":["JHN.3.16"],…}
$ curl -sS "http://localhost:8000/v1/resolve?ref=J%C3%B3%203,16"
{"reference":"Jó 3,16","book":"JOB","ids":["JOB.3.16"],…}
```

**3. A range that crosses a chapter boundary resolves correctly.** Met.
`Ex 13,21-14,2` comes back as `EXO.13.21`, `EXO.13.22`, `EXO.14.1`, `EXO.14.2`,
pinned by a test, and a range crossing a book boundary is pinned beside it.

**4. Every response carries the structured verse id.** Met. Every response that
carries a verse carries `id`, on the verse route, inside a chapter, inside a
book, aligned in a passage, and as `ids` from `resolve`. The version and book
listings carry no verse and so carry no id.

**5. Request and response schemas are typed and the OpenAPI document is
published.** Met. Every route declares a Pydantic response model and a test
fails any that does not.

**6. `openapi.json` is committed and a CI job regenerates it and fails when the
committed copy differs.** Met.

```
$ uv run scripts/build-openapi.py --check
the committed document matches the routes
```

Proved against a mutation rather than trusted. Editing one summary in the
committed document made both the script and the test fail, and regenerating made
them pass.

```
$ uv run scripts/build-openapi.py --check
openapi.json does not match the routes. run `make openapi`
exit 1
```

**7. No route reaches the document naked.** Met, with one exemption written
down. A test walks the routes and fails any with no summary or no response
model. A second test requires a documented failure from every route that takes
input, and `/v1/versions` reads no parameter and cannot fail. A third test
asserts that route is the only exemption, so a second one cannot appear quietly.

Also proved by mutation. Deleting the summary from the verse route failed the
walk by name.

```
FAILED test_no_route_reaches_the_document_naked[…/chapters/{chapter}/verses/{verse}]
```

**8. The API is read-only. No endpoint writes.** Met, proved twice. A test walks
every route and fails anything that is not a `GET`. The connection is opened
`mode=ro`, so the driver refuses rather than a convention holding.

```
$ docker compose exec -T api python -c "…connect().execute('DELETE FROM texts')"
OperationalError attempt to write a readonly database
```

**9. An unresolvable reference returns a structured error explaining why.** Met
now, and it was not met when this walk was first written. Twelve reason codes in
a closed set, five new here and seven carried through from B1 unchanged, with a
test asserting the two sets stay in step.

**This walk said met and was wrong.** The review tool found
`?versions=,,` answering `500 Internal Server Error`, which is the stack trace
the criterion forbids, on a shape I had not tried. Fixed, and five separator
shapes are pinned. The same pass found the published 422 schema promising an
object while FastAPI's own validation failure answered a list, so a generated
client broke on the first malformed request. Both gates were blind to it because
both compare the document to the decorators and neither sends a request. Three
parameterized cases now send real malformed requests and read the shape back.

```
$ curl -sS "http://localhost:8000/v1/resolve?ref=Habakuk%203,2"
{"detail":{"reason":"unknown_book","message":"no book named 'Habakuk'","input":"Habakuk 3,2"}}
```

**10. The whole service runs from `docker compose up` on a clean checkout with
no external database.** Met, run rather than reasoned about.

```
$ docker compose up -d --build --wait
Container catholic-bible-api-1  Healthy

$ curl -sS http://localhost:8000/v1/versions/vulgata-clementina/books/SIR/chapters/24/verses/1
{"id":"SIR.24.1",…,"reference":"Eccli. 24,1","text":"Sapientia laudabit animam suam,…"}
```

That response is byte for byte what `README.md` publishes, and the CI quickstart
job now asserts it rather than asserting a subset.

## The verification the epic names

**Test driven on the handlers and the resolver.** 442 tests, of which 113 go
through HTTP.

**Contract tests against the published schema.** The document gate above, in
both directions.

**The conformance corpus through the HTTP layer.** All 40 cases run, not a
subset, and a test asserts the count so a case cannot be skipped quietly.

Five of the fifteen mapping cases name a book only another scheme has, `SUS`,
`S3Y`, `BEL` and `ESG`. They were failing with `unknown_book` because the
reference grammar knows the 73 canon books and nothing else. Rather than
excluding them and calling the corpus covered, the parser took a resolver and
the scheme brings its own code space. `SUS 1,1` under `org` now answers
`DAN.13.1`, named `Dn 13,1`.

## Defects found during QA

**The reference echoed the input while the ids carried the answer.**
`?ref=Sl 51,1&scheme=org` came back `{"reference":"Sl 51,1","ids":["PSA.50.1"]}`.
A caller rendering the reference shows psalm 51 while the id says 50, on the
one endpoint whose whole purpose is that those two numbers are different. Fixed
so the reference names where the addresses landed, with the disjoint parts kept.

**The parser sent most English references to the disjoint branch.** Found by
round tripping the formatter. The lectionary shape `Mc 5,22-24.35-43` is
detected by a period, every English and Latin abbreviation ends in one and no
Portuguese abbreviation does, so `Ex. 13:1-14:5` came back malformed. The period
is now read on the numbers rather than on the whole string, and it carries a
conformance case.

**The route walk found no routes.** The first version of the document gate read
`app.routes`, which does not flatten an included router, so it walked `/health`
and passed. A test asserting seven public routes exist is what caught it, and it
stays in the file for the next person who writes a walk.

**The order range per book was the last chapter's range.** A dict comprehension
keyed by book kept only the final entry, so Genesis reported orders 1508 to
1533. Caught by asserting the ranges are contiguous and cover all 35845
addresses rather than by reading the query.

## What was cross-checked rather than assumed

The ported psalm table against B1's `to_scheme`, verse by verse across all 150
psalms. They agree on 148 and disagree on 2, both at the last verse, and both
are pinned. `LIMITS.md` says which side the API trusts and why.

Every authored abbreviation resolves back to its own book through the alias
table, and the three invariants were proved to bite by mutating `Ecclus.` into
`Eccles.` and watching three tests fail.

## What is not covered

No load test. There is now one latency number, 5 ms for a 500 verse three
version passage on a laptop, down from 21 ms once the per address point queries
became one range query. One number on one machine is not a load test and
`LIMITS.md` says which is which.

Nothing is deployed. B6 is where a public URL exists.

No commentary, no cross-references, no search. B4 and B9.
