# Limits

What this repo cannot do, what it has not measured, and what it publishes
without being able to prove. Written when the limit is found rather than when
someone asks.

B2 opened this file because two of its acceptance criteria name it. B7 expands
it.

## A stranger cannot rebuild this dataset

The corpus is exported from a private repository, through a committed script,
and it is not regenerated here. That was a deliberate call and `DECISIONS.md`
carries the reasoning and what it cost.

The cost lands here. Two checks exist and they prove different things.

**The checksum check runs anywhere.** It recomputes the sha256 of every
published file and compares it to `PROVENANCE.json`. It runs in CI, on a clean
checkout, with no access to the private source, and anyone who clones this repo
can run it. What it catches is a truncated file, a bad merge, a partial commit.

**It cannot catch a hand edit.** The data and its hash are committed together,
so whoever edits a verse recomputes the hash and commits both. A self
referential hash is an integrity check and it is never an authorship check.
Nothing in this repo, and nothing a stranger can run, closes that gap.

**The check with teeth needs the private source.** `make verify-export` reruns
the export at the recorded commit, into a scratch directory, and compares byte
for byte with what is committed. A hand edited verse shows up there and nowhere
else. It needs the private repository and a running database, this project has
no self hosted runner, and so it is a documented command rather than a CI job.

A stranger can verify integrity and cannot verify authorship. Wiring the second
check to a badge and calling a green build proof would be worse than this
paragraph.

## A stale database ships without a sound

A file has a git hash. A database table does not.

`PROVENANCE.json` records the source commit, the commit date, and the sha256 of
the two input fixtures the import declares. Those plus the import code at that
commit are what produce the tables. What none of it detects is a database built
from an older commit and never rebuilt, because nothing readable from inside a
database says when it was filled.

Only the reimport half of the export check closes that, and it lives where the
private source lives.

## Two things are called the orphan rate and only one of them is measured here

The word covers two different failures and this repo can answer for one.

**A scheme address that reaches no slot on the spine.** Measured, published in
`orphans.json`, and the rest of this section is that number. Every address the
Copenhagen table declares is run through the mapping function and the misses are
counted by book and by reason.

**A source verse the import dropped before the corpus was written.** Not
measured, and not measurable from inside this repository. The import runs where
the private source lives and it discards what it could not place, so nothing
that crossed over remembers what did not. Publishing a zero would read as clean
when it means unmeasured.

### Orphans per scheme

| Scheme | Addresses examined | Resolved | Orphans |
|---|---|---|---|
| Clementine Vulgate | 39046 | 35838 | 3208 |
| `org` | 38371 | 35498 | 2873 |
| Douay | not reportable | | |

Douay has no declared coordinate space here. It arrives with the text in B2, and
a zero in that row would be a claim rather than a measurement.

| Cause | Vulgate | `org` |
|---|---|---|
| The book has no counterpart on the spine | 3039 | 2705 |
| A Vulgate psalm title, addressed at verse 0 | 147 | 147 |
| The chapter is past the end of the book | 13 | 13 |
| The verse is past the end of the chapter | 9 | 8 |

### Where the concentration is, and why

Almost all of it is one thing. The Copenhagen table names books this canon does
not carry as books, and 3039 Vulgate addresses are pointed at them.

| Book | Vulgate | `org` |
|---|---|---|
| 2 Esdras | 942 | 942 |
| 4 Maccabees | 482 | 482 |
| 1 Esdras | 451 | 426 |
| Greek Esther | 267 | 267 |
| Greek Daniel | 241 | 175 |
| 3 Maccabees | 228 | 228 |
| 6 Ezra | 141 | 141 |
| Letter of Jeremiah | 72 | 0 |
| Song of the Three | 67 | 1 |
| Susanna | 64 | 0 |
| Bel and the Dragon | 42 | 1 |
| Laodiceans | 20 | 20 |
| Prayer of Manasseh | 15 | 15 |
| Psalm 151 | 7 | 7 |

Two different causes sit in that table. 2 Esdras, 4 Maccabees, 1 Esdras, 3
Maccabees, 6 Ezra, Laodiceans, the Prayer of Manasseh and Psalm 151 are not
received as Scripture by the Catholic Church, and holding them would make the
canon larger than the 73 books this dataset claims. The rest is canonical text
that has no book of its own here, because Greek Esther lives inside Esther,
Susanna and Bel and the Song of the Three live inside Daniel, and the Letter of
Jeremiah is Baruch 6. Four of those fall to nearly zero in the `org` column,
which is the table doing its job and folding them back where they belong.

