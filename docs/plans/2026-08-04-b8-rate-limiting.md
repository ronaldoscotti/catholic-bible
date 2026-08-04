# Plan, B8 rate limiting

*Stage 4. Written 2026-08-04, against the spec approved the same day.*

**Gate.** This is a human review gate and it is open. No implementation code
exists. The spec's three open questions came back answered: fail open and loud,
ship the `RateLimit-*` headers, off by default in the suite.

## Where the code goes

Two modules, split on the dependency rule rather than on size.

```
src/catholic_bible/storage/ratelimit.py   buckets, windows, counting
src/catholic_bible/api/ratelimit.py       requests, addresses, headers, 429
```

The counter knows nothing about HTTP. It takes a string and a moment and returns
a number, which makes the window arithmetic testable without a request and keeps
the arrow pointing the way `CLAUDE.md` says it points. The middleware knows about
`X-Forwarded-For` and knows nothing about SQL.

A single module would be about 110 lines and would put `sqlite3` inside `api/`,
which is the import direction this repo treats as a bug.

## Task 1. The counter

`storage/ratelimit.py`. No HTTP anywhere in this file or its tests.

Red first, one test at a time.

- A first hit on a bucket returns 1, a second returns 2
- Two buckets do not see each other
- The same bucket in the next window starts again at 1
- A second connection to the same file sees the first one's count, which is the
  whole reason this is not a dictionary
- Pruning deletes windows older than the longest one and leaves the live ones
- Opening against an unwritable path raises rather than silently counting nothing

The schema and pragmas are the ones the spec measured. `WITHOUT ROWID`, WAL,
`synchronous=NORMAL`, a `busy_timeout` so a concurrent worker waits instead of
raising.

Pruning runs opportunistically rather than on a timer, on roughly one request in
a few hundred, chosen by the counter value it just wrote rather than by a random
number. `Math.random` style non-determinism in a hot path is a thing nobody can
reproduce in a test.

## Task 2. Resolving the client address

`api/ratelimit.py`, still no middleware.

- With no trusted proxies configured, the socket address wins and any
  `X-Forwarded-For` is ignored. This is the spoofing case and it is the first
  test written
- With the socket address in the trusted set, the header is read
- The chosen entry is the rightmost one that is not itself trusted, not the
  leftmost
- A header of only trusted proxies falls back to the socket address
- A malformed header does not raise, it falls back
- A request with no client at all falls back to a fixed bucket rather than to
  `None`, so an unattributable request is limited rather than exempt

## Task 3. Configuration

Frozen dataclass built from `os.environ`, read once at startup.

- Defaults are 60, 1000, no trusted proxies, enabled
- Each is overridable
- `0` on a window disables that window and leaves the other one enforcing
- `RATE_LIMIT_ENABLED=false` yields a limiter that never refuses and never writes
- An unparseable value fails at startup rather than silently reverting to the
  default, because a typo in a limit is the kind of thing nobody notices until
  the bill arrives

The store path defaults inside the system temporary directory. Ephemeral is the
intent and the spec says so.

## Task 4. The middleware

Raw ASGI rather than `BaseHTTPMiddleware`. Both get measured against the 1.94 ms
baseline before the choice is written down, because the counter costs 15.5 us and
a wrapper that costs half a millisecond would be the actual expense. If the
measurement says the difference is noise, the simpler one wins and the number
goes in the plan record.

- A request under the limit reaches the route untouched
- Request 60 passes and request 61 is refused
- The refusal is `429` with the published error body and
  `reason: "rate_limited"`
- `Retry-After` counts to the end of the blocking window, not to a fixed number
- With both windows exceeded, the hour is what `Retry-After` reports
- The next window admits the caller again
- Two addresses do not share a budget
- Loopback is never counted and never refused
- `/health` counts against the same budget as `/v1`
- `RateLimit-Limit`, `RateLimit-Remaining` and `RateLimit-Reset` appear on a
  normal 200, not only on the refusal

## Task 5. Fail open and loud

- A counter that raises on write lets the request through with its normal status
- The failure is logged once at error level rather than per request
- `/health` reports `degraded` while the limiter is unusable
- A healthy response is byte for byte what it is today

That last one is not decoration. `ci.yml` greps `{"status":"ok","version":...}`
out of `README.md` and compares the live response to it exactly, so a new field
serialised as `null` breaks the quickstart job. `Health` gains
`status: Literal["ok", "degraded"]` and an optional `limiter` field that the
route excludes when it is absent, and a test asserts the healthy body still
matches the README line character for character.

## Task 6. The published contract

`openapi.json` is committed and CI fails on a difference.

- `Reason` gains `rate_limited`
- The `429` is declared once on the router and once on `/health`, since that
  route sits outside the versioned surface
- `make openapi` regenerates and the diff is reviewed rather than accepted blind
- The existing document tests keep passing, in particular the one asserting that
  every reason the document publishes is one a route can return

## Task 7. Wiring and defaults

- `compose.yaml` and the `Dockerfile` leave the limiter enabled
- The test suite runs with it disabled, which is the approved answer to 596 tests
  arriving from one address
- A test asserts the shipped compose file does not disable it, so the default
  that protects the suite cannot leak into production

That test is the point of the whole task. Turning something off for the tests is
how it ends up off everywhere.

## Task 8. Documentation

- `README.md` publishes the limits, the headers and the window, under the
  reading section where a caller would look
- `LIMITS.md` says this is abuse control and not DDoS protection, that a
  distributed flood under the per address limit is answered politely, that the
  store is ephemeral so a restart forgives a window, and that a fixed window
  admits up to double the limit across a boundary
- `DECISIONS.md` records SQLite over a dictionary with the worker multiplication
  that lost, the fixed window over the sliding one, trusting no proxy by default,
  and the trigger that would make keys necessary
- The epic's `Depends on B6` line becomes the note the spec proposed

## What does not get built

No keys, no quotas, no accounts. No per route limits. No admin route to inspect
or reset a bucket, because that is a write endpoint on a read only service and it
would need an account to be safe.

No sliding window. No Redis. No `slowapi`. The installed dependency set stays
`fastapi` and `uvicorn`.

## Verification

The epic asks for test driven, including the boundary case and the reset window.
Both are in task 4 by name.

Beyond the suite, one manual run against `docker compose up` with the limit
lowered by environment, hitting it until it refuses, reading `Retry-After`,
waiting it out and being admitted again. The output goes in the QA document
rather than being summarised, and it is what proves the environment variables
actually reach the running container.

## Order and why

Counter, then address, then configuration, then middleware. Each one is testable
alone and the middleware is the only piece that needs all three. Fail open comes
after the happy path exists, because a fallback written before the thing it falls
back from is a fallback nobody has seen fire.

Documentation last, against what shipped rather than against what was planned.
