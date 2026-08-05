# QA, B10 packages on PyPI and npm

*Stage 6. Run 2026-08-04 and 2026-08-05, against the branch before the pull
request opened. Exercised as a person installing this, not by reading the diff.*

## The verification the epic names

> An install test in CI does a clean install of each published package and runs
> the documented quickstart against it.

**Half of it ran and the other half cannot run yet**, because nothing is
published. What ran is a clean install of the package this branch builds, which
answers the question the epic is actually asking about the artifact. What did
not run is the install from the registry, which answers a different question
about the registry, and that one waits for `v1.1.0-rc.1`.

The job that will run it is written, in `release.yml`, and it retries both
registries the way `cdn.yml` retries jsDelivr.

## What the installed package does

Built with `uv build`, installed into an empty virtualenv, run with the source
tree nowhere on the path.

```
$ /tmp/probe/bin/python -c "import catholic_bible; print(catholic_bible.__file__)"
/tmp/probe/lib/python3.13/site-packages/catholic_bible/__init__.py

$ /tmp/probe/bin/python -c "
from catholic_bible.canon.reference import parse_reference
print(parse_reference('Eclo 24,1'))
print(parse_reference('Jo 3,16'), parse_reference('Jó 3,16'))
"
Reference(book='SIR', bounds=((24, 1), (24, 1)), whole_chapter=False, parts=None)
Reference(book='JHN', ...) Reference(book='JOB', ...)
```

`Jo` is John and `Jó` is Job, out of the installed wheel rather than out of the
checkout, which is the one behaviour this project exists for.

The conformance corpus runs there too, 85 cases, copied out of the checkout into
a bare directory so no sibling `conftest.py` can reach it.

## The failure this epic was actually fixing

Before any of it, on the same clean install.

```
$ ./probe/bin/catholic-bible-api
$ curl -i http://localhost:8000/health
HTTP/1.1 503 Service Unavailable
{"reason":"store_unavailable","message":"no database at
 /.../site-packages/catholic_bible/data/derived/bible.db. run `make db` to build it"}

$ curl http://localhost:8000/v1/versions
Internal Server Error
```

`make db` is a Makefile target in a repository the reader does not have, so the
one instruction the failure offered was unreachable from where they stood.

After.

```
$ /tmp/probe/bin/catholic-bible-api
building the read database at /Users/scotti/Library/Caches/the-catholic-bible/1.0.1/bible.db, once, this takes a moment

$ curl http://localhost:8000/health
{"status":"ok","version":"1.0.1"}
$ grep -m1 '^{"status"' README.md
{"status":"ok","version":"1.0.1"}

$ curl http://localhost:8000/v1/versions/vulgata-clementina/books/SIR/chapters/24/verses/1
{"id":"SIR.24.1",...,"text":"Sapientia laudabit animam suam, ..."}
```

Byte identical to what the README publishes, both of them, from a package
rather than from a checkout.

Search works from the install as well, which nothing asked for and is the sort
of thing that quietly does not survive a packaging change. `?q=coracao` returns
914 hits with the accented form marked.

## The measurement that changed a decision

The spec said the first boot costs 4.9 seconds. That was a warm rebuild inside
the checkout, and the plan refused to let it reach the README until a cold
runner produced one.

```
laptop, cold, into the cache directory      10 s
CI runner, cold                              6 s
checkout, warm                               5 s
```

Two of those differ by 40%, so the first-boot message names no duration at all.
Had the plan not carried that refusal, the README would have published whichever
number happened to be measured first.

## What the CI runner caught that this laptop could not

The `package` job failed on its first run.

```
ERROR: Package 'the-catholic-bible' requires a different Python: 3.12.3 not in '>=3.13'
```

The runner's default interpreter is 3.12 and the other two jobs never see it,
because `uv` installs its own. This job deliberately uses plain `pip`, since
that is what a stranger uses, and that is exactly why it was the only one
standing in the reader's shoes. It reads `.python-version` now.

## What `npm pack` said that `package.json` did not

```
375 files, 48.2 MB unpacked, 13.2 MB packed
stray [ 'README.pt-BR.md' ]
```

npm ships every `README*` whatever the `files` field says. The manifest was
describing a tarball npm does not produce, so the Portuguese README is listed
now. The CI check reads its allowlist out of `package.json` rather than
repeating it, so a file added to one and not the other fails.

Size is not a risk. `aws-sdk` is live at 93.6 MB unpacked over 2287 files and
`@next/swc-linux-x64-gnu` at 92.2 MB, so this sits under half of both.

## Three defences mutated before being believed

Each was broken on purpose and the suite was watched.

**The version in the cache path.** Removed it, and
`test_the_cache_path_carries_the_version` failed. Without it, `pip install -U`
reads a database built by the previous version and `LIMITS.md` already has a
heading for that failure.

**The database override.** Deleted the branch that reads `CATHOLIC_BIBLE_DB`,
and the `/health` test failed. That test used to patch the packaged path
instead, which only moved resolution down to the per-user cache, so on a
machine that had ever run an installed copy it passed for the wrong reason.

**The first boot itself.** Removed `bootstrap.ensure()` from `main()`, and
`test_the_entry_point_builds_before_it_serves` failed. Nothing else in 782
tests would have noticed, because the process still starts and the failure only
shows up as a 503 that reads like a missing file.

**And the artifact gate.** Hand edited the version inside `package.json` and ran
the check.

```
$ uv run scripts/build-artifacts.py --check ; echo $?
data is not what the sources produce. run `make artifacts`
  differs: package.json
1
```

The first attempt at that measurement printed `exit=0`, because the command was
piped into `tail` and the exit code belonged to `tail`. Reading it without the
pipe is what gave the real answer. That is the third time this class of shell
trap has appeared in this repository, and `docs/method/README.md` records the
first two.

## The defect this walk found in the thing it was checking

Re-running the whole verification for the acceptance walk, rather than citing
the earlier run, turned up a real one.

```
$ catholic-bible-api > api.log 2>&1
$ head -5 api.log
INFO:     Started server process [57203]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
building the read database at /Users/.../1.0.1/bible.db, once, this takes a moment
```

The build genuinely runs before uvicorn and a test already held that. The
*message* arrived after uvicorn had reported itself up, because redirected
stdout is block buffered while uvicorn logs to stderr unbuffered.

**On a terminal this is invisible and in a log it is the whole failure.** The
line exists because ten seconds of silence reads as a hang, and a service runs
with its output redirected, which is precisely where the line was late.

`flush=True`. The notice is the first line of the log now.

`capsys` could never have caught it, since pytest replaces the stream, so the
new test runs the real interpreter into a real pipe and reads the line while the
build is still going. Removing the flush fails it.

## What is not covered

**Nothing here proves the OIDC configuration.** Both trusted publisher setups
live in the registries and cannot be tested from a pull request. The rehearsal
tag is the test.

**The Windows cache path is written and never executed.** `LOCALAPPDATA` is
covered by reading the code, not by running it, and no runner here is Windows.
The Linux branch runs on every push and the macOS branch ran on this laptop.

**`catholic-bible-build-db` is exercised only in CI**, where it produced 107103
verses over 35845 spine addresses into
`/home/runner/.cache/the-catholic-bible/1.0.1/bible.db`. Nobody has used it in
a real Dockerfile layer, which is the caller it was written for.
