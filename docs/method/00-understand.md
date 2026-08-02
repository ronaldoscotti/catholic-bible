# 00. Understand the problem

*Stage 0. Written 2026-08-01, before any research.*

## The problem, plainly

A developer who wants to put the Catholic Bible in an application cannot get
it. What is available is the 66-book Protestant canon in English, or a scraped
JSON file of unclear origin, or a dump with its own numbering that disagrees
with the dump the person next to them used.

Underneath that sits a harder problem than missing text. There is no stable way
to say "this verse" in a way that means the same thing tomorrow and in someone
else's system. Without that, a commentary, a cross-reference, a liturgical
reading and a highlight cannot all point at the same place.

## Who it is for

A developer building something Catholic. Most of them are hobbyists building on
weekends, and most of them speak Portuguese, because that is the community with
no option at all today.

A second reader exists and shapes the work without being the user. Someone
evaluating whether the author can build infrastructure other people depend on.
Serving the first reader well is what produces anything worth showing the
second one, so where the two pull apart, the developer wins.

## The insight that shapes the design

The corpus is not the asset. The corpus is a consequence.

The asset is a stable, portable verse identity for the Catholic canon plus a
total function that translates any other scheme into it. Everything hangs off
that, and it depends on nothing.

The Protestant world solved this with OSIS and the Copenhagen scheme. The
Catholic world has no equivalent, and that hole is the whole reason to build.

Two consequences follow. The identity has to be human readable rather than a
database integer, because a portable id needs to survive without the database
that produced it. And the mapping function has to be total, returning an orphan
with a reason rather than raising, because an address with no target is a fact
about the two schemes rather than an error in the caller.

## How I would build it by hand

Enumerate the 73 books with stable codes and canonical order. Build a
versification spine as a Vulgate-numbering superset that records how many
verses each chapter has, which makes every valid address enumerable. Write the
mapping function to pick, per book, between identity and applying a map,
choosing whichever produces fewer orphans against the spine. Import three
translations against the spine and report what fails to land. Serve it read-only
over HTTP and publish the same data as static files.

The commentary and the cross-references come after, and they are the proof that
the anchor works, because two independent layers attaching with no schema change
is the only real evidence that an anchor is an anchor.

## Success criteria

A developer who has never seen this gets Sirach 24:1 in Portuguese, correct,
with commentary on that verse, in under five minutes, without asking me
anything. That is the whole gate and someone other than me has to be able to
run it.

Two things beyond it. The orphan rate is published per book with its cause, and
a sibling project consumes the published artifact rather than the database,
which is the only cheap way to find out whether the contract holds.

## What stage 1 has to resolve

Whether this already exists. If there is a package with the Catholic canon in
Portuguese, the honest move is to use it rather than build a seventh one.

Whether the sources are actually free to redistribute, per translation, per
commentary, per cross-reference set, with the legal basis written down rather
than assumed.

Whether the reference parser problem is solved somewhere already, and whether
any existing solution handles the Portuguese ambiguity between John and Job.

What the current tooling actually is, since the last time I picked a Python
stack was not recently.
