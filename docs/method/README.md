# The method

This repo is built with a spec-first, review-gated, AI-assisted workflow. This
directory is not a description of that workflow. It is the residue of running
it. Each stage deposits a real artifact and the git history records the order.

If you want to check the claim that this was built with a disciplined process,
read the commits and read these documents. Nothing here is aspirational.

## The pipeline

| # | Stage | Artifact | Gate |
|---|---|---|---|
| 0 | Understand the problem | [`00-understand.md`](00-understand.md) | |
| 1 | Gather context | [`01-context.md`](01-context.md) | |
| 2 | Brainstorm | dialogue, ending in a spec | |
| 3 | Spec | `docs/specs/<date>-<slug>.md` | **human review** |
| 4 | Plan | `docs/plans/<date>-<slug>.md` | **human review** |
| 5 | Implement | code and tests | tests green |
| 6 | QA | notes under `docs/qa/` | works as a user |
| 7 | Code review | review notes | issues resolved |
| 8 | PR | pull request | reviewed before merge |

Stages 3 and 4 are human review gates. Silence is not approval and neither is
the agent's own confidence. Scaffolding and isolated changes skip both, under
the rule in [`SESSION_PROMPT.md`](../../SESSION_PROMPT.md) and the conditions in
[The short route](#the-short-route) below.

Epics run this pipeline one at a time. The epic is the unit of work and it
lives in `docs/epics/` with a matching GitHub issue.

## Live status

```
[x] 0  Understand       docs/method/00-understand.md
[x] 1  Context          docs/method/01-context.md
[x] 2  Brainstorm       ran, one question at a time, ending in the roadmap
[x] 3  Spec             docs/specs/, B1 B2 B3 B4
[x] 4  Plan             docs/plans/, B1 B2 B3 B4
[x] 5  Implement        B0 B1 B2 B3 merged. B4 slice one on a branch, 500 tests
