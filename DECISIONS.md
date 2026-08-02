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
where they go.

**What it costs.** A divergence from the working implementation, which is the
thing this port is most careful to avoid. It is deliberate, it is one rule in
one constructor, and a conformance case pins it so the two cannot drift quietly.

**The numbers, measured rather than estimated.** The inverse index only fires on
books the spine numbers in Vulgate, so the population is smaller than the raw
table suggests. 135 `org` addresses arrive ambiguous. In 103 of them exactly one
declared origin has a slot on the spine and the rule recovers it. In 23 no
origin has a slot and the address orphans either way. In 9 more than one origin
has a slot.

A first draft of this entry counted 157 and 105, which were measured across the
whole table without the mode gate that decides whether the index is consulted at
all. The corrected figures are above.

**Those 9 stay ambiguous and get recorded.** Six are the same merge shape, where
the Vulgate splits one `org` verse in two and the first is what an apparatus
means. Three are chapter boundaries between textual traditions, and `BEL 1:1` is
the clearest of them: Daniel 13 ends at 64 in most editions and at 65 in the one
that carries the transition into Bel, so the table declares that verse and
Daniel 14:1 as the same address. Both are legitimate and neither is a mistake.

The tempting move is a tie-break that reads nicely, nearest verse number or
whichever keeps the sequence contiguous, which would pick Daniel 14:1 and feel
better. That is choosing a textual tradition with a heuristic and calling it
arithmetic. B1 exists to stop exactly that, so the rule stays blunt and all nine
go into the conformance corpus naming both candidates.

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

## Reading a spine address back into a scheme verifies itself

Decided 2026-08-02, while implementing B1.

The epic asks for the mapping in both directions. The forward direction reads a
scheme address onto the spine and the reverse reads a spine address back out.
They are not symmetric, because the remap table is not a bijection.

Run backwards naively, the table produces addresses that look right and are not.
The spine holds `PSA.115.1`, reading it back gives `org` 115:1, and `org` 115:1
is a different psalm coming from `PSA 113:9`. Sixty two addresses behaved that
way across the three schemes.

So the reverse direction computes its candidate and then maps it forward again,
and it only returns the candidate if it lands where it started. Anything else is
an orphan.

**What lost.** Returning the candidate and documenting the caveat. It would have
been less code and a smaller diff, and it would have handed a consumer a wrong
verse address with nothing to tell them. A wrong answer someone trusts is worse
than an absent one, and this is the epic whose whole point is that distinction.

**What it costs.** Twenty one addresses have no Vulgate reading and forty one
have no `org` reading. Douay has none, because it touches only Joel and Malachi
and both are clean. Those numbers are pinned in a test rather than tolerated.

## Provenance records the source commit date and never the run date

Decided 2026-08-02, in B1, and it stayed in B2.

Every published file names when its source was committed. None of them names
when the export ran.

**What lost.** The export date, which is what `CLAUDE.md` and the B2 epic both
ask for by name, and which is what a reader expects to find in a provenance
record.

It cannot coexist with the other requirement in the same list. Running the
export twice at one source commit has to produce byte identical output, because
that is what makes the comparison against a fresh export mean anything. A run
timestamp makes every rerun differ, and then the only check in this repo that
catches a hand edit reports a difference every single time.

Between a date that says when a command ran and a date that says which version
of the source these bytes came from, the second is the one a consumer can act
on. The first answers a question nobody asks.

**What it costs.** Two documents ask for something this repo does not provide,
and both are now corrected rather than left to imply it. A reader who wants to
know when the export ran has the git history of this repo, which is a better
answer anyway because it is signed and ordered.

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
