# Spec, B1 canon and versification spine

*Stage 3. Written 2026-08-02, against issue #2.*

**Gate.** Stages 3 and 4 are human review gates and the author waived the
blocking wait for this epic, in writing, during the session that produced this
document. The artifact still gets written, because the point of the gate is a
readable record of what was decided before code existed, and that survives the
waiver. What does not survive is the claim that someone stopped and read it, so
this document does not make that claim.

## What B1 delivers

Addresses. Not text.

A stable identity for every verse in the 73-book Catholic canon, a way to name
that identity on the wire, a way to parse a human reference into it in three
languages, and a total function that translates other numbering schemes into it
and reports what does not fit.

## Where the data comes from

Frozen. The spine is not computed here. It is exported from the private repo,
which built it and tested it, under the decision recorded in
[`DECISIONS.md`](../../DECISIONS.md).

Two files cross over.

`catholic-versification.json` is the spine. A map of USX book code to a list of
verse counts, one entry per chapter. 73 keys. `PSA` has 150 entries and its
fiftieth is 21. `DAN` has 14. The sixth entry of `1CH` is 81.

`vulgata-versification.json` is the Copenhagen table for the Vulgate scheme. It
carries four keys, `maxVerses`, `mappedVerses`, `excludedVerses` and
`partialVerses`. The counts in `maxVerses` are strings rather than numbers,
which the port has to handle rather than trust.

`catholic-canon.php` is the canon, and it is a PHP array literal. It becomes
JSON on the way over. Each of the 73 entries carries a USX code, testament,
canon group, a deuterocanonical flag, a Portuguese name, an abbreviation and a
list of Portuguese aliases. Array position is canonical order.

## The spine, stated

The spine is a Vulgate-cardinality superset over the `org` scheme, applied to
the Old Testament only.

Per chapter, the count is the larger of what `org` has and what the Vulgate has.
It never reduces. Where the Vulgate has more verses, which is mostly the
genealogies in the historical books, the chapter grows. `1CH 6` growing to 81 is
that rule firing.

The New Testament is untouched. Modern NT numbering is what the liturgy, the
Catechism and every cross-reference apparatus already use, and a spine that
disagreed with all three would be correct about nothing anyone needs.

**The subtlety that a naive port destroys.** The Vulgate maximum is computed
from coordinates already passed through the Vulgate to spine map, not from raw
Vulgate coordinates. Boundary differences such as `GEN 31:55` mapping to
`GEN 32:1` would otherwise inflate chapters that did not need to grow, and
inflating them breaks the mode detection described below. Only pure cardinality
excess extends the spine.

## Mode is decided per book, by counting

The spine is mixed. The Psalter follows Vulgate numbering and most other books
follow `org`. That is a result rather than a rule.

For each book, run every verse the Vulgate has through both readings, count how
many land outside the spine each way, and keep the reading with fewer misses. A
tie keeps identity. A book with no `maxVerses` entry defaults to identity.

The inverse map, `org` to spine, applies only where the mode is identity, which
is to say only where the spine numbers that book in Vulgate. Where the spine
already numbers in `org`, an `org` input passes through untouched.

## Two identities

Internal is an integer. A dense canonical order across the whole canon,
assigned by walking books in canonical order and chapters and verses in
sequence. It is what interval arithmetic uses and it is what a range query
compares.

Published is a string, `PSA.50.3`. Book code, chapter, verse. The integer stays
in responses as a derived field for callers doing range maths, and it can be
recomputed without breaking anyone.

The reason for the split is that the integer is an artifact of the order a seed
ran in. Freezing one into a public contract is a mistake that cannot be undone
later, and every consumer of this repo would be holding it.

The spine is append-only and a published id never changes meaning. That is an
API contract and it gets stated out loud.

## The mapping function

Total. It always returns and it never raises.

```
map(scheme, book, chapter, verse) -> Mapped(book, chapter, verse) | Orphan(reason)
```

Never a guess. Where there is no target it returns an orphan, not the nearest
plausible verse.

