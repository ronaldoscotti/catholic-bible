# [B8] Rate limiting

| | |
|---|---|
| Milestone | v1.1 |
| Labels | `epic` `area/api` `milestone-spec` |
| Depends on | nothing. B6 configures one setting |

*Expanded against the code that existed when it was reached, on 2026-08-04. The spec is `docs/specs/2026-08-04-b8-rate-limiting.md` and the plan is beside it.*

**The dependency line used to say B6 and it was wrong.** Nothing in the five criteria needs a deploy, and all five were met without one. What B6 actually owns is the value of `RATE_LIMIT_TRUSTED_PROXIES`, which stays empty until a reverse proxy exists, because trusting a forwarded header from nobody in particular is worse than not reading it at all. B8 ships enforcing on the socket address, which is correct without a proxy, and B6 sets the trusted address when Caddy lands.

**As** the person paying for the server
**I need** a public endpoint that cannot be turned into someone else's free compute
**So that** the API stays free for the people it is for

## Context

A public endpoint with no limit is an abuse surface on day one. That is a real threat rather than a hypothetical, which is what separates this from infrastructure built ahead of need.

Keys and quotas come later, and only if per-IP limiting stops holding. A key is an identity and an account is a login, and a login is only needed when someone has to come back and manage something. Nobody does.

## Problem

An unlimited public API on a single box can be saturated by one careless script, and the people it was built for get a timeout.

## Acceptance criteria

- [x] Per-IP request limits are enforced
- [x] Exceeding the limit returns `429` with `Retry-After`
- [x] Limits are configurable without a code change
- [x] Current limits are documented in the README
- [x] Static CDN artifacts stay unlimited, since they cost nothing to serve

**The first came down on 2026-08-04, after the pull request opened.** A review found that the hourly window was never enforced. Housekeeping deleted rows by time alone while the window lives in the key, so pruning the minute bucket wiped every hourly bucket for every address. Reproduced at 6000 requests in ten minutes with the hourly counter reading 100 against a limit of 1000. The minute window was always correct. The box went back up the same day. The window is a column rather than part of the bucket string, housekeeping is scoped to one window, and two tests hold it, one on the mechanism and one replaying the 6000 request run.

**The same review found that nothing tested the limiter the application installs.** Every middleware test wrapped `RateLimiter` around the app by hand and `tests/conftest.py` disables the one `app.py` adds, so deleting `add_middleware` left the whole suite green. Criterion 1 was ticked against a limiter the service does not run. `test_the_application_the_service_starts_actually_refuses` boots the real import in a subprocess and asserts a 429, and it was proved to fail with the line removed.

**`RATE_LIMIT_ENABLED` is a kill switch that exists for the test suite.** It is not in these criteria and not in `compose.yaml`. Its only production use would be turning a security control off, so it is named here rather than left to be discovered. `tests/test_deployment.py` asserts nothing that ships sets it.

**The fifth is met by architecture rather than by work.** jsDelivr serves the static files and never reaches this service, so nothing here could limit them. It is recorded as a non-action instead of being dressed up as a task, and the README points a caller who hits the limit at those files.

**The verification was run against a container, not only against the suite.** The window was waited out by trusting `Retry-After` and being readmitted, and a forged `X-Forwarded-For` was proved not to buy a fresh budget. `docs/qa/B8-rate-limiting.md` pastes both.

## Constraints

No accounts. No login. No keys until per-IP limiting demonstrably fails, and when that day comes the key is issued self-service against an email with no password and no session.

The decision and its trigger go in `DECISIONS.md` when this ships.

## Verification

Test-driven, including the boundary case and the reset window.
