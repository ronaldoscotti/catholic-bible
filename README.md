# catholic-bible

A read-only API and a published dataset for the Catholic Bible. 73 books,
Portuguese, English and Latin, public domain throughout.

## Status

Scaffolding, and that is the honest word for it.

There is no Bible in this repo yet. No canon, no versification spine, no verses,
no commentary, no dataset. What exists today is a Python project that builds,
runs in a container, tests, lints and type checks, so the first real epic can be
written test first instead of test eventually. The only endpoint is `/health`.

`ROADMAP.md` says what is coming and why. `docs/epics/` holds one file per epic
and `docs/method/` records the process that produced them.

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

Interactive docs are at `http://localhost:8000/docs`.

CI runs those same commands on a clean checkout for every push and every pull
request, because a quickstart nobody executes rots within a month.

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
  storage/   SQLite, with FTS5 for lexical search
  api/       FastAPI
```

Dependencies run one way. The canon knows nothing about storage and storage
knows nothing about HTTP. A module that imports upward is a bug rather than a
shortcut.
