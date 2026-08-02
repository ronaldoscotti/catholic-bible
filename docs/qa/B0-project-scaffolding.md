# QA, B0 project scaffolding

Run on 2026-08-02, macOS 15, Docker 28.5.1, uv 0.12.1, Python 3.13.0.

## The test bites

The acceptance criteria ask for one real test rather than a placeholder, so the
claim was checked by breaking the thing it covers.

`Health(status="ok", version=__version__)` was changed to a hardcoded `"1.2.3"`
and `uv run pytest` failed on `{'version': '1.2.3'} != {'version': '0.0.0'}`.
The mutation was reverted and the suite went green again. The test reads the
version from the installed distribution metadata, so it also fails if the
package stops being installable or if the app stops importing.

## Local gate

```
make lint       ruff check and ruff format --check, both clean
make typecheck  mypy strict, 6 source files, no issues
make test       1 passed
```

## Container

`docker compose down --rmi local -v` first, so the build ran with no image and
no network to inherit.

```
docker compose up -d --build --wait   container reports healthy
curl http://localhost:8000/health     {"status":"ok","version":"0.0.0"}
curl -o /dev/null -w '%{http_code}' http://localhost:8000/docs   200
```

Two things worth checking beyond the happy path, both verified with
`docker compose exec`.

`CONTEXT.local.md` is absent from `/app`. It is private and it is in
`.dockerignore`, and an image that carried it would leak a private repo map into
anything published later.

The process runs as `app` rather than `root`.

## Not verified here

CI itself. The workflow is written and it has never executed, because the branch
has no remote yet. The first push is what verifies it, and the epic closes on CI
green on the merge commit rather than on this document.
