# Plan, B11 Catechism cross-references

*Stage 4. Written 2026-08-05, against the spec of the same date and issue #18.*

**Gate.** This is a human review gate. No implementation code exists yet. Two
things do exist, and both happened before this document rather than after it.
The link shape was verified against the live site, which the epic makes the first
act of the epic. And nine unresolved labels were traced to two defects in the
upstream extractor and fixed there, which is why this plan reads shorter than the
spec's open question suggested.

## Shape

One pull request. The epic is not large enough to slice and nothing in it waits
on a release.

Eight acceptance criteria. Seven can close inside the pull request. The eighth,
the hand check against the printed Catechism, closes on a reading rather than on
a test, and it stays unticked until that reading has a number attached.

## What this plan refuses to assume

Five. Each has to be measured before anything claims it. B9's plan carried three
refusals and two of them paid. B10's plan carried an open question it chose not
to close and that decision would have failed the first release.

**1. That the English page map is buildable.** Nineteen pages were sampled and
the first paragraph number came out clean on sixteen of them. Three returned
nothing, and one of those three, `__PD.HTM`, holds paragraphs 44 to 49 behind an
`<i>` the sample regex did not expect. The full walk over 374 pages is the only
thing that establishes the map, and the build fails rather than publishes unless
the first paragraph numbers are strictly increasing and cover 1 to 2865 with no
gap and no overlap. **A map that is 99% right sends readers to the wrong page and
looks fine.**

**2. That a built link resolves.** The shape was verified by reading the site's
structure. That is not the same as constructing a link from a paragraph number
and getting the page holding it. One link per language is opened against the live
site before either is published, and the paragraph is found on the page that
comes back.

**3. That resolving against the spine means the citation is right.** It does not.
The nine defects found so far were caught because they resolved to nothing, and a
wrong citation that happens to be a valid address resolves silently. `Ef 1,21`
where the footnote says `Eph 1:22-23` is exactly that shape and it is in the data
now. The hand check is the only instrument for this class and the plan does not
pretend otherwise.

**4. That the response model cannot leak text.** A test asserting that today's
model has no text field passes forever while somebody adds one. The test asserts
over the model's declared fields rather than over a list written beside it, so
adding a field to the response is what breaks it. It covers the reverse direction
too, which is the one where a breadcrumb would feel most natural to add.

**5. That the text fragment works.** It is a browser feature and no server
promises it. One is opened in a browser in each edition and the result is written
down, and if it does not scroll the field ships anyway, since a URL with an
unused fragment still opens the right page. What is refused is claiming it works
in the README without having watched it work.

## Where test-driven development does not apply

The English page map. It is a walk over a third-party site and there is nothing
to write a failing test against first. What it gets instead is the contiguity
check described above, which runs on every build of the map and is the real
verification, plus a committed fixture of ten known page and paragraph pairs that
a unit test reads without touching the network.

The link shape verification and the hand check are not tests either, and the
spec says so.

Everything else is test first.

## Tasks

**1. The export script.** `scripts/export-catechism.py`, beside the four exports
already there and following their shape. Reads the corrected fixture from the
private repository, parses every label with B1's parser, maps through `org`,
expands ranges onto spine orders, and writes `citations.json` keyed by verse,
`paragraphs.json` keyed by paragraph, `orphans.json` and `PROVENANCE.json`. Every
entry in both directions carries the citation as the Catechism wrote it beside
the resolved ids. The provenance record names the private commit and its date,
and names the upstream release the fixture came from and that it declares no
licence.

**2. The page map script.** `scripts/build-catechism-pages.py`. English from the
walk, Portuguese from the index file names. Writes `pages.json`. Runs on demand,
never in CI, and its output is committed with a checksum like every other
published file. Contiguity check inside it, so a broken walk fails loudly.

English is written first and it is the edition the examples use, because its
pages average 7.7 paragraphs against 106 in Portuguese. The expensive map is the
one worth having and the first draft of the spec had that backwards.

**3. The reader.** `src/catholic_bible/catechism.py`, thin, shaped after
`cross_references.py` beside it. Loads the artifact and hands back what it holds.
It answers no question about the Catechism and it holds no text.

**4. The link builder.** Paragraph number and language in, URL out. Pure, so it
is tested without the network. Both editions, the prologue special case in
Portuguese, which is the one page whose name carries a space, and the text
fragment as a second field beside the plain page link.

**5. The routes.** `GET /v1/books/{book}/chapters/{chapter}/verses/{verse}/catechism`
and `GET /v1/catechism?ref=`, mirroring the cross-references pair including its
404 reasons and its `Cache-Control`, plus
`GET /v1/catechism/paragraphs/{number}` for the reverse direction. Response
models in `models.py`, summary, response model and documented errors on all
three, because CI fails a route missing any of the three.

**6. The artifact and the manifest.** `build-artifacts.py` grows the new files so
they reach the CDN and the npm package. `openapi.json` regenerates.

**7. The prose.** `LICENSE` grows one row naming the index and its basis.
`LIMITS.md` grows a section saying the basis here is thinner than for anything
else in the repository and why. `DECISIONS.md` records the scheme, the range
expansion and the link fallback. `README.md` gains the route. All through the
voice skill, zero em-dashes.

**8. The hand check.** A sample drawn by `draw-review-sample.py`, read against
the printed Catechism, with the size and the error rate written down whatever
they are. `docs/qa/` carries it.

## Order, and why

1 before 3, because the reader reads what the export writes.

2 before 4, because the link builder needs the map to build against.

**2 before everything that claims the epic works.** If the walk cannot produce a
contiguous map the link criterion has no honest answer, and finding that out
after five tasks of work is finding it out too late. It is second for that reason
and not because it is easy.

5 last of the code, because a route over a reader that does not exist yet is a
route that tests nothing.

8 after the pull request opens if it has to. It is the only criterion whose
instrument is a person and it is the only one allowed to stay open.

## What closes and what does not

Seven criteria close inside the pull request. Given a verse the dataset returns
paragraph numbers, every entry carries a link, the link shape is verified and
recorded, no text ships, the dataset is one directory with its own licence line,
`LIMITS.md` states the basis, and an unresolved citation comes back as an orphan
with a reason.

**The hand check does not close on code.** It closes when somebody reads a sample
against print and writes the number down. Until then it stays unticked, the way
B5 left two boxes empty through a whole pull request rather than ticking them on
the mechanism that would eventually prove them.
