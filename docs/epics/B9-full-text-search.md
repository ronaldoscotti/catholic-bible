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

- [ ] Full-text search over the corpus, scoped by translation and optionally by book
- [ ] Portuguese and Latin accents and diacritics are handled correctly
- [ ] Results carry the structured verse id and a snippet with the match highlighted
- [ ] Results are ranked and paginated
- [ ] The search index is built by the B2 generator and ships as a build artifact

## Constraints

SQLite FTS5 on local disk. No external search service and no per-query cost.

Lexical only. Anything involving embeddings belongs to the sibling repo.

## Verification

Test-driven, with a small fixed query set asserting expected hits, including accented and Latin queries.
