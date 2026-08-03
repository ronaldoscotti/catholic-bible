# Limits

What this repo cannot do, what it has not measured, and what it publishes
without being able to prove. Written when the limit is found rather than when
someone asks.

B2 opened this file because two of its acceptance criteria name it. B7 expands
it.

## A stranger cannot rebuild this dataset

The corpus is exported from a private repository, through a committed script,
and it is not regenerated here. That was a deliberate call and `DECISIONS.md`
carries the reasoning and what it cost.

The cost lands here. Two checks exist and they prove different things.

**The checksum check runs anywhere.** It recomputes the sha256 of every
published file and compares it to `PROVENANCE.json`. It runs in CI, on a clean
checkout, with no access to the private source, and anyone who clones this repo
can run it. What it catches is a truncated file, a bad merge, a partial commit.

**It cannot catch a hand edit.** The data and its hash are committed together,
so whoever edits a verse recomputes the hash and commits both. A self
referential hash is an integrity check and it is never an authorship check.
Nothing in this repo, and nothing a stranger can run, closes that gap.

**The check with teeth needs the private source.** `make verify-export` reruns
the export at the recorded commit, into a scratch directory, and compares byte
for byte with what is committed. A hand edited verse shows up there and nowhere
else. It needs the private repository and a running database, this project has
no self hosted runner, and so it is a documented command rather than a CI job.

A stranger can verify integrity and cannot verify authorship. Wiring the second
check to a badge and calling a green build proof would be worse than this
paragraph.

## A stale database ships without a sound

A file has a git hash. A database table does not.

`PROVENANCE.json` records the source commit, the commit date, and the sha256 of
the two input fixtures the import declares. Those plus the import code at that
commit are what produce the tables. What none of it detects is a database built
from an older commit and never rebuilt, because nothing readable from inside a
database says when it was filled.

Only the reimport half of the export check closes that, and it lives where the
private source lives.

## The orphan rate is not measured here

The B2 epic asks for the per book orphan rate. This repo cannot produce it.

An orphan is a source verse that reached no address on the spine. The import
dropped those before the corpus was written, so nothing that crossed over
remembers them. Publishing a zero would read as clean when it means unmeasured.

What is measurable here is the other side of the same coin, and it is published
in `orphans.json` and `coverage.json`.

**Unfilled** counts spine addresses no version reached.

| Version | Published | Unfilled |
|---|---|---|
| Clementine Vulgate | 35776 | 69 |
| Douay-Rheims | 35764 | 81 |
| Matos Soares | 35563 | 282 |

The spine holds 35845 addresses. Proverbs and Sirach carry most of the
Portuguese gap, 86 and 73 verses, and the Psalter carries most of the Latin and
English one.

The epic said the Vulgate would demonstrate the spine with zero orphans and
called it a live proof inside the release. It is 69 unfilled addresses, the epic
was corrected, and no number in this repo is asserted before it is measured.

## Twelve verses of the Douay-Rheims are missing

The MIT fixture that carries both the Latin and the English leaves the English
field empty at twelve addresses, while the Latin is present at all twelve.

They are omitted from the published file rather than shipped as empty strings,
because an empty string is a lie shaped like data and a missing key is not.
`PROVENANCE.json` lists all twelve.

`2SA.13.39` `JDT.4.6` `PSA.19.10` `PSA.28.11` `PSA.150.6` `PRO.28.25`
`WIS.18.25` `ISA.46.12` `AMO.9.15` `MAL.3.12` `1TH.4.12` `2TH.2.11`

## Rights, per asset

Everything published here is public domain. The file it arrived in is a separate
question from the text, so both get an answer.

| Asset | Text | Basis | Fixture |
|---|---|---|---|
| Matos Soares | public domain | Brazilian law article 45, died 1957 with no successors | licence unstated upstream |
| Douay-Rheims | public domain | first published 1582 and 1610 | MIT |
| Clementine Vulgate | public domain | promulgated 1592 | MIT |

The machine readable version of this table travels inside each published file,
under `version.rights`, so a consumer never has to come back here to find out
what it is allowed to do.

**Excluded permanently, and this is not a deferral.** The Ave Maria text and its
pericope headings, which are under copyright and sit in the same source
database. The Portuguese Catena Aurea, whose provenance is open. The text of the
Catechism, canon law and the magisterial documents.

The Ave Maria headings deserve their own sentence, because they are the one
thing here that could ship by accident. The private repository grafts 2305 of
them onto Matos Soares at import time, in the `heading` column of the same row
as the public domain verse text. The export names its columns and never selects
that one, and a test fails if a heading reaches a published file.

## What is not here yet

No commentary and no cross references. That is B4, and two rights questions are
already open there: 673 cross references sourced from Nestle-Aland 27, which the
Deutsche Bibelgesellschaft holds, and 879 derived from the Ave Maria apparatus.

No per book files and no CDN. That is B5.

No API over any of this. That is B3.

## What the read API cannot prove, added in B3

### 219 authored strings were checked for consistency and not for tradition

The English and Latin abbreviations, and the Douay names in ordinary case, are
authored in this repo. Nothing upstream carries a book name in any language but
Portuguese, so there was nothing left to export.

Three checks run over all of them. Each resolves back to its own book through
the alias table, which is built from exported data. Each is a subsequence of a
name the book actually has, so `Ecclus.` passes against `Ecclesiasticus` and
fails against `Ecclesiastes`. And no two share a string.

All three answer whether a string is consistent with its book. None answers
whether it is the form the tradition prints. If the conventional English
abbreviation for Sirach is `Sir.` and `Ecclus.` was written instead, every check
passes. That question needs a human reading against a printed Bible, and it is
the weakest link in every formatted reference this API returns.

Nine of them carry conformance cases, chosen because they are the ones that
would hurt. The other 210 do not.

### Reading a spine address back into another scheme is wrong in two places

`to_scheme` maps a candidate forward again and keeps it only if it lands where
it started. That catches a candidate that moved and it cannot catch one that is
out of range in the target scheme, because this repo holds the Copenhagen remap
pairs and no `org` verse count table. A book that maps by identity round trips
trivially.

Two addresses are confirmed wrong. Spine `PSA.15.11` reads back as `org` 15:11
and spine `PSA.43.27` as `org` 43:27, and both are different psalms. The honest
answer for each is an orphan.

Whether more exist across the other 72 books is not measurable with what is in
this repo. Saying that is better than publishing a number nobody can stand
behind. B3 ships the ported psalm table, which is hand verified, and pins the
two disagreements so the day B1 is corrected the suite says which one moved.

The psalm counterpart the API publishes comes from the ported table and not from
`to_scheme`, so no route returns either wrong answer today.

### The published numbering covers the Psalms and nothing else

`numbering` appears on a chapter of the Psalter and nowhere else, because the
ported table covers the Psalter and nowhere else. Joel and Malachi are numbered
differently between traditions too, and this API says nothing about that.

### Nothing here measures how fast it is

The store was chosen over reading JSON with one side of the comparison measured
and the other not. 34.8 MB retained is the cost of the alternative. The SQLite
side opens a connection per request and holds a page cache per connection, and
that number does not exist. No route has been load tested and nothing is
deployed.
