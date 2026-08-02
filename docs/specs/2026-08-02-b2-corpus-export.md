# Spec, B2 corpus export and integrity

*Stage 3. Written 2026-08-02, against issue #4.*

**Gate.** This is a human review gate. Nothing here has been approved and no
code has been written.

## What B2 delivers

Text. Three translations, complete, addressed on the B1 spine, each published
with a checksum and a stated origin.

Matos Soares in Portuguese, the Douay-Rheims in English, the Clementine Vulgate
in Latin. Nothing else.

## Where the data actually is, which is not where the epic assumed

The finished corpus is not in a file. It is in the MySQL database of the private
repository, in `bible_verses` and `bible_verse_texts`, after the import command
ran the per-source normalizers and the 1956 orthography allow-list.

The `.json.gz` files next to the canon are the raw sources, not the product. B1
exported from files and was simple for that reason. B2 exports from a running
database, which is a different mechanism and a real operational precondition:
the private repository's containers have to be up for the export to run at all.

Reached through the container rather than a local client, so no database
credentials or ports enter this repo:

```
docker exec meu-feed-catolico-api-mysql-1 mysql -u… -p… meu_feed_catolico_api
```

Douay-Rheims and the Clementine Vulgate come out of the same upstream fixture,
`vulgata-source.json.gz`, separated only by which text field the normalizer
reads, `text` against `textLatin`. That is why English costs almost nothing here.

## Measured before writing this

Everything below is a query against the seeded database, not an estimate.

| Version | Verses | Spine slots unfilled | Headings | Footnotes |
|---|---|---|---|---|
| Clementine Vulgate | 35776 | 69 | 0 | 0 |
| Douay-Rheims | 35776 | 69 | 0 | 0 |
| Matos Soares | 35563 | 282 | 2305 | 0 |

The spine holds 35845 addresses, from B1.

**Footnotes and verse labels are empty in every version.** Both columns exist and
neither carries a row. So the question of whether to publish them answers itself:
there is nothing to publish. If footnotes arrive upstream later they are an epic
of their own.

## What the export refuses to carry

**The Ave Maria, entirely.** It is in the same database, 35450 verses, and it is
under copyright. It never appears in a query.

**The Ave Maria headings sitting on Matos Soares.** This is the one that would
ship by accident. The import applies `ave-maria-headings.json` to Matos Soares at
the end, and those 2305 pericope headings land in the `heading` column of the
same row as the public domain verse text.

`CLAUDE.md` names them: no Ave Maria text or headings. So the export selects the
text column and never the heading column, and that is asserted by a test that
fails if a heading reaches the published file, rather than by a `SELECT` list
that happens to be right today.

## The published shape

One file per translation. Verses keyed by the B1 published identity.

```json
{
  "version": {"code": "matos-soares", "language": "pt-BR", "year": 1956,
              "license": "public-domain", "basis": "…", "source_url": "…"},
  "verses": {"PSA.50.3": {"order": 14231, "text": "…"}}
}
```

Both identities travel, and that is deliberate rather than redundant.

Everything downstream anchors on the verse, and it does not all anchor the same
way. Cross-references hang off `verse_id` and `target_verse_id`. Commentary
entries span a range using `start_order` and `end_order`, which is the dense
integer. So B4 needs interval arithmetic and B5 needs a key a `fetch()` consumer
can read. Publishing the string alone would make every consumer recompute the
order, and B1 already proved the two are derivable from each other, so carrying
both costs one integer per verse and removes a whole class of downstream work.

Per book splitting is B5, where the consumer is a browser. Here the consumer is
code in this repo.

## Two jobs, and they prove different things

**The checksum job** runs on a clean checkout with no access to the private
source. It recomputes every hash and fails on a mismatch. It catches a truncated
file, a bad merge, a partial commit. It cannot catch a deliberate edit, because
the data and its hash are committed together, so whoever edits a verse recomputes
both. A self-referential hash is an integrity check and never an authorship check.

**The export job** runs where the private source lives, re-exports at the source
commit named in the provenance record, and diffs. That one has teeth and it
cannot run on a fork.

B1 already built the smaller half of this. The export refuses to run against a
source whose files have uncommitted changes, so provenance cannot name a commit
that does not hold the bytes shipped. The same guard extends to the database
export, and it is harder there, because a database has no working tree. The plan
has to answer that rather than inherit an answer.

## What the epic got wrong

**"The Vulgate demonstrates the spine with zero orphans."** The import command
declares a tolerance of 30 orphans for the Vulgate, 30 for Douay and 40 for Matos
Soares, and 69 spine addresses have no Vulgate verse at all. Whatever the true
orphan count is, the epic states a number nobody measured and calls it a live
proof. `LIMITS.md` publishes the per book rate that comes out, and the epic gets
corrected the way B1's 1 Chronicles 6 prediction did.

Coverage and orphans are two different measurements and the epic conflates them.
An orphan is a source verse that failed to map. An unfilled spine slot is an
address no source reached. Both belong in `LIMITS.md` and they need separate
names.

## Out of scope

No commentary, no cross-references. Those are B4.

No extraction, no scraping, no orthography work. Those stay in the private repo.

No per book files and no CDN. That is B5.

## Noticed while looking, for B4 rather than here

Two rights problems that are cheaper to know now.

The cross-reference table carries 673 rows sourced `na27`. Nestle-Aland 27 is
held by the Deutsche Bibelgesellschaft. It needs an audit before B4 ships and it
may not be publishable at all.

It also carries 879 rows sourced `ave-maria`, which are derived from the
copyrighted apparatus that `CLAUDE.md` already rules out. The 2362 Douay rows and
the 204601 OpenBible rows are the ones that port.

The commentary side is cleaner. Haydock has 20705 entries and every one carries a
Portuguese translation. The Catena has 12724 and stays out.

## Open questions carried into the plan

How the export pins a database to a commit. Files have a git hash and a table
does not, so the provenance record needs something else: the source commit plus
the import command's own inputs, or a hash of the exported payload itself, and
the second one proves less than it looks.

Whether the three files ship compressed. The Vulgate and Douay are around 4 MB of
text each and the repo carries them forever.
