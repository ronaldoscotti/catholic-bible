# QA, B8 rate limiting

*Stage 6. Run 2026-08-04 against `feat/b8-rate-limiting`.*

Reading the diff is not QA. What follows was run against a real container built
from a clean checkout, and the output is pasted rather than summarised.

## The acceptance criteria, walked

**1. Per-IP request limits are enforced.** Met. Two windows, both counted at
once, 60 a minute and 1000 an hour, which are the numbers the private source has
run in production rather than numbers chosen here.

Run against `docker compose up` with the minute lowered to 3 from the shell,
which also proves criterion 3.

```
request 1  HTTP/1.1 200 OK   ratelimit-limit: 3  ratelimit-remaining: 2  ratelimit-reset: 34
request 2  HTTP/1.1 200 OK   ratelimit-limit: 3  ratelimit-remaining: 1  ratelimit-reset: 34
request 3  HTTP/1.1 200 OK   ratelimit-limit: 3  ratelimit-remaining: 0  ratelimit-reset: 34
request 4  HTTP/1.1 429 Too Many Requests   retry-after: 34
```

**2. Exceeding the limit returns `429` with `Retry-After`.** Met, and the header
was believed rather than read.

```
$ curl -sS $VERSE
{"detail": {"reason": "rate_limited", "message": "3 requests per 60 seconds", "input": null}}

Retry-After says 27 seconds. Waiting exactly that.
after the wait  HTTP/1.1 200 OK   ratelimit-remaining: 2
```

That is the reset window the epic's verification names, run against a container
rather than a clock a test controls. Waiting exactly what the header promised
was enough, which is the only way to find out that the promise is arithmetic and
not a guess.

**3. Limits are configurable without a code change.** Met. The whole run above
used `RATE_LIMIT_PER_MINUTE=3 RATE_LIMIT_PER_HOUR=0 docker compose up`, with no
file edited. `compose.yaml` passes the shell through with the shipped defaults,
so the contract file stays the contract.

**4. Current limits are documented in the README.** Met, and a test reads the
README rather than trusting that someone updated it. `test_the_readme_publishes_the_limits_it_enforces` compares the published sentence
to the shipped settings, so changing one without the other turns the suite red.

**5. Static CDN artifacts stay unlimited.** Met, and fetched rather than argued.
Reasoning about architecture is not verification, so the URL `README.md`
publishes was requested.

```
$ curl -sS -o /dev/null -D - "https://cdn.jsdelivr.net/gh/ronaldoscotti/catholic-bible@v1.0.1/data/versions/matos-soares/books/SIR.json"
HTTP/2 200
access-control-allow-origin: *
cache-control: public, max-age=31536000, s-maxage=31536000, immutable
```

No `ratelimit-*` and no `retry-after`, because the host is `cdn.jsdelivr.net` and
this process was never involved. `routes.py` has no `StaticFiles` and no
`FileResponse`, so there is nothing here that could limit them. The README says
so where a caller hitting the limit would look, and points them at the files
instead.

## The security claim, tested rather than asserted

The one that matters. A limiter that reads `X-Forwarded-For` from anybody is
worse than no limiter, because the caller sending a fresh value per request
walks through while the honest one stays counted.

Budget spent first, then three forged headers against the same container.

```
X-Forwarded-For: 1.1.1.1    HTTP/1.1 429 Too Many Requests
X-Forwarded-For: 8.8.8.8    HTTP/1.1 429 Too Many Requests
X-Forwarded-For: 9.9.9.9    HTTP/1.1 429 Too Many Requests
```

No proxy is trusted, so the header buys nothing. When B6 configures Caddy the
header starts being read, and only from Caddy.

## Loopback, from inside the container

The health check runs twelve times a minute forever and would spend a real
budget.

```
$ docker compose exec api python -c "...urlopen('http://127.0.0.1:8000/health')"
{"status":"ok","version":"1.0.1"}
```

