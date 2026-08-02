# Code review, B1 canon and versification spine

*Stage 7. Written 2026-08-02, one author.*

**This is a self review and it is not the gate.** The repo has one person in it.
What is true is the mechanism: the work is on a branch, it lands through a pull
request, and nothing was pushed to `main`. A checklist that counts a self
approval as a review is decoration, and `docs/method/README.md` says so under
the gates that are not met.

## What the diff is

Nine modules under `src/catholic_bible/canon/`, two scripts, five committed data
files, one generated report, and 215 tests. No HTTP. The only route in this repo
is still `/health`.

## Things I changed after looking again

**Two-phase construction of the scheme maps.** `VULGATE.bind_inverse(org.index())`
runs after both objects exist, because the Vulgate map needs the inverse index
that the `org` map builds and the `org` map needs the Vulgate map's mode
detection. It is a knot rather than a cycle and it is contained in one loader
function, but a reader meeting `bind_inverse` cold will wonder. Left as is with
the docstring naming the reason, because the alternatives are a third object
that owns both indices or an import-time cycle, and neither is clearly better
for one call site.

**Duplicate `_parse` helpers.** `schemes.py` and `orphans.py` each carry a four
line address parser. Left duplicated. Hoisting it would put a shared utility
between two modules that otherwise have a clean one way dependency, for eight
lines.

## Things I am flagging rather than fixing

**The spine builds its dense index eagerly at import.** 35845 tuples and a dict
of the same size, on first import of `catholic_bible.canon.spine`. The suite
runs in two seconds so nothing here hurts, and B3 will import this inside a
request path where import time is paid once at boot. Worth measuring in B3
rather than optimizing now against no number.

**`map_address` matches on the scheme with no fallback branch.** All three
members are covered and `mypy --strict` is happy, so a fourth scheme added
without a branch is a type error rather than an unbound local at runtime. That
holds only while the type checker runs in CI, which it does.

**`Canon.__getitem__` is typed for an integer and carries an override ignore.**
Slicing a `Canon` would return a raw tuple rather than a `Canon`. Nothing slices
it. If B3 wants pagination this is the first thing to fix.

**The reverse direction costs a forward map per call.** `to_scheme` verifies its
own answer by mapping the candidate forward again. That is the whole reason it
is trustworthy, and it doubles the work. Fine at this size.

## What I checked specifically because it would fail quietly

**The accent.** `normalize` lowercases and trims and does nothing else. There is
no `unicodedata` import anywhere in the package, which is the property that
actually matters, because the failure mode is a helpful future edit rather than
a wrong line today. Two tests and two conformance cases pin it.

**The mode detection.** It is the only computation here rather than a lookup,
and a wrong mode is silent three layers down. The tests assert the mode of named
books directly, not only the mapped output, so a flip fails at the cause.

**Whether any claim outran the code.** The orphan report says Douay is not
reportable instead of showing zero. The checksum test is described as an
integrity check and never as an authorship check, in the docstring, in the
commit and in `DECISIONS.md`. The epic's own prediction about 1 Chronicles 6 was
wrong and the epic was corrected rather than the expectation bent. The two alias
collisions are reported rather than hidden.

**Whether the private repo leaked.** `CONTEXT.local.md` is absent from the clone
and from the image. No path to the private source appears in any committed file
except as an argument the operator passes to the export script. The cleanroom
run in the QA notes is the evidence.

## What a second reviewer should look at first

The inverse index rules. There are three of them now and they interact: first
declared wins, on-spine beats off-spine, and an address already on the spine is
never traded away. Each earned its place from a real defect, all three are in
`DECISIONS.md`, and together they are the densest reasoning in the diff.

Then the authored Latin names. They are the one part of B1 with no source to
check against, so they are exactly as good as one person's Latin.
