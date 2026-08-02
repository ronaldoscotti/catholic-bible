# [B8] Rate limiting

| | |
|---|---|
| Milestone | v1.1 |
| Labels | `epic` `area/api` `milestone-spec` |
| Depends on | B6 |

*Milestone spec. Expanded against the code that exists when it is reached, rather than guessed now.*

**As** the person paying for the server
**I need** a public endpoint that cannot be turned into someone else's free compute
**So that** the API stays free for the people it is for

## Context

A public endpoint with no limit is an abuse surface on day one. That is a real threat rather than a hypothetical, which is what separates this from infrastructure built ahead of need.

Keys and quotas come later, and only if per-IP limiting stops holding. A key is an identity and an account is a login, and a login is only needed when someone has to come back and manage something. Nobody does.

## Problem

An unlimited public API on a single box can be saturated by one careless script, and the people it was built for get a timeout.

## Acceptance criteria

- [ ] Per-IP request limits are enforced
- [ ] Exceeding the limit returns `429` with `Retry-After`
- [ ] Limits are configurable without a code change
- [ ] Current limits are documented in the README
- [ ] Static CDN artifacts stay unlimited, since they cost nothing to serve

## Constraints

No accounts. No login. No keys until per-IP limiting demonstrably fails, and when that day comes the key is issued self-service against an email with no password and no session.

The decision and its trigger go in `DECISIONS.md` when this ships.

## Verification

Test-driven, including the boundary case and the reset window.