That leaves 169 orphans in books the spine does carry, and each has a name.

147 are Vulgate psalm titles addressed at verse 0, which the spine does not
number. 13 are Sirach 52, the Prayer of Solomon that the Vulgate appends. The
last 9 are single verses falling one past the end of a chapter.

`MAT.14.36` `ACT.3.26` `ACT.15.41` `GAL.1.24` `2TH.2.17` `HEB.12.29` `1PE.1.25`
`REV.7.17` `JON.1.17`

Eight of those nine are in the New Testament, and they are the only orphans this
project chose rather than inherited. The superset rule stops at the Old
Testament, so a Vulgate New Testament chapter carrying one verse more than `org`
orphans instead of extending the spine. `DECISIONS.md` says why the eight slots
are not worth the numbering, and the short version is that liturgy,
cross-references and the Catechism all cite the modern New Testament and this
spine has to keep answering them.

`JON.1.17` is the ninth and it is a different animal. Jonah 1:17 in the English
reckoning is Jonah 2:1 in the Hebrew and in the Vulgate, the spine follows `org`
and ends Jonah 1 at verse 16, and the Vulgate map reads Jonah untouched. So the
address exists in one tradition, means chapter 2 verse 1 in another, and the
mapping refuses rather than guessing. It is the same refusal the reverse
direction makes, and for the same reason.

### Unfilled, which is the same question from the other side

**Unfilled** counts spine addresses no version reached.

| Version | Published | Unfilled |
|---|---|---|
| Clementine Vulgate | 35776 | 69 |
| Douay-Rheims | 35764 | 81 |
| Matos Soares | 35563 | 282 |

The spine holds 35845 addresses. Proverbs and Sirach carry most of the
Portuguese gap, 86 and 73 verses, and the Psalter carries most of the Latin and
English one. `coverage.json` breaks all three down by book.

The epic said the Vulgate would demonstrate the spine with zero orphans and
called it a live proof inside the release. It is 69 unfilled addresses, the epic
was corrected, and no number in this repo is asserted before it is measured.

## Twelve verses of the Douay-Rheims are missing

The MIT fixture that carries both the Latin and the English leaves the English
field empty at twelve addresses, while the Latin is present at all twelve.

They are omitted from the published file rather than shipped as empty strings,
because an empty string is a lie shaped like data and a missing key is not.
`PROVENANCE.json` lists all twelve.

`2SA.13.39` `JDT.4.6` `PSA.19.10` `PSA.28.11` `PSA.150.6` `PRO.28.25`
`WIS.18.25` `ISA.46.12` `AMO.9.15` `MAL.3.12` `1TH.4.12` `2TH.2.11`

## Rights, per asset

Everything published here is public domain. The file it arrived in is a separate
question from the text, so both get an answer.

| Asset | Text | Basis | Fixture |
|---|---|---|---|
| Matos Soares | public domain | Brazilian law article 45, died 1957 with no successors | licence unstated upstream |
| Douay-Rheims | public domain | first published 1582 and 1610 | MIT |
| Clementine Vulgate | public domain | promulgated 1592 | MIT |
| Haydock, English | public domain | printed 1811 to 1814, the author died 1849 | transcription, no licence stated upstream |
| Haydock, Portuguese | machine translation of a public domain text | derived here, no third party claim | same |
| Douay cross references | CC0 | the 1582 and 1610 margins | transcription dedicated to the public domain |
| OpenBible cross references | CC BY 4.0 | published under Creative Commons Attribution | attribution required and given |
| NT to deuterocanonical allusions | addresses only | see the section below | no fixture licence stated |

The machine readable version of this table travels inside each published file,
under `version.rights`, so a consumer never has to come back here to find out
what it is allowed to do.

**Excluded permanently, and this is not a deferral.** The Ave Maria text and its
pericope headings, which are under copyright and sit in the same source
database. The Portuguese Catena Aurea, whose provenance is open. The text of the
Catechism, canon law and the magisterial documents.

The Ave Maria headings deserve their own sentence, because they are the one
thing here that could ship by accident. The private repository grafts 2305 of
them onto Matos Soares at import time, in the `heading` column of the same row
as the public domain verse text. The export names its columns and never selects
that one, and a test fails if a heading reaches a published file.

## What the rate limiter cannot do, added in B8

### It is abuse control and it is not DDoS protection

