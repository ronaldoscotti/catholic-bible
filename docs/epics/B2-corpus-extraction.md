# [B2] Corpus extraction and deterministic generator

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/data` |
| Depends on | B1 |
| Blocks | B3, B4, B5, and C1 in `concordantia` |

**As** a developer who wants Catholic Scripture in my app
**I need** the full text of three translations, generated from source by a script anyone can run
**So that** I can trust the data without auditing it by hand, and so that a contributor can prove their change did what they said it did

## Context

Matos Soares goes in v1 and that isn't negotiable. The community this serves is Portuguese-speaking, and an opening release in Latin and English aimed at Brazilian Catholic developers would have its back to the user. He died in 1957 with no successors, which puts him in the public domain under Brazilian copyright law, article 45.

Douay-Rheims and the Clementine Vulgate come along because they share an MIT-licensed fixture with near-zero marginal cost, and because English is the larger pool of developers. The Vulgate earns its place a second time by demonstrating the spine with zero orphans, since the spine is Vulgate numbering. That's a live proof inside the release itself.

The English half also unblocks the most interesting thing the sibling repo will measure. A Portuguese question against English commentary is the one retrieval case where lexical search cannot work at all, and that case needs both languages present.

## Source

The import pipeline and the per-source normalizer interface already exist and pass tests in a private repo, and the corpus itself is already seeded there. `CONTEXT.local.md` maps the files and lists which translations port and which stay out. Export the existing data as a deterministic fixture first, then rebuild the generator in Python against it, and check both sides agree.

## Problem

The Portuguese Catholic Bible circulates today as scraped HTML and JSON files of unclear origin, with 1956 spellings, source errors carried forward, and no way to tell a fix from a corruption. A developer who wants Matos Soares copies a file and finds out three weeks later that a book is missing. There is no reproducible path from a source to a dataset.

## Acceptance criteria

- [ ] Matos Soares (pt), Douay-Rheims (en) and the Clementine Vulgate (la) are complete for all 73 books
- [ ] Every verse resolves against the B1 spine, and any that do not are reported as orphans rather than dropped silently
- [ ] `make` regenerates the entire dataset from source, deterministically, byte for byte identical across runs and machines
- [ ] A CI job regenerates the dataset and diffs it against what is committed. If output changed without the generator changing, the build fails
- [ ] The 1956 orthography normalization is a curated allow-list, not a dictionary pass, and the list is versioned and reviewable
- [ ] `LIMITS.md` records the per-book orphan rate with the cause, whatever the number turns out to be
- [ ] Each translation carries its license and its public-domain basis in machine-readable form

## Constraints

No JSON maintained by hand. If a value cannot be produced by the generator, it does not ship.

Normalizing 1956 spelling is where a careless pass does damage. `pacto` is a word. A naive mute-consonant rule turns real words into wrong ones, so the allow-list is curated and every entry is defensible.

Provenance for `Dancrf/biblia-db` and `mborders/vulgata` gets confirmed before extraction starts, not after.

## Out of scope

No commentary. No cross-references. No Ave Maria text, which is under copyright and stays out permanently.

## Verification

Not test-driven, and the epic says so rather than growing a decorative unit test. Golden files hold the expected output. The real gate is the CI regeneration diff, which is what actually proves the corpus was not adjusted by hand.
