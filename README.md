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
of records came back flagged and every one of them was published anyway. **No
human has read a sample and written down an error rate.** The sample is drawn
and waiting in `docs/qa/haydock-translation-sample.csv`, 200 entries, and the
day someone fills in the verdict column this paragraph gets a number in it. The
English is the 1859 transcription and it was not touched.

What has been checked is structure. No body is empty, none is identical to the
English it came from, none is wildly shorter or longer, and in the sample of 200
every digit survives. Across all 20705, one body in 115 differs in emphasis
markup and one in 245 loses or gains a digit, and reading a handful of those
shows both real losses and correct choices like `40 years` becoming
`quarenta anos`. No mechanical check separates the two, which is what the sample
is for. None of it says whether a sentence means what the Latin behind it means.
`make audit-translation` recomputes all of it.

There are no cross-references yet, no full text search, no static artifacts on a
CDN, and nothing is deployed. The API is read only and it always will be.

244 of the 20705 Portuguese bodies shipped with the translation harness's own
control markers inside the text, and one unrelated note glued on behind each.
That was found by running those checks and it is fixed. `LIMITS.md` says what
was cut and how the cut was verified not to remove content.

`ROADMAP.md` says what is coming and why. `docs/epics/` holds one file per epic,
`docs/method/` records the process that produced them, and `LIMITS.md` says what
this repo cannot prove.

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
{"status":"ok","version":"0.0.0"}
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

Nine routes, all `GET`, all under `/v1`.

```
GET /v1/versions
GET /v1/versions/{version}/books
GET /v1/versions/{version}/books/{book}
GET /v1/versions/{version}/books/{book}/chapters/{chapter}
GET /v1/versions/{version}/books/{book}/chapters/{chapter}/verses/{verse}
GET /v1/books/{book}/chapters/{chapter}/verses/{verse}/commentary
GET /v1/passage?ref=&versions=&scheme=
GET /v1/resolve?ref=&scheme=
GET /v1/commentary?ref=&scheme=
```

Commentary takes no version, because a note on John 3:16 is the same note
whichever translation is on screen. Both languages come back together and the
rights block on each source says which one a machine produced.

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
