# Decisions

The hard calls, each with the option that lost and what the choice costs. A
decision with no loser is a preference, and a preference does not need a
document.

Written when the call is made rather than reconstructed afterwards.

## The dataset is exported rather than regenerated

Decided 2026-08-02, while scoping B1.

The corpus, the canon and the versification spine already exist in the private
repository this work is extracted from. They were built there, normalized there
and tested there. This repo takes the finished data through a committed export
script and publishes it. It does not scrape, it does not read upstream dumps,
and it does not reimplement the 1956 orthography allow-list.

**What lost.** Porting the generator. Every source dump would come here, the
build chain would be rewritten in Python, and `make` would rebuild the dataset
from raw sources on any machine. That is the stronger claim and it is the one I
wrote into the roadmap first. It also puts a second implementation of extraction
and normalization next to the working one, and two implementations of the same
rules drift apart eventually. The person who finds out is a reader holding two
verse numbers that disagree.

**What it costs.** A stranger who clones this repo cannot rebuild the dataset.
The export needs the private repo and they do not have it. The reproducibility
gate stops being regeneration, and claiming otherwise would put a line in the
README that the first curious reader disproves in ten minutes.

**What replaces it.** Two checks that prove two different things, and the
difference matters enough to write down.

Every published file ships with a checksum and a provenance record naming its
source, the commit it came from, and the date it was exported. CI recomputes the
hashes on every push, on a clean checkout, with no access to the private source.
That catches a truncated file, a bad merge or a partial commit. It does not catch
a deliberate edit, because the data and the hash are both committed here and
whoever edits a verse can recompute the hash. A self-referential checksum is an
integrity check and never an authorship check.

Catching a hand edit needs an independent source, which is what the regeneration
diff had. So the second check re-runs the export where the private repo lives, at
the commit the provenance record names, and diffs it against what is committed
here. That one has teeth and it cannot run on a fork.

A first draft of this entry said the checksum proved nobody edited the corpus by
hand. It does not, a review caught it, and the sentence is corrected rather than
quietly deleted.

The cost goes in `LIMITS.md` when that file lands in B7. A stranger can verify
integrity and cannot verify authorship, and that is the honest shape of it.

## The spine is a superset of the schemes rather than their intersection

Decided 2026-08-02, while implementing B1, and inherited from the working
implementation rather than invented here.

Editions disagree about how many verses a chapter has. The Vulgate numbers
genealogies and psalm titles the modern editions fold away, so any single
numbering used as the backbone silently loses whatever the others carry.

The rule is one line. For each chapter of the Old Testament the spine holds the
larger of what `org` has and what the Vulgate has. It never reduces. The New
Testament is left exactly as `org` numbers it.

**What lost.** The intersection, meaning only the addresses every scheme agrees
on. It is the safe-sounding option and it is the one that throws away data. A
verse that exists in the Vulgate and not in a modern edition has nowhere to
live, so the Latin corpus arrives and the backbone refuses it. This project
exists to carry the books other datasets drop, and starting from the smallest
common shape would repeat that at the level of the verse.

**What also lost, and it is the subtler one.** Extending from the raw Vulgate
count instead of the remapped one. The Vulgate and `org` disagree about
boundaries as well as cardinality, Genesis 31:55 being Genesis 32:1 in the
other, and a raw extension reads that as Genesis 31 needing an extra verse. The
spine would grow a slot nothing means, and the per book mode detection below
would then measure against a chapter that was bumped for no reason. So the
Vulgate maximum is taken after mapping onto the spine, which leaves only genuine
cardinality to extend anything.

**What it costs.** The spine is mixed rather than uniform, and nobody can point
at one edition and say the numbering follows it. The Psalter ends up in Vulgate
numbering and Joel and Malachi end up in `org`, both as results of the rule and
neither as a rule of its own. It also means a version can leave addresses
unfilled, and three of them do. 69 for the Clementine Vulgate, 81 for the
Douay-Rheims, 282 for Matos Soares, against 35845 slots. An intersection would
have reported zero unfilled by having refused the verses in the first place.

Append-only from here. A published address never changes meaning.

## The remapping mode is decided per book by counting, not by a fixed table

Decided 2026-08-02, while implementing B1.

The Copenhagen table maps Vulgate coordinates to `org`. Applying it everywhere
is wrong, because the spine is mixed and the Psalter already stands in Vulgate
numbering. Applying it nowhere is wrong for the same reason from the other side.

So each book is asked rather than told. Run every verse the Vulgate declares for
that book both ways, count how many land on a real spine address untouched and
how many land there after the table is applied, and keep whichever loses less. A
tie keeps the identity, because the table is the intervention and an
intervention that buys nothing should not happen.

**What lost.** A committed list naming which books remap. It reads better, it is
one file a reader can check, and it is a second source of truth that goes stale
the first time the spine moves. The spine is append-only and the mode is derived
from it, so a list would have to be re-derived by hand on every extension and
would be wrong quietly rather than loudly.

