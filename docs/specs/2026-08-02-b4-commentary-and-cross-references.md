# Spec, B4 commentary and cross-references

*Stage 3. Written 2026-08-02, against issue #6.*

**Gate.** This is a human review gate and it was **waived in writing** before the
document was written. The author said to run the pipeline to the end and review
at the end. So this document exists as the record of what was decided before any
code, which survives a waiver, and it does not claim anyone stopped and read it
first. `docs/method/README.md` records the same thing rather than counting the
gate as met.

## What B4 delivers

Two layers hanging off the verse id B1 built. Commentary on a verse, and the
passages a verse points at. Neither one changes the verse schema, and that is
the point of the epic rather than a side effect.

One layer proves nothing about an anchor. A single table can always be shaped
around whatever it has to hold. Two independent layers, from two unrelated
sources, landing on the same integer without the spine moving, is the claim
being demonstrated.

The Portuguese Haydock is the part that is new in the world. A complete Catholic
commentary on all 73 books has never been published in Portuguese. Everything
else in this repository is careful curation of material that already circulates.

## Measured before writing this

Every number is a query against the private source database or against what is
committed here. None is an estimate.

| Fact | Value | Source |
|---|---|---|
| Haydock entries | 20705 | `bible_commentary_entries` |
| Books they reach | 73 | join on `bible_books` |
| Entries carrying a pt-BR body | 20705 | `body_html_translated IS NOT NULL` |
| Spine addresses at least one entry covers | 21040 of 35845 | coverage join |
| The same, after the export clamps two | 21042 of 35845 | the built database |
| Widest entry, in canonical order | 15 addresses | `MAX(end_order - start_order)` |
| Entries whose end sits before their start | 2 | see below |
| English HTML | 8.0 MB | `SUM(LENGTH(body_html))` |
| Portuguese HTML | 8.3 MB | `SUM(LENGTH(body_html_translated))` |
| Plain text, both languages | 15.5 MB | the two `body_text` columns |
| Translation records generated | 21875 | `done*.jsonl` |
| Of those, flagged for human review | 1196, 5.47% | the `review` field |
| Cross-references, all sources | 208515 | `bible_cross_references` |
| After dropping `ave-maria` | 207636, on 26726 anchors | same table |
| OpenBible entries touching a deuterocanonical book | **0 of 204601** | join on `is_deuterocanonical` |

That last row is the epic's problem statement, measured. Two hundred thousand
cross-references and not one of them reaches Tobit, Judith, Wisdom, Sirach,
Baruch or the Maccabees, in either direction. The books a Catholic reader most
needs connected are the ones the largest available set leaves unconnected.

## The two sources that carry the deuterocanonicals

| Source | Rows | Touching a deuterocanonical | Rights |
|---|---|---|---|
| `openbible` | 204601 | 0 | CC BY, attribution required |
| `douay` | 2362 | 258 | CC0, the 1582 apparatus |
| `na27` | 673 | 665 | see below |
| `ave-maria` | 879 | 1 | excluded |

`na27` is 292 authored pairs of addresses, expanded in both directions. It
carries no text from any source and it is where 665 of the 920 surviving
deuterocanonical links come from.

**It ships.** The author decided that, and the reasoning is worth writing down
rather than leaving as a preference. A list of verse pairs is not the apparatus
it was compiled with. It reproduces no text, no note and no editorial prose, and
a bare address is a fact about Scripture rather than an expression of anyone's
work. Excluding it would have cut deuterocanonical linkage by 61% to protect
against copying nothing.

`ave-maria` does not ship. Its 879 entries were scraped out of the Ave Maria
edition's own apparatus, which is the same protected 1957 edition whose text this
repository already refuses, and it contributes exactly one deuterocanonical link.
`LIMITS.md` records the exclusion and what it cost, which is nothing.

## How the Portuguese Haydock was produced

This is the single thing in the epic that has to be right, and it goes on the
first screen of the README rather than in a footnote.

Twenty thousand seven hundred and five notes were translated from English to
Brazilian Portuguese **by a language model**, running headless in batches, under
a fixed prompt that required faithful rendering, Catholic ecclesiastical
terminology, untouched Scripture citations and untouched Latin. The same prompt
asked the model to flag four categories without altering the translation:
polemic against Protestants, characterisations of the Jewish people that the
Church has revised since Nostra Aetate, dating and authorship claims stated as
settled, and pre-modern science presented as literal fact.

**1196 of 21875 records came back flagged, 5.47%.** They were published with the
rest.

**No human has read a sample and written down an error rate.** That sentence goes
in the README in those words. A corpus of twenty thousand entries announced as a
translation and later found to be raw machine output destroys credibility with
exactly the readers who matter. Said plainly it is a sentence about systems
instead, because a reviewed pipeline with a flagging gate is a defensible thing
to have built.

What this epic ships toward that criterion is the sample and the protocol, drawn
by a committed script with a fixed seed so anyone can redraw it and get the same
rows. The reading is a person's work and it is not done. The QA document says
so, and the acceptance criterion stays unchecked until it is.

