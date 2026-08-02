# Decisions

The hard calls, each with the option that lost and what the choice costs. A
decision with no loser is a preference, and a preference does not need a
document.

Written when the call is made rather than reconstructed afterwards.

## The dataset is exported rather than regenerated

Decided 2026-08-02, while scoping B1.

The corpus, the canon and the versification spine already exist in the private
repository this work is extracted from. They were built there, normalized there
and tested there. This repo takes the finished data through a committed export
script and publishes it. It does not scrape, it does not read upstream dumps,
and it does not reimplement the 1956 orthography allow-list.

**What lost.** Porting the generator. Every source dump would come here, the
build chain would be rewritten in Python, and `make` would rebuild the dataset
from raw sources on any machine. That is the stronger claim and it is the one I
wrote into the roadmap first. It also puts a second implementation of extraction
and normalization next to the working one, and two implementations of the same
rules drift apart eventually. The person who finds out is a reader holding two
verse numbers that disagree.

**What it costs.** A stranger who clones this repo cannot rebuild the dataset.
The export needs the private repo and they do not have it. The reproducibility
gate stops being regeneration, and claiming otherwise would put a line in the
README that the first curious reader disproves in ten minutes.

**What replaces it.** Two checks that prove two different things, and the
difference matters enough to write down.

Every published file ships with a checksum and a provenance record naming its
source, the commit it came from, and the date it was exported. CI recomputes the
hashes on every push, on a clean checkout, with no access to the private source.
That catches a truncated file, a bad merge or a partial commit. It does not catch
a deliberate edit, because the data and the hash are both committed here and
whoever edits a verse can recompute the hash. A self-referential checksum is an
integrity check and never an authorship check.

Catching a hand edit needs an independent source, which is what the regeneration
diff had. So the second check re-runs the export where the private repo lives, at
the commit the provenance record names, and diffs it against what is committed
here. That one has teeth and it cannot run on a fork.

A first draft of this entry said the checksum proved nobody edited the corpus by
hand. It does not, a review caught it, and the sentence is corrected rather than
quietly deleted.

The cost goes in `LIMITS.md` when that file lands in B7. A stranger can verify
integrity and cannot verify authorship, and that is the honest shape of it.

## Inverting the scheme table prefers the origin the spine can hold

Decided 2026-08-02, while implementing B1.

The Copenhagen table runs Vulgate to `org`, and reading `org` needs the other
direction, so the table gets inverted. Inverting is not free. The table merges
verses and it reaches the same target from more than one origin, which leaves
157 `org` addresses with two or more declared Vulgate origins. Something has to
choose.

This repo keeps the first declared origin, unless that one has no slot on the
spine and a later one does. Then the later one wins.

**What lost.** Keeping whichever origin the file listed last, which is what
falls out of building the index without thinking about it and what the source
implementation does. It is arbitrary in a way that shows: the Song of the Three
is declared from both `DAN` and `DAG`, only `DAN` exists on the spine, and last
wins picks `DAG`. Sixty five addresses then orphan while the table itself says
where they go. Across the whole table the rule recovers 105 of the 157.

**What it costs.** A divergence from the working implementation, which is the
thing this port is most careful to avoid. It is deliberate, it is one rule in
one constructor, and a conformance case pins it so the two cannot drift quietly.

The 29 addresses whose origins all have slots keep the first declared one, and
that is a convention rather than a finding. Where the Vulgate splits one `org`
verse in two, the first is the one an apparatus means.

## The mapping layer decides what is an orphan

Decided 2026-08-02, while implementing B1.

The source implementation keeps its scheme maps pure and detects orphans in the
importer, so one place decides and the maps stay simple. That is the right call
there because an importer exists.

Here it does not. The importer is B2 and B1 has to publish `orphans.json`, so
detection moves into the mapping layer and the scheme maps stay pure below it.

**What lost.** Waiting for B2 and keeping the shape identical to the source. It
would leave B1 unable to meet its own acceptance criteria, which is a high price
for a structural match.

## An unresolvable reference is a value, not an exception

Decided 2026-08-02, while implementing B1.

The source parser throws on an unknown book or a malformed reference. Here both
come back as values carrying the reason.

**What lost.** The exception, which is idiomatic in the framework the original
lives in and which makes the happy path read cleanly.

The rule in `CLAUDE.md` is that a domain error the caller can act on is a return
value and an exception is for a genuine fault. A reader typing a book name that
does not exist is not a fault. It is the most ordinary thing that happens to a
reference parser, and B3 has to turn it into a structured HTTP error rather than
a stack trace.