**What it costs.** Which books remap is not visible by reading. It has to be run.
The conformance corpus pins the modes that matter so the counting cannot drift
without a test saying so, and the psalm mapping, which is the case anyone will
actually hit, is published rather than left to be inferred.

## An address with no slot is dropped and reported, not accommodated

Decided 2026-08-02, while implementing B1.

The mapping function can always be made to succeed. Widen the spine until every
declared address fits and the orphan count goes to zero.

It goes to zero by changing what the dataset claims to be. 3208 Vulgate
addresses have no slot, and 3039 of them are addressed to a book the spine does
not carry as a book. Two groups, and the difference matters.

2286 belong to books the Church does not receive as Scripture at all. Second
Esdras contributes 942, Fourth Maccabees 482, First Esdras 451, Third Maccabees
228, then Sixth Ezra, the Letter to the Laodiceans, the Prayer of Manasseh and
Psalm 151. Holding those means publishing a canon of more than 73 books inside a
dataset whose first sentence says 73.

The other 753 are canonical text with no book of its own here. Greek Esther,
Greek Daniel, Susanna, Bel and the Dragon, the Song of the Three and the Letter
of Jeremiah are Scripture, and the spine carries them inside Esther, Daniel and
Baruch, which is where the Catholic canon puts them. Giving them separate books
would match the Copenhagen table and contradict the canon the project is named
after.

The remaining 169 are the honest ones and each has a cause. 147 are Vulgate
psalm titles addressed at verse 0, which the spine does not number. 13 are
Sirach 52, the Prayer of Solomon that the Vulgate appends and the Catholic canon
does not carry. 1 is Jonah 1:17, which is Jonah 2:1 in the Hebrew and in the
Vulgate and which the mapping refuses rather than guesses. The last 8 are single
verses at the end of a New Testament chapter, and those are the sharpest thing
in this entry.

**Those 8 are the cost, stated exactly.** Matthew 14:36, Acts 3:26, Acts 15:41,
Galatians 1:24, 2 Thessalonians 2:17, Hebrews 12:29, 1 Peter 1:25 and
Revelation 7:17. The superset rule stops at the Old Testament, so a Vulgate New
Testament chapter carrying one more verse than `org` orphans instead of
extending the spine by one slot.

**What lost.** Extending the spine to hold them, which is eight slots and would
read as a rounding error. The New Testament numbering in this spine is the one
liturgy, cross-references and the Catechism cite. Bending it to the Vulgate for
eight verses breaks every citation arriving from outside, in exchange for eight
addresses that the Latin can reach through its own scheme anyway.

**What it costs.** A Latin apparatus pointing at one of those eight gets an
orphan back rather than a verse. `orphans.json` publishes all of it by book and
by reason, and `LIMITS.md` carries the table, because a failure mode counted and
published is worth more than a zero that was bought.

## Inverting the scheme table prefers the origin the spine can hold

Decided 2026-08-02, while implementing B1.

The Copenhagen table runs Vulgate to `org`, and reading `org` needs the other
direction, so the table gets inverted. Inverting is not free. The table merges
verses and it reaches the same target from more than one origin, which leaves
157 `org` addresses with two or more declared Vulgate origins. Something has to
choose.

This repo keeps the first declared origin, unless that one has no slot on the
spine and a later one does. Then the later one wins.

**What lost.** Keeping whichever origin the file listed last, which is what
falls out of building the index without thinking about it and what the source
implementation does. It is arbitrary in a way that shows: the Song of the Three
is declared from both `DAN` and `DAG`, only `DAN` exists on the spine, and last
wins picks `DAG`. Sixty five addresses then orphan while the table itself says
where they go.

**What it costs.** A divergence from the working implementation, which is the
thing this port is most careful to avoid. It is deliberate, it is one rule in
one constructor, and a conformance case pins it so the two cannot drift quietly.

**The numbers, measured rather than estimated.** The inverse index only fires on
books the spine numbers in Vulgate, so the population is smaller than the raw
table suggests. 135 `org` addresses arrive ambiguous. In 103 of them exactly one
declared origin has a slot on the spine and the rule recovers it. In 23 no
origin has a slot and the address orphans either way. In 9 more than one origin
has a slot.

A first draft of this entry counted 157 and 105, which were measured across the
whole table without the mode gate that decides whether the index is consulted at
all. The corrected figures are above.

**Those 9 stay ambiguous and get recorded.** Six are the same merge shape, where
the Vulgate splits one `org` verse in two and the first is what an apparatus
means. Three are chapter boundaries between textual traditions, and `BEL 1:1` is
the clearest of them: Daniel 13 ends at 64 in most editions and at 65 in the one
that carries the transition into Bel, so the table declares that verse and
Daniel 14:1 as the same address. Both are legitimate and neither is a mistake.

The tempting move is a tie-break that reads nicely, nearest verse number or
whichever keeps the sequence contiguous, which would pick Daniel 14:1 and feel
better. That is choosing a textual tradition with a heuristic and calling it
arithmetic. B1 exists to stop exactly that, so the rule stays blunt and all nine
go into the conformance corpus naming both candidates.

