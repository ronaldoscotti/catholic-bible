# Plan, B5 static artifacts and CDN

*Stage 4. Written 2026-08-03, against the spec of the same date.*

**Gate.** Stage 4 is a human review gate and it is open. The three questions the
spec carried came back answered. Cross-references ship. The tag is `v1.0.0`. The
directory is `data/`. No implementation code exists yet.

## What the answers settled

Everything B2 and B4 published goes out as artifacts, split per book, which is
365 files and roughly 48 MB against a package limit of 150 MB.

`v1.0.0` is the number, on the author's word that B6 and B7 land tomorrow. **The
tag does not get pushed until they do.** The plan builds and merges the
artifacts, and the release is a separate act, because a tag under a ruleset that
blocks `update` cannot be taken back and a `v1.0.0` pointing at a repository with
no deploy would be permanent. M14 is where that decision gets made and it is the
only milestone that can be deferred without stranding the rest.

## Shape of every published file

Rights travel inside the file. This is the whole reason the shape is not just the
verses.

```jsonc
// data/versions/matos-soares/books/SIR.json
{
  "version": { "code", "name", "abbreviation", "language", "year",
               "source_url", "rights": { … } },
  "book":    { "code", "name", "abbreviation", "testament", "group",
               "deuterocanonical", "chapters" },
  "verses":  { "SIR.24.1": { "order": 24380, "text": "…" }, … }
}
```

```jsonc
// data/commentary/haydock/books/SIR.json
{
  "source": { "code", "name", "author", "language", "translations",
              "rights": { "text", "text_basis", "translation", "translation_basis" } },
  "book":   { … },
  "entries": [ { "start", "end", "start_order", "end_order", "label",
                 "position", "body": { "en-US", "pt-BR" } }, … ]
}
```

```jsonc
// data/cross-references/books/SIR.json
{
  "sources": { "openbible": { "name", "rights", "rights_basis",
                              "attribution", "url" }, … },
  "book": { … },
  "references": { "SIR.24.1": [ { "to", "end", "whole_chapter",
                                  "primary", "source" }, … ] }
}
```

The OpenBible notice sits in all 73 cross-reference files. CC BY requires
attribution to travel with the data and a static file has no envelope to put it
in.

## Milestones

TDD throughout except M11, M14 and M15, which are named below with the real
verification instead of a decorative test.

**M1. The generator refuses to invent.**
`scripts/build-artifacts.py` with `--check`, mirroring `build-openapi.py`. Red
test first, that the script writes nothing when a source file is missing and
exits non-zero. No timestamp anywhere in the output, for the reason B2 has no
export date.

**M2. Corpus per book.**
219 files. Test asserts 73 books per version, that every verse id in the split
appears exactly once, and that the union of the splits equals the monolith
verse for verse. That last one is the test that matters, because a partition bug
loses a book quietly.

**M3. Commentary per book.**
73 files. Test asserts the entry count sums to 20705, that no body carries a
`[[[` marker, and that the published source set is exactly `haydock`. The Catena
Aurea shares the source tables and must never appear.

**M4. Cross-references per book.**
73 files. Test asserts the anchor and reference counts sum to what the monolith
holds, that `ave-maria` appears in no file, that the OpenBible attribution is
present in every one of the 73, and that `WIS` and `SIR` carry references, which
is the deuterocanonical claim the epic exists for.

**M5. The four small artifacts.**
`canon.json`, `spine.json`, `orphans.json`, `coverage.json`. Copied through with
their shape unchanged, tested by comparing against the committed source.

**M6. `index.json`.**
The entry point. Lists versions, commentaries, cross-reference sources, the
book codes, and the URL pattern as a template string. Test asserts every path it
advertises resolves to a file that exists on disk.

**M7. `manifest.json`.**
`sha256` and byte count per file, plus the dataset version and the B2 source
provenance. Test recomputes every hash from the tree and fails on a mismatch,
which is the same job CI will run on a clean checkout.

**M8. Determinism.**
Test generates twice into two temporary directories and compares byte for byte.
B2 promises this of the export and the same promise has to hold here or the
`--check` gate flaps.

**M9. `make artifacts` and the CI gate.**
Makefile target, and `build-artifacts.py --check` added to the `checks` job. A
corpus that changed without the artifacts following fails the build, which is
what `openapi.json` already does for routes.

**M10. The negative tests.**
No Catechism text, no Catena, no Ave Maria, in any of the 365 files. Grep-level
and cheap, and they are the ones that would be catastrophic to get wrong.

**M11. The README, and the line that has to be executable.**
Not TDD. The fetch line goes in `README.md` and `README.pt-BR.md` through the
`write-in-my-voice` skill, along with the URL pattern and the versioning rule.
Real verification is M13, which runs the line rather than reading it.

**M12. `LIMITS.md` and `DECISIONS.md`.**
Not TDD. The tree size cost, the 4.3% headroom on the commentary file, the
per-chapter cut, and the sentence in `LIMITS.md` that currently says a stranger
cannot rebuild the dataset, which now needs its second half about the artifacts.

**M13. The CDN job.**
A workflow that greps the exact fetch line out of `README.md` and runs it against
the live CDN, on tag and on a weekly schedule. Weekly is the one that matters. A
check that fires only at release proves the URL worked once.

Before any of this is claimed, the mechanism gets proved with a throwaway tag
named `cdn-probe-0`, pushed, fetched, its cache headers read, and deleted. That
proves jsDelivr pins a tag the way it pins a commit, which was measured for a
commit and assumed for a tag. Assumed is not measured.

**M14. The tag ruleset.**
`refs/tags/v*`, blocking deletion and update, no bypass. Verified by pushing a
tag, moving it, and being refused, the same way `main` was verified with `GH013`
rather than with an API response.

**M15. The version bump.**
`pyproject.toml` to `1.0.0`. `__version__` reads installed metadata, so this
needs `uv sync`, and it changes the health response, the README line CI greps,
and `openapi.json`. All four move in one commit or CI catches it, which is the
gate working.

**M16. QA and review.**
`docs/qa/B5-static-artifacts.md` and `docs/reviews/B5-static-artifacts.md`. QA
includes the thing that cannot be unit tested, which is opening a blank HTML file
in a real browser and reading Sirach 24:1 off the page.

## What is not built

Per chapter files. Minified variants. An npm package, which is B10. Any change to
how the API or the SQLite build read data, because the artifacts are a new output
and not a new input, and rewiring `commentary.py` to read 73 files instead of one
would be B4 work smuggled into B5.

## The three questions this plan cannot answer

**One. Does `v1.0.0` get pushed in this pull request or after B6 and B7?** The
plan assumes after, and builds everything so that the push is a one line act. If
you want it inside this PR, say so and M14 moves ahead of M13.

**Two. Does the weekly CDN job open an issue when it fails, or just go red?** A
red badge on a repository nobody is watching that week is a check that reports to
nobody. I lean to opening an issue, and it is three lines.

**Three. Is 86 MB of clone acceptable, or should the monolithic files leave the
tree once the per-book ones exist?** Removing them is a bigger change than it
looks, because `commentary.py`, `build.py`, the provenance records and their
checksums all point at the monoliths. I recommend keeping both and paying the
bytes, and I would rather ask than assume that a clone cost this large was
obvious to you.
