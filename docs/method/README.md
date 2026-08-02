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
[ ] 3  Spec             no epic has needed one yet. B0 took the short route
[ ] 4  Plan             same
[x] 5  Implement        B0, the project scaffolding
[x] 6  QA               docs/qa/B0-project-scaffolding.md
[x] 7  Code review      docs/reviews/B0-project-scaffolding.md, one author
[x] 8  PR               open on B0, CI green, not merged
```

The checklist advances when the artifact exists and not before. One epic has
run, and it is the one that builds the project rather than any of the ones that
build the thing the project is for. B1 onward is still a plan.

## The short route

Scaffolding and isolated changes skip stages 3 and 4 and go understand,
context, implement, QA, review, pull request. The rule is written in
[`SESSION_PROMPT.md`](../../SESSION_PROMPT.md), which is committed and predates
the first epic, so the route was decided before anything ran it rather than
after. B0 ran that way. Nothing in it touches the canon, the spine, the data
model or a public seam, and a spec document describing a `pyproject.toml` would
be a description of a file rather than a decision about one.

The same file says the shape of the work gets presented and approved before any
code is written, which is what happened with the one decision in B0 that has
consequences downstream, the package layout. That approval lives in the session
transcript. A reader checking this repo cannot open a transcript, so what they
can check instead is the rule that required the approval and the commit order,
where `SESSION_PROMPT.md` lands two commits before any Python.

Anything that touches the canon, the spine, the data model or a public seam
takes the full pipeline. B1 does.

## The gates that are not met

Two of them, and both stay written down until they change.

**Nobody else has reviewed anything.** Stage 8 says a pull request gets reviewed
before it merges, and this repo has one author. What is true is the mechanism.
Work lands through pull requests and never through a push to `main`, so the gate
has somewhere to fire the day there is a second person. A checklist that counts
a self-approval as a review is decoration.

**The correctness claim is unmeasured.** This repo promises a versification
spine, a total mapping function and an honest orphan report. The orphan rate is
not known yet. It will be published when it is measured, whatever it turns out
to be, and until then no number appears anywhere in this repo.

## Reference documents

Written when the question actually comes up rather than in advance, which is
why there are none yet. A document on error handling written before there is
error handling would be a description rather than residue.
