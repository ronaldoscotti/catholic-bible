# Session prompt

Paste one of these at the start of a Claude Code session. Replace `[N]` with the
GitHub issue number and `[B]` with the epic id, which are not the same thing.
The epic id is what names the file.

## The issue to epic map

Read this before picking one up. The first run of `scripts/sync-issues.sh`
walked the epic files in shell glob order, where `B10` sorts before `B2`, so the
issues were opened in that order and everything from B2 down carries a number
one higher than it looks. Issue numbers cannot be renumbered. The script now
sorts by version so the next epic does not join them.

| Issue | Epic | | Issue | Epic |
|---|---|---|---|---|
| #1 | B0 project scaffolding | | #7 | B5 static artifacts and CDN |
| #2 | B1 canon and versification spine | | #8 | B6 production deploy |
| #3 | **B10** packages | | #9 | B7 decisions and limits |
| #4 | **B2** corpus export | | #10 | B8 rate limiting |
| #5 | B3 read API | | #11 | B9 full-text search |
| #6 | B4 commentary and cross-references | | #18 | B11 catechism cross-references |

These do not restate the rules. `CLAUDE.md` loads automatically and carries the
conventions, the pipeline and the boundaries. A session prompt that repeats them
drifts from them within a month, and then two documents disagree about how the
repo works.

## Starting an epic

```
Working on issue #[N] in this repo.

Read in order:
1. CLAUDE.md
2. CONTEXT.local.md, required. If it is missing, stop and ask for it.
3. docs/method/README.md, the pipeline and where this repo actually stands
4. The issue body, which is docs/epics/[B]-*.md

Route: check the epic. Scaffolding and isolated changes take the fast lane,
which is understand, context, TDD, QA, review, PR, with no spec document and no
plan document. Anything touching the canon, the spine, the data model or a
public seam takes the full pipeline, and stages 3 and 4 are my review gates.

Branch off main as <type>/<epic>-<slug>. Land through a pull request. Never push
to main.

Before writing any code, tell me what you understood about the epic and what you
intend to do. Wait for my answer.
```

## Continuing an epic

```
Continuing issue #[N]. Read CONTEXT.local.md, the issue body, and the branch
diff so far. Tell me which acceptance criteria are already met and which are
not, then pick up from there.
```

## Finishing an epic

```
I think issue #[N] is done. Before opening the pull request:

1. Run the full suite and the linter. Paste the real output, not a summary.
2. Walk the acceptance criteria one by one and say which are met, with the
   evidence for each. Anything unmet stays unchecked.
3. Run the verification named in the epic. If it is not a test, do the thing it
   actually says and record the result.
4. If the epic touched the HTTP surface, regenerate openapi.json and commit it.
   Say which routes changed and confirm every route still carries a summary, a
   response model and its error responses.
5. Check that no rule in CLAUDE.md was broken, including em-dashes in prose and
   any JSON that got edited by hand rather than generated.
6. Update the status block in docs/method/README.md only for stages whose
   artifact now exists.
7. Open the pull request. The description says what changed, why, what is still
   broken, and what you would do next with more time.

Do not mark a criterion met because the code looks right. Met means verified.
```

## Reviewing before merge

```
Review the pull request for issue #[N] against its epic. I want the acceptance
criteria checked against the diff, the conventions in CLAUDE.md checked, and
anything the epic put out of scope that crept in anyway.
```