## The mapping layer decides what is an orphan

Decided 2026-08-02, while implementing B1.

The source implementation keeps its scheme maps pure and detects orphans in the
importer, so one place decides and the maps stay simple. That is the right call
there because an importer exists.

Here it does not. The importer is B2 and B1 has to publish `orphans.json`, so
detection moves into the mapping layer and the scheme maps stay pure below it.

**What lost.** Waiting for B2 and keeping the shape identical to the source. It
would leave B1 unable to meet its own acceptance criteria, which is a high price
for a structural match.

## Reading a spine address back into a scheme verifies itself

Decided 2026-08-02, while implementing B1.

The epic asks for the mapping in both directions. The forward direction reads a
scheme address onto the spine and the reverse reads a spine address back out.
They are not symmetric, because the remap table is not a bijection.

Run backwards naively, the table produces addresses that look right and are not.
The spine holds `PSA.115.1`, reading it back gives `org` 115:1, and `org` 115:1
is a different psalm coming from `PSA 113:9`. Sixty two addresses behaved that
way across the four schemes.

So the reverse direction computes its candidate and then maps it forward again,
and it only returns the candidate if it lands where it started. Anything else is
an orphan.

**What lost.** Returning the candidate and documenting the caveat. It would have
been less code and a smaller diff, and it would have handed a consumer a wrong
verse address with nothing to tell them. A wrong answer someone trusts is worse
than an absent one, and this is the epic whose whole point is that distinction.

**What it costs.** Twenty one addresses have no Vulgate reading and forty one
have no `org` reading. Douay has none, because it touches only Joel and Malachi
and both are clean. Those numbers are pinned in a test rather than tolerated.

## Provenance records the source commit date and never the run date

Decided 2026-08-02, in B1, and it stayed in B2.

Every published file names when its source was committed. None of them names
when the export ran.

**What lost.** The export date, which is what `CLAUDE.md` and the B2 epic both
ask for by name, and which is what a reader expects to find in a provenance
record.

It cannot coexist with the other requirement in the same list. Running the
export twice at one source commit has to produce byte identical output, because
that is what makes the comparison against a fresh export mean anything. A run
timestamp makes every rerun differ, and then the only check in this repo that
catches a hand edit reports a difference every single time.

Between a date that says when a command ran and a date that says which version
of the source these bytes came from, the second is the one a consumer can act
on. The first answers a question nobody asks.

**What it costs.** Two documents ask for something this repo does not provide,
and both are now corrected rather than left to imply it. A reader who wants to
know when the export ran has the git history of this repo, which is a better
answer anyway because it is signed and ordered.

## An unresolvable reference is a value, not an exception

Decided 2026-08-02, while implementing B1.

The source parser throws on an unknown book or a malformed reference. Here both
come back as values carrying the reason.

**What lost.** The exception, which is idiomatic in the framework the original
lives in and which makes the happy path read cleanly.

The rule in `CLAUDE.md` is that a domain error the caller can act on is a return
value and an exception is for a genuine fault. A reader typing a book name that
does not exist is not a fault. It is the most ordinary thing that happens to a
reference parser, and B3 has to turn it into a structured HTTP error rather than
a stack trace.

## The API returns its models directly and wraps nothing

Decided 2026-08-02, while specifying B3.

Every route returns its typed model. There is no `data` envelope.

**What lost.** The envelope the ported implementation uses, which is a Laravel
convention and which every response there carries. Keeping it would have made
migration a rename rather than a reshape.

It puts one polymorphic generic over the whole published document, and a
consumer unwraps every response before reading it. FastAPI generates a clean
schema from a returned model and a wrapper is the one thing that makes it
unreadable.

**What it costs.** A consumer moving from the private API rewrites its response
handling. That is one of two breaking differences and the other is below.

## The verse id on the wire is the published string

Decided 2026-08-02, in B3, following the identity split B1 made.

Responses carry `"id": "PSA.50.3"`. The private API carries
`"verse_id": 30489`.

**What lost.** The integer, which is smaller, which sorts, and which every
existing consumer of the private API already stores.

It is an artifact of the order a seed ran in. B1 decided it stays internal
because a published contract that freezes it can never be undone, and the dense
integer still exists inside this repo where the range arithmetic needs it.

**What it costs.** Every consumer migrating breaks on this field, and it breaks
loudly rather than quietly, which is the only reason it is acceptable.

## Storage is SQLite even though nothing here searches yet

Decided 2026-08-02, in B3, and argued against in review before it stood.

The API reads a SQLite file built from the published corpus by a committed
script. The file is derived, reproducible, and not committed.

**What lost.** Reading the published JSON into memory. `corpus.load` already
exists, is already cached, already guards its argument against a path, and costs
34.8 MB retained and 52.4 MB peak, measured rather than estimated. It is one
line and it serves every route in B3.

The reason to pay now is B9. Search needs FTS5, FTS5 needs the store, and
changing the store under routes that already shipped is the expensive version of
this decision rather than the cheap one. The seam costs less before there are
consumers.

