# Spec, B5 static artifacts and CDN

*Stage 3. Written 2026-08-03, against issue #7.*

**Gate.** This is a human review gate and it is open. Nothing was waived this
time. No implementation code exists and none gets written until this document
comes back approved. The B4 gates were waived in writing and `docs/method/`
records them as waived rather than met, which is the difference this run is
meant to close.

## What B5 delivers

A verse, fetched from a blank HTML file, with no install, no key, no account and
no server that can go down.

Everything this repository has built so far costs a `docker compose up` before it
returns a single word of Scripture. That is a fair price for an API and an unfair
one for someone putting a verse on a page. B5 makes the smallest possible use of
this project cost one line.

The second reason is written into the epic and is easy to miss. `concordantia`
builds its index from a published artifact rather than from this repository's
database. Until the artifact exists, the sibling repo either does not start or
starts coupled to the wrong thing.

## Measured before writing this

Every number is a command that ran on 2026-08-03 against what is committed at
`58e745d`, or a response from a live CDN. None is an estimate.

| Fact | Value | How |
|---|---|---|
| jsDelivr limit, single file | 20 MiB | their terms of use |
| jsDelivr limit, whole package | 150 MB | same |
| jsDelivr soft limit, files per repo | 10000 actively accessed | same |
| `haydock.json`, as committed | 20068650 bytes | `stat` |
| The same file, fetched from the CDN | `200`, 20068650 bytes | `curl` |
| Headroom before it stops being served | 902870 bytes, 4.3% | arithmetic |
| Tracked working tree today | 50.3 MB | `git ls-files` |
| Corpus split per book, three versions | 219 files, 16.8 MB | measured |
| Median corpus book | 48 KB | same |
| Largest corpus book | `PSA` in Douay-Rheims, 329 KB | same |
| Commentary split per book | 73 files, 19.1 MB | measured |
| Median commentary book | 149 KB | same |
| Largest commentary book | `PSA`, 2135 KB | same, and see below |
| CORS header from the CDN | `access-control-allow-origin: *` | response |
| Cache header at a pinned commit | `immutable`, `max-age=31536000` | response |
| Edge that answered from here | Curitiba | `x-served-by` |

*Corrected 2026-08-03, after the review. The two per book size rows were
measured by grouping the sources in memory, before the emitter existed, so they
miss the metadata block and the newlines every published file carries. Psalms in
the Haydock is 2187332 bytes on disk rather than the 2135 KB written here, which
is 1187 KB under the limit instead of 1189. Nothing that follows changes.
`LIMITS.md` carries the measured figure.*

The headroom row is the one that decides the shape of this epic. The commentary
is served today and is one commit from not being served, and no error would
appear here when it crosses. It would appear in somebody else's browser.

## What already exists, and the gap measured rather than described

Two projects have solved most of this and both are worth reading before adding a
third.

**HelloAO** publishes 1256 translations as static JSON on its own domain, at
`/api/{translation}/{book}/{chapter}.json`, with a parallel namespace for
commentaries at `/api/c/{commentary}/...` and a `sha256` per translation inside
the index. It is a better piece of engineering than most paid Bible APIs.

**wldeh/bible-api** publishes straight off jsDelivr at
`/gh/wldeh/bible-api/bibles/{version}/books/{book}/chapters/{chapter}.json`.

The gap, queried against HelloAO's own index on 2026-08-03.

| Question | Answer |
|---|---|
| Translations published | 1256 |
| Portuguese translations | 5 |
| Of those, Catholic | 0 |
| **Highest book count across all 1256** | **66** |
| Translations carrying a deuterocanonical book | **0** |

Twelve hundred and fifty six translations and not one of them has 73 books. The
`ROADMAP.md` says this in prose. This is the same claim with a number under it.

Two things get taken from the prior art and one gets deliberately refused.

