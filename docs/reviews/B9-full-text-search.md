# Code review, B9 lexical full-text search

*Stage 7. Run 2026-08-04, one author plus a review agent, before the pull
request opened. Second epic in a row in the right order.*

## The one that would have shipped

**A repeated term turned one `GET` into eight seconds of CPU.**

FTS5 intersects a document list once per term. Repeating one broad term never
shrinks the set being intersected, so the cost is linear in how many times a
reader writes the same word. Reproduced against the built corpus.

```
    1 x 'a*'  q=  2 chars    0.13 s
   20 x 'a*'  q= 59 chars    0.55 s
  100 x 'a*'  q=299 chars    2.67 s
  300 x 'a*'  q=899 chars    8.46 s
```

No key, no account, 899 characters, and the rate limiter counts it as one
request out of sixty. Sixty a minute is inside the published allowance, sync
handlers run in a bounded threadpool, and the reader asking for a verse waits
behind it. B8 exists to stop one careless script from becoming everybody else's
timeout, and B9 handed that script a much better weapon than a loop.

Deduplication, a cap of 32 distinct terms and a 500 character ceiling on `q`.
The same 300 term query is 0.11 seconds now and 5000 distinct terms are 0.004,
because a set that collapses after the first intersection was never the
expensive case. Distinct terms were not the problem and the fix does not pretend
they were.

**`LIMITS.md` was publishing a ceiling this branch had already broken.** The
table said the worst page is 79 ms while the branch shipped a query three orders
of magnitude past it. That is not a prose problem, it is a claim the code had not
earned, and the section now carries both the number and the correction.

## The one that was a false statement about the corpus

`source=haydok` answered `200` with `total: 0`. The route already refuses an
unknown book and an unknown version, and its own document declared a `404` it
never raised. An empty result there reads as Haydock having nothing to say, which
is not what happened.

The same held for an empty value. A client rendering `&language=${selected}` with
`selected` unset dropped the filter and got both languages back while its
interface claimed one. Both are `404` now, and the empty string is refused rather
than read as no filter.

This contradicted an argument the branch makes about itself, three hundred lines
above, when it refuses `!!!` because an empty result is an answer about the
corpus. The rule was written down and then not applied to the next two
parameters.

## Three tests that passed against broken code

Each one was mutated to confirm it now fails.

**The commentary source filter was untested.** `SOURCES` has one element, so
asserting the answer's sources are `{"haydock"}` passes whether the clause runs
or not. Deleting the filter left 741 green. It is pinned against a source nobody
has now, which is zero only if the clause reaches the query.

**Two count assertions were tautologies.** `COUNT(*)` on an external content FTS5
table reads through to the content table, so both sides of
`counted("verse_search") == counted("texts")` were the same rows. Demonstrated in
isolation: a never rebuilt index counts 2 and matches 0. They read the
`_docsize` shadow table now, which is the number of documents actually indexed
and is zero on an index nobody built.

**The commentary route had no paging test at all**, which left the ranked and
paginated criterion half proven.

## The test that was decoration, including the one I had already praised

The review said the commentary tie break was undefended. It was, and so was the
verse one, which this branch had shipped with a docstring claiming the opposite.

> Without a deterministic tie break, two pages of the same query can hand back
> the same verse twice and never show another. Nothing else in the suite would
> catch that, because each page on its own looks right.

Deleting either tie break leaves the suite green. SQLite sorts equal keys the
same way on every run against this file, so the instability the test describes
cannot be provoked here. The docstring was confident and wrong, and it was
written by the same author who then cited it as evidence.

The guarantee is asserted on the text of the query now, the same call already
made for the tokenizer argument and for the same reason. The behaviour that would
break cannot be provoked, and the thing that prevents it can be read. Both paging
tests stay, saying what they actually prove, which is that pages compose into the
answer they are pages of.

## What was checked and found sound

Reported rather than assumed, because a review that only lists faults says
nothing about what was examined.

**The dependency direction holds.** `search.py` imports `re` and nothing else.
`reader.py` imports `sqlite3` and one canon module. Nothing imports upward.

**The SQL assembly is not injectable and its parameters are not misordered.**
Both comprehensions in `_filtered` walk the same dictionary in insertion order
under the same predicate, so clause order and parameter order cannot diverge.
Every column name is a literal at the call site. The signature invites a future
caller to pass a supplied column name, which is worth remembering and is not a
bug today.

