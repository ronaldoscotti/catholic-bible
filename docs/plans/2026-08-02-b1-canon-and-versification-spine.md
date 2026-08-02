# Plan, B1 canon and versification spine

*Stage 4. Written 2026-08-02, against issue #2 and the spec dated the same day.*

**Gate.** This is a human review gate and it was met. The plan was presented
with the three decisions below that it could not make on its own, and approved
in one message. Implementation started after that and not before.

The three answers were: Douay names canonical in English, a fifth orphan reason
for the Vulgate psalm titles, and liturgical Latin as the canonical form.

**One thing this plan missed.** The epic asks for the mapping in both
directions and none of the nine milestones below covers reading a spine address
back into a scheme. It was found during the acceptance criteria walk and built
then. A plan that had decomposed it would have caught the asymmetry earlier,
because running the table backwards turns out to need its own rule.

## What changed since the spec

Three things, all found by reading the frozen data rather than the PHP.

**`excluded_by_scheme` is dropped.** The spec proposed a fifth orphan reason
reading `excludedVerses` from the Copenhagen table. That key is present in
`vulgata-versification.json` and it is empty. So is `partialVerses`. A reason
nothing can produce is dead code wearing a rationale, and the spec rejected
`partialVerses` on exactly that ground while accepting `excludedVerses` without
checking. Four reasons, not five.

**Verse zero is a real orphan class and it has no reason yet.** The Copenhagen
table carries 147 Psalm entries whose ranges start at verse 0, which is the
Vulgate Psalm title. `PSA 50:0-21` maps to `PSA 51:0-21`. The spine records 21
verses for `PSA 50`, so the title has no slot and every one of those 147
addresses orphans. Reporting them as `verse_out_of_range` is technically true
and practically misleading, because a title is not a verse that ran off the end.
This one is grounded in data rather than invented, so it is a real decision and
it goes to the gate below.

**English aliases carry a collision the Portuguese ones do not.** The Douay
names in the private repo map `1 KINGS` to `1SA` and `3 KINGS` to `1KI`, which
is correct Douay usage. Modern English maps `1 Kings` to `1KI`. Adding both
without a rule means one reader asks for `1 Kings 3` and lands in Samuel while
another lands in Kings, in the same language, with no error anywhere. It is the
`Jo` against `Jó` problem with a worse failure mode, because both spellings are
correct English. The gate decides the rule.

Two smaller corrections. The Latin abbreviations are not authored here after
all, they port from the Douay apparatus parser, which already carries `ios`,
`iudic`, `sap`, `eccli`, `apoc` and about a hundred more. What is authored here
is the full Latin book names. And the English user-facing names come from
`DouayCanonMap`, not from `DouayReferenceParser`, which parses the Latin
apparatus rather than English input.

## Milestones

Bite-sized for M1 through M6. M7 through M9 are milestone specs, expanded when
reached against the code that exists by then, because their shape depends on
what M6 produces.

### M1. The frozen data crosses over

Not test-driven. It is an export, and the epic says to name the real
verification rather than grow a decorative unit test.

- `scripts/export-spine.py`, reading the private repo from an environment
  variable, writing `data/canon.json`, `data/versification.json` and
  `data/vulgate-scheme.json`
- `catholic-canon.php` is a PHP array literal, so the export shells out to `php`
  to emit JSON rather than parsing PHP in Python
- `data/PROVENANCE.json` carries the source repository, the source commit, the
  export date and a sha256 per file
- One test, and it is an integrity test rather than an authorship test. It
  recomputes the hashes of the committed files and compares them to the
  committed record

Verification. Run the export twice at the same source commit and diff. Byte
identical or it does not land. B2 generalizes this mechanism for the corpus and
adds the second job that catches a hand edit, and B1 does not claim to have that
job.

