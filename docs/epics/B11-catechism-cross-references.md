# [B11] Catechism cross-references

| | |
|---|---|
| Milestone | v1.1 |
| Labels | `epic` `area/data` `milestone-spec` |
| Depends on | B1, B2, B4 |
| Blocks | nothing |

*Milestone spec. Expanded against the code that exists when it is reached.*

**As** a developer showing a verse to a reader
**I need** to know which paragraphs of the Catechism cite that verse, and to be able to send the reader to the official text
**So that** Scripture and the Church's reading of it are one click apart instead of two searches apart

## Context

The Catechism cites Scripture constantly and the citations run one way in print. You read a paragraph and it points you at a verse. Nobody publishes the reverse, so a developer holding a verse cannot ask which paragraphs of the Catechism have something to say about it.

That index is small, it is factual, and it is the sort of thing that makes an application feel like it knows what it is talking about. It costs one file and it needs no text.

This is deliberately less than what the private repo does. There the Catechism is present as a corpus. Here only the citation graph crosses over, and the reader goes to `vatican.va` for the words.

## Source

The extracted citations exist in the private repo named in `CONTEXT.local.md`, as `catechism-scripture-citations.json.gz`. They come out through the B2 export like everything else, with a checksum and a provenance record.

The private repo also serves a `catechism` endpoint that returns Catechism text. That endpoint does not port and this epic is not a smaller version of it.

## Problem

A reader who wants to know what the Church teaches about a verse has to open the Catechism and search it, which means leaving the application and knowing what to search for. The link between the two exists in print and nowhere in machine-readable form on the Catholic side.

## What the live site returned

*Run 2026-08-05, before any code in this epic was written, which is what the
third criterion asks for.*

**A per-paragraph deep link does not exist, in either edition.** The fallback
named below is not a fallback. It is the only shape available, and this is the
record of finding that out.

**English**, at `/archive/ENG0015/`, is an IntraText build across 374 pages named
`__P1.HTM` through `__PAE.HTM`. Those ids are a base 36 sequence in document
order and carry no paragraph number. The pages hold anchors and the anchors are
footnote markers. `__P16.HTM` opens at paragraph 199, which is knowable only by
reading the page.

**Portuguese**, at `/archive/cathechism_po/index_new/`, puts the paragraph range
in the file name, as in `p1s2c1_198-421_po.html`. Twenty six such pages, running
from 26 to 2865 with no gap, plus one for the prologue.

The two are not symmetric and no pattern relates them.

**English is the edition worth linking**, which is the opposite of what the cost
of building the map suggests. Its pages average 7.8 paragraphs. Portuguese
averages 106, so a Portuguese link opens a page holding a hundred paragraphs and
leaves the reader searching it.

The map is built and committed, and the first one that passed every structural
check was wrong. It read footnote markers as paragraphs, so the prologue page
claimed 1 to 4 off three superscripts and a scripture reference, and every page
to 17 was one page early. Coverage, ordering and uniqueness all passed, because a
map that is uniformly early is still contiguous. A reader following a link for
paragraph 1 would have landed on a page with no paragraph 1 on it.

What catches that is opening the page and looking, so `--verify` does exactly
that. On the corrected map, 134 paragraphs sampled across both editions and the
whole range, including 1, 2, 3, 4, 17, 624 and 2865, and every one was on the
page the map names. Run against the map that shipped, the same check reports
paragraph 1 absent from the page it was sent to.

## What blocked this, and how it was cleared

**Issue #36.** `Scheme.ORG` is hebrew numbering and counts a psalm superscription
as verses. The Catechism cites in english numbering, which does not. An english
address is a valid `org` address, so it mapped cleanly, produced no orphan, and
landed one or two verses early. B4's published apparatus had the same defect,
which is why the issue was against B1 rather than here.

Closing it added `Scheme.ENGLISH`, corrected 15672 addresses in the published
apparatus, recovered 5631 references that had been dropped rather than misplaced,
and moved the dataset to `2.0.0`.

## Acceptance criteria

- [x] Given a verse id from the B1 spine, the dataset returns the Catechism paragraph numbers that cite it
- [x] Every entry carries a link to the official text on `vatican.va`
- [x] The deep-link shape is verified against the live site before anything else in this epic is built, and the epic records what was found
- [x] Not one word of Catechism text ships. No paragraph text, no first line, no summary, no paraphrase, no title
- [x] The dataset ships as its own artifact with its own license line, so withdrawing it is deleting one file
- [x] A sample of citations is checked by hand against the Catechism, and the sample size and the error rate are recorded
- [x] `LIMITS.md` states the legal basis for the index, and states that it is thinner than the basis for everything else here
- [x] A citation that does not resolve against the spine comes back as an orphan with a reason, the same way B1 and B2 handle it

**The sixth criterion was amended on 2026-08-06 and the change is the record.**
It read *against the printed Catechism*. There is no printed Catechism here and
there was never going to be one, so as written it could not close and the box
would have stayed empty forever over a book nobody owns.

What it says now is *against the Catechism*, and what was done is a reading of
the footnotes the Holy See publishes on `vatican.va`, per paragraph rather than
per page, using the superscript markers to attribute each footnote to the
paragraph that owns it. That is the official text. It is not the printed book and
the difference is written down rather than smoothed over.

**Fifteen paragraphs sampled, ten with readable footnotes, 34 published citations
examined, zero wrong.** What turned up instead was omission, references print
carries that the upstream transcription dropped, which is a limit on completeness
rather than on correctness and this dataset never claimed completeness.

The number that nearly shipped is in the QA document. An automated matcher
reported a 51.2% error rate over 45 citations and every disagreement was its own,
because it read the Catechism's english abbreviations through this repository's
portuguese-first alias table, where `Lk` resolves to nothing and `Jn` resolves to
Jonah.

Amending a criterion to fit what was done is the move this file should be most
suspicious of, so both readings are above and `docs/qa/B11-catechism-cross-references.md`
carries the evidence.

## Constraints

References and links. Never text. The line is not subtle and it does not move.

A summary of a paragraph is the paragraph wearing a hat. So is a title, so is a first line, so is an extractive snippet. If a reader can learn what a paragraph says without leaving this dataset, the line was crossed.

The legal basis is thinner here than anywhere else in this repo. Paragraph numbers are facts and links are links, and neither is anybody's property. The selection of which verse a paragraph cites is editorial work done by the authors of the Catechism, and a compilation of that selection attracts thin protection in some jurisdictions, including Brazil under article 7 of the copyright law. The Holy See is also more protective of this text than most rights holders are of theirs. The answer is to ship the least that is useful and to write the basis down, rather than to reason from how small the file is.

The link shape is the first risk and it is not a detail. The Catechism on `vatican.va` is published as paginated sections with anchors rather than one address per paragraph, so a per-paragraph deep link may not exist. If it does not, the fallback is the containing section plus the paragraph number, and the epic says which one shipped.

## Out of scope

No Catechism text, permanently.

No canon law and no magisterial documents. The same reasoning would apply and the same discipline would be needed, and neither is asked for.

No commentary on the citation. What the paragraph means is the reader's business and the Church's, not this dataset's.

## Verification

Test-driven on the resolution from verse id to paragraph list, the same as B4 anchor resolution.

Two checks that are not tests. The link shape is verified against the live site by opening one, and the citation sample is checked by hand against print with the error rate recorded whatever it turns out to be.
