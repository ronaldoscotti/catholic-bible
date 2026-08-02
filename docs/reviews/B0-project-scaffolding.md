# Review, B0 project scaffolding

Self-review. This repo has one author, so this does not satisfy the gate in
`docs/method/README.md`, which says a pull request gets reviewed before it
merges. What follows is what a reviewer would have asked, asked by the person
who wrote the code, and it is written down so the next reader can see the
reasoning rather than trust it.

## Resolved before the commit

**The health test could have been a placeholder.** It reads the version from
`importlib.metadata` instead of asserting a literal, which ties it to packaging.
Proven by mutation in `docs/qa/B0-project-scaffolding.md`.

**`httpx` was deprecated by Starlette on the first sync.** The suite went green
with a `StarletteDeprecationWarning` telling us to install `httpx2` instead. The
dev dependency was swapped, so the repo does not begin life with a warning
everybody learns to scroll past.

**The image could have carried `CONTEXT.local.md`.** It is in `.dockerignore`
and its absence is checked in QA.

**`.dockerignore` had drifted from `.gitignore` and a `.env` reached the
image.** `.gitignore` excluded `.env` and `.dockerignore` did not, so `COPY .
/app` carried anything git was hiding. Found by writing a `SECRET_TOKEN` into a
local `.env`, rebuilding, and reading it back out of `/app/.env`. Both files now
carry the same exclusions and the reason sits at the top of `.dockerignore`.

**The container could have run as root.** It runs as `app`, uid 1000.

## Accepted, with the reason

**Host and port are hardcoded in `main()`.** `0.0.0.0:8000`, no environment
variable. B6 is the epic that deploys this and it is the one that knows what the
production box needs. A config layer written now would be guessing at a
requirement that does not exist yet.

**Dependencies carry no version floors.** `uv.lock` is committed, so a clean
checkout is reproducible today. Floors become necessary when B10 publishes to
PyPI and a consumer resolves against their own tree, and B10 is where they get
written with a reason each.

**The image copies tests and docs.** `COPY . /app` after `.dockerignore`, which
keeps the private context, the caches and the environment files out. The suite
cannot run in there, because `UV_NO_DEV=1` means `pytest` is never installed, so
the extra files buy nothing beyond a smaller diff in the Dockerfile. Kept
because the cost is a few hundred kilobytes on an image nobody has deployed
yet, and B6 is the epic that has a reason to care about image size.

An earlier draft of this document justified the same decision by claiming the
suite could run inside the container. That was false and it was caught in
review, by running `python -m pytest` in the image and reading `No module named
pytest`.

**CI runs on both push and pull request, so a PR branch runs twice.** The epic
asks for both by name. The waste is two minutes of a free runner.

**No dependency direction check.** The three packages are empty and there is
nothing to violate yet. `import-linter` earns its place in B1, when the canon
has code that storage could reach into.

## Left open

There is no `LICENSE` file and `pyproject.toml` declares no license. B10 cannot
publish without one and `LIMITS.md` is where the rights audit goes, so the
decision belongs to whichever of those lands first. Nothing here claims a
license in the meantime.
