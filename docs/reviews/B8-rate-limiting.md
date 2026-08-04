# Code review, B8 rate limiting

*Stage 7. Written 2026-08-04, one author, before the pull request opened.*

**The order is right for once.** B3, B4, B5 and B7 all reviewed after the pull
request was already up, and each recorded that as wrong rather than tidying it.
This one ran first.

## What the review found in its own diff

**The gate chain was reporting green over a real failure.** `uv run mypy 2>&1 |
tail -1` yields the exit status of `tail`, so a chain joined with `&&` walked
past a type error and printed ALL GREEN. It had done that for several rounds
before anyone looked at the line above the banner.

The type error itself was one line and harmless. The mechanism was not. Every
gate now runs under `set -o pipefail`, and the reason CI never lied is that it
runs each step as its own line, so the only thing at risk was what this session
claimed between pushes.

**A test asserted the right thing about the wrong window.** The reset test used
the shared fixture, spent all five of its hourly allowance inside one minute, and
then read the 429 on the next window as proof that the minute had not reset. It
would have passed while measuring nothing. It builds its own limiter with the
hour switched off now.

That is the second time in two epics that a test was wrong before the code was,
which is worth noticing rather than filing.

**The counter leaked its connection and the fixture got blamed first.**
`filterwarnings = ["error"]` caught an unclosed database and the obvious fix was
to close it in the test. The real defect was that the middleware never closed the
store at all. In a process that lives forever that is invisible and it is still a
leak, so it closes on lifespan shutdown, and the fixture stopped being the
explanation.

## What the design got right and why it is written down

**Reading `X-Forwarded-For` unconditionally is the whole attack.** It is the
default in most examples and it makes the limiter work out of the box behind a
proxy, by being bypassable. The first test written in this epic is the spoofing
case, before any happy path, and it was run again against a live container.

**An unparseable entry stops the walk.** The first implementation skipped
invalid hops and kept looking leftward, which reads as robustness and is the
hole coming back through a side door. Anything a trusted proxy appended is a real
address, so garbage on the right means nothing vouched for what is left of it. A
test caught this, the test was right and the code was changed.

**The refusal is built rather than raised.** An ASGI middleware sits outside the
application, so its exception handlers never fire and a `raise ApiError` up there
escapes as a 500. There is a comment saying so, because the tidy refactor is
obvious and wrong.

## What is still open

**This is not DDoS protection and the epic's framing invites the confusion.**
Per address limits stop one careless script. A distributed flood, each address
under the limit, is answered politely and on time. `LIMITS.md` says it in those
words.

**A fixed window admits up to double across a boundary.** 60 at 11:00:59 and 60
at 11:01:00 breaks no rule. Published rather than hoped over.

**A shared exit is one caller.** A carrier NAT or a university puts thousands of
readers behind one address and they share one budget. Telling them apart needs an
identity, an identity is an account, and this project has none.
`DECISIONS.md` records what would have to happen first.

**Fail open means the limiter can stop working while the API keeps answering.**
That was the author's call against my recommendation being the same, so it is not
a disagreement, but it is the kind of decision that reads differently in six
months. The defence is that `/health` reports `degraded` with the reason and the
log fires at error level, and a test holds both.

**The trusted proxy setting ships empty and that is deliberate.** B8 enforces on
the socket address, which is correct without a proxy and wrong behind one. B6
fills it in. A limiter briefly too strict for proxied callers is recoverable, and
one that was never enforcing is found out later.

## What did not creep in

No keys, no accounts, no quotas. No per route limits. No admin route to inspect
or reset a bucket, which would have been a write endpoint on a read only service.
No sliding window, no Redis, no `slowapi`. The installed dependency set is still
`fastapi` and `uvicorn`.

One thing did arrive that the plan did not name. `compose.yaml` gained an
`environment` block passing the limits through from the shell. It is how
criterion 3 was demonstrated against a real container rather than asserted, the
defaults in it are the shipped defaults, and a test pins the three lines.

## Second pass, after the pull request opened

*2026-08-04. A review agent run against the diff, the epic and the conventions.
Eight findings, seven fixed and one refused with a reason. The first two are the
kind that make a pull request worth reviewing at all.*

**The hourly limit was never enforced.** Housekeeping deleted rows by time
alone, while the window lived glued into the bucket string, so pruning the
minute bucket wiped every hourly bucket for every address on the box. Reproduced
against the real counter: 6000 requests over ten minutes left the hourly tally
reading 100 against a limit of 1000. One abusive client also handed every other
address a free reset.

`README.md`, `LIMITS.md`, the epic and the pull request body all sold the hour as
the defence against the polite crawler. It was decoration. The window is a column
now, housekeeping is scoped to it, and two tests hold it, one on the mechanism
and one replaying the run that found it. Criterion 1 came down and went back up
the same day.

**Nothing tested the limiter the application installs.** Every middleware test
wrapped `RateLimiter` around the app by hand and `tests/conftest.py` disables the
one `app.py` adds. Deleting `add_middleware` from `app.py` left all 654 tests
green. The service could ship with rate limiting entirely absent and every gate
would pass.

That is the more frightening of the two, because the first was a bug and this was
a hole in the proof. `test_the_application_the_service_starts_actually_refuses`
boots the real import in a subprocess and asserts a 429, verified to fail with
the line commented out.

**Three more that were real.** `degraded` latched forever and the dead connection
was kept, so a two second lock past the busy timeout meant a permanent alarm and
permanent fail open. The loopback exemption covered every path rather than the
health route, which would have become a silent total bypass the moment B6 put
Caddy on the same box before filling in the trusted proxy setting. `_forwarded`
read only the first `X-Forwarded-For` line, and the field may repeat, which would
have let a caller control the chain on a proxy that appends rather than joins.

**Two smaller ones.** The unauthenticated `/health` published the server path and
the raw sqlite error, and the store lived at a fixed world known name in a shared
temp directory, which combined with fail open is a one command local off switch.

**One refused.** A request the minute window turned away still counts against the
hour, and the review called it a defect. It is a decision. A caller who reads
`Retry-After` never meets it, and escalating a caller who ignores the answer is
what the second window is for. `LIMITS.md` now says so in those words rather than
leaving it undocumented, which was the fair half of the finding.

## The process finding, which is worth more than the eight

The prune mechanism was never specced. `PRUNE_EVERY` and the housekeeping delete
do not appear in the spec, the plan, the QA document or the first review. They
arrived during implementation, passed through no gate, and were the one thing
that broke an acceptance criterion.

Both human gates were met on this epic and the review still ran before the pull
request, which was the improvement this epic was proud of. None of that caught
it, because none of it was looking at a mechanism nobody had written down. What
caught it was a second reader with no stake in the answer.
