# Spec, B9 lexical full-text search

*Stage 3. Written 2026-08-04, against issue #11.*

**Gate.** This is a human review gate. Five design questions were asked before
this document was written and the answers are folded in. Four more were at the
bottom, they came back answered on 2026-08-04, and the answers are folded in
too. Each of the four is recorded where it lands rather than only in the list.

## What B9 delivers

Finding a verse by what it says, without downloading 73 books first.

This is the one thing the static artifact cannot do, which is why it belongs to
the API. A reader who wants "cordeiro de Deus" today either fetches 27 MB and
writes a scan, or stands up a search service. Both are the wrong price for a
question this small.

## What the port gives, and what it does not

The private repo answers this at `/api/bible/search` and its engine does not
port. It runs Laravel Scout over **Meilisearch**, which is the external search
service this epic's constraints forbid, and the fallback engine underneath it is
a `LIKE` scan.

What ports is the contract, and it ports whole. The query parameters `q`,
`version`, `book` and `testament`. The hit carrying a structured verse id, the
book code, a formatted `reference`, a `snippet` with the match in `<em>`, the
version, and enough to open a reader at that point. Twenty results a page.

One documented caveat stops being true here, and the improvement is the reason
to say so out loud. `BIBLE_API.md` warns that when a match comes from accent
folding, you searched `coracao` and the text holds "coração", the `<em>` may not
appear, because the highlight is a literal string replace after the fact. FTS5
highlights the token it actually matched, so the accented form is marked. This
goes in `DECISIONS.md` as a divergence rather than passing unremarked.

## Measured before writing this

Every number ran on 2026-08-04 against the database built from what is committed
at `f8989b1`. None is an estimate.

| Fact | Value | How |
|---|---|---|
| SQLite in the runtime | 3.51.2 | `sqlite3.sqlite_version` |
| FTS5 compiled in | yes | virtual table created |
| Verse index, build time | 0.40 s | `INSERT INTO ... VALUES('rebuild')` |
| Both indexes, build time | 1.01 s | same |
| `coracao` finds "coração" | 914 hits | executed |
| Latin, `Dominus` | 3336 hits | executed |
| One page of the worst common word | 20 to 31 ms | `"a"`, `"e"`, `"de"`, both indexes |
| Counting the same match | ~1 ms | same run |
| A page at offset 5000 | 68 ms | same |

### The storage number is the surprise

`commentary_body` is `WITHOUT ROWID`, and an FTS5 external content index
addresses its content table by rowid, so the notes cannot be indexed as the table
stands. `build.py` anticipated this for `texts` and for `commentary` and missed
it here.

Rebuilding that one table with a rowid pays for both indexes and hands money
back.

| Database | Size |
|---|---|
| As built today | 93.1 MB |
| The same file, vacuumed | 91.5 MB |
| With `commentary_body` keeping its rowid | 68.2 MB |
| With both search indexes on top | 86.1 MB |

A `WITHOUT ROWID` table stores the whole row inside the primary key B-tree, and
this one carries two large text columns. That cost 23 MB. Search costs 18 MB.
B9 ships full-text search over Scripture and over 41410 commentary bodies and
leaves the file 7 MB smaller than it is now.

## Decisions

### The tokenizer does the accents, and nothing downstream repeats it

`unicode61` with `remove_diacritics 2`. Folding happens once, when the token is
written and when the query is parsed, so no column is stored twice and no
normalisation runs on the request path. Criterion 2 is closed by a tokenizer
argument rather than by code.

**No stemmer.** FTS5 ships `porter`, which only knows English, and this corpus is
Portuguese, English and Latin in one index. A stemmer right for one language and
wrong for two others is worse than none, because the wrongness is invisible. What
replaces it is the prefix operator, described below, which the reader controls.

Latin gets no special handling and needs none. It tokenises on the same rules and
was checked against a real query.

### Two indexes, external content, no copy of the text

`content='texts'` and `content='commentary_body'`. The index holds postings and
the text stays where it already lives. A contentless index would be smaller still
and cannot produce a snippet, which is criterion 3, so it is not an option.

`commentary_body` gains an `id INTEGER PRIMARY KEY` and keeps a unique index on
`(commentary, language)`. The addressing it had is preserved and the reader above
it does not change.

