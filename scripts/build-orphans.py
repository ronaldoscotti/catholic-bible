#!/usr/bin/env python3
"""Writes the orphan report from the committed data.

Derived rather than exported, so it carries no provenance record of its own. It
names the spine checksum it describes instead, and a test regenerates it and
diffs.
"""

import sys

from catholic_bible.canon.orphans import REPORT_PATH, build_report, render


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render(report), encoding="utf-8")

    for name, section in report["schemes"].items():  # type: ignore[attr-defined]
        if section.get("reportable") is False:
            print(f"  {name}: not reportable yet")
            continue
        print(
            f"  {name}: {section['orphans']} orphans of {section['addresses_examined']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
