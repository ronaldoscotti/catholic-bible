# Spec, B8 rate limiting

*Stage 3. Written 2026-08-04, against issue #10.*

**Gate.** This is a human review gate and it is open. No implementation code
exists and none gets written until this document comes back approved. Five
design questions were asked before it was written and the answers are folded in.
Three more are at the bottom, and those are the ones this document cannot settle
on its own.

## What B8 delivers

A public endpoint that one careless script cannot turn into everybody else's
timeout.

There is nothing hypothetical here. The API is read only, free, keyless and about
to be deployed, which is the exact profile of a thing that gets scraped by a
loop with no sleep in it. The people this was built for then get a 504 while
somebody's crawler warms up.

## Measured before writing this

Every number ran on 2026-08-04 against what is committed at `94d303a`. None is
an estimate.

| Fact | Value | How |
|---|---|---|
| SQLite in the runtime | 3.51.2 | `sqlite3.sqlite_version` |
| Upsert with `RETURNING` | supported | executed |
| Counted hits per second, one connection | 64543 | 20000 upserts in 310 ms |
| Cost of counting one hit | 15.5 us | same run |
| A verse read, end to end | 1.94 ms | 300 requests through `TestClient` |
| `/health`, end to end | 1.56 ms | same |
| Store for 20001 live buckets | 475136 bytes | `stat` |

**Two limits cost 31 microseconds against a 1.94 millisecond read.** That is 1.6%
of the work the request was already doing, which is what makes SQLite the
uninteresting choice here rather than the expensive one.

**`/health` is not a cheap route.** It opens a connection and queries the store,
and it lands within 20% of the cost of reading a verse. Anything that treats it
as free because it returns nine bytes is reading the response and not the work.

## The shape

One ASGI middleware, in front of everything, with no new dependency. The
installed set is `fastapi` and `uvicorn` and it stays that way. A fixed window
counter is about forty lines and `slowapi` would bring Redis and a plugin system
to hold two integers.

```
request
  -> client_ip()          who is this, and can I believe it
  -> count(ip, minute)    upsert, returning the new count
  -> count(ip, hour)      same
  -> over any limit?      429 + Retry-After
  -> otherwise            the route, untouched
```

Fixed window rather than a sliding one. A sliding window is more correct at the
boundary and needs per request timestamps instead of one integer per bucket. The
failure it prevents is a caller getting 120 requests across two adjacent windows,
which for a limit that exists to stop a runaway loop is not worth the storage.

## Where the client IP comes from, which is the whole security of this

Behind Caddy, `request.client.host` is the proxy. Every caller in the world lands
in one bucket and the limit becomes a global cap that the first crawler
exhausts.

The fix is `X-Forwarded-For`, and taking that header at face value is worse than
having no limit at all. It is attacker controlled. Anyone sending a random value
per request gets a fresh bucket every time and walks straight through, while an
honest client stays limited. That is a rate limiter that only limits people who
are not attacking you.

**So the header is read only when the connection came from an address that is
configured as a trusted proxy, and the default is to trust nothing.** With no
configuration the middleware uses the socket address, which is correct for
`docker compose up` on a laptop and correct for anyone running this without a
proxy. B6 sets the Caddy address when it lands, and until then the setting is
empty rather than guessed.

When trusted, the client is the rightmost entry of `X-Forwarded-For` that is not
itself a trusted proxy. Taking the leftmost is the common mistake, because the
left end is whatever the client sent.

## The store

**A separate SQLite file, never the corpus store.** `CLAUDE.md` says this repo is
read only and that stands. The corpus database is built from committed data and
nothing writes to it. The limiter gets its own file, its own connection and its
own schema, so the read only claim about published Scripture stays literally
true.

```sql
CREATE TABLE hits (
  bucket       TEXT    NOT NULL,
  window_start INTEGER NOT NULL,
  count        INTEGER NOT NULL,
  PRIMARY KEY (bucket, window_start)
) WITHOUT ROWID
```

WAL, `synchronous=NORMAL`, and a `busy_timeout` so concurrent workers wait rather
than raise. One row per address per window. Rows older than the longest window
are deleted opportunistically, which keeps the file at the size of live traffic
rather than of all traffic ever.

The reason this is SQLite and not a dictionary is that a dictionary is per
process. Four uvicorn workers with in memory counters enforce four times the
configured limit, and a limit that quietly multiplies by the worker count is a
limit nobody can reason about. Shared state was the author's call and it is the
right one for something whose purpose is security.

The file is ephemeral by design. A restart resets the windows, which costs one
window of amnesty and buys no volume, no backup and no migration.

## The limits, ported rather than invented

`app/Providers/AppServiceProvider.php` in the private source has run these
numbers in production.

| Scope | Window | Limit | Where it comes from |
|---|---|---|---|
| Everything, per IP | 60 s | 60 | the source's `api` limiter |
| Everything, per IP | 3600 s | 1000 | the source's `api:global` limiter |

The source's 300 per minute for authenticated users does not port, because there
are no accounts. Its trusted prerender bypass does not port either, because that
consumer does not exist here.

