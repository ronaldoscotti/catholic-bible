# [B6] Production deploy

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/infra` |
| Depends on | B3 |
| Blocks | the MVP gate |

**As** a developer evaluating this project
**I need** a live URL I can call right now
**So that** I can decide whether it is useful before deciding whether to clone anything

## Context

The API runs on a Hetzner VPS that already exists and is already paid for, which makes marginal cost zero and beats a free tier with a cliff in it. It also removes cold starts. Free tiers that spin down take seconds to answer the first request after idle, and for an API someone is trying by copying a line out of a README, ten seconds is indistinguishable from broken.

Deployment is a script in the repo rather than a control panel, because a `deploy.sh` can be read by whoever reads the GitHub repo and a sequence of clicks cannot.

## Problem

A project that only runs after a clone, a generator run and a local server is a project most people never evaluate. Without a live endpoint, the first impression costs twenty minutes, and most readers do not spend them.

## Acceptance criteria

- [ ] The API answers over HTTPS on a stable hostname
- [ ] TLS certificates renew without manual work
- [ ] A health endpoint reports build version and dataset version
- [ ] `deploy.sh` lives in the repo, runs over SSH, and is the only deploy path
- [ ] A push to the default branch triggers deploy after tests pass
- [ ] A smoke test runs in CI against the public URL after every deploy
- [ ] `docker compose up` reproduces the same service locally with no changes
- [ ] Structured request logs exist, with no personal data retained
- [ ] The README states plainly that this runs on a single box and is best-effort

## Constraints

`compose.yaml` is the contract. The VPS is one deployment target and never the only runtime. A repo that runs on my machine and nowhere else quietly invalidates every reproducibility claim in the sibling repo.

Caddy over nginx, for automatic certificates and a config file short enough to read in one screen.

Single VPS means single point of failure, and that goes in the README as a fact. Best-effort availability stated out loud is stronger than an SLA nobody can enforce.

## Out of scope

No autoscaling. No multi-region. No paid uptime monitoring.

## Verification

The deployed URL is the test target. A CI smoke test asserts the health endpoint and one real Scripture lookup after every deploy, so a green build that shipped a broken service is not possible.
