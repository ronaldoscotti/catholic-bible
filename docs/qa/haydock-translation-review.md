# The Portuguese Haydock, read entry by entry

*2026-08-03. The 200 entry sample at `haydock-translation-sample.csv`, compared
against its English source. Verdicts in `haydock-translation-verdicts.csv`.*

**A language model reviewed a language model.** That is weaker than a person and
the number below has to be read knowing it. The reviewer and the translator are
not the same model under the same prompt, and the reviewer had the English beside
the Portuguese for every entry, which the translator did not have for the whole
corpus at once. It is still one machine grading another.

The author read the sample first and reported nothing that stood out, then asked
for the entry by entry pass rather than a second human. That is what this is.

## The number

| | |
|---|---|
| Sample | 200 of 20705, seeded, drawn by `draw-review-sample.py` |
| Entries with a defect | 5 |
| **Observed error rate** | **2.5%** |
| 95% Wilson interval | 1.1% to 5.7% |
| Of the five, meaning changed | 2 |

The interval is what 200 entries support. It is not the rate of the corpus, it is
the range the corpus rate plausibly sits in, and the lower bound is not zero.

## The five

**JER.9.5, the meaning is inverted.** The Septuagint reading in Haydock is
`they have not left off, (6) in order to be converted`, meaning they never
stopped sinning so as to be converted. The Portuguese reads
`não deixaram de (6) converter-se`, which says they never stopped converting.
The sentence now asserts the opposite of the reproach it belongs to.

**LUK.19.42, the meaning is inverted.** Christ weeps over Jerusalem
`though determined on his destruction`, meaning Jerusalem was bent on killing
him. The Portuguese reads `ainda que resolvido a destruí-la`, which makes Christ
the one resolved to destroy the city. The paragraph exists to argue that we
should weep for our enemies, so the inversion removes its point.

**EXO.30.1, the note changes hands.** The English signs it `Ch.` and the
Portuguese signs it `C.` In Haydock those are Challoner and Calmet, two different
authorities, so the reader is told the wrong person said it.

**NUM.10.10, the lemma stops being a lemma.** A Haydock note opens with the words
of the verse it comments on. `And on.` became `E assim por diante.`, which reads
as `et cetera` and points the reader at nothing.

**2KI.6.14, an English word survived.** `of the army` became `do the exército`.
The article did not get translated and sits inside the Portuguese sentence.

## Why the mechanical audit could not have found any of them

`scripts/audit-translation.py` checks for an empty body, a body identical to the
source, a length outside a band, emphasis markup that moved and a digit that did
not survive. **All five entries pass every one of those checks.** Two of them say
the opposite of the English and pass, because an inversion is the same length,
carries the same markup and contains the same digits.

That is the boundary between the two kinds of checking, and it is the reason the
epic asked for a read rather than a script.

## What this does not establish

The sample is 200 of 20705, so 20505 entries have not been read by anyone.

The reviewer judged fidelity to the English, not the truth of the theology, not
the quality of the Portuguese as prose, and not whether a Catholic reader in 2026
would be misled by a nineteenth century commentary rendered faithfully.

Nothing here re-examines the 244 bodies the export cut at a leaked marker. Those
were verified structurally in B4 and none of them fell in this sample.

A second reviewer would not produce these five. Judgement about where drift
becomes error is exactly where two readers differ, and three of the five are the
kind a stricter reader might have let pass while a stricter one still might flag
entries this pass called faithful.