**What it costs.** A build script, a Makefile target, two ignore file entries, a
Dockerfile layer and a CI step, for an epic that does no searching. The review
called that gold plating and the argument is recorded here rather than won
quietly. If B9 arrives and FTS5 does not need this shape, that is the entry that
gets written next.

## Reason codes are a closed set and the message is a courtesy

Decided 2026-08-02, in B3.

Errors go under FastAPI's own `detail` key with a typed body inside. `reason`
comes from an enum of eleven members, four of them new here and the rest carried
through from B1 unchanged.

**What lost.** RFC 9457 problem details, which is the broader standard. Adopting
it means either overriding FastAPI's built in validation error shape or
publishing two error shapes in one document, and neither is worth the
conformance.

Also lost, a `message` a caller could branch on. It is prose, it is English, and
it is free to change. A caller reading it breaks when somebody edits a sentence.

**What it costs.** A consumer that already parses problem details has to special
case this one API.

## An incoming reference says which numbering it was written in

Decided 2026-08-02, in B3, after a review found the gap.

`passage` and `resolve` take `scheme`, defaulting to `spine`.

**What lost.** Silence, which is what the first draft of the spec had. `Sl 51,1`
parses, lands on the spine, and returns Psalm 51, which is `org` Psalm 52. A
reader asking for the Miserere gets the next psalm with a 200 and nothing
anywhere saying so.

The roadmap opens by naming that exact failure as the reason this repo exists,
and the spec had spent a section on printing both numbers on the way out and
nothing on reading them on the way in.

**What it costs.** Four values on a public surface from the first day, and three
of them go through B1 code carrying a known defect. Two wrong answers are pinned
by a test and whether more exist in the other 72 books is not measurable here.
`LIMITS.md` says so.

## A whole chapter reference is refused rather than answered

Decided 2026-08-02, in B3.

`Sl 23` and `Ex 13-14` come back 422 from `passage` and `resolve`, naming the
shape that was refused and pointing at the chapter route.

**What lost.** Answering them. The parser already reads `Ex 13-14` as chapter 13
with chapter 14 dropped, so answering would be a 200 returning less than was
asked for, with nothing to tell the caller. A wrong answer someone trusts is
worse than an absent one, which is the rule B1 was built on.

**What it costs.** A caller pasting a chapter reference into `passage` gets an
error where a helpful API would guess. Guessing is what this repo does not do.

## Commentary hangs off the verse id and the schema did not move

Decided 2026-08-02, in B4.

Two new tables plus a source table, anchored on the same `canonical_order` the
spine already publishes. No column was added to `spine` and no column was added
to `texts`.

**What lost.** Nothing was seriously proposed against it, and that is the point.
The claim B1 made was that a dense integer is a usable anchor for anything that
attaches to a verse, and a claim like that is worth exactly as much as the first
thing built on it. Two independent layers arriving without the addressing moving
is the evidence, and if the schema had needed a column, this section would be
recording that instead.

**What it costs.** A coverage query rather than an equality. A note spans a range
of addresses and finding the notes on a verse is a range test in both directions,
which is a different index and a different cost from reading a verse.

## The commentary route takes no version

Decided 2026-08-02, in B4.

`/v1/books/{book}/chapters/{chapter}/verses/{verse}/commentary` sits beside the
reading routes and not underneath a version segment.

**What lost.** Nesting it under `/v1/versions/{version}/...` for symmetry with
everything else. The symmetry would have been a lie. A Haydock note on John 3:16
is the same note whichever translation is on screen, and putting a version in the
path claims the answer depends on one. It would also have multiplied the cache
surface by the number of published versions for identical bytes.

**What it costs.** Two route shapes on one API, and a reader who has learned the
version prefix has to notice this one does not take it.

## The body is a row per language rather than a column per language

Decided 2026-08-02, in B4.

`commentary_body` is keyed on the entry and a language tag. The private original
carries `body_html` and `body_html_translated` side by side.

**What lost.** The simpler two column shape, which is one fewer table and one
fewer join. It also encodes today's two languages into the schema, so a Spanish
Haydock or an English Catena would arrive as a migration rather than as rows.

**What it costs.** A join on every commentary read, and a response assembler that
groups rows instead of reading fields.

## Plain text is derived at build time and never published

Decided 2026-08-02, in B4.

The published file carries HTML only. The build strips the markup and stores both.

**What lost.** Publishing what the source database holds, which is both columns
already computed. That would have been 15.5 MB of a file that is already 20 MB,
for a column any consumer can compute from the one beside it with a regular
expression.

**What it costs.** A consumer reading the published JSON rather than the API has
to strip the tags. `LIMITS.md` records that the stripping is a regular expression
over a corpus known to contain two tags, and that a third tag would survive it.

## The coverage query carries a floor, and the floor was measured

Decided 2026-08-02, in B4.

Finding the notes covering an address is `first_order <= wanted AND last_order >=
wanted`, plus `first_order >= wanted - widest`, where `widest` is the widest
published entry and is computed at build time.

