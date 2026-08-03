# QA, B5 static artifacts and CDN

*Stage 6. Run 2026-08-03 against `feat/b5-static-artifacts` at `806be05`.*

Reading the diff is not QA. What follows was run, and the output is pasted
rather than summarised.

## The acceptance criteria, walked

**1. JSON artifacts are produced per translation and per book by the B2 export.**
Met on the substance, and the wording is wrong in a way worth naming. 371 files,
219 of them a translation split per book. They are produced by
`scripts/build-artifacts.py` reading the committed corpus, not by the B2 export,
which needs the private source. `DECISIONS.md` carries why. The change makes the
artifacts reproducible on a clean checkout, which the export is not.

```
$ make artifacts
wrote 371 files, 48.2 MB, to /Users/scotti/work/personal/catholic-bible/data
```

**2. Artifacts are served over a CDN with no signup and no key.** Met.

```
$ curl -sS -o /dev/null -D - "https://cdn.jsdelivr.net/gh/ronaldoscotti/catholic-bible@806be05/data/versions/matos-soares/books/SIR.json"
HTTP/2 200
access-control-allow-origin: *
content-type: application/json; charset=utf-8
x-served-by: cache-fra-etou8220160-FRA, cache-cwb-sbct2070025-CWB
```

No token, no account, and the last edge is Curitiba.

**3. A one-line `fetch()` copied out of the README works from a blank HTML
file.** Met, and verified in a browser rather than in node alone.

The two lines were extracted from `README.md` with the same `grep` the CI job
uses, pasted into a file whose entire body is a `<pre>` and a module script, and
rendered in headless Chrome.

```
$ "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
    --virtual-time-budget=20000 --dump-dom http://localhost:8777/blank.html
<pre id="out">A sabedoria faz o seu próprio elogio, honra-se em Deus, gloria-se no meio do
seu povo; abre a sua boca na Assembleia do Altíssimo, glorifica-se diante dos
seus exércitos,</pre>
```

Served over `http://localhost` rather than `file://`, because the browser
extension was not connected and headless Chrome needed an origin. The CORS
header is `*`, which accepts both.

**4. Artifacts are versioned, and a published version is immutable.** Not met
yet, and it cannot be until the tag exists. The mechanism is built and measured.

**5. The canon, the spine and `orphans.json` ship as artifacts too.** Met.
`data/canon.json`, `data/spine.json`, `data/orphans.json`, and
`data/coverage.json` alongside them. A test asserts each is byte identical to
what it was copied from.

**6. A checksum manifest lets a consumer verify what it downloaded.** Met, and
verified against the CDN rather than against the local file.

```
370 files listed, versions/matos-soares/books/SIR.json verified
```

**7. The README documents the artifact URL pattern and the versioning rule.**
Met. `## The cheapest way in` carries the fetch line, the file inventory, and
`### The version in the URL is the whole contract`.

## The assumption I refused to carry, and it was wrong

The spec measured `immutable` and a one year cache on a **pinned commit** and
said a tag was assumed to behave the same. The plan called that out and required
a throwaway tag before anything was claimed.

It does not behave the same.

```
@806be05...   cache-control: public, max-age=31536000, s-maxage=31536000, immutable
@probe-0      cache-control: public, max-age=604800, s-maxage=43200
@v0.0.1       cache-control: public, max-age=31536000, s-maxage=31536000, immutable
no ref        cache-control: public, max-age=604800, s-maxage=43200
```

jsDelivr caches a **semver** tag permanently and treats anything else as a
mutable ref, on the same footing as the default branch. `probe-0` is a tag and
it got the mutable headers.

Had the spec's assumption gone in unchecked, a release tagged `release-1` or
`dataset-v1` would have been documented as immutable and would not have been.
`v1.0.0` parses as semver, so the shipped rule is correct, and it is correct on
purpose now instead of by luck.

Both probe tags were deleted afterwards. **`v0.0.1` is burned**, because
jsDelivr has cached that name against branch content forever and the name must
never be reused for a real release. That is what the probe cost.

## What I checked because it would fail quietly

**Whether the split loses a book.** The count of files is the check that looks
right and proves nothing. `test_the_split_loses_no_verse` rebuilds each
translation from its 73 files and compares the whole dictionary against the
monolith, and it asserts no two book files claim the same verse id.

**Whether a verse landed in the wrong book.** A separate test, because a
partition can be complete and still misfiled.

**Whether the Catena Aurea leaked.** `data/commentary/` is asserted to contain
exactly `haydock`.

**Whether the Ave Maria apparatus leaked.** Grepped in all 73 cross-reference
files, absent from all of them.

**Whether the pipeline markers came back.** `[[[` grepped across all 73
commentary files. Absent. This is the third gate on the B4 contamination and the
first one that reads the file a consumer downloads.

**Whether the gate can fail.** A gate nobody has watched fail is a gate nobody
has tested. `test_the_gate_fails_on_an_edited_verse` edits one word in a
generated tree and asserts the exact difference is reported.
`test_the_gate_fails_on_a_missing_file` deletes `TOB.json` and asserts the same.

**Whether the CDN serves the committed bytes.** `cmp` between
`git show 806be05:data/.../SIR.json` and what jsDelivr returned.

```
IDENTICO, 227872 bytes
```

## The suite

```
$ uv run pytest -q
561 passed in 20.33s

$ uv run ruff check . && uv run ruff format --check .
All checks passed!

$ uv run mypy
Success: no issues found in 60 source files
```

29 of those 561 are new and all of them read the published tree.

## What QA did not cover

Nobody fetched all 371 files from the CDN. One was fetched and compared byte for
byte, and the manifest was verified for that one. A file that failed to upload
would show as a 404 nobody has looked for.

The weekly job checks one file too. Checking 371 every week is 371 requests
against a service this project does not pay for, and the failure mode it would
catch is a partial publish, which the `--check` gate already catches before the
tag exists.

Nobody has measured what the artifacts cost a consumer on a slow connection. The
median book is 48 KB and Psalms in the Haydock is 2135 KB, and those are file
sizes rather than a measurement of anything.
