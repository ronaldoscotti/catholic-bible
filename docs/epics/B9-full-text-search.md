# [B9] Lexical full-text search

| | |
|---|---|
| Milestone | v1.1 |
| Labels | `epic` `area/api` `milestone-spec` |
| Depends on | B2, B3 |

*Milestone spec. Expanded against the code that exists when it is reached.*

**As** a developer building a reading app
**I need** to find verses by word or phrase
**So that** my users can search Scripture without me standing up a search service

## Context

This is the one thing a static file cannot do, which is exactly why it belongs in the API rather than in the artifact.

Lexical search lives here. Semantic search lives in `concordantia`, and the split is deliberate. This repo owns the data layer and the exact-match path. The sibling repo owns the comparison between approaches and the number that comes out of it.

## Problem

Finding "cordeiro de Deus" in the text requires downloading the whole corpus and writing a search yourself.

## Acceptance criteria

- [x] Full-text search over the corpus, scoped by translation and optionally by book
- [x] Portuguese and Latin accents and diacritics are handled correctly
- [x] Results carry the structured verse id and a snippet with the match highlighted
- [x] Results are ranked and paginated
- [x] The search index is built by the committed build step from the published corpus, and no hand-built index ships

**The last criterion had its wording changed rather than being ticked against
text the rest of the repo denies.** It said the index comes out of the B2 export
and ships as a build artifact. The B2 export needs the private source and writes
JSON. The index is built by `scripts/build-db.py` from files that are already
committed, on a clean checkout, by anyone with a clone.

B5 hit the same sentence and rewrote it for the same reason. An index shipped out
of the export would be one more file a stranger has to take on trust, and the
whole point of splitting the build downstream is that they do not have to.

**Commentary was added to the scope at the spec gate.** The epic says the corpus
and the author asked for the notes as well, so there are two routes rather than
one. `DECISIONS.md` carries why they are not one merged ranked list.

## Constraints

SQLite FTS5 on local disk. No external search service and no per-query cost.

Lexical only. Anything involving embeddings belongs to the sibling repo.

## Verification

Test-driven, with a small fixed query set asserting expected hits, including accented and Latin queries.