### The query is compiled, never handed to `MATCH` raw

FTS5's `MATCH` takes an expression language. Passing a person's typing into it
straight is the difference between a search box and a 500. Ten realistic inputs
went in raw:

```
'cordeiro de Deus'   -> 10 hits
'Deus (pai)'         -> OperationalError: fts5: syntax error near "Deus"
'Jo 3:16'            -> OperationalError: no such column: 3
"o Senhor's"         -> OperationalError: fts5: syntax error near "'"
'AND'                -> OperationalError: fts5: syntax error near "AND"
'fé -'               -> OperationalError: fts5: syntax error near ""
'a OR'               -> OperationalError: fts5: syntax error near ""
```

Six of ten. A reader searching for a parenthesis, an apostrophe or a chapter and
verse gets a server error, and one of those is how half the world writes a
reference.

So `q` is parsed here and an expression is built. The rules are small and they
are the contract.

| The reader types | What runs | Why |
|---|---|---|
| `cordeiro de Deus` | all three words, in any order | what a search box means |
| `"cordeiro de Deus"` | that phrase, in that order | quoting is the one operator everyone knows |
| `coracao` | matches "coração" | the tokenizer |
| `amar*` | prefix match | there is no stemmer, so this is how a reader reaches inflections |
| `Deus (pai)`, `Jo 3:16`, `Senhor's` | punctuation dropped, words kept | nothing a person types is a syntax error |
| `AND`, `OR`, `NEAR` | searched as words | they are words in this corpus, and `NEAR` alone has 217 hits |

Everything else in the FTS5 grammar stays unreachable. `NEAR`, boolean `OR` and
column filters are power tools for an audience this endpoint does not have, and
exposing them means every one of their failure modes becomes a public error.

A `q` that survives parsing with nothing left, empty, whitespace, or `!!!`, is a
`422` carrying the existing `malformed` reason. It is not an empty result set,
because empty results say the corpus lacks the word.

### One ranked list per corpus, so two routes

`GET /v1/search` searches Scripture. `GET /v1/search/commentary` searches the
notes.

Merging them into one ranked list would mean comparing a bm25 score computed over
107103 verses against one computed over 41410 notes, and those numbers share a
name and not a meaning. Pagination over the merged list would then page through
an order nobody can explain. Two routes keep ranking honest inside each, and a
client that wants both makes two requests it can cache separately.

### `version` defaults, `book` and `testament` filter

`version` is optional and falls back to `matos-soares`, the same default the rest
of the API already uses. Without a default, searching all three translations
returns the same verse three times and ranks Latin against Portuguese, which is
a list with no meaning at the top of it.

**`version=all` exists, and the objection above is published rather than
designed away.** A reader comparing translations has a real reason to want three,
and refusing it would mean three requests to answer one question. What it costs
is that the same address can appear three times and that bm25 is comparing a
Portuguese document set against a Latin one. Every hit carries its own `version`
so the repetition is visible rather than confusing, and `LIMITS.md` says what the
ranking means when the corpus is mixed.

`book` takes a USX code and goes through the same alias resolution the read
routes use, so `Sl` and `PSA` both work. `testament` takes `OLD` or `NEW` and is
carried over from the ported contract rather than invented.

On the commentary route the equivalents are `source`, `language` and `book`.

**The Portuguese Haydock is searched as ordinary text.** It was produced by a
language model, `LIMITS.md` says so, and `docs/qa/haydock-translation-review.md`
carries the sample it was measured on. It is not demoted here and it does not
have to be asked for. Every hit says which language it came from, the limit is
already published where a reader looking for it would look, and a search route
that quietly hid half the corpus would be solving a documentation problem with a
missing result.

### `offset` and `limit`, which is what FastAPI's own documentation does

The framework's tutorial pages a read endpoint with `offset: int = 0` and
`limit: Annotated[int, Query(le=100)]`. That is the convention this repo adopts,
capped at 100 and defaulting to 20, which is the page size the port used.

The response carries `total` alongside the hits, because counting a match costs
about a millisecond and a client cannot build a pager without it.

