# Plan, B2 corpus export and integrity

*Stage 4. Written 2026-08-02, against issue #4 and the spec dated the same day.*

**Gate.** The spec was approved before this was written. Implementation starts
after this document, not before.

## The one question the spec left open

**How a database gets pinned to a commit.** A file has a git hash. A table does
not, and the export cannot tell a database built from the current code from one
built three weeks ago and never rebuilt.

The answer here is to record what the content is a function of, and to say
plainly what that does not cover.

Provenance records the source commit, and the sha256 of every fixture the import
declares as its input, `matos-soares.json.gz` and `vulgata-source.json.gz`. Those
two plus the import code at that commit are what produce the tables. The export
already refuses a source whose files are dirty, carried over from B1.

What it does not cover is a stale database: fixtures and code at commit X, tables
still holding the result of commit W. Nothing readable from inside the database
detects that. The job that closes it re-runs the import at the recorded commit
and diffs, which is criterion six, and `LIMITS.md` says so in those words rather
than letting the checksum imply more than it proves.

## Milestones

Written against the ten acceptance criteria rather than against a shape, because
the B1 plan decomposed nine milestones and still missed a criterion.

### M1. One version crosses over, with the exclusion proved

Criteria 1 and 3, for one translation.

- `scripts/export-corpus.py`, reading the private repository the way
  `export-spine.py` does, through `docker exec` into the MySQL container so no
  credentials and no port reach this repo
- The query emits JSON from MySQL directly rather than TSV. Verse text is prose
  and a delimiter format invites a quoting bug that shows up in one verse out of
  35000
- Per book, so no single result has to fit in one aggregation buffer
- Matos Soares first, because it is the one carrying the material that must not
  travel

The test that matters here is not that the text arrived. It is that the heading
did not. 2305 Ave Maria pericope headings sit in the `heading` column of the same
rows. A test asserts no published record carries a heading field and that the
export query names its columns explicitly, so a future `SELECT *` fails rather
than ships.

### M2. All three, with their licences

Criteria 1 and 10.

- Clementine Vulgate and Douay-Rheims, both out of the same upstream fixture
- Each file carries its version metadata as data rather than as prose: code,
  language, year, licence, the public domain basis, the source URL
- Matos Soares carries article 45 of the Brazilian copyright law and the 1957
  death with no successors. The Vulgate and Douay carry the MIT fixture

Tests. 73 books present in each. Book codes match the canon exactly. Every key
parses as a B1 published id. Counts match what the database holds, so a silent
truncation fails.

### M3. Every verse resolves, and what does not is reported

Criterion 2, and the honest half of the epic.

Each exported address goes through the B1 spine. Anything that does not resolve
is reported rather than dropped.

Two different measurements, named separately because the epic conflates them:

- **Orphan**, a source verse that reached no spine address
- **Unfilled**, a spine address no version reached. 69 for the Vulgate and Douay,
  282 for Matos Soares, measured during the spec

Published per book, in the same shape B1 used for `orphans.json`, with a test
that regenerates and diffs.

### M4. Checksums and provenance

Criteria 4 and 5.

- Every published file gets a sha256 in the provenance record, alongside the
  source commit, the source commit date and the input fixture hashes
- The CI job recomputes on a clean checkout with no access to the private source

This extends `PROVENANCE.json` rather than adding a second record. B1 already
ships the file and the test that recomputes it.

### M5. The job with teeth

Criteria 6 and 7.

`make verify-export` re-runs the export at the recorded source commit and diffs
against what is committed. Byte identical or it fails.

**This does not run on GitHub.** It needs the private repository and a running
database, and this project has no self-hosted runner. So it is a documented
command that runs where the source lives, and `LIMITS.md` says a stranger cannot
run it. Wiring it to CI and claiming a green build proves authorship would be the
worst possible outcome here, so the plan names the limit instead of hiding it.

Determinism has to be built in rather than hoped for. Rows come back ordered by
canonical order, JSON keys are written in a fixed order, and the export date is
the source commit date, carried over from B1.

### M6. LIMITS.md

Criteria 8 and 9.

The file lands here rather than waiting for B7, because two of B2's criteria
name it. B7 expands it.

It records the per book orphan rate with the cause, the unfilled counts, that a
stranger cannot rebuild the dataset, and which of the two jobs a stranger can
actually run. Also the residual the checksums cannot see, a database built at an
older commit.

Prose, so it goes through the voice skill and carries no em-dashes.

### M7. The epic gets corrected

Not a criterion, a consequence.

The epic says the Vulgate demonstrates the spine with zero orphans and calls it a
live proof inside the release. The import declares a tolerance of 30 and 69 spine
addresses hold no Vulgate verse. The claim is replaced with whatever M3 measures.

## Where test-driven does not apply

M1's query against a live database is not unit tested, because the thing under
test is a database this repo does not own. What is tested is everything after the
query: the shape of the published record, the absence of headings, the resolution
against the spine, the counts.

M5 is a verification and not a test, and it is named as one.

## Risks

**The heading leak is the one that matters.** It is copyrighted material one
column away from material that ships. The mitigation is that the export names its
columns and a test asserts the published files carry no heading key, so both the
query and the output have to fail together for it to escape.

**A stale database ships silently.** Named above, closed only by M5, stated in
`LIMITS.md`.

**Size.** Three files of a few megabytes each, in git forever. If compression
wins, it costs a decompression step in every consumer including B5's `fetch()`.
Decide against a measured number in M2 rather than now.
