# Plan, B4 commentary and cross-references

*Stage 4. Written 2026-08-02, against the spec of the same date.*

**Gate.** Waived in writing with stage 3, before either document existed. Same
handling: the artifact is real, the blocking wait did not happen, and
`docs/method/README.md` says waived rather than met.

## The three questions the spec left open

### Getting 16.3 MB of HTML out without holding it twice

The corpus export builds a dictionary of 35000 short strings and serialises it in
one call. Doing the same here means the rows, the dictionary and the serialised
bytes all live at once, which is roughly 50 MB of peak for a 16 MB file. That is
survivable and it is also unnecessary.

The export streams instead. It selects ordered by anchor, writes the opening
object, writes one entry per line, and closes. `json.dumps` per entry rather than
per document. The file stays valid JSON and readable, the peak is one entry, and
the checksum is taken over the bytes as they are written.

This costs the pretty-printed shape the corpus files have. That is fine, because
nobody reads a 20000 entry file by eye and the per-line form is what makes a diff
between two exports legible.

### Whether the coverage floor is needed in SQLite

Not assumed either way. **M4 measures it.** Build the table, run the coverage
query for an address in Revelation with and without the floor, read
`EXPLAIN QUERY PLAN` and time both.

If SQLite uses the index without the floor, the floor is cut and the plan output
goes in `DECISIONS.md` as the reason the port diverged. If it scans, the floor
stays and the widest span goes in a table rather than being computed per request.

A floor that buys nothing is a magic number with a paragraph defending it, which
is exactly the kind of thing this repo's comment rule exists to stop.

### Where the review sample lives

A CSV. `docs/qa/haydock-translation-sample.csv`, drawn by a committed script with
a fixed seed, one row per entry with the address, the label, the English and the
Portuguese.

Markdown loses because a 200 row table with two paragraphs per cell is
unreadable in a diff and unfillable in an editor. CSV opens in a spreadsheet,
which is where a person doing 200 judgements actually wants to be, and the
verdict column comes back as a file this repo can count.

The sample is 200 entries, drawn uniformly over the whole corpus with a seed of
20705. Two hundred gives a usable interval on an error rate near a few percent
and it is a weekend rather than a month. The script prints the interval it
supports so the README states a bound rather than a vibe.

## Milestones

Slice one is M1 through M8. Slice two is M9 through M14. Each slice ends in its
own pull request with issue #6 linked.

### M1. The export, and what it refuses

`scripts/export-commentary.py --source <private repo>`, following
`export-corpus.py` exactly: credentials read from the private `.env` and passed
on stdin as a defaults file, never on the command line, `utf8mb4` forced, the
source commit and its date recorded rather than the run time.

Named columns, never `SELECT *`. The Catena is in the same table and one careless
star ships a corpus with uncertain provenance.

Refuses, loudly, at export time:

- any source whose code is not `haydock`
- an entry whose start or end is not on the spine
- an entry whose body is empty in the original language

Clamps, and counts what it clamped:

- an entry whose end order sits before its start order, of which there are two

Tests: a fixture-backed test that the clamp fires on an inverted pair and leaves
a normal one alone, and a test that the writer's output parses back to the rows
that went in. The export itself needs the private database and cannot run in CI,
which is the same limit `export-corpus.py` already carries.

### M2. The published file, verified

`PROVENANCE.json` beside it with the sha256, the entry count, the clamped
addresses and the source commit. A test reads the committed file, recomputes the
hash and fails on a difference, matching `test_provenance.py`.

A second test asserts the file carries 20705 entries across 73 books, both
languages present on every entry, and no entry anchored off the spine.

### M3. Loading it

`commentary.py` beside `corpus.py`. Same shape, a frozen dataclass and a cached
loader, deliberately thin. It reads the file and does not query it.

Red first: a test that asks for the entry covering `GEN.1.1` and gets one.

### M4. The tables, and the floor measurement

Schema from the spec. `build_commentary` verifies the anchor against the spine
the way `build_texts` verifies the corpus, and stops the build on a
disagreement.

Then the measurement described above, with the query plan pasted into
`DECISIONS.md` whichever way it goes.

### M5. The coverage query

`reader.commentary_covering(connection, first, last)`. One query, entries and
bodies joined, ordered by source position then entry position.

Tests, red first:

- a single verse returns the note that names it
- a verse inside a spanning note returns that note
- the widest note, 15 addresses, is found from its last address
- a verse with no note returns nothing rather than raising
- the range form does not return the same entry twice when two addresses in the
  range share it

That last one is the bug the private repo's `forRange` deduplicates, and a range
query that returns a note once per covered verse is the obvious way to get it
wrong.

