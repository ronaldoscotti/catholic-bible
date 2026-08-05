# [B10] Packages on PyPI and npm

| | |
|---|---|
| Milestone | v1.1 |
| Labels | `epic` `area/distribution` `milestone-spec` |
| Depends on | B1, B2, B5 |

*Milestone spec. Expanded against the code that exists when it is reached.*

**As** a developer starting a project
**I need** to install this the way I install everything else
**So that** using it costs one command instead of a decision

## Context

`npm i` beats `git clone` by an order of magnitude for adoption, and a download count is the only public, falsifiable evidence that other people's work got easier because this exists. That evidence is worth more than any README paragraph.

Two packages with two different jobs. The Python package carries the reference parser and the canon logic, which is code. The npm package carries data only, since the parser in JavaScript would be a second implementation and nobody has asked for one.

**The first half of that paragraph is what this epic proposed and not what it shipped.** The author chose one Python distribution carrying everything, corpus included, so `pip install` leaves a running API rather than a parser alone. The wheel is 13 MB against the 84 KB this framing implies. `DECISIONS.md` carries the reasoning and what it cost under *One Python distribution carrying everything, against the epic's two*. The paragraph stays as written because the issue body is the record of what was proposed, and this note is the record of what happened to it.

The npm half held exactly as written.

## Problem

Adoption dies at the install step. A developer who has to clone a repo and run a generator to get a Bible will paste a JSON file from somewhere else instead, which is how the current situation came about.

## Acceptance criteria

- [x] A Python package publishes the reference parser, canon data and the spine, installable with `pip install`
- [ ] An npm package publishes the JSON dataset, installable with `npm i`, with no runtime dependency
- [x] Package versions track dataset versions, and the rule is documented
- [ ] Both packages are published from CI on tag, never from a laptop
- [ ] The README quickstart uses the package rather than a clone
- [x] The Python package passes the B1 conformance corpus in CI

**Three of six. The three left empty all say the same thing, which is that
nothing has been published.** They stay empty through the whole pull request
rather than being ticked on the mechanism that would eventually prove them. B5
did that once, ticked its fetch criterion on a browser run against a rewritten
URL, and the acceptance walk caught it.

**One.** The wheel installs into a clean virtualenv and answers. `parse_reference('Eclo 24,1')` returns `SIR 24,1`, `Jo` resolves to `JHN` and `Jó` to `JOB`. The CI `package` job asserts the import comes from `site-packages` before anything else runs, because a source tree on the path would answer for the repository.

**Two.** `package.json` is generated and `npm pack --dry-run` produces 375 files at 48.2 MB unpacked. Nobody can run `npm i the-catholic-bible`, which returns `404` today, so the criterion says installable and this is not.

**Three.** `pyproject.toml` is the only place the number is written. `build-artifacts.py` puts it in `package.json`, `index.json` and `manifest.json`, and FastAPI puts it in `openapi.json` by a separate path. One test asserts all five, which is what stops the generator vouching for the two files it does not own. The rule is in the README under *One number for both packages and the dataset*.

**Four.** `release.yml` exists and has never run. A workflow that reads correctly is not a workflow that publishes.

**Five.** The README leads with `pip install` and the container moved to Development. The command answers `404`, so the quickstart names a package rather than using one, and the README says so in the paragraph above it. That paragraph comes down with the tag and this box goes up with it.

**Six.** 85 conformance cases pass against the installed copy in CI, with the source tree off the path and the files copied out of the checkout so no sibling `conftest.py` can reach them.

## Measured on the branch

| Fact | Value |
|---|---|
| Cold database build, CI runner | 6 s |
| Cold database build, author's laptop | 10 s |
| Warm rebuild inside a checkout | 5 s |
| npm tarball | 13.2 MB packed, 48.2 MB unpacked, 375 files |
| Python wheel | 13 MB, 49.4 MB unpacked |
| Conformance cases against `site-packages` | 85 |

The first two rows are why the first-boot message promises no number. They differ by 40% and the README would have published whichever one was measured first.

## Constraints

Package names get checked and claimed before this starts.

No JavaScript parser. Data only on npm until someone asks, in public, with a use case.

## Verification

An install test in CI does a clean install of each published package and runs the documented quickstart against it.