The epic's own framing invites this confusion, so it gets said plainly. Per
address limits stop one careless script. A distributed flood arrives from
thousands of addresses, each one comfortably under 60 a minute, and this
middleware answers every one of them politely and on time.

Stopping that needs something in front of the box that can drop a packet without
a Python process waking up. Nothing here is that, and nothing here will be.

### It counts the request after it has already arrived

The connection was accepted, TLS was done, the ASGI scope was built and the
middleware ran. What a refusal saves is the database read and the
serialisation, measured at 1.94 ms, and it saves nothing below that. A flood
large enough to fill the accept queue is not affected by any of this.

### A restart forgives a window

The counter lives in a file under the system temporary directory and it is
deliberately not persisted. Restarting the service resets every window, so a
caller who was three seconds from being unblocked and a caller who just spent
their hour are treated the same.

The alternative is a volume, a backup and a migration for data whose whole value
expires in sixty minutes. This is the cheaper wrong answer and it is chosen
knowingly.

### A fixed window admits up to double the limit across a boundary

60 requests at 11:00:59 and 60 more at 11:01:00 is 120 requests in two seconds
and none of it breaks a rule. A sliding window would catch it and needs a
timestamp per request instead of one integer per bucket.

For a limit that exists to stop a runaway loop rather than to meter a paid
product, the boundary is the cheapest thing to give away. `DECISIONS.md` carries
the trade.

### The limiter can stop working and the API keeps answering

Fail open, by decision. A disk error, a read only filesystem or a corrupt file
leaves the counter unusable, and the request is served rather than refused. The
posture before B8 was unlimited, so this is a return to it rather than a new
hole.

What makes it survivable is that it says so. `/health` reports `degraded` with
the reason and the log fires at error level. A limiter that quietly stopped
limiting is the classic hole in security middleware, and the only defence
against it is the report.

### A refused request still spends the other window, on purpose

A request the minute window turned away is still counted against the hour. A
caller who reads `Retry-After` and waits never meets this. A caller who ignores
the 429 and keeps hammering spends the hourly budget on refusals and is locked
out for the rest of it.

A review called this a defect and it is a decision. Escalating a client that
ignores the answer is what the second window is for, and the request was
answered, logged and paid for whatever its status code said.

### An address behind a shared exit is one caller

A university, an office or a mobile carrier NAT puts thousands of people behind
one address, and they share one budget. There is no way to tell them apart
without an identity, and an identity is an account, which this project does not
have. `DECISIONS.md` records what would have to happen before that changes.

## What is not here yet

No per book files and no CDN. That is B5.

## What the commentary cannot prove, added in B4

### No person has read the Portuguese

Twenty thousand seven hundred and five notes were translated from English by a
language model. The prompt required faithful rendering rather than paraphrase,
Catholic ecclesiastical terminology mapped to the terms the Magisterium defines,
and Scripture citations and Latin left untouched.

Nothing in the English was softened on the way through. A 19th century commentary
that has been quietly modernised is a worse artifact than one that is dated in
the open, so the text reads as Haydock wrote it.

**Human review is pending and wanted.** The sample is drawn, seeded and committed
at `docs/qa/haydock-translation-sample.csv`, 200 entries with their English
beside them, ready for a person to work through.
`docs/qa/haydock-translation-review.md` holds the record of what has been checked
so far and by what.

**What has been checked is structure, not meaning.** Five mechanical comparisons
run against the English each entry came from, over the sample and over all
20705. `make audit-translation` recomputes every number below and a test pins
them, because a number in this file that nothing recomputes is a number nobody
can check.

| Check | Sample of 200 | All 20705 |
|---|---|---|
| Portuguese body empty | 0 | 0 |
| Portuguese identical to the English | 0 | 0 |
| Length outside 0.6 to 1.8 of the source | 0 | 0 |
| `<em>` and `<strong>` counts differ | 1, 0.5% | 181, 0.87% |
| A digit does not survive | 0 | 84, 0.41% |

The digit check joins thousands groups on both sides first, because English
writes `400,000` and Portuguese writes `400.000` and a naive comparison reports
112 differences where 28 of them are punctuation. Of the 84 that remain, reading
six found a mix of legitimate choices and real losses. `100 fold` rendered as
`cêntuplo` and `40 years` as `quarenta anos` are correct and count as
differences here. A chapter number dropped from a citation is a defect.
**Nothing mechanical can separate those two, which is the whole reason a person
has to read the sample.**

