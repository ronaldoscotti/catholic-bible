# [B0] Project scaffolding

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/infra` `blocks-everything` |
| Depends on | nothing |
| Blocks | every other epic |

**As** whoever picks up the first epic
**I need** a Python project that runs, tests and lints on a clean checkout
**So that** B1 can be written test-first instead of test-eventually

## Context

Every other epic in this repo assumes a working project. None of them creates
one, which is a hole in the roadmap rather than an oversight in the plan.

Test-driven from the first commit is a rule in `CLAUDE.md`, and it is
unenforceable until a test runner exists. B0 is what makes that rule real.

Nothing here is interesting and that is the point. It should be boring, current,
and done in one sitting.

## Problem

There is no project. A contributor cloning this repo today gets documentation
and no way to run anything, and the first epic cannot follow its own testing
rule.

## Acceptance criteria

- [x] `pyproject.toml` declares the project, its dependencies and its entry points
- [x] `uv` manages dependencies and the lockfile is committed
- [x] The package layout separates canon and spine, storage, and HTTP, with the dependency direction enforceable by inspection
- [x] `ruff` runs lint and format with configuration committed
- [x] Type checking runs with configuration committed
- [x] `pytest` runs, with one real test that fails when the code it covers is broken
- [x] `Makefile` exposes at minimum `make test`, `make lint`, `make fmt`, `make run`
- [x] `compose.yaml` brings the service up on a clean checkout with no credentials
- [x] A CI workflow runs lint, type check and tests on every push and every pull request
- [x] CI is green on the first commit that lands this epic
- [x] `README.md` has a quickstart that a stranger can follow, and it is the path CI exercises

## Constraints

Boring and current. The stack is written in `CLAUDE.md` and this epic implements
it rather than revisiting it.

No placeholder test that asserts `True`. The one test that ships here covers
something real, however small, because a green suite that proves nothing teaches
the repo the wrong habit on day one.

`compose.yaml` is the contract from the first commit. Anything that only works
outside the container is a defect.

No application code beyond what the smoke test needs. B0 builds the room, not
the furniture.

## Out of scope

No canon, no spine, no data, no endpoints. Those are B1 onward.

No deploy. That is B6.

## Verification

CI green is the verification, and it has to be green on the merge commit rather
than on a rerun. The quickstart is verified by a CI job that follows it on a
clean checkout, because a quickstart nobody executes rots within a month.