## The two entries whose end sits before their start

Two Haydock notes are labelled `26–7` and `73–4`, meaning verses 26 to 27 of
Matthew 15 and 73 to 74 of Luke 1. The upstream extraction read the elided
second number literally, so one entry claims to run from verse 26 to verse 7 and
the other from 73 to 4.

The coverage test is `start <= wanted AND end >= wanted`, which no address
satisfies when the range is inverted. Both notes are therefore invisible in the
source system, and Matthew 15:26 and Luke 1:73 read as having no Haydock note
when they have one.

**The export clamps the end to the start** and counts what it clamped in the
provenance record. Reading `27` out of the label and the start is the obvious
repair and it is not the one taken, because that would be the export authoring a
value the source does not hold, and the rule that no hand-made value ships does
not get an exception for a value a script made up convincingly. Clamping loses
the note on the second verse of each pair and keeps it on the first, which is an
under-claim rather than a fabrication. `LIMITS.md` names both addresses.

## What gets published

Two new files under `src/catholic_bible/data/`, both written by committed export
scripts, both checksummed, both recorded in a provenance file naming the source
commit and its date.

```
data/commentary/haydock.json          the notes, both languages
data/commentary/PROVENANCE.json
data/cross-references/references.json the pairs
data/cross-references/PROVENANCE.json
```

**Plain text is derived at build time and not published.** Stripping tags out of
the HTML is deterministic, the build already runs, and publishing both doubles
the file for a column a consumer can compute. It saves 15.5 MB against 16.3 MB
kept, which is the difference between a repository that clones and one that
annoys.

**A commentary entry is anchored by verse id and by order, and the build checks
they agree.** Exactly what `build_texts` already does for the corpus. The
published file carries `GEN.1.1` and `1`, the spine walks its own order, and a
disagreement stops the build rather than pointing a note at a neighbouring
verse.

```jsonc
{
  "source": {
    "code": "haydock",
    "name": "Haydock Catholic Bible Commentary",
    "author": "Rev. George Leo Haydock (1774-1849)",
    "language": "en-US",
    "rights": { "text": "public-domain", "text_basis": "...", "translation": "..." }
  },
  "entries": [
    {
      "start": "GEN.1.1", "end": "GEN.1.1",
      "start_order": 1, "end_order": 1,
      "label": "1", "position": 0,
      "body": { "en-US": "<em>In the beginning</em> ...", "pt-BR": "<em>No princípio</em> ..." }
    }
  ]
}
```

Cross-references group by anchor, so the anchor is written once instead of 26726
times across 207636 rows.

```jsonc
{
  "sources": {
    "douay": { "name": "...", "rights": "CC0", "weight": 100 },
    "na27": { "name": "...", "rights": "...", "weight": 90 },
    "openbible": { "name": "...", "rights": "CC BY 4.0", "attribution": "openbible.info" }
  },
  "references": {
    "GEN.1.1": [
      { "to": "JHN.1.1", "end": null, "chapter": false, "weight": 100, "source": "douay" }
    ]
  }
}
```

## The orphan report, which B2 could not produce

Criterion 3 wants entries that fail to resolve reported rather than dropped. The
source system counts them at import and throws them away, so the resolved rows
in the database cannot answer the question. That is the same wall B2 hit with
the corpus.

This epic can do better, because the fixtures the importer read are files. The
export reads the fixture beside the resolved rows and reports every fixture
entry with no counterpart among them. That is a diff against the input, not a
second implementation of the resolver, and a second resolver would be a second
set of bugs rather than a check.

The number goes in `derived/cross-reference-orphans.json` next to the existing
orphan report, and `LIMITS.md` says which question it answers.

## Storage

Four tables. The commentary body is a separate table keyed by language rather
than a `body_pt` column, because two languages exist in the data today and a
column named after one of them is a schema that has to change the day a third
arrives.

```sql
CREATE TABLE commentary_sources (
    code TEXT PRIMARY KEY, name TEXT NOT NULL, author TEXT,
    description TEXT, language TEXT NOT NULL, rights TEXT NOT NULL,
    position INTEGER NOT NULL
) WITHOUT ROWID;

CREATE TABLE commentary (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL REFERENCES commentary_sources(code),
    first_order INTEGER NOT NULL,
    last_order INTEGER NOT NULL,
    label TEXT,
    position INTEGER NOT NULL
);

CREATE INDEX commentary_coverage ON commentary(source, first_order, last_order);

CREATE TABLE commentary_body (
    commentary INTEGER NOT NULL REFERENCES commentary(id),
    language TEXT NOT NULL,
    html TEXT NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (commentary, language)
) WITHOUT ROWID;

CREATE TABLE cross_reference_sources (
    code TEXT PRIMARY KEY, name TEXT NOT NULL, rights TEXT NOT NULL,
    attribution TEXT, url TEXT
) WITHOUT ROWID;

CREATE TABLE cross_references (
    from_order INTEGER NOT NULL REFERENCES spine(canonical_order),
    to_order INTEGER NOT NULL REFERENCES spine(canonical_order),
    to_end_order INTEGER,
    whole_chapter INTEGER NOT NULL,
    weight INTEGER NOT NULL,
    source TEXT NOT NULL REFERENCES cross_reference_sources(code),
    PRIMARY KEY (from_order, to_order)
) WITHOUT ROWID;
```

