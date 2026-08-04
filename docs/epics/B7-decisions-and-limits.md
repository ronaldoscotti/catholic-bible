# [B7] Decisions and limits

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/docs` `voice` |
| Depends on | B1, B2, B4 |
| Blocks | the MVP gate |

**As** a developer deciding whether to depend on this
**I need** to know what it gets wrong and why the hard calls went the way they did
**So that** I can trust the parts that work instead of discovering the limits in production

## Context

Every Bible repo says it works. Publishing the failure rate per book, with the cause, is the cheapest thing in this project and the one that communicates the most, because the number already falls out of B1 and B2.

The orphan rate is not a bug to hide. Genealogies have genuinely different cardinality across editions, no lookup table fixes that, and pretending otherwise is worse than reporting it. A commentary anchored to the wrong verse is worse than a commentary that is missing.

## Problem

A developer choosing between this dataset and another one on GitHub has nothing to choose on. Both READMEs claim correctness, neither publishes a failure mode, and the difference only surfaces after the choice is expensive to undo.

## Acceptance criteria

- [x] `DECISIONS.md` records each hard call with the alternative that lost and why, covering at minimum: a superset spine instead of an intersection, per-book conditional remapping instead of a fixed table, dropping orphans instead of extending the spine, a structured public id instead of an opaque integer, and orphans as return values instead of exceptions
- [x] `LIMITS.md` states the orphan rate per book and per scheme, with the cause for each concentration
- [x] `LIMITS.md` records the rights audit per asset, with the legal basis and what was excluded
- [x] `README.md` and `README.pt-BR.md` both exist and link to each other from the top
- [x] `CONTRIBUTING.md` states that no alias and no scheme enters without a conformance case
- [ ] A diagram shows schemes entering, the spine in the middle, and the layers hanging off it
- [x] Every prose document passes the voice check, including zero em-dashes

**The second criterion was nearly abandoned on a misreading.** It was called
unmeetable earlier in the session, because `LIMITS.md` said the orphan rate is
not measured here and that sentence was taken at face value. Two failures share
the word. A source verse the import dropped is not measurable from inside this
repository. A scheme address that reaches no slot on the spine has been measured
since B1 and sits in `orphans.json` with a breakdown by book and by reason. The
old section answered only with the unfilled counts, which are the other
question. It is split in two now and the measurable half is published.

**The diagram box is empty on purpose.** The mermaid block is written and its
syntax is valid, which is not the same as a diagram anyone has looked at.
`docs/qa/B7-decisions-and-limits.md` says it gets ticked after it has been seen
rendering on the pushed branch, and not before.

**The seventh is ticked on the half a machine can answer.** `make lint-voice`
runs clean over 18 documents and a test keeps it that way. The human read named
in the verification below is the author's, at the review gate on the pull
request, and no document here ticks that on his behalf.

## Constraints

Written in my voice, not in generic documentation register. Human-facing prose in this repo goes through the voice skill and I read it before it lands.

Claims are limited to what the code has earned. No feature banner over an unfinished path.

The English README does not apologize for the corpus being Portuguese-first. Portuguese is the gap and it is the point.

## Out of scope

The formal specification document and the essays are later work. `DECISIONS.md` covers the v1 need.

## Verification

Human read, and a lint pass that fails on em-dashes and on the banned-phrase list.
