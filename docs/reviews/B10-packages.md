# Code review, B10 packages on PyPI and npm

*Stage 7. Run 2026-08-05, one author, before the pull request opened. Third
epic in a row in the right order.*

**This one has no second reader.** B8 and B9 both had a review agent read the
diff and both times it found the worst thing in the epic. Nothing here got that,
so what follows is the author reading his own work, which `docs/method/README.md`
already records as a gate this repository does not meet.

## The one the spec gate would have shipped

**The recommendation that decided the shape of this epic rested on a premise
nobody had run.**

The author was asked to choose between one Python distribution and two, and the
argument for one was that `pip install` leaves a working API in a single
command. That argument was made, accepted, and was false. The wheel does not
carry `bible.db`, because it is derived and therefore gitignored, so an
installed copy answered 503 on `/health` and 500 on every route.

It was caught by building the wheel and running it, which took four minutes and
happened before the spec was written rather than after the code was. Had the
spec been written on the argument instead, the first person to install this
would have found it.

The lesson is narrow and worth keeping. A recommendation that describes what a
command does is a claim, and a claim about a command is cheap to check by
running the command.

## The one that came back from the registry rather than the documentation

The plan listed *whether npm will trust a name that has never been published* as
an open question, chose a fallback, and moved on. That reads as rigour and is a
stall. One invocation of `npm help trust` answered it.

> Package must exist: The package you're configuring must already exist on the
> npm registry.

The fallback was not a fallback. It is the only path, and two more constraints
came with it that the plan had not imagined. Trust commands need `npm@11.15.0`,
against 11.6.2 on the author's machine, and they refuse the bypass 2FA tokens
that continuous integration must use, so the credential that performs the first
publish cannot perform the configuration.

**Had this waited for the tag, `v1.1.0` would have failed on npm** with the
trusted publisher correctly configured against a package that does not exist.

The same shape appeared twice more. The npm size limit was written as
unestablishable from the documentation, and one query against `aws-sdk` settled
it at 93.6 MB over 2287 files. Both times the registry answered a question about
itself that the documentation did not.

## What the machines caught that the author did not

**CI found a real defect on the first run of the new job.** The runner's default
interpreter is 3.12 and `requires-python` is 3.13. The other two jobs never see
this because `uv` installs its own interpreter, and the new job deliberately
uses plain `pip` because that is what a stranger uses. Being the only job
standing in the reader's shoes is exactly why it was the only one to fail.

**`npm pack` found the manifest describing a tarball npm does not produce.** npm
ships every `README*` whatever the `files` field says, so the Portuguese README
was travelling unlisted. The check reads its allowlist out of `package.json` now
rather than repeating it, so the two cannot disagree silently.

**The suite found a leaked sqlite handle** in code written ten minutes earlier.
`with sqlite3.connect(...)` commits and does not close, and `filterwarnings =
["error"]` turned the unraisable warning into a failure. The same pattern is in
`scripts/build-db.py` and always was, where it is harmless because the process
exits.

## A test that passed for the wrong reason

`test_health_fails_when_the_store_is_unreadable` patched the packaged path to a
file that does not exist. Under the new three step resolution that only moves
the lookup down to the per-user cache, so on any machine that had ever run an
installed copy it would have found a real database and passed while asserting a
503.

It uses the override now, which is the documented seam, and deleting the
override branch makes it fail.

Two other defences were mutated and both held. The version in the cache path,
without which `pip install -U` reads a stale database. And `bootstrap.ensure()`
in `main()`, without which nothing in 782 tests notices, because the process
still starts.

## The shell trap, for the third time

Measuring whether the artifact gate rejects a hand edited `package.json`
printed `exit=0`. The command was piped into `tail` and the exit code belonged
to `tail`. The real answer was 1.

B8 found this printing green over a type error. B9 found `grep -c` exiting 1 on
zero matches and breaking an `&&` chain, which also happened again here. Three
epics, three variations, and the fix each time was to stop reading a pipeline's
exit status. It is written down for the third time and the honest reading is
that writing it down is not working.

## What was checked and found sound

**The dependency direction holds.** `bootstrap.py` imports `storage.build` and
`storage.database` and nothing above it. `app.py` imports storage, which is the
direction the rule allows.

**Nothing published lost its provenance.** All 371 artifacts regenerate byte
identical, `openapi.json` regenerates byte identical, and the working tree is
clean after every generator runs.

**The private context is nowhere near git or the image.** Not tracked, and
matched by both `.gitignore` and `.dockerignore`.

**No text under copyright moved.** This epic adds a `LICENSE` and a manifest and
touches no corpus file.

**Zero em-dashes** across every prose document including the new ones, and the
voice lint passes on 18.

## What is still open

**Nothing is published, so three criteria are unticked.** They will close on
`v1.1.0-rc.1` and `v1.1.0` and not before.

**The README names a command that returns 404.** That is a claim the code has
not earned, so the quickstart carries a paragraph saying so, and that paragraph
comes down with the tag. B5 left the same gap and recorded it the same way.

**The Windows cache path has never executed.** Read, not run. No runner here is
Windows.

**One long-lived npm token will exist for the length of one release.** It is the
only way to bring the name into existence, npm's own notice says tokens that
bypass 2FA are being restricted for direct publishing, and the window for the
cheap bootstrap is open now with nobody promising how long.
