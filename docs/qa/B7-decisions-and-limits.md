# QA, B7 decisions and limits

*Stage 6. Run 2026-08-03 against `docs/b7-decisions-and-limits`.*

Reading the diff is not QA. What follows was run, and the output is pasted
rather than summarised.

## What the epic got wrong, and it was in this project's favour

Criterion 2 asks for the orphan rate per book and per scheme. Earlier in the
session I said it could not be met as written, on the grounds that `LIMITS.md`
already declares the orphan rate unmeasurable here. That was half right and the
wrong half was acted on.

Two different failures share the word. A source verse the import dropped is
genuinely not measurable from inside this repository, because the import runs
where the private source lives. A scheme address that reaches no slot on the
spine is measured, has been measured since B1, and sits in `data/orphans.json`
broken down by book and by reason. The old section conflated them and answered
only with the unfilled counts, which are the B2 side of the question.

So the criterion is met on the data the repo already had. The section is split
in two, both senses are named, and the measurable one is published.

## The acceptance criteria, walked

**1. `DECISIONS.md` records each hard call with the alternative that lost and
why, covering the five named.** Met. Two were already there and three were not.

| Named in the criterion | Entry | Status |
|---|---|---|
| Superset spine instead of an intersection | The spine is a superset of the schemes rather than their intersection | added |
| Per-book conditional remapping instead of a fixed table | The remapping mode is decided per book by counting, not by a fixed table | added |
| Dropping orphans instead of extending the spine | An address with no slot is dropped and reported, not accommodated | added |
| A structured public id instead of an opaque integer | The verse id on the wire is the published string | already there |
| Orphans as return values instead of exceptions | An unresolvable reference is a value, not an exception | already there |

The three added ones were absent because they were inherited from the working
implementation rather than decided here, and `DECISIONS.md` only started being
written partway through B1. Each was written after reading the source it came
from, `VersificationSuperset.php` and `VulgataVersificationMap.php`, so the
alternative that lost is the one that actually lost rather than a plausible
opposite invented to fill the slot.

**2. `LIMITS.md` states the orphan rate per book and per scheme, with the cause
for each concentration.** Met. Three tables and every number pinned to
`orphans.json` by a test.

```
| Scheme             | Addresses examined | Resolved | Orphans |
| Clementine Vulgate | 39046              | 35838    | 3208    |
| org                | 38371              | 35498    | 2873    |
| Douay              | not reportable     |          |         |
```

Every one of the 3208 has a named cause and the causes sum to the total. 3039
are addressed at a book the spine does not carry as a book, 147 are Vulgate
psalm titles at verse 0, 13 are Sirach 52, and 9 are single verses one past the
end of a chapter. The per-book table names all fourteen off-spine books and the
nine single verses are listed by address.

**3. `LIMITS.md` records the rights audit per asset, with the legal basis and
what was excluded.** Met, and it was met before this epic. Eight assets, each
with the text status, the legal basis and the fixture licence, plus the
permanent exclusions and the paragraph on the Ave Maria headings. Read and left
alone rather than rewritten for the sake of a diff.

**4. `README.md` and `README.pt-BR.md` both exist and link to each other from
the top.** Met. `README.pt-BR.md` is a short door by decision rather than a
mirror, and the author asked for the small version now with iteration later.

The `fetch()` one-liner is duplicated in both, which is the one thing that can
drift. `cdn.yml` reads the tag out of the English README and verifies it against
the live CDN, and nothing verifies the Portuguese copy, so a release bumping one
and not the other would leave a documented 404 nobody runs.
`test_the_two_readmes_publish_the_same_fetch_line` closes that.

**5. `CONTRIBUTING.md` states that no alias and no scheme enters without a
conformance case.** Met, and it says why with the case that makes it concrete.
`Jo` is John and `Jó` is Job, and folding the accent turns every Portuguese
reference to Job into John without failing anything a reader would notice.

**6. A diagram shows schemes entering, the spine in the middle, and the layers
hanging off it.** Not ticked yet. Mermaid in `README.md`, so it needs no image
binary and no build step, and GitHub renders it natively.

Valid syntax is not a rendered diagram. The criterion says the diagram shows
something, and that is answered by looking at it on the pushed branch. Ticked
below once it has been.

**7. Every prose document passes the voice check, including zero em-dashes.**
Met on the half a machine can answer.

```
$ uv run scripts/lint-voice.py
18 documents clean
```

The human read is the author's and it is the review gate on this pull request,
not something this document can tick on his behalf.

## The lint, and proving it is not decorative

A lint that passes on everything is worse than no lint, so each rule was made to
fail on purpose before it was trusted.

```
$ sed -i '' '1s/^# catholic-bible/# catholic-bible — a porta/' README.pt-BR.md
$ uv run scripts/lint-voice.py
README.pt-BR.md:1: em-dash

1 findings across 18 documents
exit 1
```

The banned word, banned phrase and signposting opener rules each have a failing
case in `tests/test_voice.py`, along with the cases that must not fire.
`overwhelmed` does not trip `realm`, a banned word inside a fence or inside
backticks is a filename rather than a voice, and `Old Testament` is allowed
because `testament` is on the voice skill's English list and a repository about
the Catholic canon has to be able to write it.

## The number tests, proved the same way

Every table in the orphan section is read out of the markdown and compared to
the JSON it came from.

```
$ sed -i '' 's/^| 2 Esdras | 942 | 942 |/| 2 Esdras | 943 | 942 |/' LIMITS.md
FAILED test_every_book_row_is_the_count_the_report_carries

$ sed -i '' '/^| Psalm 151 | 7 | 7 |$/d' LIMITS.md
FAILED test_the_published_book_table_leaves_no_off_spine_book_out
```

The second one matters more than the first. Changing a number is loud and a
reader would probably catch it. Deleting a row is silent, and a book quietly
missing from the concentration table is exactly the failure this document
promises not to have.

```
$ sed -i '' 's|catholic-bible@v1.0.1|catholic-bible@v1.0.0|' README.pt-BR.md
FAILED test_the_two_readmes_publish_the_same_fetch_line
```

## What this cost

One mistake, recorded rather than tidied. Undoing a mutation with `git checkout
LIMITS.md` reverted the whole uncommitted B7 rewrite of that section, because
the file was modified and not yet committed. It was rewritten from the same
edit and the suite confirms it came back identical. Mutating a tracked file with
uncommitted work in it needs a copy first, and that is the lesson rather than
the checkout being wrong.

## The full suite

```
$ uv run pytest -q
586 passed in 22.45s

$ uv run ruff check . && uv run ruff format --check . && uv run mypy
All checks passed!
124 files already formatted
Success: no issues found in 62 source files

$ uv run scripts/build-openapi.py --check
the committed document matches the routes

$ uv run scripts/build-artifacts.py --check
the committed artifacts match the sources
```

565 before this epic and 586 after, which is 21 new tests. 11 on the voice lint
and 10 on the numbers `LIMITS.md` publishes.