Orphan reasons are a closed set, and each one is a distinguishable cause rather
than a single "not found".

- `unknown_book`, the code is not in the canon
- `chapter_out_of_range`, the book exists and the chapter does not
- `verse_out_of_range`, the chapter exists and the verse number exceeds it
- `no_counterpart`, the scheme has a verse the spine has no slot for, which is
  the Susanna and Bel case
- `excluded_by_scheme`, the Copenhagen table marks it excluded

The last one is new. The private repo carries `excludedVerses` and
`partialVerses` in the Copenhagen table and uses neither. Reading `excludedVerses`
turns a class of orphan from "no counterpart" into a stated cause, which is the
difference between a report and a shrug. `partialVerses` stays unused in B1 and
the reason is written in the epic rather than left to inference.

`orphans.json` is generated from running every address of every supported scheme
through the function, broken down by book and by scheme, with the reason.

## Where orphans live, and why that moved

The private implementation keeps `mapToSpine` pure and detects orphans in the
importer, so there is one place that decides. Here the importer is B2 and B1 has
to publish `orphans.json`, so the responsibility moves into the mapping layer.

This is a real divergence and it goes in `DECISIONS.md` when the code lands.

## The reference parser

Returns a result rather than raising. An unresolvable reference is a domain
error and the caller can act on it, which is the rule in `CLAUDE.md`. The
private implementation throws `InvalidArgumentException`, and that is the second
divergence for `DECISIONS.md`.

Grammar, ported from the working implementation.

- `Jo 3,16` and `Jo 3:16`, single verse
- `Jo 3,16-18`, range inside a chapter
- `Ex 13,1-14,5`, range across a chapter boundary
- `Mc 5,22-24.35-43`, disjoint lectionary parts, with the chapter inherited by a
  part that does not carry its own
- `Sl 23`, whole chapter
- `Ex 13-14`, chapter range, anchored on the first chapter

**`Jo` against `Jó` is the load-bearing case.** Alias normalization lowercases
and trims and does nothing else. It does not strip accents. A port reaching for
Unicode normalization to be helpful would collapse `Jó` into `jo` and make Job
unreachable, and the reader would land in John's gospel with no error anywhere.
The absence of that normalization is the feature and it gets a test that says so.

## Aliases in three languages

Portuguese ports from the canon file, 73 names plus abbreviations plus alias
lists, already collision-free there.

English ports from the Douay reference parser in the private repo.

Latin is authored here, from the traditional names, and it is the one part of
B1 that is not a port. `Genesis`, `Exodus`, `Canticum Canticorum`,
`Ecclesiasticus` for Sirach, `Apocalypsis` for Revelation. Where the tradition
disagrees with itself the choice goes to the author of this repo rather than
being decided quietly, and both forms are recorded.

No collisions, within a language or across the three. The check is a test, not
a reading.

Nothing enters without a case in the conformance corpus. Not even one alias.

## The conformance corpus

Every case records input, expected output, provenance and a note on why it is
hard. That last field is an acceptance criterion and it is what makes the corpus
readable a year from now.

Minimum set, from the epic.

- Psalm 51 in `org` resolving to Psalm 50 on the spine, and the Miserere landing
  where the missal has it
- Daniel 13 and 14, Susanna and Bel, which `org` has no slot for at all
- The Greek additions to Esther
- Sirach numbering
- The Joel and Malachi chapter breaks
- Tobit's two textual traditions
- `1CH 6`, where the spine has 81 and an `org` source has fewer, so the expected
  answer is an orphan rather than a mapping
- `Jo 3,16` and `Jó 3,16` landing in different books

## Out of scope

No text, no commentary, no cross-references, no HTTP. B1 is addresses.

No import mechanism. The data arrives frozen.

## Open questions carried into the plan

Whether the exported spine ships as one JSON file or split per book. The
consumer is code in this repo, so one file is likely right and B5 is where the
per-book split earns its place.

Whether `partialVerses` deserves a sixth orphan reason. It is unused in the
working implementation and adding a reason nobody has hit would be inventing a
requirement.
