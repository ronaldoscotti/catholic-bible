#!/usr/bin/env python3
"""Splits the published dataset into the static artifacts served from the CDN.

Reads only what is already committed under `src/catholic_bible/data/`, so a
stranger on a clean checkout regenerates every published artifact and diffs it.
The B2 export cannot be run that way, because it needs the private source.

Deterministic. Sorted keys, no run timestamp, for the same reason `PROVENANCE`
records the source commit date and never the export date. Two runs at the same
commit produce identical bytes or the `--check` gate flaps and stops meaning
anything.

Records are emitted one per line. A book file is 48 KB at the median, and a
single-line 48 KB diff tells a reviewer that something changed without telling
them what.

Usage:
    scripts/build-artifacts.py            write data/
    scripts/build-artifacts.py --check    fail if data/ is not what this produces
    scripts/build-artifacts.py --dest DIR write somewhere else
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from catholic_bible.canon.aliases import (  # noqa: E402
    Language,
    abbreviation_of,
    name_of,
)

SOURCE = ROOT / "src" / "catholic_bible" / "data"
DEST = ROOT / "data"

REPOSITORY = "ronaldoscotti/catholic-bible"
URL = f"https://cdn.jsdelivr.net/gh/{REPOSITORY}@{{version}}/data/"

VERSIONS = ("matos-soares", "douay-rheims", "vulgata-clementina")
COMMENTARIES = ("haydock",)

LANGUAGES = {"pt-BR": Language.PT, "en-US": Language.EN, "la": Language.LA}

# Copied through with their shape untouched. Renaming versification to spine is
# the one change, because `spine` is the word every document in this repository
# uses and `versification.json` is the exporter's filename.
VERBATIM = {
    "canon.json": "canon.json",
    "spine.json": "versification.json",
    "orphans.json": "derived/orphans.json",
    "coverage.json": "derived/coverage.json",
}


def load(name: str) -> Any:
    return json.loads((SOURCE / name).read_text(encoding="utf-8"))


def document(head: dict[str, Any], key: str, records: Any) -> str:
    """One artifact, with the bulk emitted a record per line.

    `head` is the metadata every file carries. `records` is the dict or list
    that makes the file big.
    """
    parts = [
        f"{json.dumps(name, ensure_ascii=False)}:"
        f"{json.dumps(value, ensure_ascii=False, sort_keys=True)}"
        for name, value in sorted(head.items())
    ]
    opened = "{" + ",".join(parts) + f",{json.dumps(key)}:"

    if isinstance(records, dict):
        body = ",\n".join(
            f"{json.dumps(name, ensure_ascii=False)}:"
            f"{json.dumps(value, ensure_ascii=False, sort_keys=True)}"
            for name, value in records.items()
        )
        return opened + "{\n" + body + "\n}}\n"

    body = ",\n".join(
        json.dumps(value, ensure_ascii=False, sort_keys=True) for value in records
    )
    return opened + "[\n" + body + "\n]}\n"


def book_block(
    code: str, spine: dict[str, list[int]], language: Language
) -> dict[str, Any]:
    canon = CANON_BY_CODE[code]
    return {
        "code": code,
        "name": name_of(code, language),
        "abbreviation": abbreviation_of(code, language),
        "testament": canon["testament"],
        "group": canon["canon_group"],
        "deuterocanonical": canon["deutero"],
        "chapters": len(spine[code]),
    }


CANON = load("canon.json")
CANON_BY_CODE = {record["code"]: record for record in CANON}
BOOKS = tuple(record["code"] for record in CANON)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(dest: Path) -> None:
    spine = load("versification.json")

    for code in VERSIONS:
        raw = load(f"corpus/{code}.json")
        language = LANGUAGES[raw["version"]["language"]]
        grouped: dict[str, dict[str, Any]] = {book: {} for book in BOOKS}
        for verse, record in raw["verses"].items():
            grouped[verse.split(".")[0]][verse] = record
        for book in BOOKS:
            write(
                dest / "versions" / code / "books" / f"{book}.json",
                document(
                    {
                        "version": raw["version"],
                        "book": book_block(book, spine, language),
                    },
                    "verses",
                    grouped[book],
                ),
            )

    for code in COMMENTARIES:
        raw = load(f"commentary/{code}.json")
        entries: dict[str, list[Any]] = {book: [] for book in BOOKS}
        for entry in raw["entries"]:
            entries[entry["start"].split(".")[0]].append(entry)
        for book in BOOKS:
            write(
                dest / "commentary" / code / "books" / f"{book}.json",
                document(
                    {
                        "source": raw["source"],
                        "book": book_block(book, spine, Language.EN),
                    },
                    "entries",
                    entries[book],
                ),
            )

    raw = load("cross-references/references.json")
    anchors: dict[str, dict[str, Any]] = {book: {} for book in BOOKS}
    for anchor, records in raw["references"].items():
        anchors[anchor.split(".")[0]][anchor] = records
    for book in BOOKS:
        # Every source record travels in every file, not only the ones this book
        # happens to draw on. CC BY wants the notice present, and a consumer
        # holding one file should not have to fetch another to learn the terms.
        write(
            dest / "cross-references" / "books" / f"{book}.json",
            document(
                {
                    "sources": raw["sources"],
                    "book": book_block(book, spine, Language.EN),
                },
                "references",
                anchors[book],
            ),
        )

    for published, origin in VERBATIM.items():
        write(
            dest / published,
            json.dumps(load(origin), ensure_ascii=False, indent=1, sort_keys=True)
            + "\n",
        )

    write(dest / "index.json", index(dest))
    write(dest / "manifest.json", manifest(dest))


def index(dest: Path) -> str:
    corpus = load("corpus/PROVENANCE.json")
    entry = {
        "dataset": "catholic-bible",
        # The entry point has to answer the question it poses. `url_pattern`
        # carries a {version} placeholder and a consumer who fetched only this
        # file had no way to fill it in.
        "dataset_version": version(),
        "books": len(BOOKS),
        "book_codes": list(BOOKS),
        "url_pattern": URL + "{path}",
        "manifest": "manifest.json",
        "versions": [
            {
                "code": code,
                **{
                    field: load(f"corpus/{code}.json")["version"][field]
                    for field in ("name", "abbreviation", "language", "rights")
                },
                "books": f"versions/{code}/books/{{book}}.json",
            }
            for code in VERSIONS
        ],
        "commentaries": [
            {
                "code": code,
                **{
                    field: load(f"commentary/{code}.json")["source"][field]
                    for field in ("name", "author", "language", "rights")
                },
                "books": f"commentary/{code}/books/{{book}}.json",
            }
            for code in COMMENTARIES
        ],
        "cross_references": {
            "sources": load("cross-references/references.json")["sources"],
            "books": "cross-references/books/{book}.json",
        },
        "source": corpus["source"],
    }
    return json.dumps(entry, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def manifest(dest: Path) -> str:
    files = {}
    for path in sorted(dest.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        payload = path.read_bytes()
        files[str(path.relative_to(dest))] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
    record = {
        "dataset_version": version(),
        "files": files,
        "source": load("corpus/PROVENANCE.json")["source"],
    }
    return json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def version() -> str:
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split('"')[1]
    raise RuntimeError("pyproject.toml carries no version")


def differences(built: Path, committed: Path) -> list[str]:
    left = {str(p.relative_to(built)) for p in built.rglob("*.json")}
    right = {str(p.relative_to(committed)) for p in committed.rglob("*.json")}
    found = [f"missing: {name}" for name in sorted(left - right)]
    found += [f"not produced: {name}" for name in sorted(right - left)]
    found += [
        f"differs: {name}"
        for name in sorted(left & right)
        if (built / name).read_bytes() != (committed / name).read_bytes()
    ]
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dest", default=None)
    args = parser.parse_args()

    if args.check:
        scratch = DEST.parent / ".artifacts-check"
        shutil.rmtree(scratch, ignore_errors=True)
        build(scratch)
        if not DEST.is_dir():
            print(f"{DEST} is missing. run `make artifacts`")
            return 1
        found = differences(scratch, DEST)
        shutil.rmtree(scratch, ignore_errors=True)
        if found:
            print(f"{DEST} is not what the sources produce. run `make artifacts`")
            for line in found[:20]:
                print(f"  {line}")
            return 1
        print("the committed artifacts match the sources")
        return 0

    dest = Path(args.dest).resolve() if args.dest else DEST
    # Built beside the target and moved into place, because the sources are read
    # lazily as the tree is written. Deleting first and building second meant a
    # missing source left 219 of 371 files on disk and the committed tree gone,
    # which is the state `make artifacts` is supposed to repair.
    scratch = dest.parent / f".{dest.name}-build"
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        build(scratch)
    except Exception:
        shutil.rmtree(scratch, ignore_errors=True)
        raise

    written = sorted(scratch.rglob("*.json"))
    total = sum(path.stat().st_size for path in written)
    shutil.rmtree(dest, ignore_errors=True)
    scratch.rename(dest)
    print(f"wrote {len(written)} files, {total / 1048576:.1f} MB, to {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
