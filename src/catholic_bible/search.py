"""What a reader typed, turned into an expression FTS5 will run.

Pure text. It reaches no database and no HTTP, so it is the layer that decides
what the query language of this API is, independently of what SQLite's happens
to be.

FTS5's `MATCH` takes an expression language with operators, column filters and
its own quoting rules. Handing a person's typing to it unchanged means a
parenthesis, an apostrophe or `Jo 3:16` comes back a 500. What is exposed here
instead is small enough to document in a table and closed enough that nothing a
reader types is a syntax error.
"""

from __future__ import annotations

import re

# A quoted run, or a run of anything that is not whitespace. Order matters, so
# an opening quote wins over the bare branch.
_TOKEN = re.compile(r'"([^"]*)"|(\S+)')

# What survives into the expression. Everything else is punctuation the reader
# did not mean as an operator, and dropping it is what makes `Deus (pai)` a
# search rather than a syntax error.
#
# `\w` minus the underscore, because `unicode61` does not tokenise one. Plain
# `\w` let `___` through as a phrase that matches nothing, so `Deus ___` came
# back empty and hid every verse `Deus` reaches.
_WORD = re.compile(r"[^\W_]+", re.UNICODE)

# FTS5 intersects a doclist once per token, and repeating a broad one never
# shrinks the set being intersected. 300 copies of `a*` cost 8.5 seconds of CPU
# on the built corpus, in an 899 character query the rate limiter counts as one
# request. Deduplication answers that, and the cap bounds what it cannot: a
# reader with 32 distinct words has a different problem from a search box.
#
# Words rather than terms. A quoted run is one term however many words it holds,
# so counting terms let a 497 character phrase past both defences at 269 ms
# against 49 ms for an ordinary query. The phrase and the bare words share one
# budget, or the quotes are a way of buying more words than the cap allows.
TOKEN_CAP = 32


def compile_query(raw: str) -> str | None:
    """The expression for `MATCH`, or `None` when nothing searchable is left.

    `None` is a refusal rather than an empty result, because an empty result
    says the corpus does not hold the word.
    """
    terms = []
    budget = TOKEN_CAP
    for term in dict.fromkeys(term for term in _terms(raw) if term):
        if budget <= 0:
            break
        terms.append(_truncated(term, budget))
        budget -= len(term.strip('"*').split())
    return " AND ".join(terms) if terms else None


def _truncated(term: str, budget: int) -> str:
    """The term, cut to what is left of the budget, keeping its prefix star."""
    words = term.strip('"*').split()
    if len(words) <= budget:
        return term
    return f'"{" ".join(words[:budget])}"' + ("*" if term.endswith("*") else "")


def _terms(raw: str) -> list[str]:
    terms = []
    for quoted, bare in _TOKEN.findall(raw):
        if quoted:
            terms.append(_phrase(quoted))
        elif bare:
            terms.append(_phrase(bare, prefix=bare.endswith("*")))
    return terms


def _phrase(source: str, prefix: bool = False) -> str:
    """One phrase, quoted once.

    Quoting each word separately would read to FTS5 as an implicit conjunction,
    which answers a different question and looks identical in the string.

    Nothing that reaches here can carry a quote, since only `\\w+` survives, so
    there is no escaping to get wrong.
    """
    words = _WORD.findall(source)
    if not words:
        return ""
    return f'"{" ".join(words)}"' + ("*" if prefix else "")