Both windows, stacked. The minute limit stops a loop with no sleep. The hour
limit stops the polite crawler that respects one request per second and still
walks the whole corpus overnight, which the minute limit alone never notices.

**`/health` counts against the same budget.** It is one bucket per address
covering every route, so hammering the health check spends the same allowance as
reading Scripture, and there is no second budget to exhaust. This is the direct
answer to not letting anyone flood that endpoint, and the measurement above says
it costs nearly what a verse costs anyway.

**Loopback is exempt.** The container health check runs inside the container
against `127.0.0.1`, twelve times a minute, forever. That is the service asking
itself whether it is alive and it is not traffic. Exempting it also keeps
`docker compose up --wait` from ever racing the limiter.

## What a refused request looks like

The same error body as everything else, with one new reason in the closed set.

```json
{"detail": {"reason": "rate_limited", "message": "60 requests per minute"}}
```

`429`, with `Retry-After` in seconds, counted to the end of whichever window is
the one blocking. When both are exceeded the hour wins, because that is the one
the caller actually has to wait out.

Alongside it, on every response rather than only on the refusal:

```
RateLimit-Limit: 60
RateLimit-Remaining: 41
RateLimit-Reset: 23
```

Three headers so a well behaved client can slow down before it is refused. A
limit a caller can only discover by being refused is a limit that guarantees at
least one refusal per client.

## Configurable without a code change

Environment, read at startup. No file, no reload, no admin route.

| Variable | Default |
|---|---|
| `RATE_LIMIT_PER_MINUTE` | `60` |
| `RATE_LIMIT_PER_HOUR` | `1000` |
| `RATE_LIMIT_TRUSTED_PROXIES` | empty |
| `RATE_LIMIT_DB` | a path under the runtime state directory |
| `RATE_LIMIT_ENABLED` | `true` |

`0` on either limit disables that window, which is how the test suite gets a
deterministic single window without reaching into internals.

## What changes in the published contract

`openapi.json` is committed and CI fails on a difference, so this is a real
change to a published document rather than an internal one.

The `429` is declared once on the router and reaches all eleven routes, plus
`/health` separately, since it sits outside the versioned surface. `Reason` gains
`rate_limited`. `tests/api/test_document.py` already asserts that every reason
the document publishes is one a route can return, so the new value is policed by
a test that exists.

## What this does not do

**It is not DDoS protection.** It is abuse control. A distributed flood arrives
from thousands of addresses, each one under the limit, and this middleware
answers every one of them politely. Stopping that needs something in front of the
box and it is not a Python middleware. `LIMITS.md` will say so in those words,
because the epic's own framing invites the confusion.

**It counts the request after it arrived.** The connection was accepted, the ASGI
scope was built and the middleware ran. What it saves is the database read and
the serialisation, not the socket.

**Static artifacts are untouched and that is a non-action.** The CDN serves them
from jsDelivr and never reaches this service. Criterion five is met by
architecture rather than by work, and it will be recorded that way instead of
being dressed up as a task.

## Out of scope

Keys, quotas and accounts. The epic is explicit that a key comes only when per-IP
limiting demonstrably fails, and the trigger for that goes in `DECISIONS.md` when
this ships.

Per-route limits. One budget per address is simpler to reason about and the
measurement says the routes cost within 20% of each other.

## The dependency this epic declares

The epic says `Depends on B6`. Nothing in the five criteria needs a deploy, and
this document was written without one. What B6 actually owns is the value of
`RATE_LIMIT_TRUSTED_PROXIES`, which is empty and correct until Caddy exists.

Proposed change to the epic file, for approval along with this document. The
dependency line becomes a note saying B8 ships enforced and untrusted, and B6
configures the trusted proxy when the reverse proxy lands. Leaving `Depends on
B6` while shipping B8 first would leave the file lying about the order.

## Open questions

**1. When the limiter's own store fails, does the API fail open or closed?**

A disk error, a read only filesystem or a corrupt file makes the counter
unusable. Failing closed turns a storage problem into a total outage of a free
public dataset. Failing open turns it into no rate limiting at all, silently,
which is the classic hole in security middleware.

My recommendation is fail open and make it loud. Serve the request, log at error
level, and have `/health` report `degraded` with the reason, so the failure is
visible in the same place everything else about this service is visible. The
threat is abuse rather than authorisation, and the state before B8 was unlimited,
so failing open is a return to the previous posture rather than a new hole. You
said this is for security, so if you want it closed instead, say so and the
health route becomes the thing that has to stay honest.

**2. Do the `RateLimit-*` headers ship, or only `Retry-After`?**

The criterion asks for `Retry-After` on the refusal. The three headers on every
response are about eight lines and let a client behave. They also tell a scraper
exactly how hard it can push without being refused, which is either the point or
the objection. I lean toward shipping them.

**3. Does the limit apply in the test suite by default?**

596 tests run through `TestClient` from one address. At 60 per minute the suite
trips its own limiter partway through. The options are defaulting
`RATE_LIMIT_ENABLED` to false and turning it on in the tests that care, or
leaving it on and exempting the test client address. I lean toward the first,
with a test asserting that the shipped `compose.yaml` and `Dockerfile` leave it
enabled, so the default that protects the tests cannot become the default in
production.
