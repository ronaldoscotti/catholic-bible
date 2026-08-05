# Spec, B11 Catechism cross-references

*Stage 3. Written 2026-08-05, against issue #18.*

**Gate.** This is a human review gate. Three questions went out before this
document was written. One of them was withdrawn on the answer, one was answered
by measuring instead of arguing, and one came back as a decision. The three
sections that carry them are marked.

## What B11 delivers

The index that runs the other way.

The Catechism cites Scripture on nearly every page and the citation points from
the paragraph to the verse. A developer holding a verse cannot ask the reverse
question, because nobody publishes it. This epic publishes it, as paragraph
numbers and links, and sends the reader to `vatican.va` for the words.

Not one word of Catechism text ships, permanently.

## Measured before writing this

Every number ran on 2026-08-05 against `56fb037`, the merge commit of B10. None
of them is an estimate and none of them is from documentation.

| Fact | Value | How |
|---|---|---|
| Paragraphs carrying a citation | 1193 of 2865 | the source fixture |
| Citation labels | 3549, of which 2483 distinct | the source fixture |
| Labels the B1 parser reads | 3549 of 3549, 100% | `parse_reference` over all of them |
| Scheme the source is written in | `org` | 3547 map, against 3527 for vulgate and douay |
| Verses carrying at least one citation | 4123 | ranges expanded onto the spine |
| Verse to paragraph pairs | 6967 | the same run |
| Most cited verse | `MAT.28.19`, 17 paragraphs | the same run |
| The artifact | 84 KB, 19 KB gzipped | `json.dumps` and `gzip.compress` |
| Labels that do not reach the spine | 9 of 3549, 0.25% | the same run |
| English edition pages | 374 | the live index |
| Portuguese edition pages | 26, plus the prologue | the live index |
| Upstream licence | none declared | the GitHub API |

## The link shape, verified against the live site

The epic makes this the first thing that happens, before anything is built, and
it was. What follows is what the site returned on 2026-08-05.

**A per-paragraph deep link does not exist, in either edition.** The fallback the
epic named is not a fallback. It is the only shape available.

**English**, at `/archive/ENG0015/`, is an IntraText build split across 374
pages named `__P1.HTM` through `__PAE.HTM`. Those ids are a base 36 sequence in
document order and they carry no paragraph number. The pages do contain anchors,
and the anchors are footnote markers rather than paragraphs. A request for
`__P16.HTM` comes back opening at paragraph 199, which is knowable only by
reading the page.

**Portuguese**, at `/archive/cathechism_po/index_new/`, puts the paragraph range
in the file name. `p1s2c1_198-421_po.html`, `p1s1c2_50-141_po.html`. Twenty six
such pages, contiguous from paragraph 26 to paragraph 2865 with no gap, plus one
page for the prologue. The map from a paragraph to its page comes out of the
index page alone, without reading a line of the text.

The two editions are not symmetric and no pattern relates them.

## Decisions

### The dataset is one directory, and deleting it withdraws the epic

`src/catholic_bible/data/catechism/`, holding `citations.json`, `pages.json`,
`orphans.json` and `PROVENANCE.json`. The criterion asks that withdrawing this
be deleting one file, and one directory honours that better than one file does,
because the link map and the orphan report are part of what would have to go.

Nothing else in the repository grows a Catechism field. The corpus, the
commentary and the cross-references are untouched.

### The source numbering is `org`, and converting it is B1's job

The citations arrive in modern numbering, not in the spine's. Read against the
spine directly, 22 addresses fall outside it, and 20 of those are Psalms where
the Hebrew and the Greek numbering part company. Through B1's `org` map, 3547 of
3549 land.

This is not a new mechanism. It is the mapping layer B1 already ships, pointed at
a new source, and the spec records the scheme so that a later reader does not
have to rediscover it from an orphan report.

### Ranges are expanded onto every verse they cover

A paragraph citing `Mt 28,19-20` answers for both verses. The alternative,
storing the range and expanding at read time, moves work into every request to
save 19 KB once. The expansion is 6967 pairs over 4123 verses.

### Nine labels do not reach the spine, and they ship as orphans

Two of them name a book the source got wrong. `Jd 13,18` and `Jd 6,11-24` are
impossible in Jude, which has one chapter and twenty five verses, and both are
valid in Judith. The alias table here is correct, `Jd` is Jude and `Jt` is
Judith, so the error is upstream in the extraction rather than in B1.

The other seven are range ends that run past the end of their chapter.
`Gn 6,12-32` against a chapter of 22 verses, `Is 53,12-14` against a chapter of
12. The upstream extractor recovers the start of a range from a link and the end
from display text, and its own docstring says so. That recovery is what fails.

They ship as orphans with a reason, the way B1 and B2 handle it. Clamping a
range end to the last verse of the chapter would be authoring data, and this
repository does not author data. **Whether to fix the extractor upstream and
re-export instead is the one question this document leaves open.**

### The link is a section page plus a paragraph number, in both languages

Portuguese comes free, from the ranges in the file names.

English needs the map built once, by walking the 374 pages and recording the
first paragraph number on each. That walk is a committed script, it runs on
demand rather than in CI, and its output is committed with a checksum like every
other published file here. It self-checks: unless the first paragraph numbers are
strictly increasing and cover 1 to 2865 without a gap, the build fails rather
than publishing a map that sends a reader to the wrong page.

The script reads paragraph numbers and page boundaries. It stores no text.

### One route, mirroring the cross-references pair

`GET /v1/books/{book}/chapters/{chapter}/verses/{verse}/catechism`, shaped after
`.../cross-references` beside it, and `GET /v1/catechism?ref=` for a written
reference, shaped after `/v1/cross-references`. Same 404 reasons, same
`Cache-Control`, same resolution path.

The response carries paragraph numbers and links. It carries no title, no first
line, no summary and no snippet, and a test asserts that the response model has
no field that could hold one.

### The licence line is its own

`LICENSE` grows one row in its data section, naming the citation index, its
upstream and the basis. `LIMITS.md` grows a section saying the basis here is
thinner than for anything else in the repository, and why.

## Boundaries

No Catechism text. Not a paragraph, not a title, not a first line, not a
summary, not an extracted snippet. If a reader can learn what a paragraph says
without leaving this dataset, the line was crossed.

No canon law and no magisterial documents.

No commentary on a citation.

No search over the index. B9 searches text and there is no text here.

## Verification

Test driven on the resolution from verse id to paragraph list, the same as B4
anchor resolution.

Three checks that are not tests.

The link shape was verified against the live site, above, before anything was
built. That criterion is already met and this document is the record.

One built link is opened against the live site and returns the page holding that
paragraph.

A sample of citations is read by hand against the printed Catechism, with the
sample size and the error rate recorded whatever they turn out to be. The two
Judith labels are already known defects and the sample measures whether they are
alone.

## The question this document leaves open

**The nine unresolved labels.** Ship them as orphans, which is what this document
assumes and what criterion 8 literally asks for. Or fix the two book codes in the
upstream extractor, re-export, and ship seven orphans instead of nine. The fix is
one line in a file this repository does not own, and taking it means the export
here waits on a change over there.

The provenance question was raised and withdrawn. The citation graph is the same
fact whoever transcribed it, what decides whether it is right is the hand check,
and the upstream name is one line in `PROVENANCE.json` rather than a decision
about scope.
