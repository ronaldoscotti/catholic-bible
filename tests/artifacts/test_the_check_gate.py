"""The gate that catches a corpus which moved without the artifacts following.

`openapi.json` has the same gate against the routes. Running the generator into a
scratch directory and comparing is both the determinism claim and the freshness
claim in one build.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "build-artifacts.py"


def generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_artifacts", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_committed_tree_is_what_the_sources_produce() -> None:
    finished = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert finished.returncode == 0, finished.stdout + finished.stderr


def test_the_gate_fails_on_an_edited_verse(tmp_path: Path) -> None:
    """A gate that has never been seen to fail is a gate nobody has tested."""
    module = generator()
    built = tmp_path / "built"
    module.build(built)

    edited = tmp_path / "edited"
    module.build(edited)
    target = edited / "versions" / "matos-soares" / "books" / "GEN.json"
    target.write_text(
        target.read_text(encoding="utf-8").replace("No princípio", "No principio", 1),
        encoding="utf-8",
    )

    assert module.differences(built, edited) == [
        "differs: versions/matos-soares/books/GEN.json"
    ]


def test_a_missing_source_leaves_the_committed_tree_alone(tmp_path: Path) -> None:
    """The plan required this and the first version did the opposite.

    Sources are read lazily as the tree is written, so deleting the destination
    first meant a source that vanished mid-run left 219 of 371 files on disk with
    the committed tree already gone.
    """
    hidden = tmp_path / "haydock.json"
    source = ROOT / "src" / "catholic_bible" / "data" / "commentary" / "haydock.json"
    before = sorted(p.relative_to(ROOT) for p in (ROOT / "data").rglob("*.json"))

    source.rename(hidden)
    try:
        finished = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=ROOT
        )
    finally:
        hidden.rename(source)

    assert finished.returncode != 0
    assert "FileNotFoundError" in finished.stderr
    after = sorted(p.relative_to(ROOT) for p in (ROOT / "data").rglob("*.json"))
    assert after == before
    assert not (ROOT / ".data-build").exists()


def test_the_gate_fails_on_a_missing_file(tmp_path: Path) -> None:
    module = generator()
    built = tmp_path / "built"
    module.build(built)

    short = tmp_path / "short"
    module.build(short)
    (short / "versions" / "matos-soares" / "books" / "TOB.json").unlink()

    assert module.differences(built, short) == [
        "missing: versions/matos-soares/books/TOB.json"
    ]
