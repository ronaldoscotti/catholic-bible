# CLAUDE.md

A read-only API and a published dataset for the Catholic Bible. 73 books,
Portuguese, English and Latin, public domain throughout.

## Read this first

**`CONTEXT.local.md` is required reading before any work.** It is not in git. It
carries the source this repo is ported from, the epic-to-source map, and the
scope boundaries.

**If `CONTEXT.local.md` is missing, stop and ask for it.** Working without it
means reinventing logic that already exists, tested, elsewhere, and diverging
from it silently.

Then read `ROADMAP.md`, `docs/method/`, and the epic you are picking up.

## The method

Understand, gather context, brainstorm, spec, plan, implement, QA, review, PR.
The full pipeline and the live status are in [`docs/method/`](docs/method/).

Stages 3 and 4 are human review gates. Stop, present the artifact, wait for an
explicit approval message. Silence is not approval. Your own confidence is not
approval.

An epic is the unit of work. One epic, one issue, one branch, one pull request,
one pass through the pipeline. Small fixes take a shorter route because there is
less to review, never because review got relaxed.

Do not write implementation code without an approved plan on the full route.

## Scope discipline

Every slice has a reason to exist. It moves a metric, proves a concept, or
validates an idea. Not because a framework looks nice, not because the
architecture would be more correct.

I once handed the "how to build it" decision to three senior engineers and let
them gold-plate for six months. Nothing reached production, the money ran out,
and the whole engineering team went with it. The imperfect first version is
still running four years later. That does not happen here. If a stage is
growing scope, name it and cut it.

## Honesty rules

Never fabricate a stage. No test file for code that does not exist. No empty
directory implying work happened. No "reviewed" that was not.

Degrade rather than fake. When something is blocked, say so and fall back.

Claim only what the code has earned. No feature banner over an unfinished path.
No number in the README that has not been measured.

Status checklists advance when the artifact exists.

## Stack and conventions

Python and FastAPI. Read-only HTTP, typed request and response models with
Pydantic, OpenAPI published.

`openapi.json` is committed and CI regenerates it. A route that changed without
the document following fails the build, and so does a route carrying no summary,
no response model or no documented errors. FastAPI serves an undocumented route
without complaining, and that is how a published contract goes quietly out of
date while every test stays green.

SQLite on local disk, with FTS5 for lexical search. **No external database, and
this is a decision rather than a limitation.** The corpus is 73 books and it is
static, which makes a file the correct store. It gives sub-millisecond reads, no
network hop, no per-query cost, and it is what makes running this cost close to
nothing.

`uv` for dependencies and virtualenvs. `ruff` for lint and format. `pytest` for
tests. Type hints throughout, checked in CI.

`compose.yaml` is the contract. `docker compose up` reproduces the service on a
clean checkout with no credentials. The production box is one deployment target
and never the only runtime, because a repo that runs on one machine invalidates
every reproducibility claim in the sibling repo.

Caddy in front, for automatic certificates and a config short enough to read in
one screen.

Dependency direction runs one way. The canon and the spine know nothing about
storage. Storage knows nothing about HTTP. HTTP knows nothing about the
generator. A module that imports upward is a bug rather than a shortcut.

The dataset is exported and never authored. It comes out of the private
repository named in `CONTEXT.local.md`, already normalized and already tested
there, and it reaches this repo through a committed export script. No JSON is
edited by hand, and a value no script produced does not ship. Extraction,
scraping and orthography normalization stay in the private repo, because they
are solved there and a second implementation of them here would be a second set
of bugs.

Every published file carries a checksum and a provenance record naming its
source, its commit and its export date. CI recomputes the hashes on a clean
checkout, which catches corruption and not a deliberate edit, because the data
and the hash are committed together. Catching an edit needs the independent
source, so a second job re-exports where the private repo lives and diffs. Do not
describe the first job as proof that nothing was hand-edited. It is not, and
`docs/epics/B2-corpus-extraction.md` spells out which job proves what.

What this costs goes in `LIMITS.md` in B7 rather than being argued away, because
a reproducibility claim this repo cannot honour on a clean checkout is worse
than an honest limit.

