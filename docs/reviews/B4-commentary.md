# Code review, B4 slice one, commentary

*Stage 7. Written 2026-08-02, one author, plus a review agent run against the
epic and the conventions.*

**A self review is not the gate.** One person, one repo. What is true is the
mechanism. Branch, pull request, never a push to `main`.

Stage 7 ran after the pull request opened again, which is the same wrong order
B3 had. Recorded rather than tidied.

## What the diff is

20705 Haydock notes in two languages, exported by a committed script, three new
tables, two routes, and the provenance paragraph that had to be right. 499 tests.

## The thing worth most attention

**The schema did not move.** B1 claimed a dense integer is a usable anchor for
anything that attaches to a verse. A claim like that is worth exactly what the
first thing built on it proves, and this is the first thing. Three new tables
arrived, `spine` and `texts` gained no column, and the diff shows no `ALTER`.

If the anchor had needed a change, this document would be recording that instead,
and B1's central claim would be weaker than it reads.

## What the review agent found

**The agent had no shell.** It could not run the suite, send a request, start the
container or recompute a checksum, which is most of what it was asked to do. It
said so at the top of its report rather than writing plausible transcripts, which
is the right call and is also the reason the hostile input pass below was run by
hand afterwards.

One real defect, traced rather than reproduced by the agent, and confirmed here.

**A lectionary reference returned commentary on verses nobody asked for.**
`Mc 5,22-24.35-43` is a disjoint reference and the parser is built to read it.
`_commentary_out` asked the reader for the whole envelope, verses 22 through 43,
and never filtered the answer back down to the addresses in the request.

```
$ GET /v1/commentary?ref=Mc 5,22-24.35-43
ids:     MRK.5.22 … MRK.5.24, MRK.5.35 … MRK.5.43
entries: MRK.5.23  MRK.5.28  MRK.5.30  MRK.5.35  MRK.5.36  MRK.5.41
```

Verses 25 to 34 were not requested and two notes anchored there came back
anyway. The response contradicted itself, because `ids` was built correctly and
the notes were not. `resolve` and `passage` both filter by the requested set and
this was the one place that did not, so it was a regression against a pattern the
codebase had already settled.

Fixed by filtering the rows, with a bisect over the sorted orders rather than a
scan per row, and pinned by a test that asserts every entry start appears in the
`ids` beside it.

The agent also noted that the export refused an entry with no body in any
language where the spec said no body in the source language. Tightened. The
export was re-run afterwards and the published file is byte identical, so the
change touches the refusal path and nothing that ships.

## What the hostile input pass found, run by hand

Sixteen malformed references and nine malformed paths, because B3 shipped a 500
that every test missed and only a weird request found.

**A path integer wider than 64 bits was a 500 with a traceback.**

```
$ GET /v1/books/GEN/chapters/99999999999999999999/verses/1/commentary
500 Internal Server Error
OverflowError: Python int too large to convert to SQLite INTEGER
```

**This is a B3 defect and it is already merged.** The same number on
`/v1/versions/matos-soares/books/GEN/chapters/99999999999999999999` fails
identically, and that route shipped in #23. B4 inherited it by taking a chapter
in a path.

Fixed for both epics in one place. The path integers carry an upper bound of
`2**63 - 1`, which is the driver's limit rather than the canon's, so the guard
refuses what cannot be stored and nothing that can. The four affected routes now
answer 422 in the published error shape. Three cases were added to the
parameterized validation test that already sends real malformed requests.

Everything else held. Empty and whitespace references, a bare comma, a reference
spanning the whole Bible, a chapter of zero, a negative chapter, a scheme value
outside the enum, a mathematical alphanumeric book name, a path traversal
attempt in the book segment, and a reference with four hundred range separators
all came back 422 or 404 with a structured body and a reason code.

## What I checked because it would fail quietly

**Whether the Catena Aurea leaked.** It shares both tables with the Haydock and
must never ship. The export refuses any source code but `haydock`, a test asserts
the published source set is exactly that, and the agent grepped the 20 MB file
for `catena` and found five hits, all of them Haydock citing the work by name in
his own public domain text.

**Whether the published file was hand edited.** Mutated one anchor by one order
and watched the checksum test and the spine agreement test both fail.

**Whether the coverage floor drops a note.** The floor is a performance bound and
a performance bound that changes an answer is a bug. Compared against the
unbounded query over a thousand addresses rather than argued from the widest
span, because the argument is the part that could be wrong.

**Whether the performance claims reproduce.** The agent could not run them and
said so. Both were measured here twice, before and after the container rebuild,
and the numbers in `DECISIONS.md` are the second run.

## Found after this document was first written

**244 published Portuguese bodies carried the translation harness's control
markers**, `[[[REVIEW:category|reason]]` and `[[[ID:n]]]`, with the whole
translation of an unrelated note behind them. 56 books. The English was clean.

Nothing in the suite could have caught it. Every test asked whether a body
existed, what language it was in and whether its anchor was right. None asked
what the body said. The published file test checked a checksum of the
contamination and passed.

It was found by running the structural half of the epic's own verification,
which is the half nobody thought needed running because the other half needs a
person.

The export cuts at the first marker, the build refuses a body that still holds
one, and a test over the published file is the third gate. That the cut removes
contamination rather than content was checked two ways rather than asserted:
what remains measures 0.85 to 1.32 of its English source with a median of 1.01,
and all 119 absorbed passages whose entries survive the upstream reseed carry
their own translation on their own entry.

## A second review, and it found the same blind spot twice

A review agent ran against the stack. It had no shell again, said so at the top
rather than writing transcripts, and traced one real defect that reproduced
immediately.

**The overflow guard was asymmetric.** `Path(le=2**63 - 1)` bounds the top and
nothing bounds the bottom, so a negative chapter of the same magnitude still
reached `sqlite3` and still raised `OverflowError`.

```
$ GET /v1/books/GEN/chapters/-99999999999999999999/verses/1/commentary
500  'Internal Server Error'
$ GET /v1/versions/matos-soares/books/GEN/chapters/-99999999999999999999
500  'Internal Server Error'
```

Four route shapes, two of them B3's and already merged. The body is not even
JSON, so the one published error shape was absent rather than wrong.

The guard now reads `Path(ge=-(2**63), le=2**63 - 1)` and the comment says both
ends. A chapter of 0 or of -1 still answers 404 `not_on_spine` as it always did,
because the bound is the driver's and not the canon's.

**The hostile pass that missed it was mine.** Twenty five requests, and every
overflow case in it was positive. Three negative cases are now in the
parameterized test that sends real malformed requests.

**The second finding was a process gap and it was fair.** The two structural
audit numbers quoted in `README.md` and `LIMITS.md`, 181 and 84, had no committed
script. Every other number in those tables is recomputed by a test.
`scripts/audit-translation.py` is now committed, `make audit-translation` runs
it, and a test asserts both figures so the prose cannot drift from the corpus.

## What a second reviewer should look at first

The Portuguese. Nobody has read it, the sample is drawn and waiting, and every
other check in this diff answers a structural question rather than a question
about meaning. A translation can be perfectly anchored, perfectly checksummed,
and wrong on the page, and for 244 entries it was perfectly anchored, perfectly
checksummed and visibly broken.

Then the two clamped anchors and the 244 cut bodies, which are the only places
in this repository where a published value differs from what the source holds.
Both differ by removing rather than by inventing, and both are counted in
`PROVENANCE.json`.
