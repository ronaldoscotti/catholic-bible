# Code review, B11 Catechism cross-references

*Stage 7. Two passes by a review agent, 2026-08-05 and 2026-08-06, both after the
pull request opened rather than before. That is the wrong order and it is
recorded rather than tidied.*

**This is the fourth epic in a row where a second reader found the worst thing.**
B8, B9, B10 and now this. The pattern is not carelessness. Both human gates were
met here, the spec carried a measured table, the plan carried five refusals, and
the first review still found a published file that was wrong.

## The one that shipped

**The page map read footnote markers as paragraphs.** The walk searched the whole
page for the next number it was owed, and the whole page includes the superscript
markers and the footnote block. On the prologue page the markers `1`, `2` and `3`
satisfied paragraphs 1 to 3 and the footnote text `1 Tim 2:3-4` satisfied 4. Every
page to paragraph 17 was one page early, and 624 was taken off the previous
page's footnotes the same way.

A reader following a link for paragraph 1 landed on a page with no paragraph 1
on it.

```
$ paragraph 1 present in the body of __P1.HTM: False
$ paragraph 2, 3, 4 present:                   False False False
```

**The check that was trusted to catch this could not.** `refuse_a_broken_map`
passed, and correctly. Coverage, ordering and uniqueness are all true of a map
that is uniformly one page early, because being early is contiguous. The plan
had written the refusal naming this exact failure, in these words, and the author
then read the map instead of the site.

Two documents said all 2865 paragraphs land on the page that holds them. That was
false for at least seventeen, and the five spot checks cited could not have
included any paragraph under 16. Both sentences came down.

`--verify` opens the page the map names and looks for the paragraph on it. 134
sampled, zero wrong, and run against the map that shipped it reports paragraph 1
absent from the page it was sent to.

## What the second pass found

**A range was expanded on spine order rather than in the source numbering.**
`Dn 3,1-30` came back as 97 addresses, because this spine carries the Song of the
Three inside Daniel 3 and English does not, so the range swallowed 67 verses
nobody cited and reported nothing wrong. It also swapped an inverted span, which
turned a 67 verse citation into two addresses, and published a verse named twice
twice.

**`InputScheme` duplicated `Scheme` and the two diverged.** Adding `english` left
it unreachable over HTTP, so the README's own example was wrong. It promised that
`?scheme=org` on `Sl 51,1` gives the Miserere, and that returns the psalm's
heading. No accepted query value reached the Miserere at all.

**The export clobbered the page map's provenance.** `record_provenance` exists to
merge into that file and its docstring states the contract. Only one side honoured
it, so running the export after the page build erased the map's only checksum and
broke a committed test. Nobody would have seen it until the next step of the epic.

**A latent one worth the name.** The Portuguese range pattern read
`prologo%201-25_po.html` as a page starting at 201. Harmless only because a dict
key happened to collide, and an invented page passes every structural guard,
because a page holding nothing has no duplicate and leaves no gap.

## The measurement that was wrong before it was right

**Twice, and the second time nearly reached the user.**

The first diagnosis of the psalm defect said the Copenhagen table was broken. It
is not. Issue `#22` is what suggested looking at the input instead, because a
table that shifts verses for some psalms is not a table that ignores verses. The
correction went out before anybody acted on the first version.

The blast radius was then reported as psalms only, from the mechanism rather than
from measurement, because no other book numbers a superscription. Measured, 5605
of the 15672 addresses that move are in Daniel, Hosea, Deuteronomy, Isaiah,
Jeremiah and Joel. The issue carries the correction.

**The sample check produced a 51.2% error rate that was entirely its own.** It
resolved the Catechism's English abbreviations through this repository's alias
table, which is Portuguese first, so `Lk` resolved to nothing and `Jn` resolved
to Jonah. Fifteen paragraphs were read by eye instead.

Three wrong numbers in one epic, all caught before publication, none by a test.

## What was checked and found sound

**No text ships.** Asserted on the shape of every response and every artifact
rather than on a list of banned field names, so adding a field is what breaks it.

**The dependency direction holds.** `catechism.py` imports the canon and nothing
above it. The routes import it. The export imports the canon and the scheme.

**Every published link resolves.** Five opened directly, 200 in both editions,
with the paragraph present on the page that came back.

**Zero em-dashes** across every prose document, and the voice lint passes on 18.

## What is still open

**The sample check has no printed Catechism behind it** and the criterion stays
unticked. What was done instead reads the footnotes the official site prints.

**`--verify` is not the independent check its docstring claimed.** It shares
`body()` and the search with the walk, so on a freshly built map it cannot fail.
It caught the shipped defect only because `body()` changed in between. A
genuinely independent check needs a second extractor and this epic has no other
use for one. Recorded rather than fixed.

**The page map is never verified in CI.** Re-walking 374 pages on somebody else's
server does not belong in a build. CI holds that the committed map is internally
sound and matches its checksum, and nothing more.
