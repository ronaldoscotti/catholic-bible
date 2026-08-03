# Code review, B4 slice two, cross-references

*Stage 7. Written 2026-08-03, one author.*

**A self review is not the gate.** One person, one repo. What is true is the
mechanism. Branch, pull request, never a push to `main`.

## What the diff is

207636 references on 26726 anchors from three sources, an orphan report that
says what it cannot answer, one new table plus a source table, two routes, and
the attribution that CC BY requires. 532 tests.

## The thing worth most attention

**Two layers now hang off the same integer and neither one moved it.** That was
the whole argument of B4 and it is now checkable rather than arguable. Five
tables were added across the two slices, `spine` and `texts` are untouched, and
the diff contains no `ALTER`.

Second, and it is the reason this epic was worth doing at all: **OpenBible
carries 204601 references and not one of them reaches a deuterocanonical book.**
That is asserted by a test rather than described in prose, so if a future import
changes it the suite says which side moved.

## The defect the measurements found

**One verse cost 35 ms and a five hundred verse passage cost 1.5 ms.** The
inversion is what gave it away, because a correct implementation cannot be
faster on more work.

A cross-reference target set runs from Genesis to Revelation. The route was
asking for the spine addresses as a range covering the targets, and the range
covering Genesis to Revelation is the whole spine, so answering thirty
references read 35845 rows.

```
before   one verse   35.44 ms
after    one verse    2.80 ms
```

This is the same class of defect the B3 review found, and the opposite mistake.
There the fix was replacing per address queries with one range. Here the fix was
replacing one range with addressed lookups, because the data is scattered and
not contiguous. Both functions now exist and a test pins which shape belongs to
which.

## What was applied before it could be reported

**The lectionary filter.** Slice one shipped a defect where a disjoint reference
returned commentary on verses nobody asked for, found by the review agent. The
same envelope query exists here, so the same filter was written into the
cross-reference route before the first request. A test pins it on both routes.

That is the cheap half of a review working. The expensive half is that the
defect existed at all.

## What I checked because it would fail quietly

**Whether the attribution can be dropped by accident.** CC BY requires it and a
notice living only in a README is a notice a consumer never sees. It is in three
places now, and both the response and the running container are asserted. A
refactor that drops the field fails a test and CI.

**Whether the excluded source can come back.** `ave-maria` is not a flag on the
export. It is absent from the source list, so shipping it takes an edit rather
than an oversight, and a test asserts the published source set is exactly three.

**Whether the orphan report overstates.** It does, and it says so. The gap it
reports holds entries that failed to resolve and entries another source had
already written, and the diff cannot tell them apart. Printing 7203 as an orphan
count would have been a bigger and more impressive number that was not true.

**Whether the Daniel losses are noise.** They are not. 655 of the 7203 are
Daniel pointing at Daniel and another 425 run between Daniel and the Psalms,
which is exactly where the `org` scheme carries Susanna and Bel as their own
books and this spine folds them into Daniel 13 and 14. Named in `LIMITS.md`, not
chased here.

**The hostile input pass.** Twenty one deliberately malformed requests against
the two new routes. No 500 and no unstructured body.

## What the second review found here

The same overflow guard was asymmetric on these two routes as on the other four,
and the fix landed in #24 where the guard lives. Both cross-reference routes
answered `500 Internal Server Error` with a body that was not JSON for a negative
chapter of 64 bit magnitude, and both answer 422 in the published shape now.

The document gate caught the rest of it. Regenerating after the bound changed
failed `--check` until `openapi.json` carried the new `minimum`, which is the
gate doing what it exists for rather than a passing build being trusted.

## What a second reviewer should look at first

The rights position on the 292 allusion pairs. It is the only thing in this
repository published on a reading of copyright law rather than on a clear
licence, the author took the decision knowingly, and `LIMITS.md` states the cost
of being wrong. A reader who disagrees should be able to find the reasoning in
one place, and that is what `DECISIONS.md` is for.

Then the Daniel remap, which is losing 655 references and is a B1 concern
surfacing through B4.