None of these five answers whether a sentence means what the Latin behind it
means. They catch a body that was never translated, a body that was truncated
and a citation that moved. They do not catch a fluent paragraph that says the
opposite of the original, and that is the failure that would matter most.

### Two hundred and forty four bodies shipped with pipeline markers in them

Found while running the checks above, after the first pull request was open.

The translation harness wrote its own control markers into the Portuguese text
rather than into the field beside it. A reader of Genesis 35:6 saw the note, then
`[[[REVIEW:exegese_datada|...]]`, then `[[[ID:484]]]`, and then the entire
translation of an unrelated note glued on behind it. 244 of 20705 entries across
56 books. The English was never touched.

The export now cuts each body at the first marker. What that keeps measures
between 0.85 and 1.32 of its English source, median 1.01, so the cut removes
contamination rather than content, and every absorbed passage that still exists
upstream carries its own translation on its own entry. The build refuses any body
that still contains a marker, and a test over the published file is the third
place the same contamination would have to get past.

`PROVENANCE.json` records the count. It is the second value in this dataset that
differs from what the source holds, after the two clamped anchors, and both
differ by removing rather than by inventing.

### Two notes lost their second verse

Two entries are labelled `26-7` and `73-4`, meaning Matthew 15:26 to 27 and Luke
1:73 to 74. The upstream extraction read the elided second number literally, so
each entry ran from 26 to 7 and from 73 to 4, which no coverage test can match.
Both notes were invisible in the source system.

The export clamps the end onto the start, so each note is published on the first
verse of its pair and absent from the second. Deriving the 27 from the label
would have been this repository inventing a value no source holds, and it would
have been right. Being right about a guess is not the same as having the data.
Matthew 15:27 and Luke 1:74 read as having no Haydock note when a printed
edition would show one.

### 14803 addresses have no note at all

Of 35845 spine addresses, 21042 are covered by at least one Haydock entry. The
rest come back with an empty source list and a 200. That is the source edition
being a commentary rather than a gloss on every verse, and it is not a gap this
repository can close.

### The plain text column is derived and never checked against a parser

Every body carries HTML and the same body with the markup removed. The removal
is a regular expression over a corpus that contains `<em>` and `<strong>` and
nothing else, counted over all 41410 bodies. A tag this corpus does not have
would survive into the text column, and nothing here would notice.

## What the read API cannot prove, added in B3

### 219 authored strings were checked for consistency and not for tradition

The English and Latin abbreviations, and the Douay names in ordinary case, are
authored in this repo. Nothing upstream carries a book name in any language but
Portuguese, so there was nothing left to export.

Three checks run over all of them. Each resolves back to its own book through
the alias table, which is built from exported data. Each is a subsequence of a
name the book actually has, so `Ecclus.` passes against `Ecclesiasticus` and
fails against `Ecclesiastes`. And no two share a string.

All three answer whether a string is consistent with its book. None answers
whether it is the form the tradition prints. If the conventional English
abbreviation for Sirach is `Sir.` and `Ecclus.` was written instead, every check
passes. That question needs a human reading against a printed Bible, and it is
the weakest link in every formatted reference this API returns.

Nine of them carry conformance cases, chosen because they are the ones that
would hurt. The other 210 do not.

### Reading a spine address back into another scheme is wrong in two places

`to_scheme` maps a candidate forward again and keeps it only if it lands where
it started. That catches a candidate that moved and it cannot catch one that is
out of range in the target scheme, because this repo holds the Copenhagen remap
pairs and no `org` verse count table. A book that maps by identity round trips
trivially.

Two addresses are confirmed wrong. Spine `PSA.15.11` reads back as `org` 15:11
and spine `PSA.43.27` as `org` 43:27, and both are different psalms. The honest
answer for each is an orphan.

Whether more exist across the other 72 books is not measurable with what is in
this repo. Saying that is better than publishing a number nobody can stand
behind. B3 ships the ported psalm table, which is hand verified, and pins the
two disagreements so the day B1 is corrected the suite says which one moved.

The psalm counterpart the API publishes comes from the ported table and not from
`to_scheme`, so no route returns either wrong answer today.

### The published numbering covers the Psalms and nothing else

`numbering` appears on a chapter of the Psalter and nowhere else, because the
ported table covers the Psalter and nowhere else. Joel and Malachi are numbered
differently between traditions too, and this API says nothing about that.

### One latency number is not a load test

