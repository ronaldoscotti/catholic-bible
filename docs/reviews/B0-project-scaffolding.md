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
keeps the private context and the caches out and lets the suite run inside the
container. Trimming further would buy a few hundred kilobytes and cost the
ability to reproduce a test failure in the same environment that runs it.

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
