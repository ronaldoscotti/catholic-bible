# [B5] Static artifacts and CDN

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/data` `area/distribution` |
| Depends on | B2 |
| Blocks | C1 in `concordantia` |

**As** a developer putting a verse on a page
**I need** to fetch the data with one line and no install step
**So that** the smallest possible use of this project costs nothing and depends on nothing that can go down

## Context

A repo is where code lives. It is not how something gets adopted. Static JSON served from a CDN is already a read API, free, fast, with no server, no uptime to defend, no abuse surface and no bill. For most of the people this serves, it is the whole product.

It also decouples `concordantia` from this repo's availability. The sibling repo builds its index from a published artifact, so a deploy here cannot break an eval there.

## Problem

Someone building a small page or prototyping in a single HTML file has no way to get Catholic Scripture without installing a package manager, running a generator, or calling an API that might be down. The cheapest possible path to a verse does not exist.

## Acceptance criteria

- [x] JSON artifacts are produced per translation and per book, by a committed generator reading what B2 published
- [x] Artifacts are served over a CDN with no signup and no key
- [ ] A one-line `fetch()` copied out of the README works from a blank HTML file
- [x] Artifacts are versioned, and a published version is immutable
- [x] The canon, the spine and `orphans.json` ship as artifacts too, not only the text
- [x] A checksum manifest lets a consumer verify what it downloaded
- [x] The README documents the artifact URL pattern and the versioning rule

Three of those need saying out loud rather than being ticked or left in silence.

**The first criterion had its wording changed rather than being ticked against
text it contradicts.** It originally said the artifacts come out of the B2
export. They come out of a generator reading what B2 already committed, and a
ticked box whose sentence the rest of the document denies is the drift that
keeping the epic file as the source of truth exists to prevent.

The export needs the private source, so an artifact produced that way would be
one more file a stranger has to take on trust. Splitting downstream means anyone
with a clone regenerates all 371 files and diffs them. `DECISIONS.md` carries the
trade and `LIMITS.md` carries what it costs.

**The last two boxes were ticked after the release, not before it.** Neither
could be proven while `v1.0.0` did not exist, and both were left empty through
the pull request rather than ticked on the mechanism.

`v1.0.0` was pushed at `02e2f49`, the merge commit on `main`. Then the
documented line was run with nothing edited.

```
$ node --input-type=module -e "$(grep -A1 '^const book = await' README.md)"
A sabedoria faz o seu próprio elogio, honra-se em Deus, gloria-se no meio do seu
povo; abre a sua boca na Assembleia do Altíssimo, glorifica-se diante dos seus
exércitos,
```

The same two lines in a blank HTML file, rendered in headless Chrome, put the
verse on the page. The bytes served match the tag byte for byte, 227872 of them,
and the header is the one the semver probe predicted.

```
cache-control: public, max-age=31536000, s-maxage=31536000, immutable
access-control-allow-origin: *
```

Immutability is ticked because the ruleset was seen refusing, not because it
exists.

```
$ git push --force origin v1.0.0
remote: - Cannot update this protected ref.
remote: - Cannot force-push to this tag
$ git push origin :refs/tags/v1.0.0
remote: - Cannot delete this tag
```

**The fetch box came off once, in the middle.** It had been marked met on a
browser run with the tag rewritten to a commit hash, which is a different line
from the one the README publishes, and the acceptance walk caught it. The
correction is recorded in `docs/qa/B5-static-artifacts.md` rather than tidied
away, and the box is ticked now on the published URL.

## Verification, run

`.github/workflows/cdn.yml` fired on the tag push and went green, asserting all
three things against the live CDN.

```
documented https://cdn.jsdelivr.net/gh/ronaldoscotti/catholic-bible@v1.0.0/data/versions/matos-soares/books/SIR.json
identical, 227872 bytes
A sabedoria faz o seu próprio elogio, honra-se em Deus, ...
370 files listed, versions/matos-soares/books/SIR.json verified
```

It runs again every Monday, which is the run that matters, because a check that
fires only at release time proves the URL worked once.

**Unticked again on 2026-08-03, and it is the release process rather than the
artifact.** The 1.0.1 release moved the README to `@v1.0.1` before that tag
exists, so the documented line returns 404 while `@v1.0.0` still returns 200.
Running it is the whole verification and it fails, so the box comes down.

The order cannot be reversed. `cdn.yml` reads the tag out of the README, so a
README left on `@v1.0.0` while `v1.0.1` is pushed would send the workflow to
verify the previous release and pass without testing anything. The window
between merging and tagging is the cost, and it closes when the tag lands and
`cdn.yml` goes green against `@v1.0.1`. Re-tick then, and not before.

## Constraints

Artifacts are generated by the B2 pipeline. Nothing is hand-placed.

A published artifact URL keeps returning the same bytes forever. Corrections ship as a new version.

## Out of scope

The npm and PyPI packages are B10. This epic is files over HTTP.

## Verification

An end-to-end check runs the exact `fetch()` line from the README against the live CDN and asserts on the result, so the documented path is the tested path.
