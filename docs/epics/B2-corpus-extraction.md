# [B2] Corpus export and integrity

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/data` |
| Depends on | B1 |
| Blocks | B3, B4, B5, and C1 in `concordantia` |

**As** a developer who wants Catholic Scripture in my app
**I need** the full text of three translations, published with a checksum and a stated origin
**So that** I can tell a correction from a corruption without auditing 73 books by hand

## Context

Matos Soares goes in v1 and that isn't negotiable. The community this serves is Portuguese-speaking, and an opening release in Latin and English aimed at Brazilian Catholic developers would have its back to the user. He died in 1957 with no successors, which puts him in the public domain under Brazilian copyright law, article 45.

Douay-Rheims and the Clementine Vulgate come along because they share an MIT-licensed fixture with near-zero marginal cost, and because English is the larger pool of developers. The Vulgate earns its place a second time by demonstrating the spine with zero orphans, since the spine is Vulgate numbering. That's a live proof inside the release itself.

The English half also unblocks the most interesting thing the sibling repo will measure. A Portuguese question against English commentary is the one retrieval case where lexical search cannot work at all, and that case needs both languages present.

## Source

Extraction already happened. The import pipeline, the per-source normalizer and the curated 1956 orthography allow-list live in the private repo named in `CONTEXT.local.md`, they pass tests there, and the corpus is seeded there. None of that moves here.

What moves here is the finished data, through an export script that lives in this repo and reads that one. See [`DECISIONS.md`](../../DECISIONS.md) for why the generator stayed behind and what the choice costs.

## Problem

The Portuguese Catholic Bible circulates today as scraped HTML and JSON files of unclear origin, with 1956 spellings, source errors carried forward, and no way to tell a fix from a corruption. A developer who wants Matos Soares copies a file and finds out three weeks later that a book is missing. Nothing published states where it came from or whether it still matches.

## Acceptance criteria

- [ ] Matos Soares (pt), Douay-Rheims (en) and the Clementine Vulgate (la) are complete for all 73 books
- [ ] Every verse resolves against the B1 spine, and any that do not are reported as orphans rather than dropped silently
- [ ] A committed export script produces the published dataset from the private source, and running it twice on the same source commit gives byte for byte identical output
- [ ] Every published file carries a checksum and a provenance record naming its source, the source commit and the export date
- [ ] A CI job verifies every checksum and every provenance record on a clean checkout, with no access to the private source. A byte that moved without its provenance moving fails the build
- [ ] `LIMITS.md` records the per-book orphan rate with the cause, whatever the number turns out to be
- [ ] `LIMITS.md` states plainly that a stranger cannot rebuild this dataset, and why
- [ ] Each translation carries its license and its public-domain basis in machine-readable form

## Constraints

No JSON edited by hand. A value no script produced does not ship.

The export reads the private repo and writes here. It never reaches the other way, and it never rewrites what it exported.

The 1956 orthography allow-list is not reimplemented. It is curated in the private repo, it is already reviewable there, and a second copy of it here would be a second thing to keep right.

Provenance for `Dancrf/biblia-db` and `mborders/vulgata` is confirmed in the private repo before anything is exported, not after.

## Out of scope

No commentary. No cross-references. No Ave Maria text, which is under copyright and stays out permanently.

No extraction, no scraping, no upstream dumps. Those stay in the private repo.

## Verification

Not test-driven, and the epic says so rather than growing a decorative unit test.

The gate is the CI integrity job, and it has to pass on a runner with no access to the private source. It recomputes every checksum, reads every provenance record, and fails when a published byte moved without its record moving. That is what proves the corpus was not adjusted by hand, which is the only thing the old regeneration diff was ever proving.
