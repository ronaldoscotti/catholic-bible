# QA, B9 lexical full-text search

*Stage 6. Run 2026-08-04 against `docker compose up --build`, on the image the
compose file builds, not against the test client.*

Everything below is pasted from the run. Nothing is retyped and nothing is
summarised into a claim.

## The engine

```
$ curl -s 'localhost:8000/v1/search?q=cordeiro%20de%20Deus'
total 10 version matos-soares
  Jo 1,36 | Vendo Jesus que ia passando, disse: "Eis o <em>Cordeiro</em> <em>de</em> <em>Deu…
  Ap 22,1 | Depois (o anjo) mostrou-me um rio <em>de</em> água viva resplandecente como cris…
  Ap 22,3 | Não haverá ali jamais maldição; o trono <em>de</em> <em>Deus</em> e do <em>Corde…
```

**The phrase and the conjunction are different questions and the reader controls
which.**

```
  cordeiro de Deus       total 10
  "cordeiro de Deus"     total 2
```

**Accents are optional and the answer shows the word the text carries.** This is
the divergence from the ported implementation, where the highlight is a literal
replace and this exact query marks nothing.

```
$ curl -s 'localhost:8000/v1/search?q=coracao'
 total 914
  Eclo 25,31 | <em>Coração</em> abatido, rosto triste e chaga do <em>coração</em>, eis (o que produz) uma
```

## The seven that were server errors

Each of these is a `fts5: syntax error` when handed to `MATCH` unchanged. One of
them is how half the world writes a reference.

```
  Deus (pai)       HTTP 200
  Jo 3:16          HTTP 200
  o Senhor's       HTTP 200
  fé -             HTTP 200
  a OR             HTTP 200
  AND              HTTP 200
  NEAR             HTTP 200
```

## Commentary, and the round trip it promises

The hit says where the note hangs. That address opens through the commentary
route that already existed, with nothing new to learn.

```
$ curl -s 'localhost:8000/v1/search/commentary?q=coracao&language=pt-BR'
 total 497
  haydock pt-BR Eclo 51,28 | <em>Coração</em>. Ou entendimento, pois os hebreus situam este no <em>…
  haydock pt-BR At 5,3     | Por que Satanás tentou o teu <em>coração</em>? [2] As cópias gregas at…

$ curl -s 'localhost:8000/v1/books/PSA/chapters/21/verses/1/commentary'
  Sl 21,1 -> 1 source(s)
```

## `version=all`, and the cost being visible rather than argued

The same address comes back once per translation, and each hit names its own.
The reference is written the way that translation writes it, which is the
existing rule rather than a new one.

```
$ curl -s 'localhost:8000/v1/search?q=Jerusalem&version=all&limit=8'
 total 2588
  vulgata-clementina   ISA.52.9     Is. 52,9
  vulgata-clementina   EZR.10.7     Esdr. 10,7
  matos-soares         ISA.52.9     Is 52,9
  vulgata-clementina   ZEC.12.3     Zach. 12,3
  matos-soares         ACT.1.12     At 1,12
  vulgata-clementina   JDG.1.21     Iudic. 1,21
  vulgata-clementina   2KI.15.2     IV Reg. 15,2
  vulgata-clementina   JER.38.28    Ier. 38,28
```

`ISA.52.9` is in that list twice, once as `Is. 52,9` and once as `Is 52,9`. That
is the repetition `LIMITS.md` publishes and the notation rule working together.

## The bounds and the refusals

```
  offset=1000  HTTP 200
  offset=1001  HTTP 422
  limit=100    HTTP 200
  limit=101    HTTP 422
  limit=0      HTTP 422

  q=Deus&book=Hogwarts         HTTP 404
  q=Deus&version=king-james    HTTP 404
  q=!!!                        HTTP 422
```

```json
{"detail":{"reason":"malformed","message":"the query carries no searchable word","input":"!!!"}}
{"detail":{"reason":"unknown_book","message":"no book named 'Hogwarts'","input":"Hogwarts"}}
{"detail":{"reason":"unknown_version","message":"no version named 'king-james'","input":"king-james"}}
```

## Caching, and the document

A verse is immutable for a year. A result list is not, because it depends on
what is published.

```
  search  cache-control: public, max-age=300
  verse   cache-control: public, max-age=31536000, immutable

  /openapi.json paths: ['/v1/search', '/v1/search/commentary']
```

## What the measurements actually say

The spec's timings were taken on the bare index with no join and no filter. The
plan refused to publish them and required the real query to be measured first,
and the real query is slower. Warm, median of seven, on the built database.

| Query | Hits | Count | First page | Page at offset 1000 |
|---|---|---|---|---|
| `coracao`, one translation | 914 | 1.0 ms | 2.1 ms | 6.2 ms |
| `Deus`, one translation | 4539 | 5.0 ms | 16.7 ms | 21.5 ms |
| `a`, one translation | 18904 | 13.4 ms | 30.4 ms | 44.9 ms |
| `a`, `version=all` | 29007 | 14.8 ms | 38.7 ms | 54.3 ms |
| `a`, commentary | 22393 | 18.2 ms | 36.3 ms | 78.7 ms |

A real query costs about 3 ms. A single letter costs about 50 ms for the first
page and about 100 ms at the cap. The cap of 1000 was chosen against these
numbers rather than the optimistic ones, and both are in `LIMITS.md`.

`EXPLAIN QUERY PLAN` on the filtered query.

```
SEARCH books USING PRIMARY KEY (code=?)
SCAN verse_search VIRTUAL TABLE INDEX 0:M1
SEARCH texts USING INTEGER PRIMARY KEY (rowid=?)
SEARCH spine USING INTEGER PRIMARY KEY (rowid=?)
USE TEMP B-TREE FOR ORDER BY
```

The temporary B-tree is inherent. Ranking has to sort every match before it can
page, which is the whole reason the cost grows with the offset and the reason
there is a cap at all.

## The storage change, on the real build

```
built: 88.0 MB
verse_search 107103
note_search  41410
```

B8 left the file at 93.1 MB. B9 adds full-text search over 107103 verses and
41410 commentary bodies and the file is 88.0 MB.

The spec predicted 86.1 MB. That number came from a vacuumed scratch copy and
the build does not vacuum, so the honest figure is 88.0 and the prediction is
recorded rather than quietly replaced.

## What QA found that the tests did not

**The container would not start, and the reason was not B9.**

```
File "/app/src/catholic_bible/api/ratelimit.py", line 141, in default_store
    home.mkdir(mode=0o700, exist_ok=True)
OSError: [Errno 28] No space left on device: '/tmp/catholic-bible-1000'
INFO: 192.168.16.1:60644 - "GET /health HTTP/1.1" 500 Internal Server Error
```

The immediate cause was a full Docker VM disk on this laptop, and pruning 6.6 GB
of build cache cleared it. The defect underneath is B8's and it is not
environmental.

`default_store()` creates the directory. That call sits inside
`Settings.from_env()`, which sits inside `RateLimiter.__init__`, and nothing
catches it. B8's stated posture is fail open and loud, and
`test_an_unusable_store_serves_the_request_and_says_so` proves it for a store
that cannot be **opened**. A store whose directory cannot be **created** takes
the whole API down instead, on every request, including `/health`.

Reproduced away from the full disk, so the finding does not rest on this
laptop's state.

```
$ python -c "... rl.default_store = raises OSError(28) ..."
the whole application refused to start: OSError [Errno 28] No space left on device
```

Same class of failure, opposite outcome, and the one that actually happened on a
real box is the one that crashes. It is not B9's and it is not fixed here. It
needs its own issue and its own branch, under the one epic per pull request rule.
