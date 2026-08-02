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

## Problem

Adoption dies at the install step. A developer who has to clone a repo and run a generator to get a Bible will paste a JSON file from somewhere else instead, which is how the current situation came about.

## Acceptance criteria

- [ ] A Python package publishes the reference parser, canon data and the spine, installable with `pip install`
- [ ] An npm package publishes the JSON dataset, installable with `npm i`, with no runtime dependency
- [ ] Package versions track dataset versions, and the rule is documented
- [ ] Both packages are published from CI on tag, never from a laptop
- [ ] The README quickstart uses the package rather than a clone
- [ ] The Python package passes the B1 conformance corpus in CI

## Constraints

Package names get checked and claimed before this starts.

No JavaScript parser. Data only on npm until someone asks, in public, with a use case.

## Verification

An install test in CI does a clean install of each published package and runs the documented quickstart against it.