### M6. The two routes

`/v1/books/{book}/chapters/{chapter}/verses/{verse}/commentary` and
`/v1/commentary?ref=&scheme=`.

The address form reuses `_book_or_404` and `_chapter_or_404`, so `Jud` and `JUD`
keep meaning Judith and Jude. The reference form reuses `resolving.read`, so the
scheme parameter works here for the same reason it works on `/v1/passage`.

A verse the spine does not have is 404 `not_on_spine`. A verse with no note is
200 with an empty source list, because absence of commentary is an answer and
not a failure, and 21042 of 35845 addresses have one.

Tests through HTTP, not through the reader.

### M7. The document, and the four gates

`make openapi`, commit the document, and let the three existing walks run.
Summary, response model, documented failure. `/v1/commentary` takes input and can
fail, so it declares its failures. Nothing here earns an exemption.

Cache headers: both routes are `IMMUTABLE`, because the answer depends only on
the address and the published corpus, and neither has a default version in it.
That is the difference from `/v1/resolve`, which does.

### M8. Provenance, the sample, and the slice one documents

`README.md` gets the translation paragraph on the first screen, in the words the
spec fixes: produced by a language model, 5.47% flagged, no human sample read
yet.

`LIMITS.md` gets the two clamped entries by address, the unread sample, and the
14803 spine addresses with no note.

`DECISIONS.md` gets the derived plain text, the body-per-language table, the
floor measurement, and the version-agnostic route shape.

`scripts/draw-review-sample.py` writes the CSV. A test asserts the same seed
draws the same rows, because a sample that moves between runs is not a sample.

The QA document walks the criteria. Criterion 2 is met, the corpus is
addressable in Portuguese. The review criterion is **not** met and stays
unchecked.

### M9. The cross-reference export

`scripts/export-cross-references.py`. Three sources. `ave-maria` is not a flag,
it is absent from the source list, so shipping it would take an edit rather than
an oversight.

### M10. The orphan report

Reads each fixture out of the private repo, resolves nothing, and reports which
fixture entries have no counterpart among the exported rows. Writes
`derived/cross-reference-orphans.json` with the count per source and a bounded
sample of the addresses.

Tested with a hand-built pair of fixture and rows, where one entry is known to be
missing and the report has to find exactly that one.

### M11. The table and the reader

`cross_references_from(connection, first, last)`, ordered by weight descending
then canonical order, cut at thirty per anchor.

Tests: the cut fires on Genesis 1:1, the order puts a curated reference above an
OpenBible one, `primary` is true at 20 and false at 19, and a whole-chapter
reference formats without a verse number.

### M12. The two routes

Same two shapes as M6. Same 404 rules. Same immutable headers.

### M13. Attribution

OpenBible is CC BY and the licence requires attribution. It goes in `README.md`
where a person reads it, in the dataset metadata inside the published file, and
in the API response as a source block rather than only in a repository footer
nobody opens.

A test asserts the attribution string is present in the response, because an
attribution that a refactor can silently drop is a licence violation waiting for
a rebuild.

### M14. The slice two documents and the criteria walk

`LIMITS.md` gets the `ave-maria` exclusion, the orphan counts, and the sentence
that OpenBible reaches no deuterocanonical book. `DECISIONS.md` gets the `na27`
reasoning, the weight threshold and the thirty-per-anchor cut.

## Where test driven does not apply

**The export scripts.** They need the private database. What is tested is the
parts that are pure, the clamp, the writer and the orphan diff, against
fixtures. The run itself is verified by the provenance test on its output, which
is what B2 established and what CI can actually check.

**The review sample being correct Portuguese.** No test can tell a faithful
translation from a fluent wrong one. The verification is a person reading 200
rows, and this epic ships the sample rather than the verdict.

**The attribution being legally sufficient.** A test can assert a string is
present. Whether it satisfies CC BY is a reading of the licence and it is
written down in `LIMITS.md` to be argued with.

## Risks

**The export is slow or the file is unwieldy.** 16.3 MB in one JSON file that the
build parses on every `make db`. If it hurts, the fallback is one file per
language, which halves each parse and costs a small duplication of the anchors.
Measured in M2 rather than guessed at.

**The clamp hides a wider extraction problem.** Two inverted entries were found
by looking. There may be entries whose end is merely wrong rather than inverted,
and nothing here would catch that. What this ships is the check that finds
inverted ones and a limit that says the label was not parsed.

**The thirty-per-anchor cut looks arbitrary.** It is the private repo's number,
ported rather than derived. `DECISIONS.md` says so instead of dressing it as
analysis.
