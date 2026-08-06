#!/usr/bin/env python3
"""Builds the map from a Catechism paragraph number to the page that holds it.

`vatican.va` publishes no per-paragraph address in either edition, so a link can
only ever be a page plus a number. This script establishes which page.

English is the edition worth having. Its 374 pages average 7.7 paragraphs, so a
link lands on the paragraph and its neighbours. Portuguese has 27 pages averaging
106, and the map for it comes out of the file names without fetching a page.

Runs on demand and never in CI. The output is committed like every other
published file here. Nothing it writes contains Catechism text.

Usage:
    scripts/build-catechism-pages.py
    scripts/build-catechism-pages.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from html import unescape as html_unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

DEST = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "catholic_bible"
    / "data"
    / "catechism"
)
PAGES = DEST / "pages.json"
PROVENANCE = DEST / "PROVENANCE.json"

LAST = 2865
"""The Catechism runs to 2865 numbered paragraphs. The map covers all of them."""

ENGLISH = "https://www.vatican.va/archive/ENG0015/_INDEX.HTM"
PORTUGUESE = (
    "https://www.vatican.va/archive/cathechism_po/index_new/prima-pagina-cic_po.html"
)

HREF = re.compile(r"""(?i)href\s*=\s*["']?([^"'> ]+)""")

TAG = re.compile(r"(?s)<[^>]+>")

# Portuguese carries the range in the file name: `p1s2c1_198-421_po.html`.
# Anchored to a separator, because the prologue href is `prologo%201-25_po.html`
# and an unanchored pattern reads `201-25` out of it and invents a page at 201.
RANGE_IN_NAME = re.compile(r"[_/](\d+)-(\d+)_po\.html$")


@dataclass(frozen=True, slots=True)
class Page:
    file: str
    first: int
    holds: list[int]


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as answer:
        body: bytes = answer.read()
    return body.decode("latin-1")


SUPERSCRIPT = re.compile(r"(?is)<sup\b.*?</sup>")

# The footnote block repeats every marker as a number followed by its source, so
# everything under it is a second stream of digits running the same direction as
# the paragraphs. It opens with a short left rule and its entries are anchored
# `name=$`. Both boundaries were checked on four pages and agree, and matching
# either one means a page that drops the rule still gets cut.
# A bare `<hr>` will not do. The navigation bar carries two above the text.
FOOTNOTES = re.compile(r"(?i)<hr\b[^>]*width\s*=\s*30%|<a\s+name=\$")


def body(html: str) -> str:
    """The reading text, with both other sources of digits removed.

    A footnote marker is a number in a `<sup>` and a footnote is a number at the
    foot of the page. Both look exactly like a paragraph number once the tags are
    gone, and both come earlier in the document than the paragraph they belong
    to, so a walk that sees them runs ahead of the text.

    Entities are decoded rather than left alone, because a numeric character
    reference is digits too. `&#8220;` is live on these pages and a three digit
    one would claim a paragraph.
    """
    text = html.split("Previous", 1)[-1]
    text = FOOTNOTES.split(text, maxsplit=1)[0]
    text = SUPERSCRIPT.sub(" ", text)
    return re.sub(r"\s+", " ", html_unescape(TAG.sub(" ", text)))


def english_pages() -> list[Page]:
    """Every page of the IntraText build, with the paragraphs it holds.

    Detecting where a paragraph begins from the markup does not work. Most open a
    `<p>`, the "IN BRIEF" pages wrap the number in `<i>`, 2076 and 2077 share one
    `<p>` mid sentence and 2436 follows a bare `<br>`. Three shapes were found by
    three separate failures and there is no reason to believe there is not a
    fourth.

    So this reads the sequence instead. Numbers run 1 to 2865 in document order,
    the pages are in document order, and the walk looks for the next number it is
    owed. Two pages cannot claim the same paragraph and the order cannot invert,
    because neither is something this can express.

    That leaves running ahead, which is what the first version did. It read the
    footnote markers and the footnote block as paragraphs, so the prologue page
    claimed 1 to 4 off three `<sup>` markers and a `1 Tim 2:3-4`, and every page
    to 17 was one page early. Coverage, ordering and uniqueness all passed,
    because a map that is uniformly early is contiguous. `--verify` is what
    catches that class and the coverage check is not.
    """
    index = fetch(ENGLISH)
    names = list(dict.fromkeys(re.findall(r"(?i)(__P[0-9A-Z]+\.HTM)", index)))
    print(f"english: {len(names)} pages", file=sys.stderr)

    pages: list[Page] = []
    expected = 1
    for position, name in enumerate(names, start=1):
        text = body(fetch(urljoin(ENGLISH, name)))
        held = []
        cursor = 0
        while expected <= LAST:
            found = re.compile(rf"(?<!\d){expected}(?!\d)").search(text, cursor)
            if found is None:
                break
            held.append(expected)
            cursor = found.end()
            expected += 1
        if held:
            pages.append(Page(file=name, first=held[0], holds=held))
        if position % 50 == 0:
            reached = expected - 1
            print(f"  {position}/{len(names)}, at paragraph {reached}", file=sys.stderr)
        time.sleep(0.2)
    return pages


def portuguese_pages() -> list[Page]:
    """The ranges are in the file names, so one request answers the whole edition."""
    index = fetch(PORTUGUESE)
    pages: dict[str, Page] = {}
    for href in HREF.findall(index):
        name = href.rsplit("/", 1)[-1]
        found = RANGE_IN_NAME.search(name)
        if found:
            first, last = int(found[1]), int(found[2])
            pages[name] = Page(
                file=name, first=first, holds=list(range(first, last + 1))
            )

    # The prologue is the one page whose name carries a space rather than a
    # range, and dropping it would leave paragraphs 1 to 25 with no link.
    prologue = next(
        (href for href in HREF.findall(index) if "prologo" in href.lower()), None
    )
    if prologue is None:
        raise RuntimeError("the portuguese index no longer names the prologue page")
    pages[prologue] = Page(
        file=prologue.rsplit("/", 1)[-1], first=1, holds=list(range(1, 26))
    )
    return sorted(pages.values(), key=lambda page: page.first)


def refuse_a_broken_map(edition: str, pages: list[Page]) -> None:
    """Every paragraph on exactly one page, in order, with nothing missing.

    This catches a gap, a duplicate and an inversion. **It does not catch a map
    that is uniformly wrong**, because a walk that runs one page ahead of the
    text still covers 1 to 2865 exactly once and still ascends. That is not a
    hypothetical. It shipped, and `--verify` is the check that sees it.
    """
    firsts = [page.first for page in pages]
    if firsts != sorted(firsts) or len(set(firsts)) != len(firsts):
        raise RuntimeError(f"{edition}: pages are not in ascending paragraph order")

    seen: dict[int, str] = {}
    for page in pages:
        for number in page.holds:
            if number in seen:
                raise RuntimeError(
                    f"{edition}: paragraph {number} is on "
                    f"{seen[number]} and {page.file}"
                )
            seen[number] = page.file

    missing = sorted(set(range(1, LAST + 1)) - set(seen))
    if missing:
        raise RuntimeError(
            f"{edition}: {len(missing)} paragraphs reach no page, first {missing[:8]}"
        )
    beyond = sorted(number for number in seen if number > LAST)
    if beyond:
        raise RuntimeError(f"{edition}: paragraphs past {LAST}: {beyond[:8]}")


def build() -> dict[str, Any]:
    editions: dict[str, Any] = {}
    for name, base, pages in (
        ("en", ENGLISH, english_pages()),
        ("pt", PORTUGUESE, portuguese_pages()),
    ):
        refuse_a_broken_map(name, pages)
        editions[name] = {
            "base": base.rsplit("/", 1)[0] + "/",
            # `holds` is dropped. It exists to prove the map covers everything
            # and the reader only ever needs where a page starts.
            "pages": [{"file": page.file, "first": page.first} for page in pages],
        }
    return {"paragraphs": LAST, "editions": editions}


def render(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def record_provenance(digest: str, record: dict[str, Any]) -> None:
    """Merges into the file the export also writes, rather than clobbering it.

    Two scripts fill this directory and they run at different times. Whichever
    runs second must not erase what the first recorded.
    """
    held: dict[str, Any] = {}
    if PROVENANCE.is_file():
        held = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    held.setdefault("files", {})["pages.json"] = {
        "sha256": digest,
        "paragraphs": record["paragraphs"],
        "pages": {
            name: len(edition["pages"])
            for name, edition in sorted(record["editions"].items())
        },
    }
    held["pages_source"] = {
        "en": ENGLISH,
        "pt": PORTUGUESE,
        "carries_no_text": True,
    }
    PROVENANCE.write_text(render(held), encoding="utf-8")


def page_for(edition: dict[str, Any], number: int) -> str:
    chosen = edition["pages"][0]
    for page in edition["pages"]:
        if int(page["first"]) > number:
            break
        chosen = page
    return str(edition["base"]) + str(chosen["file"]).replace(" ", "%20")


def verify(record: dict[str, Any], sample: int) -> int:
    """Opens the page the map names and looks for the paragraph on it.

    The independent check. `refuse_a_broken_map` reasons about the map and this
    reasons about the site, which is the only thing that can catch a map that is
    self consistent and wrong. The sample is spread across the whole range rather
    than random, because the defect this exists for was concentrated at the front
    of the book where a random draw of fifty would probably have missed it.
    """
    step = max(1, LAST // sample)
    wanted = sorted({1, 2, 3, 4, 17, 624, LAST, *range(1, LAST + 1, step)})
    failures = 0
    for name, edition in sorted(record["editions"].items()):
        for number in wanted:
            url = page_for(edition, number)
            text = body(fetch(url))
            if re.search(rf"(?<!\d){number}(?!\d)", text) is None:
                print(f"{name} paragraph {number} is not on {url}", file=sys.stderr)
                failures += 1
            time.sleep(0.2)
        print(f"{name}: {len(wanted)} sampled, {failures} wrong so far")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed map without fetching anything",
    )
    parser.add_argument(
        "--verify",
        type=int,
        default=0,
        metavar="N",
        help="open the page the committed map names for N sampled paragraphs",
    )
    arguments = parser.parse_args()

    if arguments.verify:
        committed: dict[str, Any] = json.loads(PAGES.read_text(encoding="utf-8"))
        failures = verify(committed, arguments.verify)
        print(
            "every sampled paragraph was on the page the map names"
            if not failures
            else f"{failures} sampled paragraphs were not"
        )
        return 1 if failures else 0

    if arguments.check:
        if not PAGES.is_file():
            print(f"missing: {PAGES.name}", file=sys.stderr)
            return 1
        record: dict[str, Any] = json.loads(PAGES.read_text(encoding="utf-8"))
        # A missing record fails. Treating it as a pass means the only integrity
        # guard on the map disappears the moment something overwrites the file,
        # and `--check` goes on printing ok.
        if not PROVENANCE.is_file():
            print("missing: PROVENANCE.json", file=sys.stderr)
            return 1
        held = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        recorded = held.get("files", {}).get("pages.json", {}).get("sha256")
        if not recorded:
            print("PROVENANCE.json records no checksum for pages.json", file=sys.stderr)
            return 1
        if recorded != hashlib.sha256(PAGES.read_bytes()).hexdigest():
            print("pages.json does not match its checksum", file=sys.stderr)
            return 1
        for name, edition in record["editions"].items():
            firsts = [int(page["first"]) for page in edition["pages"]]
            if not firsts:
                print(f"{name}: the map names no pages", file=sys.stderr)
                return 1
            if firsts != sorted(firsts) or len(set(firsts)) != len(firsts):
                print(f"{name}: pages out of order", file=sys.stderr)
                return 1
            if firsts[0] != 1:
                print(
                    f"{name}: the map starts at {firsts[0]} rather than 1",
                    file=sys.stderr,
                )
                return 1
        print(f"ok: {PAGES.name}")
        return 0

    record = build()
    DEST.mkdir(parents=True, exist_ok=True)
    payload = render(record).encode("utf-8")
    PAGES.write_bytes(payload)
    record_provenance(hashlib.sha256(payload).hexdigest(), record)
    for name, edition in record["editions"].items():
        count = len(edition["pages"])
        print(f"{name}: {count} pages, {LAST / count:.1f} paragraphs each")
    print(f"wrote {PAGES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
