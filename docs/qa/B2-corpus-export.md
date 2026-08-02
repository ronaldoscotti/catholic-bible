# QA, B2 corpus export and integrity

*Stage 6. Run 2026-08-02, on `feat/b2-corpus-export`.*

Reading the diff is not QA. This is what ran and what came back.

## The suite, the linter and the type checker

```
$ make lint
All checks passed!
57 files already formatted

$ make typecheck
Success: no issues found in 30 source files

$ make test
263 passed
```

## The verification the epic names

The epic names two jobs and says which proves what.

**The checksum job.** It is the corpus tests, and they run in CI on a clean
checkout with no access to the private source. `make verify-export` is the other
one.

**The job with teeth, and it was proved rather than trusted.**

```
$ make verify-export SOURCE=~/…/meu-feed-catolico-api
verified: the committed data is byte for byte a fresh export
```

Then one verse was hand edited, `Tem piedade de mim, ó Deus` to `oh Deus`, and it
ran again.

```
>    "text": "Tem piedade de mim, oh Deus, segundo a tua misericórdia; …"
MISMATCH: committed data differs from a fresh export
make: *** [verify-export] Error 1
```

Re-exported and it went green again.

**The first version of that target did not work and passed anyway.** It exported
over the committed files and then diffed, which overwrites the hand edit before
looking for it. It now exports into a scratch directory and compares. This is the
whole reason to run a check against a mutation instead of trusting a green line.

## A clean checkout with no private source

```
$ git clone --branch feat/b2-corpus-export . /tmp/cleanroom2
$ ls /tmp/cleanroom2/CONTEXT.local.md
ls: CONTEXT.local.md: No such file or directory
$ uv sync && uv run pytest -q
263 passed
```

## The container carries the corpus and not the Ave Maria

```
$ docker compose up --build -d --wait
Container catholic-bible-api-1  Healthy

$ docker compose exec -T api python -c "…"
in-container Miserere pt: Tem piedade de mim, ó Deus, segundo a tua misericórd
in-container Susanna la : Et erat vir habitans in Babylone, et nomen ejus Joak

$ docker compose exec -T api sh -c "grep -c 'ave-maria' …/corpus/*.json"
0, 0, 0, 0
```

Susanna is checked on purpose. It is a chapter `org` has no slot for at all, so
text arriving there means the spine and the corpus agree about the shape of the
canon.

## Defects found during QA, and all four were silent

**The mysql client defaults to latin1.** The first export brought `ó` back as a
raw byte, surfacing as a surrogate escape. Every accented character in the
Portuguese and Latin corpus was corrupt, and a corpus corrupt in that way passes
every count, every key check and every checksum. Fixed with
`--default-character-set=utf8mb4`, and the Miserere now has a test that reads it
in three languages.

**Batch mode escapes its own output.** MySQL's `-B` escapes characters, which
corrupted the JSON the query itself builds, and the parse failed at column
100235 of a six megabyte string. `--raw` turns it off.

**Twelve Douay verses are empty upstream.** Found by a test asserting no verse is
blank. Traced to the MIT fixture, where the `text` field is `''` while
`textLatin` is present at the same twelve addresses, so it is not an export bug.
They are omitted rather than published as empty strings.

**`make verify-export` destroyed its own evidence.** Described above.

## What was cross-checked rather than assumed

The published `order` comes from the private repository's `canonical_order`
column. The spine walks the versification independently in this repo. They agree
on all 107103 verses, which is two codebases arriving at the same shape of the
canon by different routes.

Every published address exists on the spine. Zero exceptions across three
versions.

## What is not covered

No HTTP. The only route is still `/health`.

Nothing here proves the text is a faithful transcription of Matos Soares. It
proves it is faithfully what the private repository holds. Transcription
fidelity is a question for the source and it is not answerable here.

The orphan rate the epic asked for is not measurable in this repo, and
`LIMITS.md` says so rather than publishing a zero.
