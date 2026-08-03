# Code review, B5 static artifacts and CDN

*Stage 7. Written 2026-08-03, one author.*

**A self review is not the gate.** One person, one repo. What is true is the
mechanism, and this epic added a second one. `main` now refuses a direct push and
a released tag now refuses to move, both verified by attempting the forbidden
thing rather than by reading an API response.

## What the diff is

A generator, 371 published files, two rulesets, a CI gate, a weekly CDN job, and
the README section that makes the whole thing findable. 561 tests.

## The thing worth most attention

**The published URL is the first permanent promise this repository makes.**

Everything before this was reversible. A route can change shape, a table can be
rebuilt, a document can be rewritten. A URL that somebody pinned in production
cannot be taken back, and this epic ships the mechanism that makes that promise
real rather than stated.

That is why the tag ruleset exists and why it has no bypass actors. An author who
can move a released tag is an author who will eventually be asked to, at 2am,
because a file was wrong. The correct answer at that hour is a new version, and
the ruleset is what makes the wrong answer unavailable rather than merely
discouraged.

## What the probe found, and it was the point of the probe

The spec measured cache headers on a pinned commit and wrote that a tag was
assumed to behave the same way. The plan refused to let that assumption ship and
required a throwaway tag first.

The assumption was wrong. jsDelivr caches a semver tag as immutable for a year
and treats a non-semver tag exactly like the default branch, twelve hours at the
edge. `probe-0` proved it in one request.

`v1.0.0` is semver, so what ships is correct. It is correct because it was
checked, and a release named `release-1` under the same documentation would have
carried an immutability claim the CDN was not honouring.

## What I would push back on if somebody else wrote this

**371 files is a lot of second copy.** The tree went from 50.3 MB to 98 MB and
every byte of the increase already existed three directories away. I would ask
whoever wrote it to defend that, and the defence is in `DECISIONS.md`, which is
that a published file nobody can regenerate on a clean checkout is worse than a
large clone. I still think it is the right call and I do not think it is
obviously right.

**The `document()` emitter is hand rolled JSON assembly.** It concatenates
strings around `json.dumps` output rather than serialising a whole object,
which is the kind of thing that produces invalid JSON on an input nobody
anticipated. What makes it acceptable is that every one of the 371 files is
parsed back by the test suite, so a malformed emitter fails the build rather
than reaching a consumer. If that test coverage ever thins, this becomes the
first thing to rewrite.

**The CDN job checks one file out of 371.** Named in the QA notes rather than
hidden. Checking all of them weekly is 371 requests against a free service for a
failure mode the `--check` gate catches earlier.

## What I checked because it would fail quietly

**Whether the artifacts can drift from the corpus.** They can, locally, for as
long as it takes to push. `--check` runs on every push and pull request and
`LIMITS.md` states the window rather than implying it is zero.

**Whether a book file could contain another book's verses.** Two separate tests,
because completeness and correctness of a partition are different properties and
one test that checked both would be one test that checked neither well.

**Whether the naming refactor changed an answer.** `_name_of` and
`_abbreviation_of` moved out of the HTTP layer into the canon layer so the
generator could reach them without a second copy. 532 tests passed before the
move and after it, and the six parameterized cases in the artifact suite pin the
actual strings for three languages.

**Whether the repository going public exposed anything.** All 64 commits were
scanned for credential filenames and for assignment patterns holding a secret.
`CONTEXT.local.md` has never been tracked on any branch.

## Found while writing this

Nothing. The two defects this epic produced were both found earlier, one by the
probe and one by a test I wrote wrong.

The test I wrote wrong asserted that Sirach is named differently in Latin and in
Douay English. It is `Ecclesiasticus` in both, which is the tradition rather than
a bug, and the fix replaced a weak inequality with six exact strings. A test
asserting two things differ is a test that passes for the wrong reason as soon as
either one changes.

## What a second reviewer should look at first

The `document()` emitter, for the reason above.

Then `LIMITS.md`, specifically the section saying the CDN is somebody else's
machine. The README says no server that can go down, and jsDelivr is a server
that can go down. Those two sentences are in the same repository on purpose and I
would rather be told the framing is still too generous than have it quietly pass.
