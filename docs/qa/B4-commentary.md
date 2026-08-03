# QA, B4 slice one, commentary

*Stage 6. Run 2026-08-02, on `feat/b4-commentary`.*

Reading the diff is not QA. This is what ran and what came back.

## The suite, the linter and the type checker

```
$ make lint
All checks passed!
101 files already formatted

$ make typecheck
Success: no issues found in 54 source files

$ make test
500 passed
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

**What was run instead, and what it is worth.** Five mechanical comparisons of
each Portuguese body against the English it came from, over the sample and over
all 20705. `scripts/audit-translation.py` is committed and `make
audit-translation` reruns it, so these are re-derivable rather than reported.

| Check | Sample of 200 | All 20705 |
|---|---|---|
| Portuguese body empty | 0 | 0 |
| Identical to the English | 0 | 0 |
| Length outside 0.6 to 1.8 of the source | 0 | 0 |
| Emphasis markup counts differ | 1, 0.5% | 181, 0.87% |
| A digit does not survive | 0 | 84, 0.41% |

The digit check normalises thousands groups on both sides first, because English
writes `400,000` and Portuguese writes `400.000`, and skipping that reports 112
where 28 are punctuation. Of the 84 left, reading six found both real losses and
correct choices, `40 years` becoming `quarenta anos` among them. Nothing
mechanical separates those, and that is precisely the gap the human sample
exists to close.

These checks find a body that was never translated, one that was truncated and a
citation that moved. They cannot find a fluent paragraph that says the opposite
of the original.

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

## What stage 7 found after this walk was written

Two defects, and neither was visible to this document as first written.

**A lectionary reference returned notes on verses nobody asked for.**
`Mc 5,22-24.35-43` skips verses 25 to 34 and the commentary route returned the
notes anchored there, so `ids` and `sources` in the same response disagreed.
Fixed and pinned.

**A path integer wider than 64 bits was a 500 with a traceback**, on this route
and on two B3 routes already merged. `docs/reviews/B4-commentary.md` carries the
reproduction. Fixed for all four routes with a bound taken from the driver
rather than from the canon.

Neither was found by reading. The first came from a review agent tracing the
disjoint path by hand and the second from sending twenty five deliberately
malformed requests, which is the pass B3 skipped and paid for.

## What running those checks found, and it was serious

**244 Portuguese bodies shipped with the translation harness's control markers
inside the text.** A reader of Genesis 35:6 saw the note, then
`[[[REVIEW:exegese_datada|...]]`, then `[[[ID:484]]]`, and then the entire
translation of an unrelated note. 244 of 20705 entries across 56 books. The
English was never touched and no test noticed, because every test asked whether
a body existed and none asked what was in it.

It was found by running the structural pass above rather than by reading code, a
day after the pull request opened.

The export cuts each body at the first marker. The cut was verified not to
remove content two ways. What it keeps measures between 0.85 and 1.32 of its
English source, median 1.01, against a corpus median of 1.01. And every absorbed
passage whose entry still exists upstream carries its own translation on its own
entry, checked against the source database for all 119 that survive the reseed.

```
$ scripts/export-commentary.py --source ...
exported 20705 entries, 2 clamped, 244 cut at a leaked marker
```

The build refuses any body that still holds a marker, so a future export cannot
ship the same thing silently, and a test over the published file is the third
gate. The committed review sample was redrawn from the corrected corpus, same
seed, same rows.

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
