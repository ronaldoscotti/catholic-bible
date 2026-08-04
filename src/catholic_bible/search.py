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
_WORD = re.compile(r"\w+", re.UNICODE)


def compile_query(raw: str) -> str | None:
    """The expression for `MATCH`, or `None` when nothing searchable is left.

    `None` is a refusal rather than an empty result, because an empty result
    says the corpus does not hold the word.
    """
    terms = [term for term in _terms(raw) if term]
    return " AND ".join(terms) if terms else None


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
