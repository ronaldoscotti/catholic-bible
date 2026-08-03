# Code review, B4 slice one, commentary

*Stage 7. Written 2026-08-02, one author, plus a review agent run against the
epic and the conventions.*

**A self review is not the gate.** One person, one repo. What is true is the
mechanism. Branch, pull request, never a push to `main`.

Stage 7 ran after the pull request opened again, which is the same wrong order
B3 had. Recorded rather than tidied.

## What the diff is

20705 Haydock notes in two languages, exported by a committed script, three new
tables, two routes, and the provenance paragraph that had to be right. 497 tests.

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

## What a second reviewer should look at first

The Portuguese. Nobody has read it, the sample is drawn and waiting, and every
other check in this diff answers a structural question rather than a question
about meaning. A translation can be perfectly anchored, perfectly checksummed,
and wrong on the page.

Then the two clamped entries, which are the only place in this repository where a
published value differs from what the source holds, even though it differs by
being smaller rather than by being invented.
