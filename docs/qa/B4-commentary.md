# QA, B4 slice one, commentary

*Stage 6. Run 2026-08-02, on `feat/b4-commentary`.*

Reading the diff is not QA. This is what ran and what came back.

## The suite, the linter and the type checker

```
$ make lint
All checks passed!
98 files already formatted

$ make typecheck
Success: no issues found in 54 source files

$ make test
493 passed
```

## The epic criteria, walked one by one

B4 ships in two slices. Everything below says which slice it belongs to and an
unmet criterion stays unchecked rather than being softened.

**1. Haydock commentary in English is addressable by verse for all 73 books.**
Met. 20705 entries, and the book set is asserted equal to the spine's rather
than counted, because a commentary with 72 books has a hole and the hole is
always a deuterocanonical.

```
$ curl -sS "http://localhost:8000/v1/books/JHN/chapters/3/verses/16/commentary"
{"reference":"Jo 3,16","ids":["JHN.3.16"],"sources":[{"code":"haydock",…
```

**2. Haydock commentary in Portuguese is addressable by verse for all 73 books.**
Met as an addressing claim and **not** as a quality claim. Every one of the 20705
entries carries a `pt-BR` body and a test asserts it. Whether the Portuguese is
faithful is criterion nobody has checked, and the README says so in those words.

**3. Cross-references resolve in both directions and orphans are reported.**
Slice two. Unchecked.

**4. Commentary and cross-references attach to the same verse id, with no change
to the verse schema.** Half met, and the half that is met is the load-bearing
one. The commentary landed on `canonical_order` and neither `spine` nor `texts`
gained a column. The diff shows three new tables and no `ALTER`.

**5. The API exposes commentary and cross-references for a given address.**
Commentary, met. Two routes, both in the published document, both walked by the
three document gates. Cross-references are slice two.

**6. OpenBible attribution appears in the README and in the dataset metadata.**
Slice two. Unchecked.

**7. How the Portuguese translation was produced is stated on the first screen of
the README, including what a human reviewed and what a human did not.** Met.
The paragraph sits in `## Status`, above the quickstart, and says the words
`No human has read a sample and written down an error rate`. The provenance also
travels inside the API response, so a consumer who never opens the repository
still sees `"translation":"machine"`.

**8. Cross-references derived from a copyrighted apparatus are excluded, and the
exclusion is recorded in `LIMITS.md`.** Slice two. Unchecked.

## The verification the epic names

**Test driven on anchor resolution.** The coverage query has eight tests and the
routes have fourteen. Proved to bite rather than trusted, by removing the floor
margin and watching two fail.

```
$ # with `floor = first` instead of `first - widest`
FAILED tests/storage/test_commentary_coverage.py::test_a_verse_inside_a_spanning_note_finds_it
FAILED tests/storage/test_commentary_coverage.py::test_the_floor_does_not_change_the_answer
```

**The published file, proved against a mutation.** Shifting one anchor by one
order in the committed JSON failed the checksum test and the spine agreement
test.

```
FAILED tests/commentary/test_published_commentary.py::test_the_file_matches_its_recorded_checksum
FAILED tests/commentary/test_published_commentary.py::test_every_anchor_is_on_the_spine_and_agrees_with_it
```

**Three new conformance cases, run over HTTP.** The corpus is 43 cases and the
count is asserted so one cannot be dropped quietly. Two of the three are the
clamped entries, which are in the corpus because their failure mode upstream is
silence rather than an error.

**The human review sample.** Drawn, seeded, committed, and **not read**. 200 of
20705 entries in `docs/qa/haydock-translation-sample.csv` with an empty verdict
column. A test asserts the draw is reproducible from the seed and a second test
fails the day the column is filled without `LIMITS.md` being updated.

The epic says the sample gets a size and an error rate written down. The size is
written down. **The error rate is not, because nobody has read it, and this
document will not record a number that does not exist.**

## Defects found during the work

**Two notes were invisible upstream.** Labelled `26-7` and `73-4`, meaning verses
26 to 27 and 73 to 74. The extraction read the elided second number literally, so
each entry ran backwards and the coverage test `start <= wanted AND end >= wanted`
matched no address at all. Matthew 15:26 and Luke 1:73 read as having no note.
The export clamps the end onto the start, the build refuses an inverted entry so
a third one cannot arrive silently, and both addresses carry conformance cases.

**The planner was scanning 16 MB of note bodies on every request.** Found by
measuring rather than by a complaint. Without statistics SQLite drove the
coverage join off `commentary_body` instead of off the index built for it.

```
without ANALYZE   SCAN commentary_body                            9.548 ms
with ANALYZE      SEARCH commentary USING INDEX commentary_coverage  0.027 ms
```

Over HTTP, 15 ms to 4.4 ms, which is where the B3 verse read already sat.

**The coverage floor was worth keeping and the plan expected to cut it.** The
plan left it open and said to measure. SQLite uses the index either way and still
walks it from the first entry of the source, so the open range costs 0.92 ms at
the end of Revelation against 0.0065 ms bounded.

## Where the code and the plan disagree

The plan said both commentary routes would carry the immutable cache header,
because the answer depends only on the address. That was wrong and the code does
not do it. Every reference in the response is formatted in the default version's
notation, which is not in the URL, so these routes carry the same short header
`/v1/resolve` carries and for the same reason. A test pins it.

Recorded here rather than edited into the plan, because a plan that quietly
matches the code it produced is not a plan anyone can check.

## Run on a clean container

```
$ docker compose up -d --build --wait
Container catholic-bible-api-1  Healthy

$ # the README contract, unmoved
health  MATCH
Sirach  MATCH

$ # the commentary, both languages and the provenance
BOTH LANGUAGES + PROVENANCE

$ # latency, three requests each
verse note     0.0062s  0.0044s  0.0042s
chapter range  0.0054s  0.0057s  0.0057s
b3 verse read  0.0047s
```

CI now asserts the commentary response the same way it asserts the README
quickstart, so the claim rots the day it stops being true rather than a month
later.

## What is not covered

No load test. Three latency numbers on one laptop, one request at a time.

Nothing is deployed. B6.

The Portuguese has not been read by a person. That is the open criterion and it
is the reason this epic is not finished.
