# [B1] Canon and versification spine

| | |
|---|---|
| Milestone | v1.0 MVP |
| Labels | `epic` `area/data` `blocks-everything` |
| Depends on | nothing |
| Blocks | B2, B3, B4, B5, and C1 in `concordantia` |

**As** a developer building anything on Catholic Scripture
**I need** a stable, portable identity for every verse in the 73-book canon, plus a way to translate any other numbering scheme into it
**So that** a commentary, a cross-reference, a liturgical reading and a user highlight can all hang off the same anchor and still mean the same thing next year

## Context

Every Catholic developer who builds anything redoes this work alone, badly, and incompatibly with the person next to them. The reason is that the world's versification standard, the Copenhagen `org` scheme, is anchored on the Masoretic text. It has no slot for Susanna, no slot for Bel, and it numbers the Psalter the way Protestant Bibles do.

The dumps that exist are dumps. `Dancrf/biblia-db`, `mborders/vulgata` and `fidalgobr/bibliaAveMariaJSON` each carry their own numbering, their own book names, their own 1956 orthography and their own source errors. Nobody aligned them, normalized them, anchored them on a common spine, and measured what came out the other side.

Prior art check done before writing this. `pythonbible` parses references in Python over Protestant versions. `python-scriptures` covers a few apocryphal books, and the list it supports is the Protestant one, so Tobit, Judith, Baruch and the Maccabees are absent while I Esdras and the Prayer of Manasseh are present. Neither handles the Vulgate Psalter. Neither speaks Portuguese.

This is the primitive everything else depends on, and nothing else depends on anything.

## Source

This is a port, not an invention. The canon, the spine, both reference parsers and all three scheme maps already exist and pass tests in a private repo. `CONTEXT.local.md` maps every file to this epic. Read the existing implementation before writing a line of Python, and port the existing test cases rather than inventing new ones. Where idiomatic Python disagrees with the original design, Python wins and the divergence goes in `DECISIONS.md`.

## Problem

There is no stable verse identity for the Catholic canon. Without one, a commentary entry, a cross-reference and a liturgical reading cannot be anchored to the same address, and two systems built by two people disagree about which verse is which. Anyone who wants to build on top has to invent the anchor first, which is why every Catholic Bible project starts from zero and ends incompatible.

## Acceptance criteria

- [ ] All 73 books are represented with USX codes, canonical order, testament, group, and a deuterocanonical flag
- [ ] Book name aliases resolve in Portuguese, English and Latin, with no collisions
- [ ] `Jo 3,16` resolves to John and `Jó 3,16` resolves to Job
- [ ] The spine records how many verses each chapter has, so every valid address is enumerable
- [ ] A mapping function translates between the spine and at least the `org`, Vulgate and Douay schemes, in both directions
- [ ] The mapping function is total. It always returns. An address with no target comes back as an orphan carrying a reason, never as a thrown exception
- [ ] The mapping never guesses. Where there is no target it returns an orphan rather than the nearest plausible verse
- [ ] `orphans.json` is generated and published, broken down by book and by scheme, with the reason for each
- [ ] A conformance corpus passes, covering at minimum: Psalm 51 in `org` resolving to Psalm 50 on the spine, Daniel 13 and 14, the Greek additions to Esther, Sirach numbering, the Joel and Malachi chapter breaks, Tobit's two textual traditions, and 1 Chronicles 6 where the correct answer is an expected orphan
- [ ] Every conformance case records its input, expected output, provenance, and a note on why it is hard

## Constraints

The public identity is a structured, human-readable id such as `PSA.50.3`, not an opaque integer. A database id is an artifact of the order a seed ran in, and freezing one into a public contract is a mistake that cannot be undone. A derived integer for interval arithmetic ships alongside it and can be recomputed without breaking anyone.

The spine is a Vulgate-numbering superset. It takes the maximum and never reduces. The New Testament stays untouched, because modern NT numbering is what the liturgy, the catechism and every cross-reference apparatus already use.

A published id never changes meaning. The spine is append-only. That is an API contract and it gets stated out loud, because nobody hangs five layers off an anchor that might become something else in v2.

## Out of scope

No text. B1 is addresses only. No commentary, no cross-references, no HTTP.

## Verification

Test-driven throughout. The conformance corpus is the real gate and it runs in CI. Nothing enters this repo without a case in it, including a new alias.