The floor changes no result, because no entry is wider than the widest entry. The
private repository added it because MySQL abandoned the composite index without
it. Whether SQLite behaved the same way was left open in the plan and measured
rather than assumed, at the last address in Revelation.

```
bare    0.9213 ms   SEARCH commentary USING COVERING INDEX commentary_coverage (source=? AND first_order<?)
floor   0.0065 ms   SEARCH commentary USING COVERING INDEX commentary_coverage (source=? AND first_order>? AND first_order<?)
```

**What lost.** Dropping the floor as MySQL specific, which is what the plan
expected to happen. SQLite uses the index either way and still walks it from the
first entry of the source, so the open range is 140 times slower at the end of
the canon and free at the start.

**What it costs.** A second query to read `widest`, and a bound that a reader has
to be told does not change the answer. A test compares the floored result against
the unbounded one over a thousand addresses rather than arguing it.

## The two backwards notes are clamped and not repaired

Decided 2026-08-02, in B4.

Two entries run from a higher address to a lower one, because the printed labels
`26-7` and `73-4` elide the second number and the extraction read them literally.
The export sets the end equal to the start.

**What lost.** Reading `27` and `74` out of the label, which is what the source
means and which would restore the note on both verses. It is also this repository
producing a value no source holds, in a dataset whose whole claim is that no
value here was authored by hand. A rule that bends for a guess this good does not
hold for a guess that is merely good.

**What it costs.** Matthew 15:27 and Luke 1:74 read as having no note. Two
conformance cases pin the addresses so the day the extraction is fixed upstream
the suite says which side moved.

## The build runs ANALYZE, because the planner was guessing wrong

Decided 2026-08-02, in B4.

`build()` ends with `ANALYZE` before the commit.

Without statistics SQLite chose to scan all 41410 commentary bodies, 16 MB of
text, as the outer loop of the coverage join, rather than driving it off the
index the schema exists to provide.

```
without   SCAN commentary_body                                          9.548 ms
with      SEARCH commentary USING INDEX commentary_coverage             0.027 ms
          SEARCH commentary_body USING PRIMARY KEY (commentary=?)
```

Over HTTP that is a commentary read at 15 ms falling to 4.4 ms, which is where
the B3 verse read already sat.

**What lost.** Hinting the join order with `CROSS JOIN`, which fixes this one
query and leaves every future query guessing. And doing nothing, which was the
state this was found in, by measuring rather than by a complaint.

**What it costs.** A second of build time and a `sqlite_stat1` table in a file
that is derived anyway. The corpus is static, so the statistics are computed once
and cannot go stale.

## The allusion set ships and the Ave Maria apparatus does not

Decided 2026-08-03, in B4, by the author.

The 292 pairs of New Testament to deuterocanonical addresses are published. The
879 entries scraped from the Ave Maria margins are not.

**What lost.** Refusing both, which is what the epic's criterion says literally
and what the first reading of it recommended. The measured cost of refusing the
allusion set was cutting deuterocanonical linkage from 920 rows to 255, a 61%
loss, in an epic whose stated problem is that the deuterocanonical books are the
ones nothing connects.

The distinction that decided it: the allusion set reproduces no text, no note
and no editorial prose, so what would be copied is a list of address pairs. A
bare pair of Scripture references is a fact about Scripture. The Ave Maria set
is the editorial selection of a protected 1957 edition whose text this
repository already refuses, and it contributes one deuterocanonical link.

**What it costs.** A rights position taken on a reading rather than on advice.
`LIMITS.md` says so in those words and names the cost of being wrong, which is
673 rows and a rebuild.

## The read cuts at thirty per address and the weight stays off the wire

Decided 2026-08-03, in B4.

`primary` is published, true at weight 20 or above. The weight itself is not.

**What lost.** Publishing the weight, which is the more transparent option and
also the more misleading one. It is a vote count for OpenBible, a constant of
100 for the Douay margins and a constant of 90 for the allusion set, so the three
are not comparable and a consumer sorting by it across sources would be doing
arithmetic on three different units.

**What it costs.** A consumer cannot rank inside a source. Both numbers are
ported rather than derived and `LIMITS.md` says so instead of dressing them as
analysis.

## Scattered addresses are fetched one by one and contiguous ones as a range

Decided 2026-08-03, in B4, after measuring.

`addresses_at` joins `addresses_between` rather than replacing it.

A cross-reference target set runs from Genesis to Revelation, so the range that
covers it is the whole spine. Reading Genesis 1:1 as a range cost 35845 rows to
answer 30 and took 35 ms over HTTP, against 2.8 ms once the addresses were asked
for individually.

**What lost.** One function for both, which is tidier and wrong. A passage is
contiguous by construction and a reference target set is not, so the shape of
the read follows the shape of the data rather than the shape of the code.

**What it costs.** A bind parameter list, chunked at 900, because a passage at
the 500 verse cap can want fifteen thousand of them.

## The artifacts are split from the corpus and not from the source

The epic said the static files come out of the B2 export. They come out of what
B2 already committed instead.