**Deep paging degrades and the limit gets published rather than hidden.** Ranking
by bm25 sorts every match, so offset 5000 costs 68 ms against 25 ms for the first
page. `offset` is capped at 1000, which keeps the worst page near the cost of the
first one and means a reader cannot walk past result 1000 of 29007. The cap goes
in `LIMITS.md` with the measurement beside it, because a reader who hits it needs
to know it is a decision and not a bug.

### The snippet comes from `snippet()`

Sixty-four tokens of context, the match wrapped in `<em>`, an ellipsis where the
text is cut. Same markup vocabulary the commentary bodies already publish, so a
client that sanitises one sanitises both.

A Scripture hit is short enough that the snippet is usually the whole verse. A
commentary hit is not, and the snippet is what makes that route usable at all.

### Criterion 5 gets its wording corrected, not ticked

The epic says the index is built by the B2 export and ships as a build artifact.
The B2 export needs the private source and writes JSON. The index is built by
`scripts/build-db.py` from files that are already committed, on a clean checkout,
by anyone with a clone.

B5 hit the same sentence and rewrote it rather than ticking a box the rest of
the repo denies, and this follows that precedent. The corrected criterion says
the index is built by the committed build step from the published corpus, and
that no hand-built index ships.

## What a hit looks like

Scripture, sharing `VerseOut`'s vocabulary so nothing new has to be learned.

```json
{
  "total": 914,
  "offset": 0,
  "limit": 20,
  "query": "coracao",
  "version": "matos-soares",
  "hits": [
    {
      "id": "PSA.56.8",
      "book": "PSA",
      "chapter": 56,
      "verse": 8,
      "reference": "Sl 56,8",
      "version": "matos-soares",
      "snippet": "O meu <em>coração</em>, ó Deus, está firme, o meu <em>coração</em> está firme."
    }
  ]
}
```

`version` appears twice on purpose. The envelope repeats what was asked, which is
`all` when it was `all`, and every hit carries the translation it came from,
which is the only thing that makes an `all` result readable.

Commentary, pointing back at an address the existing route already serves.

```json
{
  "total": 497,
  "offset": 0,
  "limit": 20,
  "query": "coracao",
  "hits": [
    {
      "source": "haydock",
      "language": "pt-BR",
      "start": "1CH.21.1",
      "end": "1CH.21.1",
      "reference": "1Cr 21,1",
      "label": null,
      "snippet": "Por que Satanás tentou o teu <em>coração</em>? As cópias gregas atuais…"
    }
  ]
}
```

No full body on either route. A hit carries what a result list renders and the
addresses to fetch the rest through the routes that already exist.

## Boundaries

**Nothing about embeddings, vectors or similarity.** That is `concordantia`, it
consumes the artifact published here, and the comparison between the two
approaches is a number that repo earns rather than this one.

**No search over the cross-references.** They are addresses and not prose.

**No spelling correction and no typo tolerance.** Meilisearch gives that away for
free and FTS5 does not, and the honest answer is a limit in `LIMITS.md` rather
than a hand-rolled edit distance over 107103 rows. The prefix operator covers the
common half of what typo tolerance was doing.

**No search-specific caching.** Reads are already sub-millisecond off a static
file and the rate limiter is the thing standing between this and a loop.

## Verification

The epic asks for a fixed query set with expected hits, including accented and
Latin queries. That is the acceptance test and it is written first.

Every query in the table above becomes a case, including the six that are server
errors today. The counts get pinned against the built database, so a tokenizer
change or a corpus change that moves them fails the build rather than passing
quietly.

`openapi.json` regenerates and CI fails on a difference, which is the existing
rule and needs nothing new.

## The four questions this document could not settle

Asked at the gate on 2026-08-04 and answered the same day. Each one is written
into the section it belongs to rather than living only here.

1. **The `WITHOUT ROWID` change on `commentary_body` is inside B9.** It is a data
   model change and it was put to the author rather than assumed. The table is
   derived, nothing about it is committed, no reader above it changes, and the
   rebuild it forces is one the suite already does on any change to `build.py`.

2. **`offset` caps at 1000**, published in `LIMITS.md` with the measurement.

3. **`version=all` exists.** What it costs is written into the parameter section
   rather than argued away, and the hit carries its own version so the cost is
   visible in the response.

4. **The machine-translated commentary is searched as ordinary text.** No
   demotion, no opt in, and the `language` field on every hit is what tells a
   reader what they are looking at.