`commentary` keeps its rowid, because `commentary_body` addresses it by that
rowid and because B9 may want an FTS5 index over the notes for the same reason
`texts` keeps its own.

**The coverage query carries a floor.** Finding notes that cover a window is
`first_order <= window_end AND last_order >= window_start`, and the first half is
an open range that matches most of the table for any address late in the canon.
The private repo hit this in MySQL, which abandoned the index and scanned. The
fix there is a floor of `window_start - widest_entry`, derived from the data
rather than guessed, and it is provably free because no entry is wider than the
widest entry. The same floor ports, and the widest entry is computed at build
time and stored rather than queried per request.

## The routes

Four new ones, both layers reachable by address and by written reference.

```
GET /v1/books/{book}/chapters/{chapter}/verses/{verse}/commentary
GET /v1/books/{book}/chapters/{chapter}/verses/{verse}/cross-references
GET /v1/commentary?ref=&scheme=
GET /v1/cross-references?ref=&scheme=
```

**Neither layer nests under a version, because neither depends on one.** A note
on John 3:16 is the same note whichever translation is on screen. The version
segment would be a lie about what the answer depends on, and it would multiply
the cache surface by the number of versions for no difference in bytes.

**Both languages come back in one response.** A note is one to four entries for a
given verse, so the payload is small, and a client that wants to toggle between
the English and the Portuguese should not need a second request to do it.

## What is deliberately not built

**No `commentary_count` on the verse read.** The private repo carries one, so a
reading screen can show an indicator without fetching the note. It is genuinely
useful and it is not in any acceptance criterion. It would change `VerseOut`,
which is in every reading response this repo publishes, and it would add a
coverage query to every chapter read. The reference endpoint already returns
entries with their spans, so a client rendering a chapter gets the same
information in one request. If a real consumer asks for the field it can be
added without breaking anything, which is the argument for waiting.

**No preview text on a cross-reference.** The private reader renders the first
verse of each target in the version on screen. That makes the answer depend on a
version, which is what the route shape just refused, and B3 already answers
`/v1/passage` for any address a client wants to render.

**No Catena Aurea, in any language, under any milestone.** The Portuguese edition
on hand has open provenance. The English is public domain and is a separate epic
with a separate label so the two are never confused on a distracted evening.

**No Catechism.** B11, and only paragraph numbers and links.

**No search over the notes.** B9.

## Read cuts and what stays in the file

Thirty cross-references per anchor at read time, highest weight first, canonical
order as the tie break. Genesis 1:1 has more than sixty strong ones and a client
rendering all of them renders noise. The published file and the table keep
everything, and only the read cuts, so the cut is a presentation decision a
consumer can disagree with by reading the artifact instead of the API.

**Weight does not reach the wire.** It is a vote count from OpenBible for one
source and a fixed constant for two others, so the number is not comparable
across sources and publishing it invites arithmetic that means nothing. What
ships is `primary`, true at weight 20 or above, which separates curated Catholic
references and strong OpenBible consensus from the long weak tail. The threshold
and its reasoning go in `DECISIONS.md`.

## Verification

Test driven on the coverage query, on the anchor resolution and on both readers.
Conformance cases for the anchors, including a note that spans a range and the
two clamped entries.

The orphan path is tested against the fixture rather than against a fake, since
the fixture is a file and a real one is cheaper than a mock.

The document gates from B3 apply unchanged and will fail the build if any of the
four routes reaches the published document without a summary, a response model
or a documented failure.

The Portuguese review sample is drawn and the protocol is written. The reading
is not done and the criterion stays unchecked.

## Slices

One epic, two pull requests, issue #6 linked from both.

**B4-1, commentary.** Export, provenance, the two commentary tables, the reader,
the two routes, the translation provenance in `README.md` and `LIMITS.md`, the
review sample and its protocol.

**B4-2, cross-references.** Export of three sources, the orphan report, the
table, the reader, the two routes, and the OpenBible attribution where a person
reads it.

They are independent. The second does not touch a line the first writes, beyond
the schema file and the document, which is the argument for splitting them.

## Open questions carried into the plan

**How the export gets 20705 HTML bodies out without holding them all twice.**
The corpus export builds one dictionary and serialises it, and 16.3 MB of HTML
is a different shape from 18 MB of short verses.

**Whether the coverage floor is needed in SQLite at all.** MySQL abandoned the
index. SQLite may not, and a floor that buys nothing is a comment explaining a
number for no reason. Measured in the plan, kept or cut on the measurement.

**Where the review sample lives.** A markdown table a person fills in, or a CSV.
The answer is whichever one a person will actually complete.
