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
the agent's own confidence.

Epics run this pipeline one at a time. The epic is the unit of work and it
lives in `docs/epics/` with a matching GitHub issue.

## Live status

```
[x] 0  Understand       docs/method/00-understand.md
[x] 1  Context          docs/method/01-context.md
[x] 2  Brainstorm       ran, one question at a time, ending in the roadmap
[ ] 3  Spec             no epic has reached a written spec yet
[ ] 4  Plan             nothing planned
[ ] 5  Implement        no code exists in this repo
[ ] 6  QA               nothing to exercise
[ ] 7  Code review      nothing to review
[ ] 8  PR               no pull request has been opened
```

Everything below the third line is empty and says so. The checklist advances
when the artifact exists and not before. A roadmap with ten epics and no code
is a plan, and calling it anything else would make every other line here worth
nothing.

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