**The compiler survives hostile input.** Unbalanced quotes, a bare star, emoji,
CJK, combining marks, a hundred thousand character token and five thousand terms
all either compile and run or return `None`.

**The indexes cannot go stale.** `build_indexes` is the last write in `build()`
and the reading connection opens `mode=ro`. Nothing can write after the rebuild,
so no triggers are needed and none are missing.

**Nothing out of scope crept in.** No embeddings, no external service, no second
dependency. Commentary search was added at the spec gate with the author's
answer, and it is the only widening.

## What is still open

**A note spanning a book boundary would render a nonsense reference.** The hit
takes its book from the anchor and its end from the other end of the span. Zero
such notes exist today, verified, so it is written down rather than guarded.

**`version=all` ranks scores computed over different languages.** Documented in
`LIMITS.md` rather than solved, because solving it means either normalising
across corpora or refusing the parameter, and the author asked for the parameter.

## The finding that belongs to B8

QA, not review, and recorded in `docs/qa/B9-full-text-search.md`. The container
would not start because `default_store()` creates a directory inside
`RateLimiter.__init__` and nothing catches it. B8 fails open when the store
cannot be opened and has a test holding that. When the directory cannot be
created it takes the whole API down, on every request, including `/health`.
Reproduced away from the full disk that surfaced it. It is not fixed here.

## What this epic says about the method

**Both gates were met and the review still found the worst thing.** The spec was
written first and presented with four open questions, the answers came back, the
plan followed with three refusals in it, and the code came after. Two of those
three refusals paid, and the paging cap is honest because of one of them.

None of that found the repeated term query, because none of it was asking what a
hostile reader would type. The plan asked whether the measurements were real and
they were made real. It did not ask what the worst reachable query is, and that
is a different question that a second reader with no stake in the answer asked
instead.

That is the same shape as B8, where a mechanism nobody had written down was the
thing that broke a criterion. Here the mechanism was written down, measured and
published, and the measurement was of the wrong query.

## Third pass, on the open pull request

*2026-08-04. A review agent read the diff against the epic after the pull
request opened. Six findings, all six real, all six reproduced before anything
was changed.*

**The defence the second pass added had a door in it.** Deduplication and the
cap counted *terms*, and a quoted run is one term however many words it holds.
A 497 character phrase, inside the 500 character ceiling, compiled to a single
term and met neither defence. 269 ms against 49 ms for an ordinary query, and
`routes.py` was asserting the opposite in a comment beside the constant.

The cap counts words now and the phrase shares the budget with the bare words.
The same query is 28.7 ms, below an ordinary one.

That is two rounds in a row where the fix for an availability problem was
narrower than the problem. The first bounded repetition and left phrases open.
Naming the quantity being bounded, in the constant and in the comment, is the
part that generalises.

**An underscore ate whole queries silently.** `\w` keeps it and `unicode61` does
not, so `___` survived as a phrase that tokenizes to nothing. `Deus ___`
answered `200` with `total: 0` and hid the 6463 verses `Deus` reaches, with no
error and no hint. Exactly the claim about the corpus this module refuses to
make for `!!!`.

The fuzz test that exists to catch this had no underscore in its alphabet, so
2000 seeded inputs never reached it. It is in the alphabet now.

**The README published a response the API does not produce.** The search example
showed the rank two verse as the first hit, cut mid-sentence, with a full stop
`snippet()` cannot emit. `docs/qa/` in the same branch carried the real answer,
so the README was the only place holding the invented one, and the repo's own
rule is that no number in it goes unmeasured.

It is generated from a live response now and pinned by a test, which is the
mechanism that already guarded the `/health` line and had not been extended
here.

**Three smaller ones.** The commentary language scan ran on every request,
including the ones sending no language filter, scanning 41410 bodies to validate
nothing. The size table in `DECISIONS.md` said 86.1 MB against a build that
produces 88.0, because the figure came from a vacuumed scratch copy and the
build does not vacuum. And `test_both_orderings_are_total` read the module with
`inspect.getsource`, which fails on a reflowed line and passes on a string
surviving in a docstring; it reads the constants the queries are built from now.

**One process note taken rather than argued.** Commentary search was half the
surface of this work and answered to a criteria list that spoke only of
Scripture. There is a sixth criterion now. Written after the code, which is
weaker than written before it, and better than work that no criterion counts.
