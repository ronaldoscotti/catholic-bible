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

Douay-Rheims and the Clementine Vulgate come along because they share an MIT-licensed fixture with near-zero marginal cost, and because English is the larger pool of developers. The Vulgate earns its place a second time by demonstrating the spine, since the spine is Vulgate numbering.

*Corrected 2026-08-02, while implementing. This paragraph said the Vulgate demonstrates the spine with zero orphans and called that a live proof inside the release. It is 69 unfilled addresses out of 35845, measured. The paragraph also conflated two different things. An orphan is a source verse that reached no spine address, and this repo cannot count those because the import dropped them before the corpus crossed over. An unfilled address is a spine slot no version reached, and that is what the table in `LIMITS.md` publishes.*

The English half also unblocks the most interesting thing the sibling repo will measure. A Portuguese question against English commentary is the one retrieval case where lexical search cannot work at all, and that case needs both languages present.

## Source

Extraction already happened. The import pipeline, the per-source normalizer and the curated 1956 orthography allow-list live in the private repo named in `CONTEXT.local.md`, they pass tests there, and the corpus is seeded there. None of that moves here.

What moves here is the finished data, through an export script that lives in this repo and reads that one. See [`DECISIONS.md`](../../DECISIONS.md) for why the generator stayed behind and what the choice costs.

## Problem

The Portuguese Catholic Bible circulates today as scraped HTML and JSON files of unclear origin, with 1956 spellings, source errors carried forward, and no way to tell a fix from a corruption. A developer who wants Matos Soares copies a file and finds out three weeks later that a book is missing. Nothing published states where it came from or whether it still matches.

## Acceptance criteria

- [x] Matos Soares (pt), Douay-Rheims (en) and the Clementine Vulgate (la) are complete for all 73 books
- [x] Every verse resolves against the B1 spine, and any that do not are reported as orphans rather than dropped silently
- [x] A committed export script produces the published dataset from the private source
- [x] Every published file carries a checksum and a provenance record naming its source, the source commit and the export date
- [x] A CI job on a clean checkout, with no access to the private source, recomputes every checksum and fails on a mismatch
- [x] An export job runs where the private source is, re-exports at the recorded source commit, and diffs against what is committed here. This is the job that catches a hand edit, and it fails the build when the two disagree
- [x] Running the export twice at the same source commit gives byte for byte identical output, checked by the export job rather than asserted
- [x] `LIMITS.md` records the per-book orphan rate with the cause, whatever the number turns out to be
- [x] `LIMITS.md` states plainly that a stranger cannot rebuild this dataset, and states which of the two jobs a stranger can actually run
- [x] Each translation carries its license and its public-domain basis in machine-readable form

Three of those need their wording qualified rather than ticked in silence.

**Complete means complete where the source is.** Twelve Douay-Rheims verses are
empty in the upstream MIT fixture and are omitted rather than published as empty
strings. `LIMITS.md` names all twelve.

**The orphan rate is not the number the criterion asked for.** An orphan is a
source verse that reached no spine address, and the import dropped those before
the corpus crossed over, so nothing here remembers them. What `LIMITS.md` and
`coverage.json` publish instead is the unfilled count per book, which is the same
question asked from the side this repo can see. The criterion said whatever the
number turns out to be, and this is what it turned out to be.

**The job with teeth is a command, not a build.** It needs the private source and
a running database, this project has no self hosted runner, and so `make
verify-export` is documented rather than wired to CI. Calling a green badge proof
of authorship would be the worst outcome available here, and `LIMITS.md` says so.

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

Two jobs, and they prove different things. Saying which is which is the point, because an earlier draft of this epic claimed the first one proved something it cannot.

The checksum job runs on a clean checkout with no access to the private source. It recomputes every hash and fails on a mismatch. What it catches is a truncated file, a partial commit, a bad merge, a corrupted download. What it does not catch is a deliberate edit, because the data and its checksum are both committed here, so anyone editing a verse recomputes the hash and commits both. A self-referential hash is an integrity check and never an authorship check, and treating it as one would ship a green build that manufactures confidence.

The export job is the one with teeth. It runs where the private source lives, re-exports at the source commit named in the provenance record, and diffs against what is committed here. A hand-edited verse shows up as a diff against an independent source, which is what the old regeneration gate did and the only mechanism that does it.

The cost is that the second job cannot run on a fork or on a clean public checkout. A stranger can verify integrity and cannot verify authorship, and `LIMITS.md` says that in those words.