A 500 verse passage across three versions answers in 5 ms on a laptop, measured
after the per address point queries became one range query and down from 21 ms
before it. A commentary read answers in 4.4 ms, down from 15 ms once the build
started running `ANALYZE` and the planner stopped scanning 16 MB of note bodies
to find one. Those are three numbers, on one machine, with one request at a time.

Nothing here has been load tested, no route has been measured under concurrency,
and nothing is deployed. The memory side of the store decision is also half
measured. 34.8 MB retained is the cost of the alternative that lost, and the
resident cost of a connection per request with a page cache each does not exist.


## What the cross-references cannot prove, added in B4

### The 292 authored pairs ship on a reading, not on a ruling

The set that connects the New Testament to the deuterocanonical books is 292
pairs of addresses, expanded in both directions to 673 rows. It carries no text,
no note and no editorial prose of any kind, and it is where 665 of the 920
surviving deuterocanonical links come from.

The reading is that a bare pair of Scripture references is a fact about
Scripture rather than an expression of anyone's editorial work, so a list of
them is not the apparatus it was compiled with. That is a reading. It has not
been tested by anyone who practises copyright law and this repository is not
pretending otherwise. What is recorded here is the reasoning and the cost of
being wrong, which is 673 rows and a rebuild.

The alternative was refusing them, and the measured cost of that was cutting
deuterocanonical linkage by 61%, to protect against copying nothing.

### The Ave Maria apparatus is excluded and cost nothing

879 entries scraped from the Ave Maria edition's own margins, the same protected
1957 edition whose text this repository already refuses. They contribute exactly
one link touching a deuterocanonical book, so the exclusion costs a rounding
error. It is not a flag on the export. The source is absent from the list, so
shipping it would take an edit rather than an oversight.

### The orphan report is an upper bound and says so

The importer in the private repository counts what it could not resolve and
throws it away, so the resolved rows cannot answer the question. The fixtures
are files, so the export diffs against them instead.

| Source | Fixture pairs | Exported | Unaccounted |
|---|---|---|---|
| `openbible` | 211804 | 204601 | 7203 |
| `na27` | 341 | 673 | 5 |
| `douay` | not countable | 2362 | not countable |

The gap holds two different things and the diff cannot tell them apart. An entry
the import could not resolve is an orphan. An entry another source had already
written is dropped by the unique constraint and is not one. Both are absences.

**The OpenBible losses are concentrated in Daniel**, 655 of them on Daniel
pointing at Daniel and another 425 between Daniel and the Psalms. That is where
the `org` scheme carries Susanna and Bel as their own books and this spine folds
them into Daniel 13 and 14, so the remap is where the references go missing. It
is a real defect and it is not measured further here.

The Douay row is not countable because its fixture holds reference strings like
`Act. 14, 15. 17, 24.` rather than addresses. Splitting them needs the parser,
and a second parser in the export would be a second set of bugs rather than a
check.

### Thirty references per address is a ported number

The read returns the thirty highest weighted references on each address. Genesis
1:1 carries more than sixty strong ones and a client rendering all of them
renders noise. Thirty is the private repository's number, carried across rather
than derived from anything measured here, and the published file keeps every row
so a consumer who disagrees can read the artifact instead of the API.

### Weight does not reach the wire and `primary` is a threshold

The weight is a vote count from OpenBible, a constant of 100 for the Douay
margins and a constant of 90 for the allusion set. Those three numbers are not
comparable, so publishing them would invite arithmetic that means nothing. What
ships is `primary`, true at 20 or above. The threshold is also ported.

## What the static artifacts cannot prove, added in B5

### They are a second copy, and only CI notices when they drift

`data/` holds 371 files split out of the same corpus the API reads. Nothing
inside either tree points at the other. `scripts/build-artifacts.py --check`
regenerates and diffs on every push and every pull request, and that is the only
thing keeping them in agreement.

A local edit to the corpus with no `make artifacts` afterwards leaves the two
disagreeing until CI runs. The window is a push long. It is not zero.

### The CDN is somebody else's machine

The README says no server that can go down. jsDelivr is a server and it can go
down, and the honest version is that this repository operates none.

If jsDelivr stops serving GitHub, or the account is suspended, or the repository
is deleted, every published URL dies with it. The files themselves survive in
git and in anyone's clone, and the URL is the part that is borrowed. A consumer
who needs a guarantee stronger than that should mirror the files, and the
manifest is there so they can prove what they mirrored.

### The commentary file is 4.3% away from being unservable

