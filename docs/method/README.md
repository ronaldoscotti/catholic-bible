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
[x] 3  Spec             docs/specs/, B1 B2 B3
[x] 4  Plan             docs/plans/, B1 B2 B3
[x] 5  Implement        B0 B1 B2 merged. B3 on a branch, 442 tests
[x] 6  QA               docs/qa/, B0 B1 B2 B3
[ ] 7  Code review      docs/reviews/, B0 B1 B2. B3 has none
[x] 8  PR               B0 B1 B2 merged. B3 open as #23
```

The checklist advances when the artifact exists and not before. Four epics have
run. B0 builds the project, B1 builds the addresses, B2 publishes Scripture and
B3 serves it.

Stage 7 is unchecked because B3 has no review notes. Three epics have them and
the fourth does not, and a box ticked on three out of four is a box that reads
as four. Stage 8 is ticked because the pull request exists, which is the whole
of what that stage deposits.

The two gates on B1 were not met the same way and the difference is recorded
rather than averaged.

**Stage 3 was waived.** The author waived the blocking wait in writing before
the spec was written. The document exists as the record of what was decided
before code existed, which survives a waiver, and it does not claim anyone
stopped and read it.

**Stage 4 was met.** The plan was written, presented with the three decisions it
could not make on its own, and approved in a single explicit message. The code
came after.

Both gates were met on B2. The spec was presented with three open questions and
approved, then the plan, then the code.

Both were met on B3, and the spec gate fired the way a gate is supposed to. The
first draft was reviewed by a subagent and did not survive it. Four of its
numbers did not reproduce, it dropped four ported behaviours without naming
them, and its psalm numbering field could not represent a mapping that splits and
merges. The second draft carries a section recording what the first got wrong,
and it was that draft that was approved.

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

**The orphan rate is not measurable here.** This repo promised an honest orphan
report. B2 found that an orphan is a source verse the import dropped before the
corpus crossed over, so nothing here remembers them. What is published instead is
the unfilled count per book, which is the same question from the side this repo
can see, and `LIMITS.md` says which is which rather than printing a zero.

## Reference documents

Written when the question actually comes up rather than in advance, which is
why there are none yet. A document on error handling written before there is
error handling would be a description rather than residue.
