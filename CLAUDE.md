# CLAUDE.md

A read-only API and a published dataset for the Catholic Bible. 73 books,
Portuguese, English and Latin, public domain throughout.

## Read this first

**`CONTEXT.local.md` is required reading before any work.** It is not in git.
It carries the source material this repo is ported from, the epic-to-source
map, and the scope boundaries.

**If `CONTEXT.local.md` is missing, stop and ask for it. Do not proceed.**
Working without it means reinventing logic that already exists, tested, in
another repo, and silently diverging from it.

Then read `ROADMAP.md` and the epic under `docs/epics/`.

## Workflow

Non-trivial work follows the pipeline. Understand, gather context, brainstorm,
spec, plan, implement, QA, review, PR. The spec and the plan are both human
review gates. Silence is not approval.

Small fixes take the short route. Less pipeline because there is less to
review, never because review got relaxed.

## Rules

Everything that reaches git is written in English. Commits, pull requests,
issues, code, documentation.

Prose written for humans goes through the `write-in-my-voice` skill.
`README.md`, `README.pt-BR.md`, `DECISIONS.md`, `LIMITS.md`, `CONTRIBUTING.md`,
`ROADMAP.md` and issue bodies. Zero em-dashes anywhere.

Docstrings, OpenAPI descriptions, error messages and commit messages stay
conventional. Commits follow Conventional Commits.

Comments are the exception rather than the habit. A docblock on a public
function earns its place. A comment narrating the next line does not.

Test-driven from the first commit. Where the method does not reach, say so in
the epic and name the real verification instead of writing a decorative unit
test around it.

The dataset is generated and the generator lives here. No JSON maintained by
hand. `make` regenerates everything, byte for byte identical, and CI fails when
output changes without the generator changing.

Nothing enters without a case in the conformance corpus. Not even a new alias.

Claim only what the code has earned. No feature banner over an unfinished path,
no "tested" that has not run.

## Scope

Read-only. This repo serves Scripture, commentary and cross-references, and it
answers by reference. It does not write, and it has no users.

Semantic search, embeddings, the agent and the MCP server belong to
`concordantia`, which consumes the artifact published here rather than this
repo's datastore.

## Never

Do not add texts under copyright. The rights audit lives in `LIMITS.md` and
every asset in it has a legal basis stated.

Do not ship the Portuguese Catena Aurea. The English translation is public
domain and can come later as its own epic. The Portuguese edition has open
provenance and stays out permanently.

Do not add AI attribution to commits, pull requests or issues.