jsDelivr refuses a single file over 20 MiB. `haydock.json` is 20068650 bytes,
which leaves 902870 bytes of room. That file is a source rather than a published
artifact, and it is served today because the repository is public and everything
in it is reachable.

The per-book split is what keeps the published surface clear of the limit. The
largest published file is Psalms in the Haydock at 2187332 bytes. Nothing warns when
the monolith crosses the line, and what breaks is somebody else's browser.

### A clone costs 98 MB now

The tracked tree went from 50.3 MB to roughly 98 MB, and the whole increase is a
second copy of data already committed. Anyone cloning for the Python package
pays it too.

The alternative was building the artifacts in CI at tag time and committing
nothing, which keeps the tree small and produces published files that nobody can
verify on a clean checkout. That trade was refused deliberately.

### Granularity stops at the book, and a chapter would be cheaper

Sirach 24 is 3 KB and the whole book is 106 KB. A consumer who wants one chapter
downloads the book.

Per chapter would be roughly four thousand files against jsDelivr's soft limit of
ten thousand actively accessed, which is affordable. It was cut for scope rather
than for cost, and the path shape leaves room for it.

### A stranger can now rebuild half of this

The first section of this file says a stranger cannot rebuild the dataset, and
that stays true of the corpus. It is no longer true of the artifacts.

`scripts/build-artifacts.py` reads only what is committed. Anyone who clones this
repository regenerates all 371 published files and diffs them byte for byte,
with no private source and no credentials. What that proves is that the
artifacts match the corpus. What it still cannot prove is that the corpus matches
the source it was exported from.

### The Portuguese README is a door and not a mirror

*This section said there was no Portuguese README at all. B7 wrote one and left
the limit standing, so the file published something untrue for two epics. Found
while writing B9 and corrected here rather than quietly deleted.*

`README.pt-BR.md` exists and it is deliberately short. It carries the argument
and points at the English document for the endpoint list, the quickstart and the
versioning rule. A reader who only reads Portuguese gets the reasoning and then
has to cross over for the reference material.

## What full-text search cannot do, added in B9

### It is lexical, and that word is doing real work

The index matches words. It does not know that `misericórdia` and `piedade`
answer the same question, and it never will, because that is a different
technique living in a different repository. `concordantia` consumes what is
published here and owns the comparison.

### There is no typo tolerance

The ported implementation runs on Meilisearch, which corrects a misspelling for
free. FTS5 does not, and building an edit distance over 107103 rows here would be
a second search engine nobody asked for.

What covers half of it is the prefix operator. `amar*` reaches the inflections
that a stemmer would have reached, and a reader who types `corcao` gets nothing.

### There is no stemmer, and that is a choice about three languages

FTS5 ships `porter`, which only knows English. One index holds Portuguese,
English and Latin. A stemmer correct for one and wrong for two is worse than
none, because the wrongness never surfaces as an error.

### Ranking under `version=all` compares scores from different languages

`bm25` weighs a term against how common it is in the corpus. Under `version=all`
the corpus is Portuguese, English and Latin at once, so a Latin verse and a
Portuguese verse are ranked by scores computed over different vocabularies. The
list is useful and the order across languages does not mean what an order inside
one language means.

The same address also comes back once per translation carrying the word. Every
hit names its own version, which makes the repetition visible rather than
confusing, and it is why `version` defaults to one translation.

### Paging stops at 1000

Ranking sorts every match before it can page, so the cost grows with the offset.
Measured on 2026-08-04, warm, median of seven runs, on the built database.

| Query | Hits | Count | First page | Page at offset 1000 |
|---|---|---|---|---|
| `coracao`, one translation | 914 | 1.0 ms | 2.1 ms | 6.2 ms |
| `Deus`, one translation | 4539 | 5.0 ms | 16.7 ms | 21.5 ms |
| `a`, one translation | 18904 | 13.4 ms | 30.4 ms | 44.9 ms |
| `a`, `version=all` | 29007 | 14.8 ms | 38.7 ms | 54.3 ms |
| `a`, commentary | 22393 | 18.2 ms | 36.3 ms | 78.7 ms |

A reader cannot walk past result 1000 of 29007. Beyond the cap the answer is a
`422` rather than a slow `200`, because a request that takes a fifth of a second
to say what the first page already said is not worth serving.

### A search answer is not cached the way a verse is

A verse carries a year of immutable caching. A result list depends on what is
published and carries five minutes. Nothing here is per reader, so a proxy in
front is free to share it.