The first thing taken is that a checksum belongs inside the index a consumer
already fetches, rather than only in a file they have to know to ask for. The
second is an entry point listing what exists, so a consumer discovers the URL
pattern instead of memorising it.

What gets refused is the pinning. **wldeh's URLs pin nothing.** They resolve to
the default branch, so the
bytes behind a URL change whenever that branch moves, and a consumer has no way
to pin. That is precisely what this epic's constraint forbids, and it is the
single most common way a static dataset betrays the people who adopted it.
HelloAO states no versioning rule either.

## The URL

```
https://cdn.jsdelivr.net/gh/ronaldoscotti/catholic-bible@v1.0.0/data/versions/matos-soares/books/SIR.json
```

The tag carries the version, so the path does not repeat it. Below the tag the
path is the HTTP API's own vocabulary, minus the parts a file cannot have.

| HTTP route | Artifact path |
|---|---|
| `/v1/versions` | `data/index.json` |
| `/v1/versions/{v}/books/{b}` | `data/versions/{v}/books/{b}.json` |
| `/v1/books/{b}/.../commentary` | `data/commentary/haydock/books/{b}.json` |
| no route | `data/canon.json`, `data/spine.json`, `data/orphans.json`, `data/manifest.json` |

One vocabulary for both surfaces. Someone who learns the API can guess the
artifact path and someone who learns the artifacts can guess the route.

`data/` at the repository root, distinct from `src/catholic_bible/data/`, which
stays what it is. The generated tree carries a header file saying it is
generated and CI regenerates and diffs it, so the two cannot quietly diverge. The
directory is not called `dist/`, because `.gitignore` already ignores that under
the Python build convention and a published artifact silently not being
committed is the worst available failure here.

## Granularity stops at the book

Per chapter would be smaller. Sirach 24 is 3 KB against 106 KB for the whole
book, and the epic asks for per book.

It also multiplies files. Three versions across 1189 chapters plus commentary is
roughly four thousand files against three hundred, against a soft limit of ten
thousand actively accessed. The gain is real and it is not this epic's, and a
median of 48 KB is already a page-weight nobody notices.

**Named and cut.** If someone asks for per chapter later it is a new epic with a
new number and nothing here blocks it, because the path shape leaves room.

## What ships

| Artifact | Files | Bytes |
|---|---|---|
| `data/index.json` | 1 | small |
| `data/manifest.json` | 1 | ~40 KB |
| `data/canon.json` | 1 | 16 KB |
| `data/spine.json` | 1 | 20 KB |
| `data/orphans.json`, `data/coverage.json` | 2 | 8 KB |
| `data/versions/{v}/books/{b}.json` | 219 | 16.8 MB |
| `data/commentary/haydock/books/{b}.json` | 73 | 19.1 MB |

Rights travel inside every file. This is the CC BY lesson from B4 applied one
layer out. An HTTP response can carry attribution in an envelope and a static
file has no envelope, so the file itself carries the licence, the basis and the
required notice. A file that gets copied into somebody's project keeps its
provenance or it loses it forever.

Nothing is hand placed. `scripts/build-artifacts.py` reads what is already
committed and writes the tree, deterministically, with no run timestamp, for the
same reason B2 has no export date.

**This diverges from the criterion's wording and the divergence is an
improvement.** The criterion says the artifacts are produced by the B2 export.
The B2 export needs the private source database. Generating downstream of the
committed corpus instead means a stranger on a clean checkout can regenerate
every published artifact and diff it, which is a property this repository does
not otherwise have anywhere. `LIMITS.md` currently says a stranger cannot rebuild
the dataset. After B5 that sentence needs a second half.

## Immutability, enforced rather than promised

A git tag can be moved. Prose saying it will not be is worth what the author's
memory is worth in three years.

A repository ruleset targeting `refs/tags/v*`, blocking deletion and update, is
the same mechanism that now protects `main`, and it was verified against `main`
by attempting a push and reading `GH013` back rather than by trusting the API.
The tag ruleset gets verified the same way, by trying to move a tag and being
refused.

