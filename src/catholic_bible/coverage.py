"""What each translation reaches, and what it does not.

Two measurements, and the epic conflated them.

An **unfilled** address is a spine slot no version reached. It is measurable
here, because the spine and the published files are both in this repo.

An **orphan** is a source verse that mapped to no spine address. It is not
measurable here. The import dropped those before the corpus was written, so
nothing that reached this repo remembers them. Saying so is the honest report.
"""

from __future__ import annotations

import json

from catholic_bible.canon import DATA_DIR
from catholic_bible.canon.books import CANON
from catholic_bible.canon.spine import SPINE
from catholic_bible.corpus import VERSIONS, load

REPORT_PATH = DATA_DIR / "derived" / "coverage.json"


def build_report() -> dict[str, object]:
    provenance = json.loads(
        (DATA_DIR / "corpus" / "PROVENANCE.json").read_text(encoding="utf-8")
    )

    by_version: dict[str, object] = {}
    for code in VERSIONS:
        published = set(load(code).verses)
        missing: dict[str, int] = {}
        for book, chapter, verse in SPINE.addresses():
            if f"{book}.{chapter}.{verse}" not in published:
                missing[book] = missing.get(book, 0) + 1

        by_version[code] = {
            "published": len(published),
            "unfilled": sum(missing.values()),
            "unfilled_by_book": dict(sorted(missing.items())),
            "blank_upstream": provenance["files"][f"{code}.json"]["blank_upstream"],
        }

    return {
        "describes": {"source_commit": provenance["source"]["commit"]},
        "spine_addresses": sum(1 for _ in SPINE.addresses()),
        "books": len(CANON),
        "orphans": {
            "measurable_here": False,
            "why": (
                "An orphan is a source verse that reached no spine address. The "
                "import dropped those before the corpus was written, so nothing "
                "in this repo remembers them. Counting them needs the private "
                "source and the re-import job."
            ),
        },
        "versions": by_version,
    }


def render(report: dict[str, object]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
