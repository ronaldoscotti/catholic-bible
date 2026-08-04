# Contributing

The most useful thing anyone can do here is read Portuguese.

## What is actually wanted

**Read the Haydock translation.** 20705 notes were rendered from English by a
language model and no person has checked them. A seeded sample of 200 entries
sits at `docs/qa/haydock-translation-sample.csv` with the English beside each
one, and `docs/qa/haydock-translation-review.md` records what has been checked so
far and by what. Work through entries, record a verdict in
`docs/qa/haydock-translation-verdicts.csv`, update the record, and the suite will
tell you if the two disagree.

**Report a verse that is wrong.** Open an issue with the address, the version and
the source you are reading against. A wrong verse is the most serious defect this
project can have.

**Add a cross-reference.** The deuterocanonical gap is the reason this exists and
292 authored pairs do not close it. Bring the reading it rests on.

## Nothing enters without a conformance case

**No alias and no numbering scheme lands without a case in the conformance
corpus.** Not a nice-to-have and not waived for something obvious.

An alias is a name that resolves to a book. `Jo` is John and `Jó` is Job, one
accent apart, and the day the accent gets folded every Portuguese reference to
Job silently becomes John. A scheme is a whole coordinate space, and adding one
changes what every address in it means. Both are the kind of change that looks
harmless in a diff and is not observable until a reader gets the wrong verse
back.

So the pull request carries the case, the case fails before the change and passes
after, and a reviewer can see which behaviour is new.

## What will be refused

**Text under copyright.** `LIMITS.md` carries the rights audit and every asset
has a stated legal basis. The Ave Maria apparatus is out, the Portuguese Catena
Aurea is out, and the text of the Catechism is out. Paragraph numbers and links
to `vatican.va` are references and those are welcome. A summary, a title or a
first line of a Catechism paragraph is the text wearing a hat and it is the same
refusal.

**Hand-edited data.** No JSON is authored here. Everything under `data/` comes
out of a committed script, carries a checksum and names its source commit. A
value no script produced does not ship, and CI recomputes the hashes.

**Writing, not reading.** This is a read-only project. No accounts, no
authentication, no user data, no endpoint that writes.

**Semantic search and embeddings.** Those belong to `concordantia`, which
consumes the artifact published here.

## Before you open a pull request

```sh
uv sync
make test
make lint
make typecheck
make lint-voice
```

`make lint-voice` checks the published prose for em-dashes and for the banned
word list. It is the floor under the voice, not the voice. The real check is
somebody reading it.

If you changed a route, regenerate the contract. `openapi.json` is committed and
CI fails on a difference, and it also fails on a route with no summary, no
response model or no documented errors.

```sh
make openapi
```

If you changed anything under `data/`, the artifacts follow.

```sh
make artifacts
```

## Conventions

Everything that reaches git is English. Commits, pull request titles and bodies,
issues, code and documentation. The project content is Portuguese and the
metadata is not.

Conventional commits, imperative subject, lowercase after the type.
`feat: add vulgate psalm mapping`, not `feat: added` and not `feat: adiciona`.

Branches as `<type>/<epic>-<slug>`. Work lands through a pull request and never
through a push to `main`. The pull request links its issue, says what changed and
why, and says what is still broken.

Comments are the exception rather than the habit. Always English, few and short.
A docblock on a public function earns its place, so does a non-obvious decision
or a known limit. Never a section banner, never narration of the next line and
never commented-out code.

## How the work is organised

An epic is the unit of work. `docs/epics/` holds one file per epic and that file
is the source of truth for its GitHub issue, not the other way around. Edit the
file and run `scripts/sync-issues.sh` rather than editing the issue in a browser.

`docs/method/` records the pipeline and where the project actually stands,
including the gates that are not met. Read it before picking something up.