That is what makes a published URL keep returning the same bytes. jsDelivr then
caches a pinned reference as `immutable` for a year, which was measured above.

## The manifest

`data/manifest.json` carries, for every published file, its `sha256` and its byte
count, plus the dataset version and the source provenance already recorded in
B2. A consumer verifies what they downloaded without trusting the transport.

The checksum here answers integrity and never authorship, for exactly the reason
B2 wrote down. The file and its hash are committed together, so anyone editing a
verse recomputes the hash and commits both. `LIMITS.md` already says this about
the corpus and the same sentence covers these.

## What it costs

The tracked tree goes from 50.3 MB to roughly 86 MB, and the artifacts are a
second copy of data already committed. That is 57% of jsDelivr's package limit
spent, and a clone gets slower for everyone including people who only want the
Python package.

The alternative was generating in CI at tag time and committing nothing, which
keeps the tree at 50 MB and creates a class of published file that nobody can
verify on a clean checkout. This repository already promises the opposite, so the
bytes get paid and `LIMITS.md` states the number.

## Verification

Two checks, and saying which proves what is the point.

**On every pull request**, `build-artifacts.py --check` regenerates the tree and
fails on any difference, the same gate `openapi.json` already has. It proves the
committed artifacts are what the script produces. It cannot touch the CDN,
because the tag it would fetch does not exist until the release.

**On a tag, and on a weekly schedule**, a job runs the exact `fetch()` line taken
out of `README.md` against the live CDN and asserts on the response. The line is
grepped from the README rather than copied into the workflow, which is the
pattern the quickstart job already uses, so a README that rots fails the build.

The weekly run matters more than the tag run. A CDN check that only fires at
release time proves the URL worked once.

## What is deliberately not built

No `README.pt-BR.md` update beyond the fetch line. No npm or PyPI package, which
is B10 and is blocked on the name anyway. No per chapter files. No `.min.json`
variants, because jsDelivr compresses on the wire and a second copy of everything
to save bytes the transport already saves is the kind of thing this repository
exists to not do. No search index.

## Open questions, which are the reason this document is a gate

**One. Do the cross-references ship as artifacts?**

The question I asked covered commentary and cross-references together and the
answer named commentary. I am not going to read that as a decision about the
other one.

It is 12.1 MB and 73 more files, taking the tree past 98 MB. It also carries the
CC BY obligation, which in a static file means the OpenBible notice has to sit
inside all 73 of them.

*My recommendation is to include them.* They landed in the same epic, the
deuterocanonical allusion set is the only free one in the world that reaches
Tobit and Wisdom, and a static dataset that ships the commentary but not the
cross-references is a strange half of B4 to publish.

**Two. `v1.0.0` says something the repository has not earned yet.**

You named the number and I am not relitigating it. What I need is which of the
two claims it makes.

`ROADMAP.md` defines v1 as a live API, deployed, with the five minute stranger
test passing. B6 and B7 have not run. Tagging `v1.0.0` today and calling it the
dataset contract is defensible. Tagging it and letting a reader infer that v1
shipped is a feature banner over an unfinished path, which `CLAUDE.md` forbids by
name.

*My recommendation is to tag `v1.0.0` as the dataset and artifact contract*, bump
`pyproject.toml` to match under the rule that the two track each other, and have
the README state in one sentence what the number governs, while `LIMITS.md` keeps
saying nothing is deployed. If you would rather the number wait for B6, then this
ships as `v0.1.0` and the immutability rule is identical either way.

**Three. Does `data/` at the root bother you?**

It is the prettiest URL and it sits next to `src/catholic_bible/data/`, which is a
different tree with a different job. `artifacts/` removes the ambiguity and makes
every published URL eleven characters longer. I lean to `data/` and I would
rather be told now than after 293 files carry the path.