Expected shapes, measured from the source. 73 books in the canon. 73 keys in the
spine. 86 keys in `maxVerses`, of which 14 have no spine counterpart. 475 range
pairs in `mappedVerses`. The counts in `maxVerses` are strings and the loader
converts them rather than trusting them.

### M2. Canon

- `Book` with USX code, canonical order, testament, canon group,
  deuterocanonical flag, Portuguese name and abbreviation
- `Canon.load()` from `data/canon.json`, lookup by code, iteration in canonical
  order

Tests. 73 books. Canonical order runs 1 to 73 with no gap and no repeat. Codes
are unique. 46 books in the Old Testament and 27 in the New. Exactly seven books
carry the deuterocanonical flag, `TOB` `JDT` `WIS` `SIR` `BAR` `1MA` `2MA`, and
`DAN` and `EST` do not, because their deuterocanonical material is chapters
inside a protocanonical book rather than a book. An unknown code returns nothing
rather than raising.

### M3. Spine

- `Spine.load()` from `data/versification.json`
- `chapter_count(book)`, `verse_count(book, chapter)`, `contains(book, chapter,
  verse)`, and an iterator over every valid address

Tests. 73 books. `PSA` has 150 chapters and its fiftieth has 21 verses, which is
the Vulgate Psalter showing through. `DAN` has 14 chapters, so Susanna and Bel
have slots. `1CH 6` has 81 verses. `EST` has 16 chapters. `JOL` has 4 and `MAL`
has 3, which is `org` numbering, so the spine is mixed and the test says so.
`contains` rejects verse 0 and rejects verse 22 of `PSA 50`. The total address
count is asserted against a recorded number rather than a computed one, so a
change to the frozen data fails a test instead of passing silently.

### M4. Verse identity

- `VerseId` with book, chapter and verse, formatting to `PSA.50.3` and parsing
  back as a result rather than an exception
- `canonical_order`, a dense integer assigned by walking the spine in canonical
  order

Tests. Round trip through the string form. `GEN.1.1` has order 1. Order is
strictly increasing across the full enumeration. The last address has the order
equal to the total count. A malformed string comes back as an error value
carrying what was wrong. An address the spine does not contain has no order.

### M5. Scheme maps

Three maps, one shared mechanism.

- Range expansion, `PSA 50:0-21` into 22 positional keys, with mismatched
  lengths skipped defensively the way the source does
- The Vulgate to spine map, with per-book mode decided by counting orphans both
  ways and identity winning a tie, memoized
- The `org` to spine map, which is the inverse index applied only where the mode
  is identity, and passthrough everywhere else
- The Douay map, which is identity in 71 books and shifts `JOL` and `MAL`

Tests, with values verified against the frozen data rather than assumed.

| Case | Expected |
|---|---|
| `GEN 31:55` Vulgate | `GEN 32:1` |
| `GEN 32:1` Vulgate | `GEN 32:2` |
| mode for `PSA` | identity, the spine numbers the Psalter in Vulgate |
| mode for `MAL` | `org`, the spine has 3 chapters and the Vulgate has 4 |
| `PSA 51:1` in `org` | `PSA 50:1` on the spine, the Miserere |
| `SUS 1:1` in `org` | `DAN 13:1` on the spine |
| `S3Y 1:1` in `org` | `DAN 3:24` on the spine |
| `MAL 4:1` Douay | `MAL 3:19` |
| `JOL 2:28` Douay | `JOL 3:1` |
| `1 KINGS` Douay name | `1SA` |
| mode for a book absent from `maxVerses`, `EST` | identity |

The mode counting has to run over the remapped coordinates, not the raw ones.
The docblock in the source says why and the test that protects it is the `GEN`
boundary case above.

### M6. The total map

- `map(scheme, book, chapter, verse)` returning `Mapped(book, chapter, verse)`
  or `Orphan(reason)`
- Reasons, a closed set of four: `unknown_book`, `chapter_out_of_range`,
  `verse_out_of_range`, `no_counterpart`
