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
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

DEST = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "catholic_bible"
    / "data"
    / "catechism"
    / "pages.json"
)

LAST = 2865
"""The Catechism runs to 2865 numbered paragraphs. The map covers all of them."""

ENGLISH = "https://www.vatican.va/archive/ENG0015/_INDEX.HTM"
PORTUGUESE = (
    "https://www.vatican.va/archive/cathechism_po/index_new/prima-pagina-cic_po.html"
)

HREF = re.compile(r"""(?i)href\s*=\s*["']?([^"'> ]+)""")

TAG = re.compile(r"(?s)<[^>]+>")

# Portuguese carries the range in the file name: `p1s2c1_198-421_po.html`.
RANGE_IN_NAME = re.compile(r"(\d+)-(\d+)_po\.html$")


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as answer:
        return answer.read().decode("latin-1")


def plain(html: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", html))


def english_pages() -> list[dict[str, object]]:
    """Every page of the IntraText build, with the paragraphs it holds.

    Detecting where a paragraph begins from the markup does not work. Most open a
    `<p>`, the "IN BRIEF" pages wrap the number in `<i>`, 2076 and 2077 share one
    `<p>` mid sentence and 2436 follows a bare `<br>`. Three shapes were found by
    three separate failures and there is no reason to believe there is not a
    fourth.

    So this reads the sequence instead. Numbers run 1 to 2865 in document order,
    the pages are in document order, and the walk looks for the next number it is
    owed. Two pages cannot claim the same paragraph and the order cannot invert,
    because neither is something this can express. What is left to check is
    whether anything went unfound, and that is what the coverage check is for.

    The whole page is read and none of it is kept. Only numbers and file names
    reach the output.
    """
    index = fetch(ENGLISH)
    names = list(dict.fromkeys(re.findall(r"(?i)(__P[0-9A-Z]+\.HTM)", index)))
    print(f"english: {len(names)} pages", file=sys.stderr)

    pages = []
    expected = 1
    for position, name in enumerate(names, start=1):
        text = plain(fetch(urljoin(ENGLISH, name)).split("Previous", 1)[-1])
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
            pages.append({"file": name, "first": held[0], "holds": held})
        if position % 50 == 0:
            reached = expected - 1
            print(f"  {position}/{len(names)}, at paragraph {reached}", file=sys.stderr)
        time.sleep(0.2)
    return pages


def portuguese_pages() -> list[dict[str, object]]:
    """The ranges are in the file names, so one request answers the whole edition."""
    index = fetch(PORTUGUESE)
    pages = {}
    for href in HREF.findall(index):
        name = href.rsplit("/", 1)[-1]
        found = RANGE_IN_NAME.search(name)
        if found:
            first, last = int(found[1]), int(found[2])
            pages[name] = {
                "file": name,
                "first": first,
                "holds": list(range(first, last + 1)),
            }

    # The prologue is the one page whose name carries a space rather than a
    # range, and dropping it would leave paragraphs 1 to 25 with no link.
    prologue = next(
        (href for href in HREF.findall(index) if "prologo" in href.lower()), None
    )
    if prologue is None:
        raise RuntimeError("the portuguese index no longer names the prologue page")
    pages[prologue] = {
        "file": prologue.rsplit("/", 1)[-1],
        "first": 1,
        "holds": list(range(1, 26)),
    }
    return sorted(pages.values(), key=lambda page: page["first"])


def refuse_a_broken_map(edition: str, pages: list[dict[str, object]]) -> None:
    """Every paragraph on exactly one page, in order, with nothing missing.

    A map that is nearly right sends a reader to the wrong page and looks
    healthy, so this is a failure rather than a warning.
    """
    firsts = [page["first"] for page in pages]
    if firsts != sorted(firsts) or len(set(firsts)) != len(firsts):
        raise RuntimeError(f"{edition}: pages are not in ascending paragraph order")

    seen: dict[int, str] = {}
    for page in pages:
        for number in page["holds"]:
            if number in seen:
                raise RuntimeError(
                    f"{edition}: paragraph {number} is on "
                    f"{seen[number]} and {page['file']}"
                )
            seen[number] = str(page["file"])

    missing = sorted(set(range(1, LAST + 1)) - set(seen))
    if missing:
        raise RuntimeError(
            f"{edition}: {len(missing)} paragraphs reach no page, first {missing[:8]}"
        )
    beyond = sorted(number for number in seen if number > LAST)
    if beyond:
        raise RuntimeError(f"{edition}: paragraphs past {LAST}: {beyond[:8]}")


def build() -> dict[str, object]:
    editions = {}
    for name, base, pages in (
        ("en", ENGLISH, english_pages()),
        ("pt", PORTUGUESE, portuguese_pages()),
    ):
        refuse_a_broken_map(name, pages)
        editions[name] = {
            "base": base.rsplit("/", 1)[0] + "/",
            # `holds` is dropped. It exists to prove the map covers everything
            # and the reader only ever needs where a page starts.
            "pages": [{"file": page["file"], "first": page["first"]} for page in pages],
        }
    return {"paragraphs": LAST, "editions": editions}


def render(record: dict[str, object]) -> str:
    return json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed map without fetching anything",
    )
    arguments = parser.parse_args()

    if arguments.check:
        if not DEST.is_file():
            print(f"missing: {DEST.name}", file=sys.stderr)
            return 1
        record = json.loads(DEST.read_text(encoding="utf-8"))
        for name, edition in record["editions"].items():
            pages = [
                {"file": page["file"], "first": page["first"], "holds": []}
                for page in edition["pages"]
            ]
            firsts = [page["first"] for page in pages]
            if firsts != sorted(firsts) or len(set(firsts)) != len(firsts):
                print(f"{name}: pages out of order", file=sys.stderr)
                return 1
            if firsts[0] != 1:
                print(
                    f"{name}: the map starts at {firsts[0]} rather than 1",
                    file=sys.stderr,
                )
                return 1
        print(f"ok: {DEST.name}")
        return 0

    record = build()
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(render(record), encoding="utf-8")
    for name, edition in record["editions"].items():
        count = len(edition["pages"])
        print(f"{name}: {count} pages, {LAST / count:.1f} paragraphs each")
    print(f"wrote {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