Run after the budget from outside was already exhausted. The service can still
ask itself whether it is alive.

That response is also byte for byte the line `README.md` publishes, which
`ci.yml` greps and compares literally. `Health` gained a `degraded` status and an
optional `limiter` field in this epic, and a test asserts the healthy body did
not move, because a new field serialised as `null` would have broken the
quickstart job.

## The measurement that chose the middleware

The plan said measure both and write the number down.

```
bare  median 2.252 ms
http  median 2.582 ms      BaseHTTPMiddleware
raw   median 2.168 ms      raw ASGI

http  over bare:    330 us
raw   over bare:    -84 us
```

**The raw number is negative, which is impossible, and that is the finding.**
The harness has around 500 microseconds of variance and the effect being chased
is smaller than that. What survives is the part that repeated across two separate
interleaved runs: `BaseHTTPMiddleware` cost 330 microseconds both times, and raw
ASGI was indistinguishable from zero both times.

So the choice rests on a repeated signal rather than on a single reading, and the
comparison that decided it is 330 microseconds of wrapper around 15.5
microseconds of work.

## The full suite

```
$ uv run pytest -q
661 passed in 26.02s

$ uv run ruff check . && uv run ruff format --check . && uv run mypy
All checks passed!
137 files already formatted
Success: no issues found in 82 source files

$ uv run scripts/lint-voice.py
18 documents clean

$ uv run scripts/build-openapi.py --check
the committed document matches the routes

$ uv run scripts/build-artifacts.py --check
the committed artifacts match the sources
```

596 before this epic and 661 after, which is 65 new tests. 11 on the counter, 27
on address resolution and configuration, 20 on the middleware and 9 on what the
deployment ships.

Seven of those arrived in the second review round, and two of them are the ones
that matter: the hourly window being enforced at all, and the application
actually installing the middleware it ships.

## What a second reader found that this document had missed

Everything above was written before a review agent read the diff. It found eight
things, and this document had been confident about two of them.

**Criterion 1 was ticked while the hourly window did nothing.** Housekeeping
deleted rows by time alone and pruning the minute wiped every hourly bucket. The
container run pasted at the top of this document exercised a three request
minute limit, so it proved the minute and said nothing about the hour, and the
walk above read it as proving both.

```
requests sent:            6000
the hourly counter reads: 100
the hourly limit is:      1000
bound?                    False
```

**Criterion 1 was also verified against a limiter the application does not
install.** `conftest.py` disables the one `app.py` adds and every middleware test
wraps its own. Commenting out `add_middleware` left 654 tests passing.

Both are fixed, both have tests that were proved to fail first, and the criterion
came down in the epic file before it went back up. The lesson is narrower than
"test more": a container run with one window lowered proves one window, and a
document that says the criteria were walked has to say which numbers each run
actually touched.

## What went wrong while running this

**My gate chain was lying.** `uv run mypy 2>&1 | tail -1` reports the exit code
of `tail`, not of `mypy`, so a chain joined with `&&` ran to the end and printed
ALL GREEN over a real type error. It had been doing that for several rounds. The
error was one line and harmless, an ASGI scope value typed as `Any`, but the
mechanism was not harmless.

Fixed by running the gates under `set -o pipefail`. Worth recording because CI
runs each step as its own line and was never fooled, so the only thing at risk
was the claim made here between pushes.

**A test was wrong before the code was.** `test_the_next_window_admits_the_caller_again` used the shared fixture, where
the hour limit is 5, and spent all five inside the first minute. The 429 on the
next window came from the hour rather than from the minute, so the test would
have passed or failed on the wrong window. It builds its own limiter with the
hour switched off now, and says why.

**The counter leaked its connection.** `filterwarnings = ["error"]` caught it in
the fixture. The real fix was not in the fixture. The middleware never closed the
store, which in a process that lives forever is invisible and is still a leak, so
it now closes on lifespan shutdown.
