"""What the built wheel has to carry, which the type checker does not enforce.

`mypy` runs over `src` and `scripts` in one pass, so it resolves this package
from the source tree and never consults the marker. An installed copy is a
different question and nothing else here asks it.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_the_package_ships_its_type_marker() -> None:
    """PEP 561. Without it a consumer running mypy gets import-untyped.

    Every public function here is annotated and CI checks them, and none of
    that reaches anyone who installs the package unless this file is beside
    the code.
    """
    assert (REPO / "src" / "catholic_bible" / "py.typed").is_file()


def test_the_type_marker_is_inside_the_wheel_package_root() -> None:
    """A marker outside the packaged directory ships nothing.

    Hatchling copies the tree named here, so the assertion is that the marker
    sits under it rather than beside it.
    """
    config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    packages = config["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]

    assert any((REPO / package / "py.typed").is_file() for package in packages), (
        packages
    )


def test_the_type_checker_reads_the_scripts() -> None:
    """`scripts/` holds two CI gates and was outside the checked set until B7.

    A gate the type checker never reads breaks on a rename at the worst moment.
    """
    config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))

    assert "scripts" in config["tool"]["mypy"]["files"]
