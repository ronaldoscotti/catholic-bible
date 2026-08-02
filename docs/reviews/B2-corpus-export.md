# Code review, B2 corpus export and integrity

*Stage 7. Written 2026-08-02, one author.*

**A self review is not the gate.** One person, one repo. What is true is the
mechanism: branch, pull request, never a push to `main`.

## What the diff is

Two scripts, two small modules, three published corpus files at 18 MB, a
coverage report, `LIMITS.md`, and 48 new tests.

## The thing worth most attention

**Copyrighted material is one column away from what ships.** The private
database grafts 2305 Ave Maria pericope headings onto Matos Soares, in the
`heading` column of the same rows as the public domain text.

Two defences and they are independent. The export names its columns, so a
`SELECT *` would be a visible change to the query. And a test asserts every
published record has exactly the keys `order` and `text`, so the output has to be
clean regardless of what the query did. A third test greps the raw bytes for the
string. All three have to fail together.

That is the right amount of belt for this, because the failure is not a bug. It
is publishing someone else's property.

## Things I changed after looking again

**`build` returns a tuple now.** It was returning bytes and swallowing the blank
addresses. Returning both makes the omission visible at the call site, which is
where the count reaches provenance.

**Both export scripts grew `--dest`.** Only `verify-export` needs it, and adding
it to `export-spine.py` too keeps the two scripts symmetrical for a verification
that has to cover both.

## Things I am flagging rather than fixing

**18 MB in git, forever.** Compression was considered and skipped. It would save
about 12 MB and cost a decompression step in every consumer, including the
`fetch()` in B5 that is supposed to be one line. The number to decide against is
the CDN bill in B5, which does not exist yet.

**The corpus loader caches whole versions in memory.** `functools.cache` on
`load` means the first read of a version holds 6 MB for the process lifetime.
Fine for a test run and fine for a long lived server. It would be wrong for a
short lived worker, and B3 is where that gets measured.

**The credentials read is naive.** `read_credentials` splits `.env` lines on the
first `=` and does not handle quoting or interpolation. It works for the file it
reads. It would break on a quoted password, and the failure would be a login
error rather than anything subtle.

**Version codes reach SQL through an f-string.** They come from a tuple defined
in the same file and never from input, so it is not an injection path. It is
still the shape of one, and a future contributor adding a `--version` flag would
turn it into one.

## What I checked because it would fail quietly

**Encoding.** The whole corpus was silently corrupt on the first run. Now the
Miserere is read in three languages by a test, which is a canary for any future
change to how the query returns text.

**The two identities agreeing.** The private repository computes
`canonical_order` and this repo walks the spine. Nothing forces them to match.
They do, on all 107103 verses, and a test says so per version.

**Whether a claim outran the code.** The orphan rate is reported as not
measurable here rather than as zero. `LIMITS.md` says a stranger can verify
integrity and cannot verify authorship. The epic's zero orphan claim was
corrected to the measured 69. The twelve missing English verses are named
individually rather than summarised.

**Whether anything private leaked.** No credentials, no host, no port and no
database name in any committed file. The cleanroom clone and the container grep
are in the QA notes.

## Second pass, after the review tool ran

Seven findings, all reproduced before being acted on, and the second one was the
serious one.

**`verify-export` would have accused the author of tampering.** It re-exported
from whatever the private repository happened to be checked out at, and a fresh
export writes the current commit into provenance, so the first unrelated commit
over there makes the comparison differ. `LIMITS.md` teaches the reader that the
mismatch message means someone edited a verse. Reproduced with an empty commit,
which produced the accusation. It now refuses up front unless the source sits on
the commit provenance records, and it tells the operator what to do instead. It
also separates `diff` exit 1 from exit 2, so a missing directory is reported as
a broken comparison rather than as a finding.

**The database password reached argv and every traceback.**
`CalledProcessError` prints the whole argument list, so any failure, a stopped
container being the easy one, printed the private repository's password to the
terminal. Confirmed by running a failing command and reading the exception.
Credentials now go in on stdin as a defaults file, so they are absent from argv
and from `ps`, and a query failure raises with the server's message only.

**`load()` took any string into a path.** `load("../PROVENANCE")` read outside
the corpus directory, and `functools.cache` made every distinct string a
permanent entry. It failed later on a missing key, so it was harmless today and
would not be once B3 hands it a segment from a URL. Checked against the published
set now, one line, in the module where that set already lives.

**The published count came from the rows rather than the document.** They agree
today. They would stop agreeing the moment two source rows landed on one address,
and the number would overstate the file while the test pinned both sides to the
same constant.

**The uncommitted-changes guard covered the fixtures and not the importer**,
while the comment beside it claimed the commit described both. Widened to the
whole source tree.

**`.verify/` was in `.gitignore` and not in `.dockerignore`**, against that
file's own stated invariant, so an interrupted verification would sweep a second
copy of the corpus into the image.

**The export date criterion was ticked with no export date anywhere.** It cannot
coexist with byte identical reruns, the trade is real and deliberate, and it was
undocumented. Now in `DECISIONS.md`, with the epic and `CLAUDE.md` corrected to
say source commit date.

## What a second reviewer should look at first

`LIMITS.md`, and specifically whether it is honest enough. It is the document
that says what this repo cannot prove, and the temptation there is always to
soften. The paragraph about a stale database shipping without a sound is the one
I would most want argued with.

Then the rights table. Three assets, three legal bases, one of them resting on an
upstream dump that states no licence at all.
