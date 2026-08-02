#!/usr/bin/env python3
"""Writes the coverage report from the committed corpus and spine.

Derived rather than exported, like the orphan report. A test regenerates it and
diffs.
"""

import sys

from catholic_bible.coverage import REPORT_PATH, build_report, render


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render(report), encoding="utf-8")

    for code, section in report["versions"].items():  # type: ignore[attr-defined]
        print(
            f"  {code}  {section['published']} published,"
            f" {section['unfilled']} unfilled"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
