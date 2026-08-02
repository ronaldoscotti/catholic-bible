# 01. Context

*Stage 1. Researched 2026-08-01.*

## Prior art

Searched before writing a line, because building the obvious clone is the worst
possible outcome.

| Project | What it does | Overlap |
|---|---|---|
| [`pythonbible`](https://github.com/avendesora/pythonbible) | validates, parses and normalizes references in Python, retrieves text | Direct on the parser. Protestant versions |
| [`python-scriptures`](http://www.davisd.com/python-scriptures/) | regex reference extraction, some apocryphal books | The book list is the Protestant apocrypha. Tobit, Judith, Baruch and the Maccabees are absent while I Esdras and the Prayer of Manasseh are present |
| [`scrollmapper/bible_databases_deuterocanonical`](https://get.bible/bible-data-sets/) | CPDV in USFM and JSON | Deuterocanonical data exists, in English |
| `matosSoaresBibliaApi` | Matos Soares over HTTP | Direct. The flagship translation already has an API |
| [`holybible_api`](https://github.com/gpalleschi/holybible_api) | REST, nine languages including Portuguese | Direct on multilingual read |
| [Catholic Bible on RapidAPI](https://rapidapi.com/matheusfrota/api/catholic-bible) | hosted API | Direct, closed |
| [`awesome-catholic`](https://github.com/servusdei2018/awesome-catholic) | curated list | The index of everything above |

### What this means

A Catholic Bible API exists. Matos Soares over HTTP exists. Deuterocanonical
data exists. The naive version of this project is done, more than once, and
building it again would produce nothing.

### What none of them do

Nobody publishes a versification spine. Nobody publishes a mapping function
between schemes. Nobody reports what fails to map. Every project picks a scheme
and proceeds, which is why two of them disagree about the Miserere and neither
says so.

Nobody has the Haydock commentary in Portuguese, because it does not exist
anywhere in the world.

The Portuguese reference ambiguity between `Jo` and `Jó` is unhandled in every
English-first parser, and it is the single most common lookup in a Portuguese
Catholic app.

So the gap is not the text. The gap is everything that makes the text
addressable, plus a report of where that fails.

## Existing implementation

The business logic in this repo already exists, tested and in production, in a
private codebase. This is a port rather than an invention.

That changes the shape of the work. The canon, the spine, both reference
parsers, all three scheme maps, the import pipeline and the commentary readers
have working implementations with test suites, and those test suites are the
conformance specification, already written.

The file-by-file map lives in `CONTEXT.local.md`, which is not in git because it
points at a private repository. Anyone working here without that file should
stop and ask for it rather than reinvent what is already solved.

Where idiomatic Python disagrees with the original design, Python wins and the
divergence goes in `DECISIONS.md`. Copying framework conventions across a
language boundary means copying the wrong accent.

## Rights

Audited per asset before any extraction. The full table goes in `LIMITS.md`.

Free to redistribute. Matos Soares in Portuguese, public domain under Brazilian
law article 45 since he died in 1957 with no successors. The Clementine Vulgate
and Douay-Rheims from an MIT-licensed fixture. Haydock in English, printed 1811
to 1814. Haydock in Portuguese, translated by the author of this repo from a
public-domain work. Cross-references from the original Douay apparatus under
CC0 and from OpenBible under CC BY, which requires attribution.

Not free, and permanently out. The Ave Maria text and its headings, under
copyright. Cross-references derived from that apparatus. The Catena Aurea in
Portuguese, whose provenance is open. The Catechism, canon law and magisterial
documents, held by the Holy See. Maps, partly under Access Foundation copyright.

The canon itself, the versification numbers and the mapping algorithm are not
subject to copyright. Numbers are facts and the algorithm is original work.

## Architecture direction

Read-only. This repo serves data and answers by reference. It has no users, no
writes and no sessions, which removes an entire class of problem before it
starts.

The corpus is static and small enough to be a file. That makes SQLite on local
disk the right store rather than a compromise, and it is what lets this run for
close to nothing with sub-millisecond reads.

The dataset is generated and the generator is committed. Regeneration is
byte-identical and CI diffs it, which is what proves the corpus was not adjusted
by hand.

Two publication channels. Static files on a CDN cover the developer who wants a
chapter, at zero cost with no server to defend. The API covers the caller who
holds a reference rather than a file path.

The sibling repo `concordantia` consumes the published artifact and the public
API, never this repo's datastore. That boundary is the only thing that makes the
dataset falsifiably reusable.

## Open questions carried into brainstorming

Which package names are free on PyPI and npm. Whether the CDN artifact layout
should be per book or per translation. What the orphan rate actually is, which
only extraction can answer.
