# QA, B11 Catechism cross-references

*Stage 6. Run 2026-08-06, against the branch that carries the epic.*

## The sample check, and what it is not

The epic asks for a sample checked by hand against the printed Catechism, with
the size and the error rate recorded whatever they turn out to be.

**There is no printed Catechism here.** What was done instead is a reading of the
footnotes `vatican.va` prints, per paragraph rather than per page, with the
superscript markers inside each paragraph used to pick out the footnotes that
paragraph owns. That is the official text and it is not the printed book, and
the difference is recorded rather than smoothed over. B4 called its equivalent a
machine grading a machine. This one is closer to the source and still not what
the criterion imagined.

**The criterion stays unticked.**

### The automated attempt that produced a wrong number first

A matcher was written to compare the published citation against the printed
footnote automatically. It reported a 51.2% error rate over 45 citations, and the
number was nonsense. It resolved the Catechism's English abbreviations through
this repository's alias table, which is Portuguese first, so `Lk` resolved to
nothing and **`Jn` resolved to Jonah**. Every disagreement it reported was its own
failure to read `Lk 1:17` and `Jn 9:16`.

That number was not published. It is written down here because a measurement that
runs, produces a confident figure and is wrong is the failure this repository
keeps meeting, and this is the fourth time.

Building a trustworthy English reference parser is a real piece of work and it is
not this epic's. Fifteen paragraphs were read by eye instead.

### What fifteen paragraphs showed

Sample drawn with a fixed seed over the 1193 paragraphs that cite Scripture.

| | |
|---|---|
| Paragraphs sampled | 15 |
| Verifiable, meaning the footnotes came back readable | 10 |
| Not verifiable, extraction returned nothing or truncated | 5 |
| Published citations examined | 34 |
| Published citations absent from the printed footnotes | **0** |

**Nothing published was wrong.** Every citation this dataset carries for those ten
paragraphs is in the Catechism's own footnotes, including the ones whose book
abbreviation differs, `Sb 10,5` against `Wis 10:5` and `Hb 2,9` against `Heb 2:9`.

**What it found instead was omission.** The printed footnotes carry references
this index does not.

```
§369   ours: Gn 2,7            printed: Cf. Gen 2:7, 22.        2,22 is missing
§2628  ours: Sl 95,1-6         printed: Ps 95:1-6. Ps 24,9-10.  24,9-10 is missing
```

That is the upstream transcription rather than the export. It is one more reason
the precision figure above is not a completeness figure, and this dataset has
never claimed to carry every citation the Catechism makes.

**One redundancy.** §305 carries `Mt 6,31` and `Mt 6,31-33`, where print has only
the range. The extractor recovers a start from a link and a range from display
text, so both survive. Harmless, since the expansion covers the same verses, and
worth knowing before somebody counts citations per paragraph.

**Five of fifteen could not be checked**, because the footnote extraction came
back empty or cut off. That is a limit of the reading tool and not a finding
about the data. The rate above is over ten paragraphs and says so.

## Links, opened

Every link in the sample resolves. Five were opened directly and returned 200
with the paragraph present on the page.

```
pt §3     200  .../cathechism_po/index_new/prologo%201-25_po.html
en §199   200  .../ENG0015/__P16.HTM
en §1223  200  .../ENG0015/__P3I.HTM
pt §2865  200  .../cathechism_po/index_new/p4s2_2759-2865_po.html
en §2865  200  .../ENG0015/__PAE.HTM
```

The prologue is the one that breaks, because its file name carries a space that
the published index already percent encodes. Encoding it a second time turns
`%20` into `%25` and the link 404s. A test holds it.

## The routes, run

```
GET /v1/books/MAT/chapters/28/verses/19/catechism   200, 17 paragraphs
GET /v1/catechism?ref=Sl 51,1&scheme=english        200, ids ["PSA.50.3"]
GET /v1/catechism/paragraphs/1223                   200, cites Mt 28,19-20
GET /v1/catechism/paragraphs/1                      200, cites []
GET /v1/catechism/paragraphs/9999                   422
GET /v1/books/JHN/chapters/3/verses/999/catechism   404, not_on_spine
```

`Sl 51,1` is the one worth looking at. Under `?scheme=english` it reaches
`PSA.50.3`, which is the Miserere. Under `?scheme=org` it reaches `PSA.50.1`,
which is the psalm's heading, and before this branch there was no query value
that reached the Miserere at all. The README claimed there was.

A paragraph that cites no Scripture answers 200 with an empty list rather than
404, because 1672 of the 2865 cite none and existing while citing nothing is not
the same as not existing.

## The numbers this epic publishes

```
1193 paragraphs cite 3997 verses, 6828 pairs
5 orphans, all partial, all citations written in Vulgate numbering
   Ml 3,19 · Zc 2,14 · 2Mc 12,46 · 2Cor 9,5-18 · Dn 3,79-81
```

## What is not covered

The page map is verified against the live site on demand and never in CI, because
re-walking 374 pages on somebody else's server does not belong in a build.

The text fragment appended to each link was not opened in a browser. It is a
browser feature, it is labelled best effort in the response, and the plain URL
beside it is what was actually tested.
