# Code review, B7 decisions and limits

*Stage 7. Written 2026-08-03 against `docs/b7-decisions-and-limits`, one author.*

Same order as B3, B4 and B5. The branch was pushed before the review ran,
because the diagram criterion could not be answered without a pushed branch.
Recorded rather than tidied.

## What the review found

**The phrase rule had a hole the width of the wrap.** The lint checked banned
phrases line by line while every document here is hard wrapped at 80 columns. A
four word phrase is about as likely to straddle a break as to sit inside one, so
`it's worth noting that` was caught or missed depending on where the paragraph
happened to wrap. That is a rule whose behaviour depends on formatting, which is
the same as no rule.

Fixed by checking phrases against the joined paragraph and keeping words,
openers and em-dashes on the line, since those are genuinely line local. Two
tests, one for each side of the break, plus one proving a blank line still
separates two paragraphs so the phrase is not manufactured across a gap.

**The word rule matched one inflection and the prose uses the others.** Found in
a second pass. `\bleverage\b` catches a form nobody writes and misses
`leverages` and `leveraging`, `utilize` misses `utilizing`, `meticulous` misses
`meticulously`. Worse on the Portuguese side, where every entry was an
infinitive, so `alavancar` was listed and `alavanca` was what a document would
actually contain. The lists are stems now with a trailing `\w*`, the leading
word boundary stays so `overwhelmed` still does not trip `realm`, and the
widened rules report the same 18 documents clean.

**The opener rule was blind wherever these documents put prose.** It stripped
emphasis and blockquote markers and nothing else, so `- Moreover,`,
`## Furthermore,` and `1. Additionally,` all passed. The acceptance criteria in
every epic file, most of `CONTRIBUTING.md` and half of `LIMITS.md` sit behind
one of those markers, which makes this the common case rather than the edge.

**The opener rule still requires the comma and that is deliberate.**
`Ultimately, the` is caught and `Ultimately the` is not. Dropping the comma from
the pattern would fire on a line that merely starts with the word because the
sentence above it wrapped, and a lint that cries wolf on correct prose gets
disabled within a week. It is a narrower rule than the voice skill states and
this is where that is written down.

**`DECISIONS.md` quoted four numbers that nothing held.** 3208, 3039, 2286 and
753, in the entry whose neighbours in `LIMITS.md` are all pinned to
`orphans.json`. The document recording the lesson about prose drifting from data
was itself the example. `test_the_orphan_counts_in_decisions_are_the_measured_ones`
derives all four, including the split between books not received as Scripture
and canonical text carried inside another book, which is a judgement encoded as
two sets rather than a number typed twice.

**Criterion 4 was met and unpinned.** Deleting either cross-link left the suite
and the lint green. Two assertions on the first five lines of each README close
it.

**`testament` is off the English banned list.** The voice skill bans it and a
repository about the Catholic canon has to be able to write Old Testament. The
carve-out is in the script with the reason beside it and a test pins it, rather
than being discovered by whoever next tries to describe the superset rule.

## What the acceptance walk found

**The second criterion was nearly abandoned on a misreading of this repo's own
documentation.** Earlier in the session I read `LIMITS.md` saying the orphan rate
is not measured here, took it at face value, and reported to the author that the
criterion could not be met as written.

Two different failures share the word. The sentence was true about one of them
and the criterion was asking about the other, which had been measured since B1
and published in `orphans.json` the whole time. The document conflated them
under one heading and I inherited the conflation instead of checking the data.

The fix is the section split in two, but the lesson is not about the section. A
limit this repo publishes was wrong enough to almost cost an acceptance
criterion, and nothing failed. The prose said unmeasurable and the JSON beside
it carried the measurement.

`tests/layers/test_published_limits.py` is the answer to that. Every number in
the orphan section is read out of the markdown and compared to the file it came
from, including the claim that the book table lists all of them, so a row
deleted from the table turns the suite red rather than quietly shrinking what
the reader sees.

**A diagram with valid syntax was still the wrong diagram.** The first render
put `orphans.json` on the main rank, which left the arrow into the translations
reading as though the orphan report fed them, and the criterion says the spine
is in the middle. Nothing was invalid. Any test that could have been written
would have passed both versions. It was caught by opening the file on GitHub and
looking, which is the only thing that could have caught it.

## What this cost

One self-inflicted loss, recorded. Undoing a mutation test with `git checkout
LIMITS.md` reverted the entire uncommitted B7 rewrite of that section, because
the mutation and the work were in the same unstaged file. It was rewritten from
the same edit and the suite confirmed it came back identical, so nothing shipped
wrong. Mutating a tracked file with uncommitted work in it needs a copy taken
first.

## What is still open

**The voice lint is a floor and not the voice.** It catches an em-dash, a word
off a list and a signposting opener. It cannot catch a paragraph that is
grammatical, unbanned and reads like nobody wrote it, which is most of what the
voice skill is actually for. The epic's verification names a human read for that
reason and this document does not tick it.

**The banned lists are a subset, committed here rather than imported.** They
come from a private skill that is not in this checkout and they will drift from
it. The alternative is a lint that cannot run on a fork, which is worse.

**The type checker did not read `scripts/`, and this epic makes a script into a
CI gate.** Written into `LIMITS.md` first, on a measurement that said widening
the configuration lights up thirteen errors in nine files. The author read that
sentence and said fix it, which was the right call, because the measurement was
taken the wrong way.

Eleven of the thirteen came from running `mypy scripts` on its own, where this
package resolves as an installed dependency rather than from the source tree.
Adding `scripts` to the configured set puts `src` and `scripts` in the same
pass, the imports resolve from source, and eleven of them stop existing. Two
were real and are fixed. `provenance['source']['commit']` indexes twice into a
`dict[str, object]` in both exporters, and both now hold the commit in a local
instead, which calls git once and reads better.

75 files checked where there were 62. `LIMITS.md` loses the section, because a
limit that has been fixed is not a limit.

**The PEP 561 marker was missing and that is a separate bug.** `py.typed` did
not exist, so anything installing this package and running a type checker got
`import-untyped` on every module. It was found while chasing the above and it
is not what fixed it. With `src` in the same mypy pass the marker is never
consulted, which was proved by deleting it and watching the suite stay green.

That makes it unenforced by anything, so `tests/test_packaging.py` asserts it
exists and sits inside the packaged tree. Packaging belongs to B10 and this is
one empty file against a defect that would have shipped with the first release
to PyPI, so it lands here rather than waiting.

**The QA document went stale inside its own pull request.** It pasted 586
passing tests and concluded 21 new ones, while the branch ran 588 and the method
record in the same diff said so. Two tests had landed after the paste. It is
re-run rather than hand corrected, because a hand corrected paste is not output.
The rule this repo already had, that a number nobody recomputes is a number
nobody can check, applies to its own process documents too.
