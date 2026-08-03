# catholic-bible

A read-only API and a published dataset for the Catholic Bible. 73 books,
Portuguese, English and Latin, public domain throughout.

## Status

Scripture is here and it is readable over HTTP. Three translations, 107103
verses, addressed on a versification spine of 35845 slots.

Commentary is here too. The Haydock, 20705 notes over all 73 books, in English
and in Portuguese, anchored on the same verse ids.

**Read this before you use the Portuguese commentary.** It was translated by a
language model, not by a person. The prompt required faithful rendering,
Catholic ecclesiastical terminology and untouched Scripture citations, and it
asked the model to flag polemic, dated exegesis, pre-modern science and language
about the Jewish people that the Church has revised since Nostra Aetate. 5.47%
of records came back flagged and every one of them was published anyway. The
English is the 1859 transcription and it was not touched.

**200 of the 20705 entries have been read against the English, and 5 carried a
defect.** That is 2.5%, with a 95% interval of 1.1% to 5.7%, and two of the five
say the opposite of what the English says. `docs/qa/haydock-translation-review.md`
names all five and quotes them.

**A language model did that reading, so it is a machine grading a machine.** It
is weaker than a person and it is what exists. The author read the sample first
and flagged nothing. 20505 entries have still been read by nobody.

What has been checked is structure. No body is empty, none is identical to the
English it came from, none is wildly shorter or longer, and in the sample of 200
every digit survives. Across all 20705, one body in 115 differs in emphasis
markup and one in 245 loses or gains a digit, and reading a handful of those
shows both real losses and correct choices like `40 years` becoming
`quarenta anos`. No mechanical check separates the two, which is what the sample
is for. None of it says whether a sentence means what the Latin behind it means.
`make audit-translation` recomputes all of it.

Cross-references are here as well. 207636 of them on 26726 addresses, from
three sources, and the one thing worth knowing about them is in the next
section.

All of it is also published as static files on a CDN, which is the cheapest way
to use any of this and needs no server at all.

There is no full text search and nothing is deployed yet. The API is read only
and it always will be.

## The deuterocanonical books are the point

The largest free cross-reference set in existence is OpenBible, 204601 entries,
and **not one of them touches Tobit, Judith, Wisdom, Sirach, Baruch or the
Maccabees**, in either direction. That is not an accident and it is not a
complaint about anyone. The set was built by and for readers whose canon has 66
books.

So the passages a Catholic reader most needs connected are the ones every
available set leaves unconnected. Matthew 4:4 quotes Wisdom 16:26 and no amount
of consensus voting will tell you so.

What closes the gap here is 292 authored pairs of addresses, expanded in both
directions, carrying no text from any source. They are 665 of the 920 surviving
deuterocanonical links. `LIMITS.md` says where they came from and on what
reading they ship.

Cross-references from OpenBible are used under CC BY 4.0.
**Cross-references courtesy of OpenBible.info.** The same notice travels inside
every API response that draws on them, and inside the published dataset, because
an attribution only in a README is an attribution a consumer never sees.

244 of the 20705 Portuguese bodies shipped with the translation harness's own
control markers inside the text, and one unrelated note glued on behind each.
That was found by running those checks and it is fixed. `LIMITS.md` says what
was cut and how the cut was verified not to remove content.

`ROADMAP.md` says what is coming and why. `docs/epics/` holds one file per epic,
`docs/method/` records the process that produced them, and `LIMITS.md` says what
this repo cannot prove.

## The cheapest way in

No install, no key, no account, no server. Paste this into a blank HTML file and
open it.

```js
const book = await (await fetch('https://cdn.jsdelivr.net/gh/ronaldoscotti/catholic-bible@v1.0.0/data/versions/matos-soares/books/SIR.json')).json()
console.log(book.verses['SIR.24.1'].text)
```

That is Sirach 24:1 in Portuguese, from a book of the canon most free Bible data
does not carry. 371 files ship this way, 48 MB, covering three translations, the
Haydock in both languages, the cross-references, the canon, the spine and the
unfilled address report.

