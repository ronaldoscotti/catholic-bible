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
way across the three schemes.

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
