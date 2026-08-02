# Roadmap

*Planning. Nothing here is built yet. Last updated 2026-08-01.*

A read-only API and a published dataset for the Catholic Bible. 73 books, Portuguese, English and Latin, public domain throughout.

## Why this exists

Install a Catholic Bible package today and you get 66 books in English. No Tobit, no Wisdom, no Sirach, no Maccabees. Look for Portuguese and you find Almeida, which is Protestant. Look for a reference parser and you find a good one, `bible-passage-reference-parser`, with the deuterocanonicals switched off by default and English aliases only.

There is real work in this space and I read it before starting. `pythonbible` parses and normalizes references in Python over Protestant versions. `python-scriptures` covers a handful of apocryphal books, though the list it supports is the Protestant one. `scrollmapper/bible_databases_deuterocanonical` publishes CPDV data. `holybible_api` serves nine languages over REST. A Matos Soares API already exists.

So the text isn't the gap. The gap is everything that makes the text addressable and correct.

Two Catholic editions disagree about how many verses 1 Chronicles 6 has, and neither one is wrong. The Miserere is Psalm 50 in the Vulgate and Psalm 51 nearly everywhere else, so an app built on the wrong scheme quietly contradicts the missal in the pew. Susanna and Bel have no counterpart in the standard versification scheme at all. In Portuguese, `Jo` is John and `Jó` is Job, and a parser that drops the accent sends the reader to the wrong book.

Nobody on the Catholic side has published a spine, a total mapping function, and an honest report of what fails to map. That report is the work.

## What done means for v1

One check, and someone other than me has to be able to run it.

> A developer who has never seen this repo gets Sirach 24:1 in Portuguese, correct, with Haydock's commentary on that verse, in under five minutes, without asking me anything. The API is live. Concordantia consumes the published artifact instead of the database.

If that holds, v1 shipped. If it doesn't, it didn't, however much code exists.

## Epics

| # | Epic | Exit criterion | How it's verified |
|---|---|---|---|
| B1 | Canon and spine | `map()` is total and never raises. Orphans come back as data with a reason. `orphans.json` published | TDD, plus a conformance corpus: Ps 50/51, Dan 13-14, the Greek additions to Esther, Sirach, 1 Chr 6, `Jo` against `Jó` |
| B2 | Corpus extraction | `make` regenerates the dataset byte for byte | Not TDD. Golden files, plus a CI job that regenerates and diffs. If output changes without the generator changing, the build breaks |
| B3 | Read API | Parity with the read endpoints this replaces | TDD on handlers, contract tests against the OpenAPI schema |
| B4 | Commentary and cross-references | Haydock in English and Portuguese, cross-references, all anchored on the same verse id | TDD on anchor resolution. Machine-translation provenance stated on the first screen of the README |
| B5 | Static artifacts and CDN | A one-line `fetch()` works from a blank HTML file | Copy it out of the README and run it |
| B6 | Production deploy | Live over HTTPS, health check, cost near zero | Smoke test in CI against the public URL |
| B7 | Decisions and limits | The five hard calls written down with the alternative that lost | Human read |

That's v1. Everything below is after.

| # | Epic | Exit criterion |
|---|---|---|
| B8 | Rate limiting | Per-IP limit, `429` with `Retry-After`. No keys, no accounts, until per-IP stops holding |
| B9 | Full-text search | FTS5 over the corpus, lexical only |
| B10 | Packages | `pip install` for the parser, `npm i` for the data |

## Not doing

The Catena Aurea in Portuguese stays out. The English translation is public domain and can come later; the Portuguese edition I have is a modern one with open provenance, and publishing it would be a copyright problem wearing a nice cover. The Catechism, canon law and magisterial documents stay out for the same reason, and there is a good product already serving that corpus.

No user accounts. An account is a login, and you need a login when someone has to come back and manage something. Nobody does yet.

No TypeScript library. The data ships as JSON and the parser ships in Python. A second implementation is a fine thing to want and a bad thing to build before anyone asks.

## How it gets built

Test-driven from the first commit, with the boundary stated instead of faked. Extraction gets golden files and a byte-identical regeneration check. The eval in the sibling repo gets a regression gate rather than a unit test. Writing a fake unit test around a data dump to keep a coverage number pretty is worse than admitting where the method doesn't reach.

The dataset is generated and the generator lives in the repo. No JSON maintained by hand.

Every slice has a reason to exist, and the reason is either a metric it moves or a claim it proves. I once let a team gold-plate for six months and it cost me the engineering team. That doesn't happen here.

## Rights

Every text in v1 is public domain or MIT, and the audit is in `LIMITS.md` with the legal basis per asset. Matos Soares died in 1957 with no successors, which puts him in the public domain under Brazilian law. The Vulgate and Douay-Rheims come from an MIT-licensed fixture. Haydock was printed between 1811 and 1814. Cross-references carry CC0 and CC BY, and the CC BY attribution is in the README where a person will actually see it.

The Portuguese Haydock is the one piece here that doesn't exist anywhere in the world. A complete Catholic commentary on all 73 books, in Portuguese. That alone would be reason enough to do this.