```
data/index.json                              what exists, and the URL pattern
data/manifest.json                           sha256 and byte count for all 370
data/versions/{version}/books/{book}.json    73 books, three translations
data/commentary/haydock/books/{book}.json    20705 notes, English and Portuguese
data/cross-references/books/{book}.json      207636 references, three sources
data/canon.json  data/spine.json             the 73 books, the 35845 addresses
data/orphans.json  data/coverage.json        what fails to map, and what is unfilled
```

Every file carries its own rights record. A file copied into somebody's project
keeps its provenance or loses it forever, and the OpenBible attribution that
CC BY requires rides inside all 73 cross-reference files rather than only here.

### The version in the URL is the whole contract

`@v1.0.0` is not decoration. Pin it and the bytes behind that URL never change.

Corrections ship as a new tag and the old one keeps answering, because a
consumer who pinned a version has to be able to trust the pin. A repository
ruleset blocks deleting or moving any `v*` tag, so this survives the author
changing his mind rather than resting on him not doing so.

The package version and the dataset version are the same number. `1.0.0`
governs the shape of these files and the shape of the API. It does not claim the
API is deployed anywhere, and `LIMITS.md` says plainly that it is not.

Drop the tag and jsDelivr serves the default branch, which moves. Do not do that
in anything you ship.

## Quickstart

Docker is the only requirement, and there are no credentials to set up.

```sh
git clone https://github.com/ronaldoscotti/catholic-bible.git
cd catholic-bible
docker compose up --build
```

From another terminal.

```sh
curl http://localhost:8000/health
```

```json
{"status":"ok","version":"1.0.0"}
```

Then read a verse. Sirach 24:1, in Portuguese, by reference.

```sh
curl "http://localhost:8000/v1/resolve?ref=Eclo%2024,1"
```

Or by address, in Latin.

```sh
curl http://localhost:8000/v1/versions/vulgata-clementina/books/SIR/chapters/24/verses/1
```

```json
{"id":"SIR.24.1","book":"SIR","chapter":24,"verse":1,"reference":"Eccli. 24,1","text":"Sapientia laudabit animam suam, et in Deo honorabitur, et in medio populi sui gloriabitur,"}
```

Interactive docs are at `http://localhost:8000/docs` and the published contract
is `openapi.json` in this repository.

CI runs those same commands on a clean checkout for every push and every pull
request, because a quickstart nobody executes rots within a month.

## Reading it

Eleven routes, all `GET`, all under `/v1`.

```
GET /v1/versions
GET /v1/versions/{version}/books
GET /v1/versions/{version}/books/{book}
GET /v1/versions/{version}/books/{book}/chapters/{chapter}
GET /v1/versions/{version}/books/{book}/chapters/{chapter}/verses/{verse}
GET /v1/books/{book}/chapters/{chapter}/verses/{verse}/commentary
GET /v1/books/{book}/chapters/{chapter}/verses/{verse}/cross-references
GET /v1/passage?ref=&versions=&scheme=
GET /v1/resolve?ref=&scheme=
GET /v1/commentary?ref=&scheme=
GET /v1/cross-references?ref=&scheme=
```

Commentary and cross-references take no version, because a note on John 3:16 is
the same note whichever translation is on screen. Both languages of a note come
back together and the rights block on each source says which one a machine
produced.

A book is named by its USX code or by any name that resolves, in Portuguese,
English or Latin. `Jo` is John and `Jó` is Job, and the accent is never folded.

**Say which numbering you wrote a reference in.** `Sl 51,1` means the spine's
Psalm 51 by default and `?scheme=org` makes it the Miserere, which the spine
numbers 50. Both answers are correct and only one of them is yours.

Names, abbreviations and notation follow the language of the version being read,
so the same verse comes back as `Eclo 24,1`, `Ecclus. 24:1` and `Eccli. 24,1`.

## Development

`uv` manages dependencies and the lockfile is committed, so a clean checkout
resolves to the same versions this was written against.

```sh
uv sync
make test
make lint
make typecheck
```

`make fmt` formats and applies safe lint fixes. `make run` is `docker compose up
--build`, which keeps the container as the one way to boot the service instead
of letting a second path drift beside it.

## Layout

```
src/catholic_bible/
  canon/     the 73 books and the versification spine
  storage/   SQLite on local disk, built from the published corpus
  api/       FastAPI
```

Dependencies run one way. The canon knows nothing about storage and storage
knows nothing about HTTP. A module that imports upward is a bug rather than a
shortcut.
