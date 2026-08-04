# Plan, B9 lexical full-text search

*Stage 4. Written 2026-08-04, against the approved spec
[`2026-08-04-b9-full-text-search.md`](../specs/2026-08-04-b9-full-text-search.md).*

**Gate.** This is a human review gate and it is open. No implementation code
exists and none gets written until this document comes back approved. Three
things this plan refuses to assume are at the bottom, each with the measurement
that has to run before the claim is made.

## The shape

Seven slices, in dependency order. Each one is red before it is green and each
one leaves the suite passing.

Nothing here is a rewrite. Two virtual tables, one table that loses
`WITHOUT ROWID`, one pure function, two reader functions, two routes.

## 1. The query compiler

**New file `src/catholic_bible/search.py`.** A pure function over a string. It
imports no storage and no HTTP, so it is tested without a database and it sits
where the dependency direction already runs.

```
compile_query(raw: str) -> str | None
```

`None` means nothing survived parsing, and the route turns that into the `422`.

Tests come first and they are the table in the spec, one case each.

| Input | Expression | Why it is a test |
|---|---|---|
| `cordeiro de Deus` | `"cordeiro" AND "de" AND "Deus"` | the ordinary case |
| `"cordeiro de Deus"` | `"cordeiro de Deus"` | one phrase, not three ANDed terms |
| `amar*` | `"amar"*` | the only inflection tool there is |
| `Deus (pai)` | `"Deus" AND "pai"` | a 500 today |
| `Jo 3:16` | words kept, punctuation dropped | a 500 today |
| `o Senhor's` | words kept | a 500 today |
| `AND`, `OR`, `NEAR` | searched as words | a 500 today for two of the three |
| `""`, `   `, `!!!` | `None` | the `422`, not an empty result |

**The phrase case is the one that has already been got wrong once.** A first
draft of this function emitted `"cordeiro" "de" "Deus"`, which FTS5 reads as an
implicit AND of three terms and answered 10 hits where the phrase answers 2. The
test asserts the count, not just the string, so the next person who touches the
quoting finds out.

Property test on top of the table. Any input drawn from a rough alphabet of
letters, digits, spaces, quotes, punctuation and accents either compiles to
something FTS5 executes or returns `None`. Never a raised exception, never a
`MATCH` that fails. That is the whole reason this function exists.

## 2. `commentary_body` keeps a rowid

**`src/catholic_bible/storage/build.py`.** The table gains
`id INTEGER PRIMARY KEY` and a unique index on `(commentary, language)`. The
`WITHOUT ROWID` goes. `build_commentary` stops supplying the key it no longer
has.

The comment on that table says why, in the same voice the comment on `texts`
already uses, and it names the 23 MB rather than saying the change is for
search.

**No reader changes.** `commentary_covering` addresses the table by
`(commentary, language)`, which is still unique and still indexed, so the
existing commentary tests are the regression test for this slice. If they move,
the change was wrong.

One new test asserts the table has a rowid, because that is the property the
next slice depends on and nothing else would notice it disappearing.

## 3. The two indexes

**Same file.** Two virtual tables in `SCHEMA` and two rebuilds in `build()`.

```sql
CREATE VIRTUAL TABLE verse_search USING fts5(
    text, content='texts', content_rowid='rowid',
    tokenize="unicode61 remove_diacritics 2");

CREATE VIRTUAL TABLE note_search USING fts5(
    text, content='commentary_body', content_rowid='id',
    tokenize="unicode61 remove_diacritics 2");
```

Rebuilt after the content tables are filled, before `ANALYZE`.

Tests. Both indexes hold exactly as many rows as their content tables. A known
accented word is found by its unaccented spelling. A Latin word is found. The
tokenizer arguments are asserted against `sqlite_master`, because they are the
whole of criterion 2 and a silent edit to them would pass every other test in
this file.

**This is the slice that changes the conformance surface.** The suite rebuilds
the database whenever `build.py` moves, so the cost is paid once and the rest of
the suite proves nothing else shifted.

## 4. The reader

**`src/catholic_bible/storage/reader.py`.** Four functions, no HTTP, no
Pydantic.