Nothing enters without a case in the conformance corpus. Not even a new alias.

Comments are the exception. Always English, few, and short. A docblock on a
public function earns its place, so does a non-obvious decision or a known
limit, and so does an opaque regex. Never a section banner, never narration of
the next line, never commented-out code. Try renaming or extracting first,
because that usually removes the need. Rationale for a choice belongs in the
commit, the pull request, or a document.

*Defaults carried in from the wider Python world rather than paid for here yet.
Revisit against real code after B1 ships, and record anything that changes in
`DECISIONS.md`.* Test layout mirroring the source tree. Fixtures over mocks for
anything that touches the corpus, since the corpus is a file and a real one is
cheaper than a fake. Domain errors as return values where the caller can act on
them, exceptions only for genuine faults.

## Git

Everything that reaches git is English. Commits, pull requests, issues, code,
documentation.

Conventional commits, developer voice, imperative subject. `feat: add vulgate
psalm mapping`, not `feat: added` and not `feat: adiciona`.

A body is optional. A findable rationale is not. A subject may point at a spec,
a plan or an epic that already carries the why. What is not allowed is a subject
promising a rationale over an empty body.

Branch names as `<type>/<epic>-<slug>`. `feat/b1-versification-spine`,
`fix/b3-range-across-chapters`, `docs/b7-limits`.

Work lands through a pull request. Never a push to `main`.

One epic per pull request unless the epic is large enough to slice, and then one
slice per pull request with the epic issue linked from each. A pull request that
touches three unrelated things is three pull requests.

Pull requests link their issue and close it on merge. The description says what
changed, why, what is still broken, and what would come next with more time.

**No AI, Claude or Anthropic attribution anywhere.** Not in commit messages, not
in pull request titles or bodies, not in issues. Commits read as written by the
developer.

## Roadmap and epics

`ROADMAP.md` holds the shape and the MVP gate. `docs/epics/` holds one file per
epic, and that file is the source of truth for its GitHub issue. Title comes
from the H1, milestone and labels come from the metadata table.

`scripts/create-issues.sh` creates the issues from those files. Edit the file
and run it again rather than editing the issue in the browser, because an issue
edited in the browser drifts from the repo and the repo is what gets read.

An epic closes when its acceptance criteria are checked and its verification
ran. Not when the code merged.

Dependencies between epics are written in each body and are not enforced by
GitHub. Read them before picking one up.

## Releasing

The dataset is versioned and a published artifact URL keeps returning the same
bytes forever. Corrections ship as a new version rather than as an edit,
because a consumer pinning a version has to be able to trust the pin.

Package and dataset versions track each other, and the rule is documented in the
README.

Publishing happens from CI on a tag. Never from a laptop.

## Scope

Read-only. This repo serves Scripture, commentary and cross-references, and it
answers by reference. It does not write and it has no users.

Semantic search, embeddings, the agent and the MCP server belong to
`concordantia`, which consumes the artifact published here rather than this
repo's datastore.

## Prose

Human-facing prose goes through the `write-in-my-voice` skill. `README.md`,
`README.pt-BR.md`, `DECISIONS.md`, `LIMITS.md`, `CONTRIBUTING.md`, `ROADMAP.md`,
epic bodies and issue text.

**Zero em-dashes.** At most one colon per document, and only if it earns it.

Docstrings, OpenAPI descriptions, error messages and commit messages stay
conventional and do not go through the voice skill.

## Never

Do not add a text under copyright. The rights audit is in `LIMITS.md` and every
asset has a stated legal basis.

Do not ship the Portuguese Catena Aurea. Its provenance is open. The English
translation is public domain and can come later as its own epic with its own
label, so the two never get confused.

Do not ship the text of the Catechism. Paragraph numbers and links to
`vatican.va` are references, and B11 publishes those. A summary, a title, a
first line or an extracted snippet is the text wearing a hat and it is the same
refusal. If a reader can learn what a paragraph says without leaving this
dataset, the line was crossed.

Do not add accounts or authentication.

Do not reach into the sibling repo's datastore, and do not let it reach into
this one.