The B2 export needs the private source database, so an artifact produced that way
is one more file a stranger has to take on trust. Splitting downstream of the
committed corpus means `scripts/build-artifacts.py` runs on a clean checkout with
no credentials, and anyone can regenerate all 371 files and diff them.

What lost is a single pipeline. There are now two steps where there could have
been one, and a corpus that moves without `make artifacts` afterwards leaves the
two trees disagreeing until CI catches it.

## The tag carries the version and the path does not repeat it

`@v1.0.0/data/versions/matos-soares/books/SIR.json` rather than
`@v1.0.0/data/v1/versions/...`.

Two version numbers in one URL invite the question of what happens when they
disagree, and the answer would have to be that one of them is decoration. The
git ref is the pin, it is what jsDelivr caches as immutable, and it is the thing
a consumer actually controls.

Below the tag the path is the HTTP API's own vocabulary. Someone who learns
`/v1/versions/{version}/books/{book}` can guess the file, and the reverse holds.

## Rights travel inside every published file

An HTTP response can carry attribution in an envelope the route controls. A
static file has no envelope. It gets copied into somebody's project, renamed,
committed, and it keeps whatever it carried at the moment it was downloaded.

So the licence, the basis and the required notice sit inside all 365 book files.
The OpenBible CC BY attribution is in all 73 cross-reference files even where the
book draws on no OpenBible reference, because a consumer holding one file should
not have to fetch a second one to learn the terms.

What it costs is the same few hundred bytes repeated 365 times. That is the
cheapest insurance in this repository.

## Immutability is enforced by a ruleset rather than promised in prose

A git tag can be moved and a README saying it will not be is worth what the
author's memory is worth in three years.

A repository ruleset on `refs/tags/v*` blocks deletion and update, with no bypass
actors, which is the same mechanism protecting `main`. Both were verified by
attempting the forbidden thing and reading the refusal rather than by trusting
the API's response.

The alternative was a release checklist. A checklist is a person remembering, and
the whole point of publishing an immutable URL is that consumers do not have to
rely on that.

## Granularity stops at the book

Per chapter files would be smaller. Sirach 24 is 3 KB against 106 KB for the
book.

They would also be roughly four thousand files against three hundred and
sixty five, and the epic asked for per book. The median book is 48 KB, which is
a page weight nobody notices, and the gain is real enough that the path shape
was left able to accommodate it later.

## `versification.json` is published as `spine.json`

The exporter's filename says versification and every document in this repository
says spine. The published name is the word a reader has already met.

It is the only artifact whose name differs from its source, and the mapping is a
literal in the generator rather than a transformation, so the file itself is
byte identical to what it was copied from.

## The rate limit counter is a file, not a dictionary

Decided 2026-08-04, while implementing B8.

Counting per address in memory is one line and it is wrong the moment the
service runs more than one worker. Each process gets its own tally, so four
workers enforce four times the configured limit, and the effective number is
whatever the deployment happens to be running.

So the counter is SQLite, in its own file, shared by every process on the box.

**What lost.** A dictionary. It is faster, it needs no file and no cleanup, and
the number it enforces is unknowable without reading the deployment. A limit
nobody can state is not a limit.

**What it costs.** 15.5 microseconds per counted hit, measured, against a verse
read that costs 1.94 milliseconds. Two windows are 31 microseconds, which is
1.6% of work the request was already doing. That is what made this the boring
choice rather than the expensive one.

**It is not the corpus database.** That one is opened read only and nothing
writes to it, which is a claim `CLAUDE.md` makes about this whole repository.
The limiter has its own file, its own connection and its own schema, so the
read only claim about published Scripture stays literally true.

## The window is fixed rather than sliding

Decided 2026-08-04, while implementing B8.

A fixed window is one integer per address per window. A sliding window needs the
timestamp of every request in the period, which for 1000 an hour is a thousand
rows per address instead of one.

**What lost.** Correctness at the boundary. 60 requests at 11:00:59 and 60 more
at 11:01:00 is 120 in two seconds and breaks no rule.

**What it costs.** Exactly that, and `LIMITS.md` publishes it rather than hoping
nobody notices. The limit exists to stop a loop with no sleep in it, and such a
loop is refused within the first second either way. Paying a thousandfold in
storage to close a hole that only a deliberate attacker would aim at, on a free
read only dataset, is buying the wrong thing.

## No proxy is trusted until one is configured

Decided 2026-08-04, while implementing B8.

Behind a reverse proxy, the socket address is the proxy and every caller in the
world lands in one bucket. The fix is `X-Forwarded-For` and that header is
written by whoever is calling.

Reading it unconditionally is worse than having no limit at all. Anyone sending
a fresh value per request gets a fresh bucket every time and walks straight
through, while an honest client stays counted. That is a limiter that only
limits people who are not attacking you.

So the header is read only when the connection itself came from an address
configured as a trusted proxy, and the default configuration trusts nothing.

**What lost.** Defaulting to the first entry of the header, which is what most
examples show and what makes the limiter work out of the box behind a proxy. It
works by being bypassable.