```
search_verses(connection, expression, version, book, testament, limit, offset)
count_verses(connection, expression, version, book, testament)
search_commentary(connection, expression, source, language, book, limit, offset)
count_commentary(connection, expression, source, language, book)
```

`version=None` means all three. The route decides what the default is, because
the default is a contract and this layer has no contracts.

The verse query joins the index to `texts`, `spine` and `books`, filters, orders
by `bm25` ascending and takes its snippet from the index. The commentary query
joins to `commentary_body`, `commentary` and the spine at both ends of the
anchor.

Tests are the fixed query set the epic asks for, run against the real database,
with counts pinned. Accented, unaccented, Latin, phrase, prefix, filtered by
book, filtered by testament, filtered by version, and one query that finds
nothing. A pinned count fails when the corpus or the tokenizer moves, which is
what pinning is for.

## 5. The models

**`src/catholic_bible/api/models.py`.** `VerseHit`, `SearchOut`,
`CommentaryHit` and `CommentarySearchOut`, in the vocabulary the existing models
already use. Every field carries a description, because CI fails a route whose
document is thin.

## 6. The routes

**`src/catholic_bible/api/routes.py`.** `GET /v1/search` and
`GET /v1/search/commentary`.

`q` is required. `offset` defaults to 0 and is bounded `ge=0, le=1000`. `limit`
defaults to 20 and is bounded `ge=1, le=100`. Both bounds are FastAPI's own,
so an out of range value is the framework's `422` reshaped into this repo's one
error body, and no hand written guard exists to drift.

`book` goes through `ALIASES.resolve` and 404s the way every other route does,
so `Sl`, `PSA` and `Salmos` all work and a typo says `unknown_book`.
`version` 404s with `unknown_version` unless it is `all`.

Tests over HTTP. The happy path. The six inputs that are server errors today,
each asserting a 200 rather than a 500. The `422` for an empty query. The book
alias. `version=all` returning the same address in more than one translation,
each hit naming its own. The offset cap refusing 1001. The snippet carrying
`<em>` around the accented form when the query had no accent, which is the
divergence from the port and the thing most likely to regress silently.

## 7. The documents

`openapi.json` regenerates. `docs/epics/B9-full-text-search.md` gets criterion 5
reworded, with the reason written in the epic the way B5 did it rather than in a
commit message.

`DECISIONS.md` takes three entries. The highlight surviving accent folding, and
what the port does instead. The `WITHOUT ROWID` finding, with the four sizes.
Two routes rather than one merged list, and what a shared bm25 would have meant.

`LIMITS.md` takes three. No typo tolerance, which Meilisearch gave the port for
free. The `offset` cap with its measurement. What ranking means under
`version=all`, where the scores being compared come from different languages.

`README.md` gets the search section, through the voice skill, zero em-dashes.

## Where TDD does not apply

**The index build is verified, not unit tested.** A test that asserts an FTS5
table exists and holds the right number of rows is a real test. A test that
asserts the tokenizer folds accents is a test of SQLite. The one written here is
the first kind, plus one case of the second at the boundary this repo actually
depends on, and the difference is named rather than blurred.

**The timing numbers are measured and pasted, not asserted.** A test that fails
when a page takes 40 ms instead of 25 fails on a busy laptop and teaches the
suite to be ignored. The numbers go in the QA document with the run that
produced them.

## Three things this plan refuses to assume

1. **The measured page cost did not include the version filter.** Every number
   in the spec came from a query with no join to `versions` and no `WHERE
   version = ?`. The real query is measured before anything is claimed in
   `LIMITS.md` or the README, and if the filter changes the picture the cap in
   slice 6 gets revisited rather than shipped on a number from a simpler query.

2. **`bm25` ordering with a filter may not use the index the way the bare query
   does.** SQLite has to sort every match before it can page, and adding a
   filter that removes two thirds of them could help or could force a different
   plan. `EXPLAIN QUERY PLAN` gets read on the real query, and if the planner
   picks something bad the fix is a measured one and not a guess.

3. **Nothing here proves the routes are installed.** B8 shipped a limiter no
   test could see the application install, and deleting one line left 654 tests
   green. The same hole exists for a route. `tests/test_deployment.py` already
   boots the real import in a subprocess, and it gains a case that asks the
   running application for a search and reads the answer.
