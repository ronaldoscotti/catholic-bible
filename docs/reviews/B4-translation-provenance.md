# Code review, B4 correction, translation provenance and the 1.0.1 cut

*Stage 7. Written 2026-08-03, one author, plus a review agent run against the
epic, the conventions and what crept in.*

Same wrong order as B3 and B4 slice one. The pull request opened first and the
review ran against it. Recorded rather than tidied.

## What the diff is

The rights record inside the published data said no human had read a sample and
recorded an error rate. The author asked for that removed, and for the corpus to
state plainly that a language model produced the Portuguese and that a human
reading is pending and wanted. One string in `scripts/export-commentary.py`,
re-exported. 73 book artifacts, `index.json`, `manifest.json`, `haydock.json`
and `PROVENANCE.json` followed.

## What the review found that mattered

**The version did not move.** 75 published files changed bytes under a
`dataset_version` of `1.0.0`. `README.md` says pinning a version means the bytes
never change and corrections ship as a new tag, so the repo would have carried
two byte sets calling themselves the same release.

Nothing automated would have caught it. `build-artifacts.py --check` compares the
branch against itself and reads the version from `pyproject.toml` at build time,
so it passes on exactly this failure. That gap is real and it stays open, named
here and in the pull request rather than argued away.

**A test punished the thing the change asks for.** The sample test pinned five
defects and 2.5%, with its stated contract being agreement with prose. The prose
was gone, and a reader who accepted the README's invitation and recorded a sixth
defect would have turned the suite red. It now reads
`docs/qa/haydock-translation-review.md` and the verdict CSV and requires the two
to agree, so a sixth defect lands by editing both. Proved by mutation: the record
saying six against a CSV saying five fails.

**Three documents asserted something this change made false.** The B4 epic,
this method record and two test docstrings claimed `README.md` and `LIMITS.md`
say the reading was done by a machine in those words. Neither says it now. The
epic is the source of its GitHub issue, so the next `sync-issues.sh` run would
have republished a false claim.

## What the review found and the author overruled

The flag rate left the dataset. The old string carried 1196 records flagged and
published unedited, and that disclosure travelled inside the file rather than
only in a document. The review argued it was a separate fact from the error rate
and belonged in the data. The author had already decided, said so a second time,
and it is out of `LIMITS.md` as well. It survives in the B4 spec, which is a
dated stage artifact and was not rewritten.

## What this cost

`docs/epics/B5` criterion three came down. The README pins `@v1.0.1` because
`cdn.yml` reads the tag out of the README, and that tag does not exist until the
release lands, so the documented line returns 404 today. Running it is the whole
verification, so the box is unticked until the tag is pushed and the workflow
goes green. This is the second time that criterion has been unticked for being
claimed ahead of the evidence.