**What it costs.** B8 ships enforcing on the socket address, which is correct
without a proxy and wrong behind one. B6 sets the value when Caddy lands, and
until then the setting is empty rather than guessed. A limiter that is briefly
too strict for proxied callers is recoverable. One that was never enforcing is
found out later.

Within the header, the answer is the rightmost entry that is not itself a
trusted hop, because each hop appends and the left end is the client's own
claim. An entry that is not an address stops the walk, since anything a trusted
proxy appended is a real address, and stepping over garbage to reach a value the
client supplied is the same hole through a side door.

## The middleware is raw ASGI rather than BaseHTTPMiddleware

Decided 2026-08-04, while implementing B8, on a measurement rather than a
preference.

Starlette's `BaseHTTPMiddleware` is the documented way and it wraps each request
in a task group and a streaming response. Interleaved against the bare
application it added a repeatable 330 microseconds. The raw ASGI version was
indistinguishable from zero, showing negative in one run, which is the harness
noise rather than a speedup.

**What lost.** The readable one. `dispatch` with a request object beats reading
byte tuples out of a scope, and the 429 would have been a `JSONResponse` return
instead of two hand written send calls.

**What it costs.** The middleware speaks ASGI, so headers are byte pairs and the
refusal is assembled by hand. It also sits outside the application, which means
the exception handlers never see it and a `raise ApiError` up there would escape
as a 500. The refusal is therefore built rather than raised, and a comment in
the code says why so nobody helpfully refactors it.

The number that decided it: 330 microseconds of wrapper around 15.5 microseconds
of work is the wrapper costing twenty times what it wraps.

## Keys come only when per address limiting has visibly failed

Decided 2026-08-04, while implementing B8, and the trigger is written down so
the decision is not remade from mood.

No key, no account, no signup. The epic is explicit and this records what would
have to be true to change it.

**The trigger.** Sustained abuse that per address limiting cannot see, which in
practice means one of two things. A distributed source, where thousands of
addresses each stay under the limit and the aggregate still saturates the box.
Or a shared exit, where a university or a carrier NAT puts real readers behind
one address and the limit stops the wrong people.

**What happens then, and only then.** A key issued self service against an
email, with no password and no session, used to raise a limit rather than to
grant access. Everything stays readable without one.

**What lost.** Issuing keys now, which is the ordinary shape of a public API and
which would let the limits be generous. It is an identity, an identity needs a
store, a store of emails needs a policy, and this project has no users and no
login. Building all of it against a threat nobody has observed is the gold
plating `CLAUDE.md` exists to refuse.

## The query is compiled here rather than handed to FTS5

Decided 2026-08-04, while implementing B9.

`MATCH` takes an expression language with operators, column filters and its own
quoting. Passing what a reader typed straight into it is the shortest possible
implementation and it turns ordinary input into a 500. Ten realistic queries went
in raw and six came back a syntax error, including `Deus (pai)`, `o Senhor's` and
`Jo 3:16`, which is how half the world writes a reference.

So `src/catholic_bible/search.py` parses the query and builds the expression.
Double quotes mean a phrase, bare words are all required, a trailing star is a
prefix, and every other character is punctuation the reader did not mean as an
operator.

**What lost.** The full FTS5 grammar. `NEAR`, boolean `OR` and column filters are
real tools and every one of their failure modes would have become a public error
on an endpoint with no authentication and no support channel. `NEAR` is also a
word in this corpus, and a bare `NEAR` reaches 217 verses.

**What it costs.** A reader who knows FTS5 cannot use it. Nobody has asked, and
the reverse cost was measured.

**A query that survives parsing with nothing left is a 422.** `!!!` is not a
question about the corpus, so answering it with an empty result would claim the
corpus lacks a word that was never a word.

## The highlight marks the token, not the string the reader typed

Decided 2026-08-04, while implementing B9.

The ported implementation highlights by replacing the literal term in the text
after the match is found, and `BIBLE_API.md` warns that the tags may be absent
when the match came from accent folding. Search `coracao`, find the verse that
holds "coração", get no `<em>`.

`snippet()` marks the token the index actually matched, so the accented spelling
is highlighted by an unaccented query. This is a divergence from the port in the
reader's favour and it is written down rather than absorbed, because a client
built against the documented caveat is a client built to expect worse.

## `commentary_body` gave up WITHOUT ROWID and the file got smaller

Decided 2026-08-04, while implementing B9.

An FTS5 external content index addresses its content table by rowid. `texts` and
`commentary` keep theirs for exactly that reason, written into `build.py` during
B2. `commentary_body` was `WITHOUT ROWID` and out of reach.

Measured on the built database.

| Database | Size |
|---|---|
| As B8 left it | 93.1 MB |
| The same file, vacuumed | 91.5 MB |
| With `commentary_body` keeping its rowid | 68.2 MB |
| With both search indexes on top | 88.0 MB |

