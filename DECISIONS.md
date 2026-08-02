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

**What replaces it.** Integrity. Every published file ships with a checksum and
a provenance record naming its source, the commit it came from, and the date it
was exported. CI verifies both on every push. A byte that moved without its
provenance moving breaks the build, which is the property the regeneration diff
existed to give. Nothing here is edited by hand and the check is what proves it.

The cost goes in `LIMITS.md` when that file lands in B7.