- A fifth for the Psalm titles is pending the gate

Tests. It never raises, checked by sweeping every address in `maxVerses` across
all three schemes and asserting a return every time. It never guesses, checked
by asserting that no orphan input produces a `Mapped` at a neighbouring address.
`ESG 11:1` in `org` comes back `no_counterpart`, because Greek Esther has no
spine book. `XYZ 1:1` comes back `unknown_book`. `GEN 99:1` comes back
`chapter_out_of_range`.

The divergence from the source lands here and goes to `DECISIONS.md`. The
private implementation keeps the map pure and detects orphans in the importer,
which is the right call when an importer exists. Here the importer is B2 and B1
has to publish `orphans.json`, so the detection moves into the mapping layer.

### M7. orphans.json

Milestone spec. Generated by sweeping every scheme address through M6, grouped
by book and by scheme, with the reason and a count. Published as a data file
with a test that regenerates it and diffs, so a change in the map moves the
report or fails the build. The orphan rate is not predicted anywhere in this
repo before it is measured.

### M8. Aliases and the reference parser

Milestone spec, and the largest remaining unknown is a gate decision rather than
a technical one.

Portuguese ports from the canon file, names plus abbreviations plus alias lists,
already collision-free there. English comes from the Douay names under whatever
rule the gate sets. Latin abbreviations port from the apparatus parser and the
full Latin names are authored here.

The parser grammar ports whole: single verse with either separator, range inside
a chapter, range across a chapter boundary, disjoint lectionary parts with the
chapter inherited, whole chapter, chapter range anchored on the first chapter.
It returns a result rather than raising, which is the second divergence for
`DECISIONS.md`.

Normalization lowercases and trims and does nothing else. The test that matters
asserts `Jó` does not normalize to `jo`, and it carries a comment saying the
absence of accent folding is the feature.

A collision test runs across all three languages at once and fails on any
duplicate normalized key.

### M9. Conformance corpus

Milestone spec. A data file, one entry per case, each carrying input, expected
output, provenance and a note on why the case is hard. One test parameterized
over the file. The minimum set is the list in the epic and every case added
after that arrives as data rather than as a new test function.

## Where test-driven does not apply

M1 only. It is an export of finished data and its verification is a byte
identical rerun plus a checksum recomputation, both named above. Everything else
in B1 is pure functions over frozen input, which is the easiest thing in this
repo to drive from tests and the least excusable to skip.

## Decisions this gate has to make

**One.** English aliases. Douay only, modern only, or both with a documented
winner for `1 Kings`, `2 Kings`, `3 Kings` and `4 Kings`. My inclination is
Douay names as canonical, since this is a Catholic dataset anchored on the Douay
and Haydock apparatus, with modern names accepted as aliases except where they
collide, and the four Kings forms resolving Douay. That choice makes `1 Kings 3`
return Samuel to a reader who expected Kings, so it needs to be deliberate and
it needs to be documented on the endpoint in B3.

**Two.** Whether the Psalm titles get their own orphan reason. My inclination is
yes, a fifth reason named for what it is, because 147 addresses reported as out
of range would be the largest single orphan class in the report and the report
would be describing them wrongly.

**Three.** Latin naming where the tradition disagrees with itself. My
inclination is the liturgical form as the canonical name, `Ecclesiasticus`,
`Apocalypsis`, `Canticum Canticorum`, with the alternatives recorded as aliases.

## Risks

The mode detection is the load-bearing piece and it is the one thing here that
is a computation rather than a lookup. If a port of it disagrees with the
source, every downstream map disagrees quietly. The mitigation is that M5 asserts
the mode of specific books by name rather than only asserting the mapped output,
so a wrong mode fails directly instead of failing three layers later.

The frozen data is a snapshot. If the private repo rebuilds the spine, this repo
does not know. B2 owns the mechanism that catches that and B1 records the source
commit so the question is answerable.
