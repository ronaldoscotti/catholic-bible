# QA, B4 slice two, cross-references

*Stage 6. Run 2026-08-03, on `feat/b4-cross-references`.*

Reading the diff is not QA. This is what ran and what came back.

## The suite, the linter and the type checker

```
$ make lint
All checks passed!
104 files already formatted

$ make typecheck
Success: no issues found in 58 source files

$ make test
532 passed
```

## The epic criteria, walked one by one

Slice one carried 1, 2, 4 in part and 7. This slice carries the rest. Every
criterion is now addressed and one of the epic's two verifications is still not
done, so the epic does not close.

**1. Haydock commentary in English is addressable by verse for all 73 books.**
Met in slice one.

**2. Haydock commentary in Portuguese is addressable by verse for all 73 books.**
Met in slice one as an addressing claim and not as a quality claim.

**3. Cross-references resolve to spine addresses in both directions, and entries
that cannot resolve are reported as orphans.** Met, with the second half
qualified. 207636 references on 26726 anchors, both ends checked against the
spine by the build and by a test over every row. Bidirectionality is not assumed
either.

```
$ curl -sS ".../v1/cross-references?ref=Mt 4,4"          -> WIS.16.26
$ curl -sS ".../v1/books/WIS/chapters/16/verses/26/cross-references" -> MAT.4.4
```

The orphan report is published at `derived/cross-reference-orphans.json` and it
is **an upper bound rather than a count**. The importer in the private
repository counts unresolved entries and throws them away, so the resolved rows
cannot answer it, and the export diffs against the fixtures instead. The gap it
finds holds entries that failed to resolve and entries another source had
already written, and the diff cannot separate them. `LIMITS.md` says so rather
than printing the larger number as though it were orphans.

**4. Commentary and cross-references attach to the same verse id used by B1,
with no change to the verse schema.** Met, and this is the criterion the epic
exists for. Five new tables across the two slices, `spine` and `texts` unchanged,
no `ALTER` anywhere in the diff.

**5. The API exposes commentary and cross-references for a given address.** Met.
Four routes across the two slices, all four in the published document, all four
walked by the three document gates.

**6. OpenBible attribution appears in the README and in the dataset metadata.**
Met, and in a third place. It is in `README.md` under its own heading, in
`sources.openbible.attribution` inside the published file, and in every API
response that draws on the source. A test asserts the response carries it and CI
asserts it against the running container, because an attribution a refactor can
drop silently is a licence violation waiting for a rebuild.

**7. How the Portuguese translation was produced is stated on the first screen
of the README.** Met in slice one.

**8. Cross-references derived from a copyrighted apparatus are excluded, and the
exclusion is recorded in `LIMITS.md`.** Met, **on a reading that was decided
rather than obvious.** The Ave Maria apparatus is excluded and the exclusion is
in `LIMITS.md` with what it cost, which is one deuterocanonical link.

The 292 authored allusion pairs ship. The author decided that and the reasoning
is in `DECISIONS.md`: they carry no text of any kind, so what would be copied is
a list of address pairs rather than an apparatus. That is a reading of the
criterion and not a self evident satisfaction of it, and `LIMITS.md` says the
reading has not been tested by anyone who practises copyright law.

## The verification the epic names

**Test driven on anchor resolution and on the orphan path.** 532 tests, of which
the cross-references have 14 over HTTP, 4 over the reader and 7 over the
published file.

**The orphan path is tested against the fixtures rather than a fake**, because
the fixtures are files and a real one is cheaper than a mock. The report's own
numbers are pinned, including the fact that the Douay row is not countable.

**The Portuguese Haydock human review sample.** Drawn, seeded, committed and
**not read**. The epic asks for the sample size and the error rate written down.
The size is written down. The rate is not, because nobody has read it.

**This is the reason the epic does not close.** Every acceptance criterion is
addressed and one named verification did not happen.

## What the numbers say, and why they are the point

```
source      rows      touching a deuterocanonical book
openbible   204601    0
douay         2362    258
na27           673    665
```

Two hundred thousand cross-references and not one reaches Tobit, Judith, Wisdom,
Sirach, Baruch or the Maccabees. A test asserts that rather than the README
merely claiming it, so the day it stops being true the suite says so.

## Defects found during the work

**One verse cost 35 ms and a five hundred verse passage cost 1.5 ms.** The
inversion is what gave it away. A cross-reference target set runs from Genesis to
Revelation, so the address range covering it is the whole spine, and the route
was reading 35845 rows to answer 30.

```
before   one verse   35.44 ms
after    one verse    2.80 ms
```

Fixed by asking for the addresses individually, chunked, and by keeping the range
query for the passage itself, which is contiguous by construction. A test pins
the distinction.

## The hostile input pass

Sixteen malformed references and five malformed paths against the two new
routes. No 500, no unstructured body.

```
422  <no ref>        422  ''             422  '   '          422  ','
422  'Gn 1,1-Ap 22,21'                   422  'Gn 1'
422  scheme=bogus    422  '𝔊𝔫 1,1'       422  '../../etc/passwd 1,1'
422  400 range separators                200  'Mc 5,22-24.35-43'
422  a chapter wider than 64 bits        422  a verse wider than 64 bits
404  chapter 0       422  chapter x      404  an unknown book
```

The lectionary case is the one that returns 200, and it returns references only
for the verses it asked for. The same filter slice one needed, applied here
before it could be reported as a defect.

## Run on a clean container

```
$ docker compose up -d --build --wait
Container catholic-bible-api-1  Healthy

health  MATCH        Sirach  MATCH
attribution PRESENT  Mt 4,4 -> Wis 16,26 PRESENT

xref one verse   0.0048s  0.0050s  0.0049s
commentary       0.0061s
b3 verse read    0.0043s
```

CI asserts the attribution and the Matthew to Wisdom link against the running
container, so both claims rot the day they stop being true.

## What is not covered

No load test. A handful of latency numbers on one laptop, one request at a time.
A 176 verse psalm answers in 19 ms and that is the slowest thing measured.

The Daniel losses in the orphan report are named and not fixed. 655 OpenBible
references from Daniel to Daniel do not survive the remap and this epic does not
chase them.

Nobody has read the Portuguese.