A `WITHOUT ROWID` table stores the whole row inside the primary key B-tree, and
this row carries two large text columns. That cost 23 MB. Both indexes cost 18.
B9 adds full-text search over Scripture and over 41410 commentary bodies and
leaves the file smaller than it found it.

*The last row said 86.1 MB until a review checked it. That figure came from a
vacuumed scratch copy and the build does not vacuum, so it was 1.9 MB under a
number the argument rests on. `scripts/build-db.py` produces 87965696 bytes.*

**What lost.** Nothing. The address every reader uses is still
`(commentary, language)`, still unique and still indexed, and no query above the
storage layer changed. The existing commentary tests were the regression test.

## Two search routes rather than one ranked list

Decided 2026-08-04, while implementing B9.

Scripture and commentary are searched at `/v1/search` and
`/v1/search/commentary`.

A single merged endpoint would rank a `bm25` score computed over 107103 verses
against one computed over 41410 notes. Those numbers share a name and not a
meaning, and paging through the result would page through an order nobody can
explain.

**What lost.** One request instead of two for a reader who wants both. Two
answers are also two cache entries with different lifetimes and different
filters, which is the shape a client wants anyway.

## The distribution is `the-catholic-bible` and the import is not

Decided 2026-08-04, while specifying B10.

`catholic-bible` on PyPI is somebody else's project. Robert Colfin published
0.1.0 on 2026-03-30 and 0.2.0 a month later, and it scrapes `bible.usccb.org`.
This repository declared that exact name in `pyproject.toml` and had never
published, so the first tag would have failed on an authorisation error against
a stranger's project.

The same name is used on npm, where nothing held it, so a reader who finds one
can guess the other. `catholic_bible` stays the import, so no source file moved.

**What lost.** `catholicbible`, which is the same name with the hyphen removed
and reads as a typosquat. `catholic-canon` and `deuterocanon`, which each name
a part of this and would need explaining every time.

## One Python distribution carrying everything, against the epic's two

Decided 2026-08-04, at the B10 spec gate.

B10 describes two packages with two jobs, data on npm and code on PyPI. Under
that split the wheel would be 84 KB and `pip install` would stop giving anyone
a running service.

The wheel is 13 MB instead, and 49.3 of its 49.4 unpacked megabytes are corpus.
That is the price for a reader who only wanted to parse `Eclo 24,1`, and it
buys a reader who wanted the whole thing an install instead of a checkout.

**What lost.** Fidelity to the epic's framing, and 13 MB. A second Python
distribution would have kept both, at the cost of two versions to hold in
lockstep and a second publish job for a repository with one author.

## The database builds on a first boot rather than shipping or being asked for

Decided 2026-08-04, at the B10 spec gate.

`bible.db` is derived, so it is gitignored, so hatchling leaves it out of the
wheel. An installed copy answered 503 on `/health` and 500 on every `/v1`
route, and the message told the reader to run `make db`, a Makefile target
inside a checkout they do not have.

`catholic-bible-api` builds it when it is missing and says so. The standard
splits on whether materialising the data needs the network. Playwright and
spaCy make it an explicit command because the alternative is a surprise
download of hundreds of megabytes. Transformers and `tldextract` do it
implicitly because the work is local and cached. This is local, offline, and
ten seconds cold from bytes the reader already downloaded.

The cache path carries the version. `LIMITS.md` already has a heading called
*A stale database ships without a sound*, and a path reused across upgrades
would hand that failure to everyone who runs `pip install -U`.

**What lost.** Shipping the database costs 29 MB and publishes a derived
artifact with no checksum and no provenance record, which every other published
file here carries. A second command in the quickstart is honest and puts back
most of what the clone cost.

## The licence is MIT over the code and says so about the corpus

Decided 2026-08-04, at the B10 spec gate.

Both packages carry Scripture, commentary and cross-references. A single MIT
declaration would relicense somebody else's public domain work and drop the
attribution CC BY 4.0 requires for the OpenBible cross-references, which this
repository honours inside every published file and every API response.

`LICENSE` carries the MIT grant and a data section naming the terms per asset.
`package.json` says `SEE LICENSE IN LICENSE`, which is npm's form for a bundle
no single identifier describes, and `pyproject.toml` declares `license-files`
rather than an SPDX expression.

**What lost.** Machine readability. A single SPDX identifier is easier for a
tool to read and would have been false in one direction or the other.

## npm publishes on a token once and over OIDC afterwards

Decided 2026-08-04, while planning B10.

PyPI accepts a pending publisher, which is a trust relationship for a project
that does not exist yet, so Python is OIDC from its first byte and never sees a
token. npm has no equivalent. `npm help trust` says the package must already
exist, and it refuses the bypass 2FA tokens that continuous integration has to
use, so the credential that performs the first publish cannot perform the
configuration.

So the first release publishes to npm with a granular access token held as a
repository secret, the trusted publisher is configured against the package that
now exists, and the secret is deleted. Every release after that is OIDC on both
sides.

**What lost.** Symmetry between the two workflows, and one long-lived
credential existing for the length of one release. `release.yml` passes the
secret to a step that works without it, so the steady state needs no edit.
