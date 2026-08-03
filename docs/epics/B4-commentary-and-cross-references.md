# [B4] Commentary and cross-references

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/data` `flagship` |
| Depends on | B1, B2, B3 |
| Blocks | C2 and C3 in `concordantia` |

**As** a Catholic reader
**I need** the commentary on the verse I am reading and the passages it points to
**So that** I move from reading Scripture to studying it

**As** the author of this repo
**I need** two independent layers anchored on the same verse id
**So that** the claim that the id is a usable anchor is demonstrated rather than asserted

## Context

Haydock in Portuguese does not exist. Anywhere. A complete Catholic commentary covering all 73 books, in Portuguese, has never been published, and everything else in this project is curation of material that already circulates. This is the one piece that is new in the world, and it is reason enough to do the whole thing.

The English Haydock was printed between 1811 and 1814 and is public domain. Cross-references come from the original Douay apparatus under CC0 and from OpenBible under CC BY, which requires attribution, and the attribution goes where a person will read it rather than in a footer nobody opens.

This epic is also the load-bearing proof for B1. One layer hanging off a verse id proves nothing. Two independent layers, added without a schema change, is what makes the anchor claim real.

## Source

The commentary importer, the translation merge, the cross-reference extractor and both readers already exist and pass tests in a private repo, and the Portuguese Haydock is already translated and stored there. `CONTEXT.local.md` maps the files and marks which cross-reference sets are excluded on rights grounds. This epic is extraction and porting, and the translation work is already done.

## Problem

A reader who reaches a hard verse has nowhere to go. Catholic commentary in Portuguese is either absent, paywalled, or scattered across sites that cannot be linked to a specific verse. Cross-reference data exists in Protestant-shaped sets that point away from the deuterocanonical books, so the passages a Catholic reader most needs connected are the ones left unconnected.

## Acceptance criteria

- [x] Haydock commentary in English is addressable by verse for all 73 books
- [x] Haydock commentary in Portuguese is addressable by verse for all 73 books
- [x] Cross-references resolve to spine addresses in both directions, and entries that cannot resolve are reported as orphans
- [x] Commentary and cross-references attach to the same verse id used by B1, with no change to the verse schema
- [x] The API exposes commentary and cross-references for a given address
- [x] OpenBible attribution appears in the README and in the dataset metadata
- [x] How the Portuguese translation was produced is stated on the first screen of the README, including what a human reviewed and what a human did not
- [x] Cross-references derived from a copyrighted apparatus are excluded, and the exclusion is recorded in `LIMITS.md`

## Constraints

The translation provenance is the single thing that has to be right here. A corpus of roughly twenty thousand entries announced as a translation and later discovered to be raw machine output burns credibility with exactly the readers who matter. Said plainly up front it becomes a strength, because a reviewed machine-translation pipeline with a gate that catches drift is a sentence about systems. Hidden, it becomes a problem.

The Catena Aurea in Portuguese does not ship, under any milestone. The edition on hand has open provenance and publishing it would be a copyright problem in a nice cover. The English Catena is public domain and can come later as a separate epic with a separate label, so the two never get confused in a distracted evening.

## Out of scope

Doré illustrations. Maps. Patristic texts beyond Haydock. The Catechism and magisterial documents, permanently.

## Verification

Test-driven on anchor resolution and on the orphan path for unresolvable cross-references. The Portuguese Haydock gets a human review sample with the sample size and the error rate written down, because a quality claim without a denominator is not a claim.

**Both verifications have now run and this epic closes.** The sample is drawn, seeded and committed at `docs/qa/haydock-translation-sample.csv`, and every one of its 200 entries carries a verdict in `haydock-translation-verdicts.csv`.

| | |
|---|---|
| Sample | 200 of 20705 |
| Entries carrying a defect | 5 |
| Observed error rate | 2.5% |
| 95% Wilson interval | 1.1% to 5.7% |
| Of those five, meaning inverted | 2 |

**The reading was done by a language model, not by a person.** The author read the sample and flagged nothing, then asked for the entry by entry pass rather than a second human. A machine graded a machine, which is weaker than the criterion imagined and is what happened. `docs/qa/haydock-translation-review.md` says so in those words and holds the verdicts. `README.md` and `LIMITS.md` describe the corpus as awaiting a human reading rather than as reviewed.

All five defects pass every check in `audit-translation.py`, and a test asserts that. An inversion carries the same length, markup and digits as a faithful rendering, which is the whole reason this verification could not be a script.
